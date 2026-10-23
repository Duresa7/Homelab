# Robotic Voice on ts03

**Created:** 2026-10-22  
**Last updated:** 2026-10-22

**Status:** Resolved 2026-10-22; self-recovered at 9:32 PM; Playit relay issue; no change made. [Incident report](../../../../Security/Incidents/Teamspeak/Robotic%20Voice%20from%20Playit%20Relay%20Degradation%20-%202026-10-22.md)

## Symptom

At 9:12 PM on 2026-10-22 a player on `ts03` reported that the servers were bugging. At 9:30 PM they said everyone sounded like a robot and that it had happened twice. Five clients had been on `ts03` since 6:22 PM. Robotic voice in TeamSpeak means voice packets arriving late, unevenly, or not at all.

## What I checked

All readings are from the evening of 2026-10-22, 8:40 to 9:40 PM unless stated.

| Layer | Reading | Verdict |
|---|---|---|
| `ts-valorant-03` container | Up since 12:53 AM; no errors in its log; one client ping timeout at 8:12 PM, reconnected at 8:13 PM | Clean |
| TeamSpeak counters (`serverinfo`, read 9:30 PM) | Speech, keepalive and total packet loss `0.0000`; control loss `0.0048`; average client ping 83.6 ms | No loss at read time |
| `alpha-prod-01` (node_exporter, cAdvisor) | CPU busy at most 7.8%, steal at most 0.13%, iowait at most 1.85%, load at most 0.5; `ens18` at most 1.5 Mbit/s out; no interface drops, no UDP receive or buffer errors; `ts-valorant-03` at most 0.02 cores, `playit-agent` 0.03, `minecraft` 0.27 | Clean |
| `purple-server` `nic0` | No e1000e hang, link or Corosync message since 8:30 PM; zero TX errors or drops; TSO, GSO and GRO still off from the [2026-10-15 change](../../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/nic0%20Offloads%20Disabled%20on%20Purple,%20Green%20and%20Red%20-%202026-10-15.md) | Clean |
| UniFi gateway WAN, last hour in 5-minute averages | 1.4 to 18.5 Mbit/s down, 1.1 to 2.7 Mbit/s up; gateway CPU 17 to 26% | Not saturated |
| Collector public handshake via the Playit relay | Baseline 40 to 46 ms. Stepped to 75 to 85 ms from 9:01 to 9:10 PM, then back to 41 ms by 9:12 PM. Single readings of 57 to 64 ms at 8:54 to 8:56, 8:58, 8:59, 9:13, 9:22, 9:26, 9:28, 9:30 and 9:31 PM. Local handshake at most 1.3 ms all day | Degraded |
| `playit-agent` log | Control API returned 522 at 8:56 PM; control address reload timed out at 9:03 PM; earlier 503 responses at 7:53 PM | Playit control plane unstable over the same window |

For comparison, the collector's hourly 95th percentile for the public path was 44 to 47 ms for every hour on 2026-10-21 and until 5 PM on 2026-10-22. It rose to 62 ms in the 5 PM hour, 79 ms at 6 PM and 81 ms at 7 PM, then held at 63 ms through 9 PM.

## Finding

Everything I own on the voice path was clean: the server, the VM, the Proxmox host's NIC, the LAN and the WAN link. The only layer that degraded was the public path through Playit. Its latency doubled for ten minutes immediately before the first report, and it kept jumping after that. Over the same window the agent was logging Playit control-plane failures. I attribute it to congestion or rerouting on Playit's relay network, either between the players and the relay or between the relay and my WAN.

The attribution rests on that latency and the Playit errors, not on a packet-loss capture. The collector sends one handshake a minute, so it can't see short bursts of loss or jitter between samples, and the TeamSpeak loss counters were read after the reports and keep no history.

## Resolution

The relay path returned to its baseline at 9:32 PM without any change on my side and stayed at or below 55 ms through 9:35 PM, with public voice up and the five players still connected. I closed it as a Playit relay issue and recorded it as an incident: [Robotic voice from Playit relay degradation](../../../../Security/Incidents/Teamspeak/Robotic%20Voice%20from%20Playit%20Relay%20Degradation%20-%202026-10-22.md).

If it recurs, I'll read the affected client's Connection Info and the server's `serverinfo` packet loss while it is happening. Extending the collector to measure loss and jitter is the incident's open follow-up.
