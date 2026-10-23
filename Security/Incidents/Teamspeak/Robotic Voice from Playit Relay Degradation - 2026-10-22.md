# TeamSpeak Robotic Voice from Playit Relay Degradation

**Created:** 2026-10-22  
**Last updated:** 2026-10-22

## Incident Metadata

| Field | Value |
|-------|-------|
| Incident ID | ASU-TS3-20261022-001 |
| Detected By | User report |
| Detection Time | 2026-10-22 9:12 PM EDT |
| Recovery Time | 2026-10-22 9:32 PM EDT, self-recovered |
| Status | Resolved; closed |
| Severity | SEV-4 |
| Priority | Low |
| Impact Type | Voice quality degradation |
| Affected Users | The five players connected to `ts03` |
| Affected Services | `ts-valorant-03` public voice path through Playit |
| Unaffected Services | `ts-valorant-03` server process, `ts-valorant-02`, `alpha-prod-01`, `purple-server`, LAN and WAN |

## Summary

On the evening of 2026-10-22, players on `ts03` heard each other's voices as robotic on two occasions before 9:30 PM. A player reported it at 9:12 PM and again at 9:30 PM. Robotic voice in TeamSpeak comes from voice packets arriving late, unevenly or not at all.

I checked every layer of the voice path that I own and found nothing wrong with any of them. The only layer that degraded was the Playit relay. Its round trip doubled from 9:01 to 9:10 PM and spiked repeatedly until 9:31 PM, and the Playit agent logged failures from Playit's control API over the same window. The relay returned to its baseline at 9:32 PM without any change on my side, and the players stayed connected throughout. I attribute the incident to a Playit relay issue.

## Impact

Voice on `ts03` was intermittently distorted for the five connected players during two episodes between about 9:00 and 9:31 PM. Nobody was disconnected by it, the server never went down, and no data was lost. `ts02` had no players connected at the time.

## Affected Assets

| Asset | Role |
|---|---|
| `ts-valorant-03` on `alpha-prod-01` (`192.168.80.118`) | TeamSpeak 3 Server 3.13.8, voice 9989/udp |
| `ts03.alphasecunited.com` | Public name, SRV to the Playit relay on port 49125 |
| `playit-agent` on `alpha-prod-01` | Shared Playit agent carrying both TeamSpeak tunnels and Minecraft |

## Symptoms

The player's report: at 9:12 PM, "the servers are bugging rn"; at 9:30 PM, "everyone sounds like a robot" and "it happened twice".

The Playit agent log over the same window:

```text
2026-10-22 8:56 PM  ERROR playit_api_client::http_client: API call failed ... 522, {"error": "cloudflare origin error"}
2026-10-22 9:03 PM  ERROR playit_agent_core::playit_agent: failed to reload_control_addr error=Timeout(...)
```

## Timeline

| Time (EDT) | Event |
|---|---|
| 2026-10-22 5:38 PM | Players begin joining `ts02` |
| 2026-10-22 6:20 to 6:22 PM | The group moves to `ts03` |
| 2026-10-22, 5 PM onward | Collector's hourly 95th percentile on the public path rises from 44 to 47 ms to between 62 and 81 ms |
| 2026-10-22 7:53 PM | Playit control API returns 503 responses to the agent |
| 2026-10-22 8:12 PM | One `ts03` client drops on a ping timeout and reconnects at 8:13 PM |
| 2026-10-22 8:54 to 8:59 PM | Public handshake readings of 59 to 64 ms |
| 2026-10-22 8:56 PM | Playit control API returns 522 |
| 2026-10-22 9:01 to 9:10 PM | Public handshake steps to 75 to 85 ms, against a 40 to 46 ms baseline; first episode |
| 2026-10-22 9:03 PM | Agent times out reloading its Playit control address |
| 2026-10-22 9:12 PM | Player reports the servers bugging; public handshake back at 41 ms |
| 2026-10-22 9:13 to 9:31 PM | Public handshake spikes to 57 to 64 ms at 9:13, 9:22, 9:26, 9:28, 9:30 and 9:31 PM; second episode |
| 2026-10-22 9:30 PM | Player reports robotic voice, twice; TeamSpeak `serverinfo` reads zero speech packet loss |
| 2026-10-22 9:32 PM | Public handshake back at baseline and stays there through 9:35 PM; five players still connected |

## Technical Findings

| Control Point | Finding |
|---|---|
| `ts-valorant-03` | Up since 12:53 AM; no errors in its log over the window |
| TeamSpeak `serverinfo`, read 9:30 PM | Speech, keepalive and total packet loss `0.0000`; control loss `0.0048`; average client ping 83.6 ms |
| `alpha-prod-01`, 8:40 to 9:40 PM | CPU busy at most 7.8%, steal at most 0.13%, iowait at most 1.85%, load at most 0.5; `ens18` at most 1.5 Mbit/s out; no interface drops; no UDP receive or buffer errors |
| Containers on `alpha-prod-01` | `ts-valorant-03` at most 0.02 cores, `playit-agent` 0.03, `minecraft` 0.27 |
| `purple-server` `nic0` | No e1000e hang, link or Corosync message after 8:30 PM; zero TX errors or drops; TSO, GSO and GRO off |
| UniFi gateway, last hour in 5-minute averages | WAN 1.4 to 18.5 Mbit/s down and 1.1 to 2.7 Mbit/s up; gateway CPU 17 to 26% |
| Local voice handshake | At most 1.3 ms all day |
| Public voice handshake through Playit | Degraded as in the timeline; never failed outright during either episode |

## Root Cause

Degradation on Playit's relay network. Every layer I own was clean while the relay path's latency doubled and spiked, and Playit's own control plane was failing over the same period. The path recovered without any change on my side.

I can't measure loss between the one-minute collector samples, and TeamSpeak's loss counters keep no history, so the attribution rests on the latency and the Playit errors rather than a direct packet-loss capture.

## Corrective Actions Performed

None. The relay recovered without any action on my side. My investigation was read-only on `alpha-prod-01`, `purple-server`, `docker-main` and the UniFi controller.

## Validation

From 9:32 PM the collector's public handshake to `ts03` stayed at or below 55 ms, public voice stayed up with no tunnel fault in the preceding 30 minutes, and the server still showed six clients online (five players and the collector's query login) at 9:35 PM.

## Security Assessment

No security impact. The degradation was in a third-party relay's network path. I saw no unauthorized access, no configuration change and no abnormal traffic.

## Operational Findings

- The collector sends one handshake a minute and records latency, not loss or jitter, so it showed the relay degrading but could not prove that packets were being lost.
- TeamSpeak's `serverinfo` loss counters reflect the moment they are read, so they have to be read while the problem is happening.

## Follow-Up Actions

| Action | Owner | Priority | Status |
|---|---|---|---|
| Extend the collector to send a burst of handshakes each cycle and report loss and jitter on the public path | `AlphaSec` United | Low | Open |

## Closure

Closed on 2026-10-22. The voice path recovered at 9:32 PM without intervention and I attribute the incident to the Playit relay. The open follow-up improves detection and does not hold the incident open.

## Linked Records

- [Troubleshooting record](../../../Platforms/Teamspeak%20Hosting/Documentation/Troubleshooting/Robotic%20Voice%20on%20ts03%20-%202026-10-22.md)
- [TeamSpeak Hosting](../../../Platforms/Teamspeak%20Hosting/README.md)
- [Earlier Playit path incident: UDP relay outage (2026-04-24)](UDP%20Relay%20Outage%20-%202026-04-24.md)
