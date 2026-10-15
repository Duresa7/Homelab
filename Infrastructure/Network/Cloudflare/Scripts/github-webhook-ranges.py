#!/usr/bin/env python3
"""Keep the Zero Trust IP list of GitHub webhook ranges in step with api.github.com/meta."""
import ipaddress
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.request

GITHUB_META = 'https://api.github.com/meta'
CLOUDFLARE_API = 'https://api.cloudflare.com/client/v4'
LIST_NAME = os.environ.get('LIST_NAME', 'GitHub Webhooks')
DESTINATION = Path(os.environ.get('METRICS_FILE', '/var/lib/prometheus/node-exporter/github-webhook-ranges.prom'))
MINIMUM_RANGES = 3


def fetch(url, method='GET', body=None, headers=None):
    request = urllib.request.Request(url, method=method, headers=headers or {})
    request.add_header('User-Agent', 'edge-01 github-webhook-ranges')
    if body is not None:
        request.add_header('Content-Type', 'application/json')
        body = json.dumps(body).encode()
    with urllib.request.urlopen(request, body, timeout=20) as response:
        return json.loads(response.read(5_000_000).decode())


def github_ranges():
    hooks = fetch(GITHUB_META).get('hooks') or []
    ranges = {str(ipaddress.ip_network(value, strict=False)) for value in hooks}
    # A short or empty answer is a broken response, not a GitHub change.
    if len(ranges) < MINIMUM_RANGES:
        raise RuntimeError(f'GitHub returned {len(ranges)} hook ranges; refusing to sync')
    return ranges


class Cloudflare:
    def __init__(self):
        self.headers = {'Authorization': 'Bearer ' + os.environ['CLOUDFLARE_API_TOKEN']}
        # The token sees exactly one account, so the env file need not name it.
        self.account = os.environ.get('CLOUDFLARE_ACCOUNT_ID') or self.only_account()

    def request(self, method, path, body=None):
        answer = fetch(CLOUDFLARE_API + path, method, body, self.headers)
        if not answer.get('success'):
            raise RuntimeError(f'Cloudflare {method} {path} failed: {answer.get("errors")}')
        return answer['result']

    def only_account(self):
        accounts = self.request('GET', '/accounts')
        if len(accounts) != 1:
            raise RuntimeError(f'token sees {len(accounts)} accounts; set CLOUDFLARE_ACCOUNT_ID')
        return accounts[0]['id']

    def call(self, method, path, body=None):
        return self.request(method, f'/accounts/{self.account}{path}', body)

    def list_id(self):
        for entry in self.call('GET', '/gateway/lists?type=IP'):
            if entry['name'] == LIST_NAME:
                return entry['id']
        raise RuntimeError(f'IP list {LIST_NAME!r} not found')

    def items(self, list_id):
        return {item['value'] for item in self.call('GET', f'/gateway/lists/{list_id}/items')}

    def update(self, list_id, append, remove):
        self.call('PATCH', f'/gateway/lists/{list_id}', {
            'append': [{'value': value} for value in sorted(append)],
            'remove': sorted(remove),
        })


def previous_success():
    try:
        match = re.search(r'^github_webhook_ranges_last_success_timestamp_seconds ([0-9.]+)$',
                          DESTINATION.read_text(), re.M)
        return float(match[1]) if match else 0.0
    except OSError:
        return 0.0


def write_metrics(ok, count, changed, last_success):
    lines = [
        '# TYPE github_webhook_ranges_last_run_ok gauge',
        f'github_webhook_ranges_last_run_ok {int(ok)}',
        '# TYPE github_webhook_ranges_count gauge',
        f'github_webhook_ranges_count {count}',
        '# TYPE github_webhook_ranges_changed gauge',
        f'github_webhook_ranges_changed {int(changed)}',
        '# TYPE github_webhook_ranges_last_success_timestamp_seconds gauge',
        f'github_webhook_ranges_last_success_timestamp_seconds {last_success:.3f}',
        '# TYPE github_webhook_ranges_last_run_timestamp_seconds gauge',
        f'github_webhook_ranges_last_run_timestamp_seconds {time.time():.3f}',
    ]
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    temporary = DESTINATION.with_suffix('.tmp')
    temporary.write_text('\n'.join(lines) + '\n')
    temporary.chmod(0o644)
    os.replace(temporary, DESTINATION)


def sync():
    wanted = github_ranges()
    cloudflare = Cloudflare()
    list_id = cloudflare.list_id()
    current = cloudflare.items(list_id)
    append, remove = wanted - current, current - wanted
    if append or remove:
        print(f'adding {sorted(append)} removing {sorted(remove)}')
        cloudflare.update(list_id, append, remove)
        after = cloudflare.items(list_id)
        if after != wanted:
            raise RuntimeError(f'list holds {sorted(after)} after update, wanted {sorted(wanted)}')
    else:
        print(f'{len(wanted)} ranges, no change')
    return len(wanted), bool(append or remove)


if __name__ == '__main__':
    try:
        count, changed = sync()
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        print(f'sync failed: {error}', file=sys.stderr)
        write_metrics(False, -1, False, previous_success())
        sys.exit(1)
    write_metrics(True, count, changed, time.time())
