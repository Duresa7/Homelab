# Deployment

**Created:** 2026-09-12  
**Last updated:** 2026-09-12  
**Implementation:** 2026-09-11 through 2026-09-12  
**Verification:** 2026-09-12

I installed Windows Admin Center on `HQ-MGT01` at `192.168.65.12` so I can manage my Windows machines from https://hq-mgt01.ad.alphasecunited.com. I expanded the original ObiPC-only browser scope to all of VLAN 50 and VLAN 60, plus my MacBook Air M3 and Pixel on their observed VLAN 10 connections.

The installation and initial configuration happened before the session was interrupted. I recovered that work from the session history, then read the live state again. I did not retain the earlier installation commands as a published transcript. The [final verification capture](../../Evidence/Deployment%20-%202026-09-12/Final-Verification.json) retains the resumed SSH commands, their complete returned output and exit codes, the filtered UniFi readbacks, and the cleanup verification. The UniFi capture covers this deployment's rules and DNS record, not the whole controller.

## Gateway and connections

I verified file version `2.7.21.5`, `WindowsAdminCenter` running with automatic start, and TCP 443 listening. `WindowsAdminCenterAccountManagement` is running with manual start. The existing `AADConnectProvisioningAgent` remains running with automatic start.

Authenticated GETs of `/api/connections` and `/api/extensions` both returned HTTP 200. The shared `global` list contains three server connections, HQ-DC01, HQ-DC02 and HQ-MGT01, and two Windows client connections, ObiPC and HQ-WS001. Every name uses the `ad.alphasecunited.com` suffix. Active Directory `0.86.0` and DNS `2.76.0` both read `Installed`. All five targets answered `Test-WSMan` from HQ-MGT01; this establishes WinRM reachability, not successful management with each intended account.

## Network changes

I read back these enabled IPv4 TCP allow policies and their three enabled response companions:

| Policy | Source | Destination | Port | Index |
|---|---|---|---|---:|
| `Allow Secure and Secure Client to WAC HTTPS` | Secure VLAN 50 and Secure Client VLAN 60, network objects | `192.168.65.12` | 443 | 10003 |
| `Allow MacBook Air and Pixel to WAC HTTPS` | Two device selectors in Internal | `192.168.65.12` | 443 | 10004 |
| `Allow WAC to Secure Client WinRM` | `192.168.65.12` | Secure Client VLAN 60, network object | 5985, 5986 | 10000 |

The gateway's Windows firewall rule `WacInboundOpenException` admits `192.168.50.0/24`, `192.168.60.0/24`, and `192.168.10.0/24`; UniFi narrows VLAN 10 access to the two devices. Both workstation `WINRM-HTTP-In-TCP*` rules are enabled with remote address `192.168.65.12` only. I verified HQ-WS001 through the QEMU guest agent on grey-server and ObiPC through SSH Manager. WinRM HTTP is operational; I did not establish an HTTPS listener on 5986 merely by allowing that port.

HQ-MGT01's WinRM `TrustedHosts` contains the five exact connection FQDNs. I did not configure a wildcard. UniFi holds an enabled A record for `hq-mgt01.ad.alphasecunited.com` pointing to `192.168.65.12`, TTL 300. ObiPC resolved that address through both its default DNS and `192.168.10.1`.

## Sign-in and cleanup

ObiPC retrieved the Windows Admin Center sign-in page with HTTP 403 before authentication, matching the page title. I also confirmed that the page appeared from a personal device; the confirmation did not identify whether it was Jedi PC, the MacBook, or the Pixel. The certificate is self-signed for `HQ-MGT01.ad.alphasecunited.com`, expiring 2026-11-10 at 10:54:56 PM EST.

I subsequently confirmed successful browser sign-in on 2026-09-12. I retained the [sign-in confirmation](../../Evidence/Deployment%20-%202026-09-12/Browser-Sign-In.md); no screenshot or browser transcript was captured. This confirmation does not establish that I opened a target machine.

Setup used HQ-MGT01's current LAPS-managed local Administrator credential after its older stored credential failed. I overwrote the 15 temporary files in `C:\ProgramData\WAC-Setup-Private`, removed that directory, and verified its absence. I also overwrote and removed `/tmp/wac-setup-credential.json` on the local workstation and verified its absence. These were setup staging files, not configuration backups. The gateway remained running and listening on TCP 443 after server cleanup. I took no snapshot or backup.

## Remaining checks

Browser sign-in succeeded on 2026-09-12. I still need to open the saved connections using each target's appropriate account. I have not marked user management, DNS editing, or workstation service changes from the browser complete. Controller work is intended to use DK-t0 through **Manage as**; this account's Protected Users and no-delegation settings remain in place, and the browser flow needs verification. RSAT on ObiPC remains a separate unstarted task. I will replace the self-signed certificate before its November 10 expiry. The [Active Directory TODO](../../../Active%20Directory/Documentation/TODO.md) owns those follow-ups.
