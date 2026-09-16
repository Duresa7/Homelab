"""Status-page dashboard: real probe history, explicit gaps, four-nines target."""
from dashlib import Grid, LEGEND_OFF, dashboard, mapping, q, stat, state_timeline, thresholds

STATE_COLORS = thresholds(('gray', None), ('red', 0), ('yellow', 1), ('green', 2))
STATES = mapping({-1: ('Unknown', 'gray'), 0: ('Down', 'red'),
                  1: ('Degraded', 'yellow'), 2: ('Operational', 'green')}, ('Unknown', 'gray'))
SLO = thresholds(('red', None), ('yellow', 99.9), ('green', 99.99))

# Every endpoint in the live HTTP probe inventory, plus the four additions.
HTTP_SERVICES = {
    'aiproxy': 'CLI Proxy API', 'booklore': 'Booklore', 'dashboard': 'Homepage',
    'forgejo': 'Forgejo', 'grafana': 'Grafana', 'immich': 'Immich',
    'jellyfin': 'Jellyfin', 'mcp': 'Executor', 'mesh': 'MeshCentral',
    'netbird': 'NetBird', 'openwebui': 'Open WebUI', 'peanut': 'PeaNUT',
    'prometheus': 'Prometheus', 'prowlarr': 'Prowlarr',
    'qbittorrent': 'qBittorrent', 'radarr': 'Radarr', 'seerr': 'Seerr',
    'semaphore': 'Semaphore', 'sonarr': 'Sonarr', 'splunk': 'Splunk',
    'ts3-manager': 'TS3 Manager', 'wazuh': 'Wazuh',
}


def observed(expr, guard):
    """One scalar-valued series, with unknown explicitly represented as -1."""
    return f'((min({expr})) and on() ({guard})) or vector(-1)'


def http_state(url):
    labels = f'job="blackbox",instance="{url}"'
    success = f'probe_success{{{labels}}}'
    duration = f'probe_duration_seconds{{{labels}}}'
    # 0 failed; 1 responding but slower than two seconds; 2 responding normally.
    expr = f'{success} * (2 - ({duration} > bool 2))'
    guard = f'min(up{{{labels}}}) == 1 and on() min(time() - timestamp({success})) < 90'
    return observed(expr, guard)


def services():
    rows = []
    fresh_ts = ('min(up{job="node",host="alpha-prod-01"}) == 1 and on() '
                'min(time() - teamspeak_last_probe_timestamp_seconds{host="alpha-prod-01"}) < 180')
    for server in ('ts02', 'ts03'):
        selector = f'host="alpha-prod-01",server="{server}"'
        expr = (f'teamspeak_public_up{{{selector}}} * on(server) '
                f'(2 - (teamspeak_public_rtt_seconds{{{selector}}} > bool 0.25))')
        rows.append((f'TeamSpeak {server} · Playit', observed(expr, fresh_ts), 'Internet voice',
                     'Public DNS and UDP handshake through Playit, measured from alpha-prod-01. '
                     'Degraded above 250 ms; unknown when the collector is older than 3 minutes.'))
    fresh_edge = ('min(up{job="node",host="edge-01"}) == 1 and on() '
                  'min(time() - edge_uptime_timestamp_seconds{host="edge-01"}) < 180')
    con = 'edge_uptime_connections{host="edge-01"}'
    cf = observed(f'({con} > bool 0) + ({con} >= bool 4)',
                  f'{fresh_edge} and on() min({con}) >= 0')
    rows.append(('Cloudflare Tunnel', cf, 'Internet ingress',
                 'Connector health on edge-01: four connections operational, one to three degraded, '
                 'zero or a stopped connector down. Unreadable or stale metrics are unknown. This does not test an HTTP application.'))
    for key, name in [('caddy', 'Caddy · edge origin'), ('coolify', 'Coolify · origin')]:
        state = observed(f'edge_uptime_http_up{{host="edge-01",service="{key}"}} * 2', fresh_edge)
        rows.append((name, state, 'Internet ingress',
                     'HTTP response measured from edge-01 at the origin. Cloudflare Access login '
                     'is not treated as proof that the origin is healthy.'))
    for key, name in sorted(HTTP_SERVICES.items(), key=lambda item: item[1].casefold()):
        rows.append((name, http_state(f'https://{key}.alphasecunited.com/'), 'Internal services',
                     'HTTPS response through internal NPM. Degraded above 2 seconds; failed probe is down; '
                     'failed or stale scrape is unknown. Login and expected authorization responses count as reachable.'))
    rows.append(('Discord Alert Bot', http_state('http://alert-bot:8080/health'), 'Internal services',
                 'Health endpoint is successful only while the Discord session is ready.'))
    return rows


def build():
    rows = services()
    g = Grid()
    states = ' or '.join(f'label_replace(({expr}), "service", "{name}", "", "")'
                         for name, expr, _, _ in rows)
    total = len(rows)
    g.add(stat('Current status', [q(f'min({states})', instant=True)], w=15, h=3,
               mappings=mapping({-1: ('Monitoring incomplete', 'gray'), 0: ('Service outage', 'red'),
                                 1: ('Degraded performance', 'yellow'), 2: ('All systems operational', 'green')}),
               thr=STATE_COLORS, color_mode='background_solid', no_value='Unknown'))
    for title, condition, color in [('Down', '== 0', 'red'), ('Degraded', '== 1', 'yellow'),
                                     ('Unknown', '< 0', 'gray')]:
        g.add(stat(title, [q(f'count(({states}) {condition}) or vector(0)', instant=True)],
                   w=3, h=3, decimals=0, thr=thresholds(('green', None), (color, 1))))
    category = None
    for name, expr, group, desc in rows:
        if group != category:
            g.section(group)
            category = group
        g.add(stat(name, [q(expr, instant=True)], w=6, h=3, mappings=STATES,
                   thr=STATE_COLORS, desc=desc, no_value='Unknown'))
        history = state_timeline('Availability history',
                   [q(f'min_over_time(({expr})[$__interval:1m])', name)],
                   w=12, h=3, mappings=STATES, thr=STATE_COLORS, legend=LEGEND_OFF,
                   desc='Each bar shows the worst observed state in its interval. Gray means missing '
                        'or stale monitoring, including time before a probe was installed.', row_height=0.85)
        history['type'] = 'status-history'
        history['maxDataPoints'] = 90
        history['interval'] = '1m'
        history['options'].update({'colWidth': 0.8, 'showValue': 'never'})
        history['fieldConfig']['defaults']['custom']['fillOpacity'] = 100
        g.add(history)
        known = f'(({expr}) >= 0)'
        g.add(stat('Uptime · 99.99% target',
                   [q(f'100 * avg_over_time(({known} > bool 0)[$__range:1m])', instant=True)],
                   w=3, h=3, unit='percent', decimals=4, thr=SLO, no_value='No observations',
                   desc='Successful one-minute observations / known observations over the selected range. '
                        'Degraded responses count as reachable. Unknown time is excluded; check Coverage. '
                        'Sampled availability cannot prove uninterrupted four-nines service.'))
        g.add(stat('Coverage',
                   [q(f'clamp_max(100 * count_over_time({known}[$__range:1m]) / ($__range_s / 60), 100) or vector(0)', instant=True)],
                   w=3, h=3, unit='percent', decimals=2,
                   thr=thresholds(('gray', None), ('yellow', 1), ('green', 99.99)),
                   desc='Known one-minute observations / selected time. Retention is 15 days; '
                        'new probes have no earlier observations.'))
    d = dashboard('uptime', 'Uptime', g, tags=['homelab', 'uptime', 'status'],
                  description=f'{total} service checks. Green operational, amber degraded, red down, gray unknown. '
                              '99.99% sampled uptime target; 15-day retention. Public voice checks traverse Playit; '
                              'Cloudflare measures connector health and separate origins. Grafana remains private.',
                  refresh='1m', time_from='now-14d')
    # Stable IDs make links and visual verification unambiguous.
    for index, panel in enumerate(d['panels'], 1):
        panel['id'] = index
    return d
