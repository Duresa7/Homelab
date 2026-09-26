# ObiPC Domain Sign-in Error

**Created:** 2026-09-20  
**Last updated:** 2026-09-25

I investigated a Windows sign-in problem for `IK-user` on `ObiPC` at approximately 6:41 PM Eastern. It first looked like an invalid password, then turned out to be a domain-related error. I did not capture the exact Windows message.

I checked the account through `HQ-DC01` and `HQ-DC02`. It was enabled, unlocked, not expired, and not required to change its password. Its password was last set on 2026-09-12 at 9:58:49 AM Eastern. Both controllers returned a bad-password count of 0, allowed sign-in at the current hour, and showed `OBIPC` as the permitted workstation. The last bad-password timestamp was 1:48:48 PM on 2026-09-20.

The last successful Kerberos ticket request I found was event 4768 with status `0x0`, from `192.168.60.102` at 5:51:20 PM Eastern on `HQ-DC01`. I found no matching account events among 4771, 4776, 4740, and 4625 in either controller's preceding 24 hours. That does not establish the cause of the reported sign-in failure.

Both SSH attempts to `obipc` returned `connect EHOSTUNREACH 192.168.60.102:22`. Domain DNS still resolved the workstation to that address. I could not read its local sign-in logs or verify its secure channel. The first account query failed because nested PowerShell quoting expanded variables; rerunning with `-EncodedCommand` succeeded. No separate terminal capture was retained for these checks.

I traced the problem to a misconfigured Ethernet port serving ObiPC and corrected it on 2026-09-20. The port configuration had prevented domain sign-in on the workstation. I considered the issue fixed after correcting the port; the specific port setting and a post-fix sign-in capture were not retained. The remote investigation made no account or password changes, and I did not repeat the remote checks after the port correction. I closed this issue based on the fix at the workstation.
