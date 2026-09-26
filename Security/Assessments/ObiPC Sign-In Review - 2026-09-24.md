# ObiPC Sign-In Review

**Created:** 2026-09-24  
**Last updated:** 2026-09-24

I checked for sign-in activity on ObiPC from midnight Eastern on 2026-09-24 through approximately 4:43 PM EDT. Both attempts to reach the workstation through SSH Manager failed with `connect EHOSTUNREACH 192.168.60.102:22`. I could not read its local Security log, so I could not determine whether anyone attempted a desktop sign-in or unlock today.

I queried `HQ-DC01` and `HQ-DC02` for events 4624, 4625, 4768, 4771, and 4776 matching ObiPC's address, its workstation name, or the previously disabled `IK-user` account. Domain DNS still resolved `obipc.ad.alphasecunited.com` to `192.168.60.102`.

| Controller | Observed events today | Latest event (EDT) |
|---|---|---|
| HQ-DC01 | 381 successful type-3 network logons, all for ObiPC's computer account | 3:09:17 PM |
| HQ-DC02 | 33 successful type-3 network logons and two successful Kerberos ticket requests, all for ObiPC's computer account | 3:08:06 PM |

Neither query returned a human-user authentication event or a matching failure. Both controllers returned `Enabled=false` for `IK-user`. Computer-account authentication shows machine activity, not a person signing into the desktop. The absence of user events on the controllers does not rule out attempts rejected locally, including attempts against the disabled account.

The final controller queries completed with exit code 0 and no event-query errors. The first full `HQ-DC01` response could not be parsed as JSON; I reran it with aggregate counts and a separate list of non-computer events, which was empty. No separate terminal capture was retained. I made no live changes. Local sign-in verification remains open until ObiPC is reachable.

The previous day's [account disablement and two rejected sign-ins](../../Platforms/Active%20Directory/Documentation/Change%20Records/IK-user%20Account%20Disabled%20-%202026-09-23.md) are separate events and are not included in today's counts.
