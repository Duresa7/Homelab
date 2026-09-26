# IK-user Account Disabled

**Created:** 2026-09-23  
**Last updated:** 2026-09-25

I disabled the `IK-user` domain account used on `ObiPC` at 8:24:48 PM EDT on 2026-09-23. I matched the identity to the private alias map and the live member of `ROL-ObiPC-Restricted`. Before the change, `HQ-DC01` returned `Enabled=true` and `userWorkstations=OBIPC`.

I ran `Disable-ADAccount` against that resolved user on `HQ-DC01`. The command exited 0 with no stderr, and its immediate readback returned `Enabled=false`. This disables the domain account, including its use beyond the workstation; it is not a local-account change.

At 8:24:59 PM, `HQ-DC02` still returned `Enabled=true`. At 8:25:18 PM, fresh queries to both `HQ-DC01` and `HQ-DC02` returned `Enabled=false` and `userWorkstations=OBIPC`. Both verification commands exited 0.

On `ObiPC`, I verified domain membership and a healthy secure channel at 8:24:27 PM. At 8:25:17 PM, the Winlogon registry values were `CachedLogonsCount=0` and `ForceUnlockLogon=1`. My first unlock-policy query used the wrong registry path and returned null; the corrected query returned 1. These are configuration checks; I did not attempt an interactive sign-in.

An interactive desktop user was present during the check. I did not terminate any session, delete the profile, change passwords, or change group memberships. Account disablement does not terminate an existing session or revoke already issued tickets. Cloud synchronization and tenant session revocation were not verified. No separate terminal capture was retained for these steps. No snapshots or backups were created.

The account disablement is complete and verified on both domain controllers. Existing-session termination was outside this change.

## Same-day sign-in check

At 11:25 PM EDT on 2026-09-23, I checked the account's Security events on `ObiPC`, `HQ-DC01`, and `HQ-DC02` from midnight Eastern onward. I found two failed interactive sign-in events on ObiPC:

| Time (EDT) | Event ID | Record ID | Logon type | Status | Substatus |
|---|---|---|---|---|---|
| 9:26:29 PM | 4625 | 20561 | 2 | `0xc000006e` | `0xc0000072` |
| 9:26:33 PM | 4625 | 20562 | 2 | `0xc000006e` | `0xc0000072` |

Both attempts occurred after the disablement. Microsoft identifies logon type 2 as interactive and substatus `0xc0000072` as [an account disabled by an administrator](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4625). These events identify the account used, not the person at the keyboard. The local query matched account names and the account SID; it returned no successful 4624 or unlock 4801 events for this account today. ObiPC's oldest retained Security event was from 2026-09-18 at 8:26:34 PM EDT, so retention reached back past the start of the day I checked. I did not independently verify every audit-policy setting.

Both controllers still returned `Enabled=false` at 11:24 PM. Their logs contained successful network authentication from ObiPC at `192.168.60.102`: 107 type-3 events on `HQ-DC01` and 16 on `HQ-DC02`, plus one successful Kerberos ticket request at 6:19:04 AM on `HQ-DC02`. Seventy of the type-3 events on `HQ-DC01` occurred after disablement, from 8:53:26 PM through 9:41:18 PM. Network logons do not establish a new desktop sign-in. I did not establish which application or existing ticket produced those events. No matching 4625, 4771, or 4776 failures were returned by the controller queries, and neither controller recorded a Security-log clear today. Their retained Security logs reached back to 2026-09-15.

The initial group-only account lookup was ambiguous; adding the previously verified identity match resolved it. Broad queries timed out, so I filtered by identity in the event query. One controller response could not be parsed as JSON; I reran it with counts and selected event details. ObiPC rejected the long command line, so I used shorter read-only queries. I corrected a UTC comparison before calculating the final post-disablement counts above. No separate terminal capture was retained. I made no live changes during this check.
