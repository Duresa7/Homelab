# TeamSpeak Hosting

**Created:** 2026-07-28  
**Last updated:** 2026-09-25

I run two TeamSpeak 3 voice servers on `alpha-prod-01` (`192.168.80.118`, VLAN 80), published to the internet through a shared Playit agent and reached by Cloudflare SRV names. TS3 Manager handles administration from the LAN.

## Current State

Read back on 2026-09-25 unless a row says otherwise.

| Item | Value |
|---|---|
| Host | `alpha-prod-01` (`192.168.80.118`), Debian 13; VM 401 on `purple-server`, NVMe-backed `local-lvm` |
| Voice containers | `ts-valorant-02`, `ts-valorant-03` (image `teamspeak`, built 2026-09-17), both TeamSpeak 3 Server 3.13.8, both recreated 12:17 PM on 2026-09-18 |
| Tunnel agent | `playit-agent` (`ghcr.io/playit-cloud/playit-agent:latest`, image label 1.0) |
| Collector | `teamspeak-monitor` (`forgejo.alphasecunited.com/homelab-images/teamspeak-monitor:stable`) |
| Administration | `ts3-manager` (`joni1802/ts3-manager`) at `https://ts3-manager.alphasecunited.com` through internal NPM (proxy host 22); direct fallback `http://192.168.80.118:9000` |
| Other containers | `hawser` 0.2.49, `wud` 9.0.2, `cadvisor` 0.60.5 |
| Networking | Host networking, so each voice container needs a unique port set |

## Port and Name Map

| Server | Voice | ServerQuery | File transfer | Public name |
|---|---:|---:|---:|---|
| `ts-valorant-02` | 9988/udp | 10012/tcp | 30034/tcp | `ts02.alphasecunited.com` |
| `ts-valorant-03` | 9989/udp | 10013/tcp | 30035/tcp | `ts03.alphasecunited.com` |

Each public name is a DNS-only CNAME to its Playit relay plus an `_ts3._udp` SRV record carrying the relay host and assigned port. The SRV target points at the Playit hostname directly, not the CNAME, because some TeamSpeak clients reject an alias there.

The reachability collector reads that SRV record on every cycle, so it depends on DNS inside its container. On 2026-08-27 I pinned its resolver with `dns: [192.168.80.1]` in the Compose file. A boot race on 2026-08-10 had left it with a `resolv.conf` holding no nameserver for 17 days, and the dashboard reported both public addresses down while both servers were serving clients. Full diagnosis in [Collector DNS Failure After a Boot Race - 2026-08-27](Documentation/Change%20Records/Collector%20DNS%20Failure%20After%20a%20Boot%20Race%20-%202026-08-27.md).

ServerQuery ports are LAN only and their allowlists cover `127.0.0.1`, `192.168.80.118`, and `192.168.50.241`. They aren't tunneled, so only voice is reachable from the internet.

## Compose Projects and Volumes

Each server is a separate Compose project with its own named volume, which is why they survive a single project being recreated. Verified 2026-07-28.

| Server | Virtual server name | Compose project | Data volume |
|---|---|---|---|
| `ts-valorant-02` | `AlphaSec` United x HomeBase | `teamspeak-02` | `teamspeak-02_ts-data` |
| `ts-valorant-03` | `AlphaSec` United x Valorant 03 | `teamspeak-03` | `teamspeak-03_ts-data` |

## Monitoring

The [`teamspeak-monitor`](Source/teamspeak-monitor/) collector probes each server every 60 seconds (`TS_INTERVAL`), once at its public address and once on its local UDP port, and reports which half is at fault. Metrics reach Prometheus through the existing node_exporter scrape on port 9100. The Grafana dashboard is `teamspeak` in the Homelab folder. Since 2026-09-15 the private [Uptime dashboard](https://grafana.alphasecunited.com/d/uptime) also shows both public Playit paths, their status histories, observed uptime, and monitoring coverage. A collector timestamp older than three minutes is unknown there.

`blackbox_exporter` can't do this job because it has no UDP prober. The [change record](Documentation/Change%20Records/TeamSpeak%20Reachability%20Monitoring%20-%202026-07-28.md) explains that and why the collector runs on `alpha-prod-01` rather than `monitor-01`.

## Layout

- `Documentation/` holds the deployment reference and dated change records.
- `Source/teamspeak-monitor/` holds the reachability collector.
- `Scripts/` holds the probe and rotation helpers plus the migration job scripts.

## Key Records

- [Purple migration (2026-09-12)](../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/alpha-prod-01%20Purple%20Migration%20-%202026-09-12.md)
- [Deployment reference](Documentation/Deployment.md)
- [Reachability monitoring (2026-07-28)](Documentation/Change%20Records/TeamSpeak%20Reachability%20Monitoring%20-%202026-07-28.md)
- [Server 01 retirement (2026-08-09)](Documentation/Change%20Records/Server%2001%20Retirement%20-%202026-08-09.md)
- [Duplicate TS03 DNS alias removal (2026-08-09)](Documentation/Change%20Records/Duplicate%20TS03%20DNS%20Alias%20Removal%20-%202026-08-09.md)
- [Collector DNS failure after a boot race (2026-08-27)](Documentation/Change%20Records/Collector%20DNS%20Failure%20After%20a%20Boot%20Race%20-%202026-08-27.md)
- Incidents: [UDP relay outage (2026-04-24)](../../Security/Incidents/Teamspeak/UDP%20Relay%20Outage%20-%202026-04-24.md), [DNS and ServerQuery (2026-04-24)](../../Security/Incidents/Teamspeak/DNS%20and%20ServerQuery%20-%202026-04-24.md)
- [Scripts](Scripts/README.md)
- [Archived three-server walkthrough](../../Archive/Guides/TeamSpeak.md)

## Boot Recovery

The Playit lifecycle is deliberately independent of the voice containers, so restarting a TeamSpeak project doesn't tear down the tunnels. A boot-recovery script waits for Docker and DNS before restarting the voice projects and the agent, which fixed the startup race where containers came up before the tunnel could resolve.
