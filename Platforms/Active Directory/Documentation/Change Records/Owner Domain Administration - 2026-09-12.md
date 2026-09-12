# Owner Domain Administration

**Created:** 2026-09-12  
**Last updated:** 2026-09-12  
**Implementation and verification:** 2026-09-12

I changed my regular domain account, DK-user, from workstation administration only to administration of my Windows domain and Windows Admin Center. I explicitly chose to use this account for both controllers, HQ-MGT01, ObiPC, and HQ-WS001 rather than switch administrator accounts for each connection. This is an exception to the separate-account tier model. Microsoft 365, Azure, Linux, Proxmox, and UniFi administrative roles were outside this change.

## Membership and delegation

I added DK-user to `ADM-T0-DomainAdmins` and `ADM-T1-ServerAdmins`, retaining its existing `ADM-T2-WorkstationAdmins` membership. The Tier 0 group is nested in `Domain Admins`. Existing server and workstation Group Policy adds the corresponding tier groups to local Administrators, so the membership change also applies to future machines placed in the covered OUs. Future WAC targets still need their own WinRM HTTPS listener, certificate trust, connection entry, and gateway delegation configuration.

I configured resource-based constrained delegation on HQ-DC01, HQ-DC02, HQ-MGT01, OBIPC, and HQ-WS001, with HQ-MGT01 as the sole allowed principal on each. The earlier implementation verified DK-user against three fields in the private identity map before changing membership. In the resumed verification, I selected the same account as the unique intersection of `ROL-Staff` and `ADM-T2-WorkstationAdmins` and returned its alias and role booleans only.

Both controllers now report DK-user in all three tier groups and `Domain Admins`. The account is enabled, unlocked, and has `AccountNotDelegated=False`. Its resultant password policy is now `PSO-Admins`; I did not change the policy or reset its password. Both controllers return one delegation principal for each of the five targets, matching HQ-MGT01. The [directory verification](../../Evidence/Owner%20Domain%20Administration%20-%202026-09-12/Directory-Verification.json) retains the readback.

## WinRM HTTPS

The initial authenticated tests worked on four targets. ObiPC intermittently timed out over TCP 5985. The earlier investigation recorded UniFi intrusion-prevention flow matches for “Malicious User Agents” on HQ-MGT01's WinRM traffic to ObiPC; failed probes left HQ-MGT01 but did not arrive at ObiPC. I did not disable intrusion prevention or change a UniFi policy. I switched WAC's target transport to HTTPS instead.

I created one self-signed `WAC WinRM TLS` certificate and HTTPS listener on each target, using its FQDN and short hostname. The private keys are nonexportable. Each target has an enabled `WAC-WinRM-HTTPS-In` firewall rule allowing TCP 5986 only from `192.168.65.12`. I imported the five public certificates into HQ-MGT01's LocalMachine Root store, enabled `Set-WACWinRmOverHttps -Enabled`, and restarted Windows Admin Center. The setting reads back `true` and the service is running.

All five WinRM certificates expire on 2027-09-12 between 1:00:58 AM and 1:01:36 AM EDT. They are separate from the browser gateway certificate expiring 2026-11-10. I verified all five trusted HTTPS WinRM endpoints and read back the listener, certificate subject, expiry, and source-restricted firewall rule through fresh administrator sessions. I retained no separate transcript for the initial certificate creation, public-certificate import, or IPS investigation. The resumed certificate/firewall read returned zero, with verbose progress output truncated by the transport; its state is recorded here rather than represented as a complete transcript.

## End-to-end verification

I repeated WAC's web-form sign-in with DK-user after the HTTPS switch. It returned HTTP 200 and listed all five shared connections. The accepted username form is `ALPHASEC\<YOUR_DOMAIN_USERNAME>`; the earlier UPN attempt failed authorization. The old test's `/api/settings` probe returned 404 because that route does not exist. The actual `/api/access/admins` request returned HTTP 200, and `/api/access/check` returned HTTP 200 with `true`, confirming gateway administration access.

| Target | WAC operating-system query using the gateway session only | Fresh Kerberos over HTTPS |
|---|---|---|
| HQ-DC01 | HTTP 200, one instance, no error | Elevated administrator token |
| HQ-DC02 | HTTP 200, one instance, no error | Elevated administrator token |
| HQ-MGT01 | HTTP 200, one instance, no error | Elevated administrator token |
| HQ-WS001 | HTTP 200, one instance, no error | Elevated administrator token |
| ObiPC | HTTP 200, one instance, no error | Elevated administrator token |

The WAC requests read `Win32_OperatingSystem` through each target's `/api/nodes/.../features/cim/` endpoint. They used only DK-user's authenticated gateway cookies and the matching CSRF header, with no separate target credentials. The direct PowerShell sessions independently checked `WindowsPrincipal.IsInRole(Administrator)`. The [management verification](../../Evidence/Owner%20Domain%20Administration%20-%202026-09-12/Management-Verification.json) retains those commands and results. I did not make a production user, DNS, or service change merely to demonstrate write access.

## Cleanup and remaining work

I overwrote and removed the 26 test files under `C:\ProgramData\WAC-Access-Private` and the four local files under `/tmp/domain-admin-task`, then verified both directories absent. The gateway remained running and listening on TCP 443. Packet Monitor was stopped with no filters on HQ-MGT01 and ObiPC. I retained no credentials, cookies, or raw account-response bodies in published evidence. I created no snapshot or configuration backup.

I must sign out of WAC and sign back in with the domain-qualified username to refresh its existing session. Windows desktop sessions that predate the membership change also need a Windows sign-out and sign-in to refresh their local tokens. The authenticated API workflow is verified; clicking through every management tool in the browser remains an interactive follow-up. Certificate renewal, future-target onboarding, and the separate RSAT task remain in the [platform TODO](../TODO.md).
