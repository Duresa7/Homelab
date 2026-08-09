# TeamSpeak Server 01 Retirement

**Created:** 2026-08-09  
**Last updated:** 2026-08-09

**Date:** 2026-08-09  
**Scope:** Retire `ts-valorant-01` without changing either remaining TeamSpeak server or the shared Playit agent.

## What Changed

I removed the `ts-valorant-01` container, its `teamspeak` Compose project, the `teamspeak_ts-data` volume, & the `/home/dkadi/teamspeak` directory from `alpha-prod-01`. The volume had no snapshot or backup, so its TeamSpeak database isn't recoverable.

The host still had three TeamSpeak containers before this work. The earlier UI deletion had removed the server from TS3 Manager, not Docker.

I removed server 01 from the reachability collector, deleted its two ServerQuery variables from the collector `.env`, rebuilt `teamspeak-monitor`, & removed its restart line from `playit-boot-recover.sh`. I also deleted the two stale boot-script backup files that still carried the retired project list.

I deleted these Cloudflare records from `alphasecunited.com`:

| Type | Name |
|---|---|
| CNAME | `ts01.alphasecunited.com` |
| SRV | `_ts3._udp.ts01.alphasecunited.com` |

The three-server walkthrough & its Excalidraw/SVG pair moved to `Archive/Guides/` & `Archive/Assets/Diagrams/`. I edited the living platform record, scripts record, guide index, source collector, & Galaxy services inventory to describe the two-server deployment.

## What Remains

| Component | Result |
|---|---|
| `ts-valorant-02` | Running on 9988/udp, 10012/tcp, & 30034/tcp |
| `ts-valorant-03` | Running on 9989/udp, 10013/tcp, & 30035/tcp |
| Data volumes | `teamspeak-02_ts-data` & `teamspeak-03_ts-data` remain |
| Playit agent | Running from the independent `playit-agent` project |
| TS3 Manager | Running on host port 9000 |
| Grafana dashboard | Unchanged; it discovers servers from Prometheus labels rather than a fixed `ts01` list |
| Cloudflare | All six CNAME/SRV records for `ts02`, `ts03`, & the `ts-valorant-03` alternate name remain |

## Verification

| Check | Observed result |
|---|---|
| Docker object lookup | No `ts-valorant-01` container & no `teamspeak_ts-data` volume |
| Compose directory | `/home/dkadi/teamspeak` absent |
| Retired ports | 9987/udp, 10011/tcp, & 30033/tcp closed |
| Remaining ports | 9988/udp, 9989/udp, 10012/tcp, 10013/tcp, 30034/tcp, & 30035/tcp listening |
| Monitor labels | Only `ts02` & `ts03` present in `teamspeak.prom` |
| Public monitor result | `teamspeak_public_up` returned 1 for `ts02` & 1 for `ts03` |
| Monitor credentials | Only the TS02 & TS03 user/password variable names remain; no values were printed |
| Boot recovery | Only `$HOME/teamspeak-02` & `$HOME/teamspeak-03` remain in the script |
| Cloudflare deletion | Both server 01 DELETE requests returned HTTP 200; exact-name readback returned zero records |
| Remaining Cloudflare records | Exact-name readback returned one record for each of the six TS02/TS03 names |

I retained no separate evidence folder for this job. I repeated each check against the live host or Cloudflare API & recorded the observed state above.

## Manual Playit Removal

After the infrastructure retirement passed, I deleted the retired server 01 tunnel from the Playit website. That website action has no retained API or account readback in this record. Before the manual deletion, I had already verified that the tunnel had no local listener, Docker project, monitor target, boot dependency, or Cloudflare record.
