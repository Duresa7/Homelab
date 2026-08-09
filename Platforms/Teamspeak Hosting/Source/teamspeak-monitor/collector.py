#!/usr/bin/env python3
"""Export TeamSpeak reachability metrics for node_exporter's textfile collector.

Each cycle probes every voice server twice: once at the public address a user
types, and once at its local UDP port on the Docker host. The pair is the whole
point. Local up with public down means the Playit tunnel or DNS broke, not
TeamSpeak. Local down means the server itself is the problem.

The probe sends a real TeamSpeak 3 Init1 step-0 packet, so a pass means the
voice service answered rather than a port merely being open.

The public port is read from the live SRV record every cycle, so a Playit port
rotation follows DNS instead of needing an edit here.

ServerQuery metrics appear only when credentials are supplied. Each instance
keeps its own serveradmin account, so the passwords differ: set
TS_QUERY_PASS_TS02 and TS_QUERY_PASS_TS03, or a single TS_QUERY_PASS if they
are ever unified.

Publication note: BASE_DOMAIN comes from the environment. The deployed Compose
file carries the real internal domain; the repository copy carries a placeholder.
"""
import os
import re
import socket
import struct
import subprocess
import sys
import tempfile
import time

BASE_DOMAIN = os.environ.get("TS_BASE_DOMAIN", "example.com")
OUT = os.environ.get("TS_OUT", "/textfile/teamspeak.prom")
INTERVAL = int(os.environ.get("TS_INTERVAL", "60"))
TIMEOUT = float(os.environ.get("TS_TIMEOUT", "4"))
HOST_IP = os.environ.get("TS_HOST_IP", "172.17.0.1")

# name, host voice port, host ServerQuery port
SERVERS = [
    ("ts02", 9988, 10012),
    ("ts03", 9989, 10013),
]

HEADERS = [
    ("teamspeak_local_up", "gauge", "TS3 voice answered on the host's local UDP port."),
    ("teamspeak_local_rtt_seconds", "gauge", "Round trip of the local TS3 handshake."),
    ("teamspeak_public_up", "gauge", "TS3 voice answered at the public address users connect to."),
    ("teamspeak_public_rtt_seconds", "gauge", "Round trip of the public TS3 handshake via the Playit relay."),
    ("teamspeak_dns_srv_up", "gauge", "The _ts3._udp SRV record resolved to a host and port."),
    ("teamspeak_tunnel_fault", "gauge", "Local voice is up but the public address is not, so the tunnel or DNS is at fault."),
    ("teamspeak_server_fault", "gauge", "The local voice service itself is not answering."),
    ("teamspeak_query_up", "gauge", "ServerQuery login succeeded and serverinfo returned."),
    ("teamspeak_clients_online", "gauge", "Clients connected, from ServerQuery."),
    ("teamspeak_channels_online", "gauge", "Channels present, from ServerQuery."),
    ("teamspeak_uptime_seconds", "gauge", "Virtual server uptime, from ServerQuery."),
    ("teamspeak_max_clients", "gauge", "Configured client slots, from ServerQuery."),
    ("teamspeak_probe_duration_seconds", "gauge", "Wall time of one full collection."),
    ("teamspeak_last_probe_timestamp_seconds", "gauge", "Unix time of the last completed collection."),
]


def init1_step0():
    """Low-level TS3 Init1 step 0. A server replies with MAC TS3INIT1."""
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


def voice_probe(ip, port):
    """Return (ok, rtt_seconds). ok is True only on a valid TS3INIT1 reply."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(TIMEOUT)
    start = time.monotonic()
    try:
        s.sendto(init1_step0(), (ip, port))
        data, _ = s.recvfrom(1024)
    except OSError:
        return False, 0.0
    finally:
        s.close()
    return data[:8] == b"TS3INIT1", time.monotonic() - start


def srv_lookup(name):
    """Resolve _ts3._udp.<name>.<domain> to (host, port), or (None, None)."""
    fqdn = f"_ts3._udp.{name}.{BASE_DOMAIN}"
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


def query_credentials(name):
    """Per-server ServerQuery credentials.

    Each TeamSpeak instance keeps its own serveradmin account, so the passwords
    differ even though the login name matches. TS_QUERY_PASS_<NAME> wins;
    TS_QUERY_PASS is the fallback for a single shared value.
    """
    suffix = name.upper()
    user = os.environ.get(f"TS_QUERY_USER_{suffix}") or os.environ.get("TS_QUERY_USER")
    password = os.environ.get(f"TS_QUERY_PASS_{suffix}") or os.environ.get("TS_QUERY_PASS")
    return user, password


def query_stats(port, user, password):
    """Pull serverinfo over ServerQuery. Returns {} on any failure."""
    try:
        s = socket.create_connection((HOST_IP, port), timeout=TIMEOUT)
    except OSError:
        return {}
    out = {}
    try:
        s.settimeout(TIMEOUT)
        s.recv(4096)
        s.sendall(
            f"login client_login_name={user} client_login_password={password}\n".encode()
        )
        time.sleep(0.3)
        if "error id=0" not in s.recv(65535).decode("utf-8", "replace"):
            return {}
        s.sendall(b"use sid=1\n")
        time.sleep(0.3)
        s.recv(65535)
        s.sendall(b"serverinfo\n")
        time.sleep(0.4)
        reply = s.recv(65535).decode("utf-8", "replace")
        for key, metric in (
            ("virtualserver_clientsonline", "clients_online"),
            ("virtualserver_channelsonline", "channels_online"),
            ("virtualserver_uptime", "uptime_seconds"),
            ("virtualserver_maxclients", "max_clients"),
        ):
            m = re.search(rf"\b{key}=(\d+)", reply)
            if m:
                out[metric] = int(m.group(1))
        s.sendall(b"quit\n")
    except OSError:
        return {}
    finally:
        s.close()
    return out


def collect():
    started = time.monotonic()
    L = []
    for metric, kind, help_text in HEADERS:
        L.append(f"# HELP {metric} {help_text}")
        L.append(f"# TYPE {metric} {kind}")

    for name, vport, qport in SERVERS:
        address = f"{name}.{BASE_DOMAIN}"
        base = f'server="{name}",address="{address}"'

        lok, lrtt = voice_probe(HOST_IP, vport)
        L.append(f'teamspeak_local_up{{{base},port="{vport}"}} {int(lok)}')
        L.append(f'teamspeak_local_rtt_seconds{{{base},port="{vport}"}} {lrtt:.6f}')

        host, pport = srv_lookup(name)
        L.append(f"teamspeak_dns_srv_up{{{base}}} {0 if host is None else 1}")

        pok, prtt = False, 0.0
        if host:
            try:
                pok, prtt = voice_probe(socket.gethostbyname(host), pport)
            except OSError:
                pok = False
        relay = f'{base},relay="{host or "unresolved"}:{pport or 0}"'
        L.append(f"teamspeak_public_up{{{relay}}} {int(pok)}")
        L.append(f"teamspeak_public_rtt_seconds{{{relay}}} {prtt:.6f}")
        L.append(f"teamspeak_tunnel_fault{{{base}}} {int(lok and not pok)}")
        L.append(f"teamspeak_server_fault{{{base}}} {int(not lok)}")

        quser, qpass = query_credentials(name)
        if quser and qpass:
            stats = query_stats(qport, quser, qpass)
            L.append(f"teamspeak_query_up{{{base}}} {int(bool(stats))}")
            for metric, value in stats.items():
                L.append(f"teamspeak_{metric}{{{base}}} {value}")

    L.append(f"teamspeak_probe_duration_seconds {time.monotonic() - started:.6f}")
    L.append(f"teamspeak_last_probe_timestamp_seconds {int(time.time())}")

    body = "\n".join(L) + "\n"
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(OUT), prefix=".teamspeak-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(body)
        os.chmod(tmp, 0o644)
        os.replace(tmp, OUT)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return body


if __name__ == "__main__":
    once = "--once" in sys.argv
    while True:
        try:
            body = collect()
            if once:
                sys.stdout.write(body)
                break
        except Exception as exc:  # keep the loop alive; a stale file is visible via the timestamp
            print(f"collect failed: {exc}", file=sys.stderr, flush=True)
            if once:
                sys.exit(1)
        time.sleep(INTERVAL)
