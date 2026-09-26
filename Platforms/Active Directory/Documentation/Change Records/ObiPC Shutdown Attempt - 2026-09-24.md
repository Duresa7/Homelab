# ObiPC Shutdown Attempt

**Created:** 2026-09-24  
**Last updated:** 2026-09-25

I attempted to reach ObiPC to shut it down at approximately 10:13 PM EDT on 2026-09-24. The preliminary `hostname` command through SSH Manager's `obipc` connection failed with `connect EHOSTUNREACH 192.168.60.102:22`. No shutdown command reached the workstation.

I checked UniFi's client inventory, including offline clients, for `ObiPC`. Both recorded interfaces were offline:

| Connection | Address | Last seen on 2026-09-24 (EDT) |
|---|---|---|
| Wired | `192.168.60.102` | 4:08:53 PM |
| Wireless | `192.168.10.220` | 10:01:49 PM |

The controller query succeeded and returned two matching clients. These observations establish that remote access was unavailable, not that Windows completed a shutdown or that the physical machine was powered off. The shutdown remains unperformed. I made no live changes, queued no shutdown for later, and retained no separate terminal capture.
