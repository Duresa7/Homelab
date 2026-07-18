#!/usr/bin/env python3
"""
ts3_export_channels.py

Exports the channel hierarchy from a TeamSpeak 3 server via the TS3 client's
ClientQuery plugin (the server's ServerQuery does not need to be reachable).

Prerequisites:
  - TS3 client running and connected to the SOURCE server as ServerAdmin
  - ClientQuery plugin enabled (Tools > Options > Addons > ClientQuery > Settings)
  - The API key shown on that ClientQuery settings page

Output:
  - A JSON file (default: channels.json) describing the channel tree.

Usage:
  python ts3_export_channels.py --apikey AAAA-BBBB-CCCC-DDDD --out channels.json
"""

import argparse
import json
import socket
import sys


# --- TeamSpeak protocol escape helpers ------------------------------------
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
    out = []
    for ch in s:
        out.append(_ESC.get(ch, ch))
    return "".join(out)


def ts3_unescape(s: str) -> str:
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            nxt = s[i + 1]
            out.append(_UNESC.get(nxt, nxt))
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


# --- Tiny ServerQuery / ClientQuery client --------------------------------
class TS3Conn:
    def __init__(self, host: str, port: int, timeout: float = 10.0):
        self.s = socket.create_connection((host, port), timeout=timeout)
        self.f = self.s.makefile("rwb", buffering=0)
        # Both ServerQuery and ClientQuery emit a banner on connect.
        # ClientQuery emits 2 lines, ServerQuery emits 2 lines as well.
        self._read_banner()

    def _read_banner(self):
        # Read up to ~5 lines or until a short pause
        self.s.settimeout(2.0)
        try:
            for _ in range(5):
                self.f.readline()
        except (socket.timeout, OSError):
            pass
        self.s.settimeout(10.0)
        # Re-create the file wrapper — a timed-out readline leaves it in a
        # broken state on Python 3.12+, causing all subsequent reads to fail.
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
                        f"TS3 error on `{line}`: id={err.get('id')} msg={err.get('msg')}"
                    )
                break
            # Data line — may contain multiple |-separated records
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


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apikey", required=True, help="ClientQuery API key")
    p.add_argument("--host", default="127.0.0.1", help="ClientQuery host (default 127.0.0.1)")
    p.add_argument("--port", type=int, default=25639, help="ClientQuery port (default 25639)")
    p.add_argument("--out", default="channels.json", help="Output JSON path")
    p.add_argument(
        "--schandlerid",
        type=int,
        default=None,
        help="Server tab handler ID (default: first one). Useful if you have multiple TS3 connections open.",
    )
    args = p.parse_args()

    cq = TS3Conn(args.host, args.port)
    try:
        cq.cmd(f"auth apikey={ts3_escape(args.apikey)}")

        handlers = cq.cmd("serverconnectionhandlerlist")
        if not handlers:
            print("No server tabs open in TS3 client. Connect to the source server first.", file=sys.stderr)
            sys.exit(2)

        target = args.schandlerid or int(handlers[0]["schandlerid"])
        cq.cmd(f"use schandlerid={target}")

        whoami = cq.cmd("whoami")[0]
        print(
            f'Connected on tab {target}: client="{whoami.get("client_nickname")}" '
            f'server="{whoami.get("virtualserver_name", "?")}"',
            file=sys.stderr,
        )

        chans = cq.cmd("channellist -topic -flags -voice -limits -icon -secondsempty")
        print(f"Found {len(chans)} channels — collecting full info…", file=sys.stderr)

        # ClientQuery doesn't expose `channelinfo`, but it does expose
        # `channelvariable cid=X <var> <var> …` for reading individual properties.
        # Variables already covered by `channellist` are skipped.
        EXTRA_VARS = [
            "channel_description",
            "channel_codec_latency_factor",
            "channel_codec_is_unencrypted",
            "channel_delete_delay",
            "channel_flag_maxclients_unlimited",
            "channel_flag_maxfamilyclients_unlimited",
            "channel_flag_maxfamilyclients_inherited",
            "channel_name_phonetic",
            "channel_banner_gfx_url",
            "channel_banner_mode",
        ]

        out = []
        for i, c in enumerate(chans, 1):
            cid = c["cid"]
            # Start with channellist record — that's already most of what we need.
            merged = dict(c)
            try:
                results = cq.cmd(f"channelvariable cid={cid} " + " ".join(EXTRA_VARS))
                for rec in results:
                    for k, v in rec.items():
                        if k in ("cid", "pid"):
                            continue
                        # ClientQuery returns a bare variable name (no `=value`)
                        # for empty values; the parser maps that to True.
                        # Normalize those to empty strings so we don't import
                        # the literal text "True" as a description, etc.
                        if v is True:
                            v = ""
                        merged[k] = v
            except Exception as e:
                print(f"  warn: channelvariable cid={cid} failed: {e}", file=sys.stderr)
            out.append(merged)
            if i % 20 == 0:
                print(f"  …{i}/{len(chans)}", file=sys.stderr)

        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
        print(f"Wrote {len(out)} channels to {args.out}", file=sys.stderr)
    finally:
        cq.close()


if __name__ == "__main__":
    main()
