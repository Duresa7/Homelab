#!/usr/bin/env python3
"""
ts3_import_channels.py

Re-creates a channel hierarchy (exported by ts3_export_channels.py) onto a
target TeamSpeak 3 server via ServerQuery.

Usage:
  python ts3_import_channels.py \
      --in channels.json \
      --host 192.168.80.118 --port 10012 \
      --user serveradmin --password 'YOUR_QUERY_PASSWORD' \
      --sid 1

Add --dry-run to preview without making changes.
Add --skip-existing to skip channels with the same name+parent already present.
"""

import argparse
import json
import socket
import sys


# --- escape helpers (same as exporter) ------------------------------------
_ESC = {
    "\\": r"\\",
    "/": r"\/",
    " ": r"\s",
    "|": r"\p",
    "\a": r"\a",
    "\b": r"\b",
    "\f": r"\f",
    "\n": r"\n",
    "\r": r"\r",
    "\t": r"\t",
    "\v": r"\v",
}
_UNESC = {
    "\\": "\\",
    "/": "/",
    "s": " ",
    "p": "|",
    "a": "\a",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "v": "\v",
}


def ts3_escape(s: str) -> str:
    return "".join(_ESC.get(c, c) for c in s)


def ts3_unescape(s: str) -> str:
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            out.append(_UNESC.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


# --- ServerQuery client ---------------------------------------------------
class TS3Conn:
    def __init__(self, host: str, port: int, timeout: float = 10.0):
        self.s = socket.create_connection((host, port), timeout=timeout)
        self.f = self.s.makefile("rwb", buffering=0)
        self._read_banner()

    def _read_banner(self):
        self.s.settimeout(2.0)
        try:
            for _ in range(5):
                self.f.readline()
        except (socket.timeout, OSError):
            pass
        self.s.settimeout(15.0)
        self.f = self.s.makefile("rwb", buffering=0)

    def _send(self, line: str):
        self.f.write((line + "\n").encode("utf-8"))

    def cmd(self, line: str):
        self._send(line)
        records = []
        while True:
            raw = self.f.readline()
            if not raw:
                raise ConnectionError("Connection closed by server")
            text = raw.decode("utf-8", errors="replace").strip()
            if not text:
                continue
            if text.startswith("error "):
                err = self._parse_record(text[len("error "):])
                if err.get("id") != "0":
                    raise RuntimeError(
                        f"TS3 error on `{line}`: id={err.get('id')} msg={err.get('msg')} extra_msg={err.get('extra_msg', '')}"
                    )
                break
            for piece in text.split("|"):
                records.append(self._parse_record(piece))
        return records

    @staticmethod
    def _parse_record(piece: str) -> dict:
        d = {}
        for tok in piece.split():
            if "=" in tok:
                k, v = tok.split("=", 1)
                d[k] = ts3_unescape(v)
            else:
                d[tok] = True
        return d

    def close(self):
        try:
            self._send("quit")
        except Exception:
            pass
        try:
            self.s.close()
        except Exception:
            pass


# Properties safe to copy onto a fresh channelcreate.
# Channel passwords cannot be exported (TS3 hashes them), so we drop them.
# `channel_delete_delay` and `channel_icon_id` are rejected on creation by
# this TS3 server build (id=1538 invalid parameter), regardless of value;
# apply them post-create via `channeledit` if needed.
COPY_PROPS = [
    "channel_name",
    "channel_topic",
    "channel_description",
    "channel_codec",
    "channel_codec_quality",
    "channel_maxclients",
    "channel_maxfamilyclients",
    "channel_flag_permanent",
    "channel_flag_semi_permanent",
    "channel_flag_default",
    # channel_codec_latency_factor — deprecated in TS3 3.x+, removed.
    # channel_codec_is_unencrypted — deprecated in TS3 3.x+, removed.
    "channel_flag_maxclients_unlimited",
    "channel_flag_maxfamilyclients_unlimited",
    "channel_flag_maxfamilyclients_inherited",
    "channel_needed_talk_power",
    "channel_name_phonetic",
    "channel_banner_gfx_url",
    "channel_banner_mode",
]


def channel_depth(by_id, cid):
    d = 0
    cur = by_id.get(cid)
    while cur and cur.get("pid", "0") != "0":
        cur = by_id.get(cur["pid"])
        d += 1
        if d > 100:  # safety
            break
    return d


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--in", dest="infile", required=True)
    p.add_argument("--host", default="192.168.80.118")
    p.add_argument("--port", type=int, default=10012)
    p.add_argument("--sid", type=int, default=1)
    p.add_argument("--user", default="serveradmin")
    p.add_argument("--password", required=True)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip channels whose (name + parent) already exists on the target.",
    )
    args = p.parse_args()

    with open(args.infile, encoding="utf-8") as f:
        channels = json.load(f)

    by_id = {c["cid"]: c for c in channels}
    # Sort: parents before children, then by source channel_order
    channels_sorted = sorted(
        channels,
        key=lambda c: (
            channel_depth(by_id, c["cid"]),
            int(c.get("channel_order", "0") or 0),
        ),
    )

    sq = TS3Conn(args.host, args.port)
    try:
        sq.cmd(f"login {ts3_escape(args.user)} {ts3_escape(args.password)}")
        sq.cmd(f"use sid={args.sid}")
        me = sq.cmd("whoami")[0]
        print(
            f'Logged into virtual server "{me.get("virtualserver_name", "?")}" '
            f'as {me.get("client_login_name", args.user)}',
            file=sys.stderr,
        )

        # Existing channels (for --skip-existing)
        existing = {}
        if args.skip_existing:
            for c in sq.cmd("channellist"):
                existing[(c.get("channel_name"), c.get("pid", "0"))] = c["cid"]

        old_to_new = {"0": "0"}
        created = 0
        skipped = 0
        failed = 0

        for ch in channels_sorted:
            old_cid = ch["cid"]
            old_pid = ch.get("pid", "0")
            new_pid = old_to_new.get(old_pid, "0")

            name = ch.get("channel_name", "")
            if not name:
                print(f"  skip: channel cid={old_cid} has no name", file=sys.stderr)
                continue

            if args.skip_existing and (name, new_pid) in existing:
                old_to_new[old_cid] = existing[(name, new_pid)]
                print(f"  skip-existing: {name!r} under parent {new_pid}", file=sys.stderr)
                skipped += 1
                continue

            parts = ["channelcreate"]
            for k in COPY_PROPS:
                v = ch.get(k)
                if v is None or v == "" or v is True:
                    continue
                # TS3 ServerQuery rejects channel_maxclients=-1; use the
                # unlimited flag instead. Skip the numeric field when the
                # companion flag is already set or the value is -1.
                if k == "channel_maxclients" and (
                    str(v) == "-1"
                    or ch.get("channel_flag_maxclients_unlimited") in ("1", True)
                ):
                    continue
                if k == "channel_maxfamilyclients" and (
                    str(v) == "-1"
                    or ch.get("channel_flag_maxfamilyclients_unlimited") in ("1", True)
                    or ch.get("channel_flag_maxfamilyclients_inherited") in ("1", True)
                ):
                    continue
                # Custom icon IDs (nonzero) reference icons that don't exist
                # on the target server — skip them to avoid convert errors.
                if k == "channel_icon_id" and str(v) != "0":
                    continue
                parts.append(f"{k}={ts3_escape(str(v))}")
            parts.append(f"cpid={new_pid}")
            cmd = " ".join(parts)

            if args.dry_run:
                print(
                    f"WOULD create: name={name!r} parent={new_pid} "
                    f"perm={ch.get('channel_flag_permanent','?')} codec={ch.get('channel_codec','?')}"
                )
                old_to_new[old_cid] = f"<dry-{old_cid}>"
                created += 1
                continue

            try:
                result = sq.cmd(cmd)
                new_cid = result[0]["cid"]
                old_to_new[old_cid] = new_cid
                print(f"  + {name!r} (old={old_cid} -> new={new_cid}, parent={new_pid})")
                created += 1
            except Exception as e:
                print(f"  ! FAILED {name!r}: {e}", file=sys.stderr)
                failed += 1

        print(
            f"\nDone. created={created} skipped={skipped} failed={failed}",
            file=sys.stderr,
        )
    finally:
        sq.close()


if __name__ == "__main__":
    main()
