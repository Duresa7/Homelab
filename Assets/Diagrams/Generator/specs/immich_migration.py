#!/usr/bin/env python3
"""immich-migration: the 2026-05-28 move of LXC 110's /data from the WD-backed
ZFS pool to the Toshiba-backed one on grey-server (restyle of the 2026-07-20
diagram; a dated event, so the chip and every figure stay at 2026-05-28).
Facts: Platforms/Immich/Documentation/Change Records/Storage Migration from
WD Red Plus to Toshiba - 2026-05-28.md (layout, sizes, commands, checks),
Guides/Immich-Storage-Migration.md (the walkthrough of the same record)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from diagram import Diagram

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "immich-migration.svg")
d = Diagram("immich-migration", "Immich storage migration: WD Red Plus to Toshiba",
            "2026-05-28 on grey-server: LXC 110 docker-main's /data moved from ZFS pool hddpool (WD 4 TB) to hddpool-1 (Toshiba 2 TB) with Immich v2.7.5 stopped, verified, then the WD retired",
            state="State as of 2026-05-28",
            source="Platforms/Immich/Documentation/Change Records/Storage Migration from WD Red Plus to Toshiba - 2026-05-28.md, Guides/Immich-Storage-Migration.md",
            width=1640, row_gap=64)

# --- row 0: what lived on the pool ------------------------------------------------------
d.group("lxc", "LXC 110 docker-main · grey-server · Immich v2.7.5", badge="mp0 mounted at /data", family="Mgmt", accent="grey")
d.card("lxc", "server", "immich_server", sub1=":2283 · uploads at /data/immich/library", sub2="holds library, upload, profile, thumbs", logo="immich")
d.card("lxc", "pg", "immich_postgres", sub1="DB_DATA_LOCATION /data/immich/postgres", sub2="albums, faces, tags, favorites, links", logo="postgresql")
d.card("lxc", "ml", "immich_machine_learning", sub1="inference", sub2="no data of its own", logo="glyph:ML")
d.card("lxc", "redis", "immich_redis", sub1="cache", sub2="no data of its own", logo="redis")
d.card("lxc", "forgejo", "forgejo", sub1="2.6 MB, two repositories", sub2="moved to NVMe: /opt/docker/forgejo/data", logo="forgejo")

# --- row 1: the two pools and the rollback point -------------------------------------------
d.group("src", "hddpool · WD Red Plus 4 TB", badge="source · destroyed after", family="Dmz", notes=[
    (None, "WDC WD40EFPX-68C6CN0, single-disk ZFS pool. It also held stale calibre and"),
    (None, "Nextcloud leftovers and three empty datasets, all removed before the copy.")])
d.card("src", "old", "subvol-110-disk-0, source", sub1="Immich 1.9 TB before the purge, 825 GB after", sub2="kept mounted until every check below passed", logo="western-digital")
d.group("dst", "hddpool-1 · Toshiba 2 TB", badge="destination · ONLINE", family="Servers", notes=[
    (None, "Toshiba DT01ACA200 with prior use: SMART PASSED, zero reallocated, pending"),
    (None, "or CRC errors, but high power-on hours, so the WD copy stayed until verified.")])
d.card("dst", "new", "subvol-110-disk-0, destination", sub1="886 GB across about 32,000 files", sub2="about 132 MB/s, finished in under two hours", logo="toshiba")
d.group("dump", "Rollback point", family="Observability")
d.card("dump", "backup", "Database dump", sub1="manual job, Administration > Job Queues", sub2="40 MB gz, 103 MB raw; copied off the node", logo="postgresql")

# --- row 2: the sequence, the checks, the end state -----------------------------------------
d.group("seq", "The sequence", badge="2026-05-28", family="Internal", notes=[
    (None, "1 · map every guest and bind mount that used hddpool: LXC 110 /data; immich_server, immich_postgres, forgejo"),
    (None, "2 · move Forgejo to NVMe; delete the stale leftovers and the three empty datasets"),
    (None, "3 · fresh database dump, gzip and header/footer checked, copied off grey-server"),
    (None, "4 · wipe the Toshiba, GPT label, create hddpool-1 in the Proxmox UI by persistent device path"),
    (None, "5 · docker compose down; delete encoded-video only, 1.9 TB to 825 GB; thumbs kept"),
    (None, "6 · stop LXC 110; pct move-volume 110 mp0 hddpool-1 without the delete flag"),
    (None, "7 · start the LXC and Immich; run the checks"),
    (None, "8 · zfs destroy, zpool destroy, pvesm remove; rebuild the transcode cache; pull the WD")])
d.group("verify", "Checks before the WD was touched", family="Observability", notes=[
    (None, "/data mounted from hddpool-1, Immich directories present"),
    (None, "server, postgres, machine learning and redis healthy"),
    (None, "2283 listening, web UI HTTP 200"),
    (None, "timeline loads; album covers and named people present"),
    (None, "full-resolution photos open; videos play")])
d.group("after", "Storage after", family="External", notes=[
    (None, "Immich on hddpool-1, 825 GB dataset"),
    (None, "Forgejo on local NVMe"),
    (None, "database backup off grey-server"),
    (None, "WD removed for reuse elsewhere"),
    (None, "!hddpool-1 is one disk, no redundancy")])

d.row("lxc")
d.row("src", "dump", "dst")
d.row("seq", "verify", "after")

def align(src, dst):
    d._layout(); s, t = d.items[src], d.items[dst]
    return (t.x + t.w / 2) - (s.x + s.w / 2)

d.edge("lxc", "src", "mp0 /data until step 6", style="dashed", color="grey", s_off=align("lxc", "src"))
d.edge("lxc", "dst", "mp0 /data after the move", color="blue", s_off=align("lxc", "dst"))
d.edge("pg", "backup", "manual backup job, verified", color="green", y="gap:0:+14", label_seg=1, label_x="mid:backup:-150")
d.edge("old", "new", "pct move-volume 110 mp0 hddpool-1 · 886 GB, 32,000 files, 132 MB/s", color="orange",
       from_side="bottom", to_side="bottom", y="gap:1", label_seg=1, label_x="between:src,dst")

d.legend_family("Mgmt", "the LXC on grey-server"); d.legend_family("Dmz", "source pool, retired"); d.legend_family("Servers", "destination pool")
d.legend_family("Observability", "rollback point and checks"); d.legend_family("Internal", "the sequence"); d.legend_family("External", "end state")
d.legend_edge("bind mount before", "dashed", "grey"); d.legend_edge("bind mount after", "solid", "blue"); d.legend_edge("the volume move", "solid", "orange"); d.legend_edge("database dump", "solid", "green")
d.footnote("Database dumps hold metadata only and must be paired with the files; thumbs and encoded-video are regenerable, library, upload, profile and the PostgreSQL directory are not. The record keeps no transcript or screenshots.")
d.footnote("On 2026-09-24 Immich ran v3.2.2 on the same LXC with the library still on hddpool-1.")
d.render(OUT, png=os.environ.get("PNG") == "1", readme_width=int(os.environ.get("README_W", "0")) or None)
