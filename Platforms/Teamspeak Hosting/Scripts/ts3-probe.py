#!/usr/bin/env python3
"""Probe TeamSpeak voice endpoints with a real TS3 Init1 handshake.

A pass requires a reply whose MAC is TS3INIT1, so it proves the voice service
answered rather than a port merely being open. blackbox_exporter cannot do this:
it has no UDP prober.

Use it to answer "is the address my users type actually up" from any host with
outbound UDP, and to compare that against the local port on the Docker host.

    ./ts3-probe.py --public ts02 ts03 --domain example.com
    ./ts3-probe.py --local 9988 9989
    ./ts3-probe.py --host 192.168.80.118 --local 9988

Exit code is 0 when every probed endpoint answered, 1 otherwise, so it also
works as a check in a pipeline.
"""
import argparse
import os
import re
import socket
import struct
import subprocess
import sys
import time

TIMEOUT = 4.0


def init1_step0():
    """Low-level TS3 Init1 step 0. A live server replies with MAC TS3INIT1."""
    return (
        b"TS3INIT1"
        + struct.pack(">H", 101)
        + struct.pack(">H", 0)
        + bytes([0x88])
        + bytes([0x09, 0x83, 0x8C, 0xCF])
        + bytes([0x00])
        + struct.pack(">I", int(time.time()))
        + os.urandom(4)
        + b"\x00" * 8
    )


def probe(ip, port, timeout=TIMEOUT):
    """Return (ok, rtt_ms). ok is True only on a valid TS3INIT1 reply."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    start = time.monotonic()
    try:
        s.sendto(init1_step0(), (ip, port))
        data, _ = s.recvfrom(1024)
    except OSError:
        return False, 0.0
    finally:
        s.close()
    return data[:8] == b"TS3INIT1", (time.monotonic() - start) * 1000


def srv_lookup(name, domain):
    """Resolve _ts3._udp.<name>.<domain> to (host, port)."""
    fqdn = f"_ts3._udp.{name}.{domain}"
    try:
        out = subprocess.run(
            ["dig", "+short", "+time=3", "+tries=1", "SRV", fqdn],
            capture_output=True, text=True, timeout=8,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None, None
    if not out:
        return None, None
    m = re.match(r"^\d+\s+\d+\s+(\d+)\s+(\S+?)\.?$", out.splitlines()[0])
    return (m.group(2), int(m.group(1))) if m else (None, None)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--public", nargs="*", metavar="NAME",
                    help="server short names to resolve via their _ts3._udp SRV record")
    ap.add_argument("--local", nargs="*", type=int, metavar="PORT",
                    help="local UDP voice ports to probe directly")
    ap.add_argument("--domain", default=os.environ.get("TS_BASE_DOMAIN", ""),
                    help="base domain for --public (or set TS_BASE_DOMAIN)")
    ap.add_argument("--host", default="127.0.0.1", help="host for --local probes")
    ap.add_argument("--timeout", type=float, default=TIMEOUT)
    args = ap.parse_args()

    if not args.public and not args.local:
        ap.error("give --public and/or --local")
    if args.public and not args.domain:
        ap.error("--public needs --domain or TS_BASE_DOMAIN")

    failures = 0

    for name in args.public or []:
        host, port = srv_lookup(name, args.domain)
        if not host:
            print(f"{name:6s} SRV lookup FAILED for _ts3._udp.{name}.{args.domain}")
            failures += 1
            continue
        try:
            ip = socket.gethostbyname(host)
        except OSError as exc:
            print(f"{name:6s} {host}:{port} DNS failed: {exc}")
            failures += 1
            continue
        ok, ms = probe(ip, port, args.timeout)
        print(f"{name:6s} {host}:{port} ip={ip} -> "
              f"{'OK' if ok else 'NO RESPONSE'}{f' rtt={ms:.1f}ms' if ok else ''}")
        failures += 0 if ok else 1

    for port in args.local or []:
        ok, ms = probe(args.host, port, args.timeout)
        print(f"local  {args.host}:{port} -> "
              f"{'OK' if ok else 'NO RESPONSE'}{f' rtt={ms:.2f}ms' if ok else ''}")
        failures += 0 if ok else 1

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
