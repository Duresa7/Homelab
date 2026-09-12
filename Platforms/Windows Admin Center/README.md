# Windows Admin Center

**Created:** 2026-09-12  
**Last updated:** 2026-09-12

I run Windows Admin Center on `HQ-MGT01`, VM 303 at `192.168.65.12` in IDENTITY-A, VLAN 65. I installed it on 2026-09-11 and verified the deployment on 2026-09-12.

| Item | Verified state on 2026-09-12 |
|---|---|
| Browser address | https://hq-mgt01.ad.alphasecunited.com |
| Gateway file version | `2.7.21.5` |
| Service | `WindowsAdminCenter`, running, automatic start, TCP 443 |
| Browser network access | All of Secure VLAN 50 and Secure Client VLAN 60; the MacBook Air M3 and Pixel through a separate device-specific rule while on VLAN 10 |
| Shared server connections | `hq-dc01.ad.alphasecunited.com`, `hq-dc02.ad.alphasecunited.com`, `hq-mgt01.ad.alphasecunited.com` |
| Shared workstation connections | `obipc.ad.alphasecunited.com`, `hq-ws001.ad.alphasecunited.com` |
| Extensions | Active Directory `0.86.0`, DNS `2.76.0`, both installed |
| Certificate | Self-signed for the gateway FQDN; expires 2026-11-10 at 10:54:56 PM EST |

I verified DK-user's domain and gateway administration on 2026-09-12. All five WAC operating-system queries return HTTP 200 using the same gateway session, with no separate target credentials. Fresh Kerberos over HTTPS sessions on all five targets also report elevated administrator tokens. The gateway now uses WinRM HTTPS on TCP 5986; each target admits it only from HQ-MGT01, and HQ-MGT01 trusts the five target certificates. This resolved ObiPC's HTTP WinRM connection failures during intrusion prevention.

I sign in with my regular domain account, recorded as DK-user, using `ALPHASEC\<YOUR_DOMAIN_USERNAME>` and its usual password. After the administrative group changes I must sign out of WAC and sign back in, then use **Use my Windows account** for target connections. The original setup used HQ-MGT01's LAPS-managed local Administrator; that is no longer required for this everyday workflow.

The [original deployment](Documentation/Change%20Records/Deployment%20-%202026-09-12.md) records installation. [Owner Domain Administration](../Active%20Directory/Documentation/Change%20Records/Owner%20Domain%20Administration%20-%202026-09-12.md) records the role changes, delegation, HTTPS transport, all-five verification, and credential cleanup. The [credentials troubleshooting record](Documentation/Troubleshooting/HQ-MGT01%20Connection%20Credentials%20-%202026-09-12.md) records the original failure and resolution.

The browser certificate expires 2026-11-10. The five WinRM certificates expire 2027-09-12 and require renewal and trust updates on HQ-MGT01. The [Active Directory TODO](../Active%20Directory/Documentation/TODO.md) tracks certificates, future-target onboarding, optional browser management exercises, and RSAT.

On 2026-09-12, I checked Azure Arc agent presence over SSH on `HQ-DC01`, `HQ-DC02`, and `HQ-MGT01`. All three returned `False` for `C:\Program Files\AzureConnectedMachineAgent\azcmagent.exe` and no services named `himds`, `GCArcService`, or `ExtensionService`. The commands returned exit code 1 with empty stderr after the missing-service queries. I found no Azure Arc deployment record in the repository. This check covers those three Windows servers; I did not inspect Azure resource inventory or the Linux fleet. I made no host changes and retained no separate transcript.
