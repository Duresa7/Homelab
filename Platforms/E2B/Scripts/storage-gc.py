#!/usr/bin/env python3
"""Find (and optionally delete) template build directories no live template needs.

Run as root on e2b-01:   python3 storage-gc.py            # report only
                         python3 storage-gc.py --delete   # remove unreferenced builds

Embed keeps every build's files under /var/lib/e2b/storage/templates/<build id>/
and never removes those of failed or superseded builds. A build is a diff whose
memfile.header and rootfs.ext4.header map data to other builds by ID, so a
directory may be removed only when no live build reaches it.

Live roots: the newest uploaded or successful build of every template, every
build of a template listed in KEEP_ALL_BUILDS_FOR, every build still waiting or
building, and every build a paused sandbox's snapshot points at. From the roots,
the script follows every build ID found inside a header file, recursively.
"""
import os
import shutil
import subprocess
import sys
import uuid

STORE = "/var/lib/e2b/storage/templates"
KEEP_ALL_BUILDS_FOR = ("medsim-",)   # templates another agent owns: never touched


def psql(query):
    out = subprocess.run(["docker", "compose", "exec", "-T", "postgres", "psql", "-U", "postgres", "-At", "-F", "|", "-c", query],
                         cwd="/opt/e2b", capture_output=True, text=True, check=True).stdout
    return [line.split("|") for line in out.splitlines() if line]


def size(path):
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.lstat(os.path.join(root, f)).st_blocks * 512
            except OSError:
                pass
    return total


dirs = {d for d in os.listdir(STORE) if os.path.isdir(os.path.join(STORE, d))}
by_bytes = {}
for d in dirs:
    try:
        by_bytes[uuid.UUID(d).bytes] = d
    except ValueError:
        pass

roots = set()
rows = psql("select b.id, b.env_id, b.status, coalesce(a.alias, ''), b.created_at from env_builds b "
            "left join env_aliases a on a.env_id = b.env_id order by b.created_at")
newest = {}
for bid, env, status, alias, created in rows:
    if status in ("uploaded", "success"):
        newest[env] = bid
    if status in ("waiting", "building"):
        roots.add(bid)
    if alias.startswith(KEEP_ALL_BUILDS_FOR):
        roots.add(bid)
roots |= set(newest.values())
try:
    for (bid,) in psql("select build_id from snapshots"):
        roots.add(bid)
except subprocess.CalledProcessError:
    pass

live, todo = set(), [r for r in roots if r in dirs]
missing_roots = sorted(r for r in roots if r not in dirs)
while todo:
    b = todo.pop()
    if b in live:
        continue
    live.add(b)
    # Headers carry the data mappings; metadata.json and snapfile are scanned too, to stay conservative.
    for name in ("memfile.header", "rootfs.ext4.header", "metadata.json", "snapfile"):
        p = os.path.join(STORE, b, name)
        if not os.path.exists(p):
            continue
        data = open(p, "rb").read()
        for raw, d in by_bytes.items():
            if d not in live and (raw in data or d.encode() in data):
                todo.append(d)

dead = sorted(dirs - live)
live_size = sum(size(os.path.join(STORE, d)) for d in live)
dead_size = sum(size(os.path.join(STORE, d)) for d in dead)
print(f"build dirs: {len(dirs)}; roots: {len(roots)} ({len(missing_roots)} without a directory: {[m[:8] for m in missing_roots]})")
print(f"live: {len(live)} dirs, {live_size / 2**30:.1f} GiB")
print(f"unreferenced: {len(dead)} dirs, {dead_size / 2**30:.1f} GiB")

if "--delete" in sys.argv:
    busy = [r for r in psql("select id from env_builds where status in ('waiting', 'building')")]
    if busy:
        sys.exit(f"refusing to delete: {len(busy)} build(s) waiting or building, whose layers may not be referenced yet")
    for d in dead:
        shutil.rmtree(os.path.join(STORE, d))
    print(f"deleted {len(dead)} dirs")
