#!/usr/bin/env python3
"""Export local tunnel/origin health without publishing tunnel identifiers."""
import math
import os
from pathlib import Path
import re
import subprocess
import time
import urllib.error
import urllib.request

DESTINATION = Path('/var/lib/prometheus/node-exporter/edge-uptime.prom')


def connections():
    # Distinguish a stopped connector from a broken monitoring endpoint.
    status = subprocess.run(['systemctl', 'is-active', 'cloudflared.service'],
                            capture_output=True, text=True, timeout=5)
    if status.stdout.strip() in ('inactive', 'failed'):
        return 0
    try:
        with urllib.request.urlopen('http://127.0.0.1:20241/metrics', timeout=5) as response:
            data = response.read(2_000_000).decode()
        match = re.search(r'^cloudflared_tunnel_ha_connections ([0-9.eE+\-]+)$', data, re.M)
        value = float(match[1]) if match else float('nan')
        return value if math.isfinite(value) and value >= 0 else None
    except (OSError, ValueError):
        return None


def http_up(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return int(200 <= response.status < 400)
    except (OSError, ValueError):
        return 0


def collect():
    count = connections()
    # A stopped/unreachable metrics endpoint is unknown, not a claimed tunnel outage.
    lines = [
        '# TYPE edge_uptime_connections gauge',
        f'edge_uptime_connections {count if count is not None else -1}',
        '# TYPE edge_uptime_http_up gauge',
        f'edge_uptime_http_up{{service="caddy"}} {http_up("http://127.0.0.1:80/")}',
        f'edge_uptime_http_up{{service="coolify"}} {http_up("http://192.168.80.10:8000/")}',
        '# TYPE edge_uptime_timestamp_seconds gauge',
        f'edge_uptime_timestamp_seconds {time.time():.3f}',
    ]
    temporary = DESTINATION.with_suffix('.tmp')
    temporary.write_text('\n'.join(lines) + '\n')
    temporary.chmod(0o644)
    os.replace(temporary, DESTINATION)


if __name__ == '__main__':
    collect()
