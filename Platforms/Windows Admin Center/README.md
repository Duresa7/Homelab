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

I verified authenticated connection and extension reads through the gateway API. All five targets answer `Test-WSMan` from HQ-MGT01. I confirmed the sign-in page from a personal device, without recording which device. I confirmed successful browser sign-in on 2026-09-12. Opening the saved machines and browser changes to a user, DNS record, and workstation service remain to be verified.

The setup authenticated with HQ-MGT01's local `Administrator` account using its current LAPS-managed password. Its older stored password is stale. My intended everyday gateway sign-in is my domain account, recorded as DK-user. The successful browser sign-in confirmation did not specify the account or device. Gateway access and target-machine permissions are separate; I use **Manage as** for the account appropriate to the target. I have not changed directory roles or delegation to complete this deployment.

The [deployment record](Documentation/Change%20Records/Deployment%20-%202026-09-12.md) contains verification and cleanup. Remaining management checks, the certificate replacement, and the separate RSAT task are in the [Active Directory TODO](../Active%20Directory/Documentation/TODO.md).

On 2026-09-12, I checked Azure Arc agent presence over SSH on `HQ-DC01`, `HQ-DC02`, and `HQ-MGT01`. All three returned `False` for `C:\Program Files\AzureConnectedMachineAgent\azcmagent.exe` and no services named `himds`, `GCArcService`, or `ExtensionService`. The commands returned exit code 1 with empty stderr after the missing-service queries. I found no Azure Arc deployment record in the repository. This check covers those three Windows servers; I did not inspect Azure resource inventory or the Linux fleet. I made no host changes and retained no separate transcript.
