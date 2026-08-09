# TeamSpeak Hosting

**Created:** 2026-07-28  
**Last updated:** 2026-08-09

I run two TeamSpeak 3 voice servers on `alpha-prod-01` (`192.168.80.118`, VLAN 80), published to the internet through a shared Playit agent and reached by Cloudflare SRV names. TS3 Manager handles administration from the LAN.

## Deployment

| Item | Value |
|---|---|
| Host | `alpha-prod-01` (`192.168.80.118`), Debian 13 |
| Voice containers | `ts-valorant-02`, `ts-valorant-03` (image `teamspeak`) |
| Tunnel agent | `playit-agent` (`ghcr.io/playit-cloud/playit-agent:0.17`) |
| Administration | `https://ts3-manager.alphasecunited.com` through internal NPM; direct fallback `http://192.168.80.118:9000` |
| Networking | Host networking, so each container needs a unique port set |

## Port and Name Map

| Server | Voice | ServerQuery | File transfer | Public name |
|---|---:|---:|---:|---|
| `ts-valorant-02` | 9988/udp | 10012/tcp | 30034/tcp | `ts02.alphasecunited.com` |
| `ts-valorant-03` | 9989/udp | 10013/tcp | 30035/tcp | `ts03.alphasecunited.com` |

Each public name is a DNS-only CNAME to its Playit relay plus an `_ts3._udp` SRV record carrying the relay host and assigned port. The SRV target points at the Playit hostname directly, not the CNAME, because some TeamSpeak clients reject an alias there. `ts03` also answers on `ts-valorant-03.alphasecunited.com`, which has its own CNAME and SRV pair.

ServerQuery ports are LAN only and their allowlists cover `127.0.0.1`, `192.168.80.118`, and `192.168.50.241`. They aren't tunneled, so only voice is reachable from the internet.

## Compose Projects and Volumes

Each server is a separate Compose project with its own named volume, which is why they survive a single project being recreated. Verified 2026-07-28.

| Server | Virtual server name | Compose project | Data volume |
|---|---|---|---|
| `ts-valorant-02` | `AlphaSec` United x HomeBase | `teamspeak-02` | `teamspeak-02_ts-data` |
| `ts-valorant-03` | `AlphaSec` United x Valorant 03 | `teamspeak-03` | `teamspeak-03_ts-data` |

## Monitoring

The [`teamspeak-monitor`](Source/teamspeak-monitor/) collector probes each server twice a minute, once at its public address and once on its local UDP port, and reports which half is at fault. Metrics reach Prometheus through the existing node_exporter scrape on port 9100. The Grafana dashboard is `teamspeak` in the Homelab folder.

`blackbox_exporter` can't do this job because it has no UDP prober. The [change record](Documentation/Change%20Records/TeamSpeak%20Reachability%20Monitoring%20-%202026-07-28.md) explains that and why the collector runs on `alpha-prod-01` rather than `monitor-01`.

## Layout

- `Documentation/` holds the deployment record and dated change records.
- `Source/teamspeak-monitor/` holds the reachability collector.
- `Scripts/` holds the probe and rotation helpers plus the migration job scripts.

## Key Records

- [Deployment record](Documentation/Teamspeak-deployment.md)
- [Reachability monitoring (2026-07-28)](Documentation/Change%20Records/TeamSpeak%20Reachability%20Monitoring%20-%202026-07-28.md)
- [Scripts](Scripts/README.md)
- [Archived three-server walkthrough](../../Archive/Guides/TeamSpeak.md)

## Boot Recovery

The Playit lifecycle is deliberately independent of the voice containers, so restarting a TeamSpeak project doesn't tear down the tunnels. A boot-recovery script waits for Docker and DNS before restarting the voice projects and the agent, which fixed the startup race where containers came up before the tunnel could resolve.
