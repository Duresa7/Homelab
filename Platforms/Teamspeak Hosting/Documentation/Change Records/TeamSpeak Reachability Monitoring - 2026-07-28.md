# TeamSpeak Reachability Monitoring

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Date:** 2026-07-28  
**Scope:** Monitor the three TeamSpeak voice servers from the address my users actually connect to, and separate a local server fault from a Playit tunnel or DNS fault.

## What I wanted

Two things my existing monitoring couldn't tell me. First, whether `ts01`, `ts02`, and `ts03` are reachable at their public names rather than just running on the host. Second, when they're unreachable, whether the problem is my TeamSpeak server or the Playit tunnel in front of it.

## Why blackbox_exporter couldn't do it

`blackbox_exporter` has http, tcp, icmp, dns, and grpc probers. It has no UDP prober. TeamSpeak voice is UDP 9987 through 9989 published as UDP Playit tunnels, so no blackbox module can test the path a user takes. My 18 existing blackbox probes all reach HTTP services through NPM, which is why they work.

A TCP probe against a Playit relay proves nothing either, because those tunnels are UDP.

## Why the collector runs on alpha-prod-01

I measured this before choosing. From `alpha-prod-01` all three public endpoints answered a TeamSpeak handshake in 44 to 46 ms. From `monitor-01` all three timed out, because the observability egress policy allows approved web and NTP only and blocks everything else outbound.

I could have opened a hole from MONITOR-A to the relays. I decided against it for two reasons. Playit is a public NAT-traversal broker, and MONITOR-A shares the `<YOUR_ORG_NAME>`-Observability zone with `security-01` and `splunk-siem`, so that exception would undercut the exact rule that keeps my SIEM segment from calling out. The relay addresses also aren't stable: `ts01` and `ts02` currently share `147.185.221.224` while `ts03` uses `147.185.221.180`, and the whole reason those names are CNAME and SRV records is that the addresses behind them move. A rule pinned to an IP would fail on Playit's schedule and blame the wrong component.

Running on `alpha-prod-01` costs no firewall change. Prometheus already scrapes `192.168.80.118:9100`, and the probe still leaves the network for Playit's relay and comes back, so it exercises the real external path.

## What I built

A container at `/home/dkadi/teamspeak-monitor` writing a Prometheus textfile into `/var/lib/prometheus/node-exporter/`, which the host's `prometheus-node-exporter` already publishes on 9100. Source is versioned at [Source/teamspeak-monitor](../../Source/teamspeak-monitor/).

The probe is a real TeamSpeak 3 `Init1` step-0 packet and a pass requires a reply whose MAC is `TS3INIT1`. That means the voice service answered, not that a port happened to be open.

Each 60-second cycle does three things per server:

1. Reads the live `_ts3._udp` SRV record, so a Playit port rotation follows DNS instead of needing an edit here.
2. Probes the public relay host and port from that record.
3. Probes the same server's local UDP port on the host.

Then it derives the fault location: `teamspeak_tunnel_fault` is 1 when local is up but public is down, and `teamspeak_server_fault` is 1 when local is down.

`network_mode: host` lets it see the local voice and ServerQuery ports exactly as a local client does. It runs as root inside the container so it can write the collector directory, which is why the compose file mounts only that one path.

I used Docker rather than a systemd timer because `dkadi` can't `sudo` without a password on this host, and everything else on `alpha-prod-01` already runs under Docker.

## Metrics

| Metric | Meaning |
|---|---|
| `teamspeak_public_up` | The public address a user types answered. This is the user-facing light. |
| `teamspeak_public_rtt_seconds` | Handshake round trip through the Playit relay. |
| `teamspeak_local_up` | The voice service answered on its local UDP port. |
| `teamspeak_local_rtt_seconds` | Local handshake round trip. |
| `teamspeak_dns_srv_up` | The `_ts3._udp` SRV record resolved. |
| `teamspeak_tunnel_fault` | Local up, public down. Blame Playit or DNS. |
| `teamspeak_server_fault` | Local down. Blame the TeamSpeak server. |
| `teamspeak_last_probe_timestamp_seconds` | Freshness, so a stuck collector is visible instead of silently showing stale green. |

`teamspeak_query_up`, `teamspeak_clients_online`, `teamspeak_channels_online`, `teamspeak_uptime_seconds`, and `teamspeak_max_clients` come from ServerQuery. These are live.

Each instance keeps its own `serveradmin` account, so the three passwords differ despite sharing the login name. My first cut read one `TS_QUERY_PASS` for all three, which would have authenticated against one server and failed silently on the other two. The collector now reads `TS_QUERY_PASS_TS01`, `TS_QUERY_PASS_TS02`, and `TS_QUERY_PASS_TS03`, falling back to a single shared value only if the passwords are ever unified. `teamspeak_query_up` exists so a login failure shows as a red panel rather than a missing series.

## Verification

| Check | Observed result |
|---|---|
| Public probe, all three servers | Answered `TS3INIT1` in 44.6, 45.2, & 44.7 ms |
| Local probe, all three servers | Answered in 0.13 to 0.15 ms |
| SRV resolution | All three returned a host and port |
| Textfile written | `teamspeak.prom`, 3575 bytes, mode 0644 |
| `node_textfile_scrape_error` | 0 |
| node_exporter output | All `teamspeak_*` series present on 9100 |
| Prometheus on monitor-01 | Queried every series successfully; target count unchanged at 45 |
| Grafana dashboard | uid `teamspeak`, Homelab folder, `provisioned: true` |
| Grafana query path | `avg_over_time(teamspeak_public_up[30m])` returned 1 for all three servers |
| Fault logic, tunnel case | Forced an unresolvable domain: local 1, SRV 0, public 0, tunnel_fault 1, server_fault 0 |
| Fault logic, server case | Forced an unreachable local address: local 0, public 1, server_fault 1, tunnel_fault 0 |
| Live service during testing | Untouched; both fault tests ran in throwaway containers writing to `/tmp` |
| ServerQuery, all three servers | `teamspeak_query_up` 1; clients 1, 1, 1; channels 3, 80, 1; uptime ~5.3 days |
| Dashboard after rework | 16 panels, 3 rows, 0 descriptions, every panel returned values through Grafana's query path |
| `.env` on the host | mode 0600, six keys, untracked |

Both fault tests matter more than the green lights. A monitor whose failure path has never fired is a monitor that can lie.

## Reading the dashboard

`https://grafana.<YOUR_BASE_DOMAIN>/d/teamspeak/teamspeak`

Three rows: Public Availability, Fault Isolation, and Server Statistics.

The first cut crammed six series into a panel five grid units tall, so Grafana shrank the text until every row read as dashes. Fault location now derives one value per server, `server_fault * 2 + tunnel_fault`, mapped to HEALTHY, TUNNEL OR DNS, or TEAMSPEAK SERVER. Local voice and SRV resolution each got their own panel instead of sharing one. Three rows per panel renders at full size.

I also removed every panel description. The hover text was noise on panels whose titles already say what they show, and I stripped the 44 descriptions on the Homelab Overview dashboard for the same reason.

Collector age sits near 60 seconds. Anything climbing past a few minutes means the lights above are stale.

## Remaining work

The probe originates on the same host as the servers. It still round-trips through Playit's public relay, so it tests the external path, but a genuinely independent vantage would mean running a second collector on `edge-01` in DMZ-A. That's a cheaper firewall exception than MONITOR-A if I ever want it.
