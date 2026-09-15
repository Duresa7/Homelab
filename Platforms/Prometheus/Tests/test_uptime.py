#!/usr/bin/env python3
"""Collector failures plus PromQL fixtures for promtool test rules."""
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Tools'))
import uptime
spec = importlib.util.spec_from_file_location('edge', ROOT / 'Scripts/edge-uptime.py')
edge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(edge)


class CollectorTests(unittest.TestCase):
    def test_stopped_connector_is_down(self):
        with patch.object(edge.subprocess, 'run') as run:
            run.return_value.stdout = 'inactive\n'
            self.assertEqual(edge.connections(), 0)

    def test_missing_or_malformed_metrics_are_unknown(self):
        with patch.object(edge.subprocess, 'run') as run:
            run.return_value.stdout = 'active\n'
            for data in [b'', b'cloudflared_tunnel_ha_connections NaN\n',
                         b'cloudflared_tunnel_ha_connections -2\n']:
                with patch.object(edge.urllib.request, 'urlopen', return_value=io.BytesIO(data)):
                    self.assertIsNone(edge.connections())
            with patch.object(edge.urllib.request, 'urlopen', side_effect=OSError):
                self.assertIsNone(edge.connections())

    def test_connections_and_atomic_output(self):
        with patch.object(edge.subprocess, 'run') as run:
            run.return_value.stdout = 'active\n'
            with patch.object(edge.urllib.request, 'urlopen', return_value=io.BytesIO(
                    b'cloudflared_tunnel_ha_connections 4\n')):
                self.assertEqual(edge.connections(), 4)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'edge.prom'
            with patch.object(edge, 'DESTINATION', output), patch.object(edge, 'connections', return_value=None), \
                 patch.object(edge, 'http_up', return_value=0):
                edge.collect()
            self.assertIn('edge_uptime_connections -1', output.read_text())
            self.assertEqual(output.stat().st_mode & 0o777, 0o644)
            self.assertFalse(output.with_suffix('.tmp').exists())


def promql_fixtures():
    tests = []
    def case(name, series, expr, expected):
        tests.append({'name': name, 'interval': '1m',
                      'input_series': [{'series': s, 'values': v} for s, v in series],
                      'promql_expr_test': [{'expr': expr, 'eval_time': '5m',
                                           'exp_samples': [{'labels': '{}', 'value': expected}]}]})
    selector = '{job="blackbox",instance="https://grafana.alphasecunited.com/"}'
    expr = uptime.http_state('https://grafana.alphasecunited.com/')
    for name, success, duration, scrape, value in [
        ('healthy',1,0.1,1,2), ('failed probe',0,0.1,1,0),
        ('slow',1,3,1,1), ('exporter failed',1,0.1,0,-1)]:
        case(name, [('probe_success'+selector, f'{success}+0x5'),
                    ('probe_duration_seconds'+selector, f'{duration}+0x5'),
                    ('up'+selector, f'{scrape}+0x5')], expr, value)
    case('missing series', [], expr, -1)
    case('stale observations', [('probe_success'+selector,'1 1 stale'),
                               ('probe_duration_seconds'+selector,'0.1 0.1 stale'),
                               ('up'+selector,'1+0x5')],expr,-1)
    cf = uptime.services()[2][1]
    for connections, expected in [(4,2),(2,1),(0,0),(-1,-1)]:
        case(f'cloudflare {connections}', [
            ('up{job="node",host="edge-01"}','1+0x5'),
            ('edge_uptime_timestamp_seconds{host="edge-01"}','0+60x5'),
            ('edge_uptime_connections{host="edge-01"}',f'{connections}+0x5')], cf, expected)
    case('stale edge collector', [('up{job="node",host="edge-01"}','1+0x5'),
         ('edge_uptime_timestamp_seconds{host="edge-01"}','0+0x5'),
         ('edge_uptime_connections{host="edge-01"}','4+0x5')], cf,-1)
    ts = uptime.services()[0][1]
    ts_series = [('up{job="node",host="alpha-prod-01"}','1+0x5'),
                 ('teamspeak_last_probe_timestamp_seconds{host="alpha-prod-01"}','0+60x5')]
    ts_labels='{host="alpha-prod-01",server="ts02",relay="fixture-only"}'
    for public, latency, expected in [(1,0.1,2),(1,0.5,1),(0,0,0)]:
        case(f'teamspeak {public} {latency}', ts_series+[
            ('teamspeak_public_up'+ts_labels,f'{public}+0x5'),
            ('teamspeak_public_rtt_seconds'+ts_labels,f'{latency}+0x5')],ts,expected)
    # One failed minute among four observed minutes = 75%; two unknown minutes excluded.
    samples=[('probe_success'+selector,'1 0 1 1 stale'),
             ('probe_duration_seconds'+selector,'0.1+0x5'),
             ('up'+selector,'1 1 1 1 0 0')]
    known=f'(({expr}) >= 0)'
    case('uptime excludes unknown but includes failure',samples,
         f'100 * avg_over_time(({known} > bool 0)[6m:1m])',75)
    case('coverage exposes missing minutes',samples,
         f'100 * count_over_time({known}[6m:1m]) / 6',100*4/6)
    case('history retains brief failure',samples[:2]+[('up'+selector,'1+0x5')],
         f'min_over_time(({expr})[3m:1m] @ 180)',0)
    return {'rule_files': [], 'evaluation_interval':'1m','tests':tests}


if __name__ == '__main__':
    if '--promql-fixtures' in sys.argv:
        print(json.dumps(promql_fixtures(),indent=2))
    else:
        unittest.main()
