# Domain Machine RDP Enablement

**Created:** 2026-09-12  
**Last updated:** 2026-09-12  
**Implementation and verification:** 2026-09-12

I enabled Remote Desktop on all five machines in `ad.alphasecunited.com`: `HQ-DC01`, `HQ-DC02`, `HQ-MGT01`, `HQ-WS001`, and `ObiPC`. Before this change none of them accepted RDP. I scoped the source addresses on each host and opened the matching path through UniFi to the identity plane. I chose to give the two domain controllers the same source scope as the rest rather than force a jump through `HQ-MGT01`.

This change covers host configuration and the gateway path only. I did not create an RDP access group, publish connection shortcuts, or change Group Policy.

## Pre-change state

I read all five hosts before changing anything. Every one returned the same state: `fDenyTSConnections` 1, both `RemoteDesktop-UserMode-In` firewall rules disabled, `TermService` stopped, nothing listening on TCP 3389, and an empty `Remote Desktop Users` group. `UserAuthentication` was already 1 on all five, so Network Level Authentication was required before this change and I did not have to relax it.

I reached `HQ-DC01`, `HQ-DC02`, `HQ-MGT01`, and `ObiPC` through SSH Manager. `HQ-WS001` has no SSH session configured, so I used the QEMU guest agent on VM 310 on grey-server, the same path the Action1 and Windows Admin Center work used.

## Source scope

| Source | Address | Reason |
|---|---|---|
| Trusted VLAN 10 | `192.168.10.0/24` | Carries my MacBook Air |
| Secure VLAN 50 | `192.168.50.0/24` | Carries `Jedi PC` at `192.168.50.241`; I admitted the whole network by decision |
| `ubuntu-dev` | `192.168.40.179` | Single host on Personal-A, not the whole VLAN |
| `docker-blue` | `192.168.40.39` | Added later the same day on request; single host, not the whole VLAN |
| Management Access VPN | `10.6.0.0/24` | The entire VPN subnet |

I excluded the `FamilyVPN`, `Game-Access`, and `Temp` remote-user networks. They carry other people and other purposes, and admitting them to the domain controllers was not warranted.

`docker-blue` was not in the first pass. I added it after the initial verification, which cost me the original negative control and required a second one.

## Host configuration

On each of the five hosts I set `fDenyTSConnections` to 0, confirmed `UserAuthentication` at 1, enabled `RemoteDesktop-UserMode-In-TCP` and `RemoteDesktop-UserMode-In-UDP` with the four source addresses above, set `TermService` to Automatic, and started it. I left `RemoteDesktop-Shadow-In-TCP` disabled because session shadowing was not part of this change. I left each rule's profile binding as it was and used the remote address list as the control.

All five read back `fDenyTSConnections` 0, `UserAuthentication` 1, the TCP rule enabled, `TermService` running, and two listeners on TCP 3389 for IPv4 and IPv6. After the `docker-blue` addition the remote address list on all five reads `192.168.10.0/255.255.255.0,192.168.50.0/255.255.255.0,192.168.40.179,192.168.40.39,10.6.0.0/255.255.255.0`.

One SSH Manager connection to `ObiPC` failed with `EHOSTUNREACH` on TCP 22 during the `docker-blue` pass and succeeded on the next attempt. `ObiPC` stayed up throughout: UniFi showed it wired and current, and it answered both TCP 22 and TCP 3389 from `ubuntu-dev` while the SSH Manager attempt was failing. I changed nothing to recover it.

## Gateway policies

`ObiPC` sits on Secure Client VLAN 60 inside the Internal zone and needed no policy. The other four sit in `AlphaSec-Identity`, which is default deny from Internal, so I added three IPv4 allow policies. Each targets the four identity addresses `192.168.65.10`, `192.168.65.11`, `192.168.65.12`, and `192.168.65.20` on TCP and UDP 3389, with the response companion enabled and the Always schedule.

| Policy | Source |
|---|---|
| `Allow Admin Networks to Identity RDP` | Internal, Trusted and Secure networks |
| `Allow Personal-A Hosts to Identity RDP` | Internal, `192.168.40.179` and `192.168.40.39` |
| `Allow VPN to Identity RDP` | Vpn, Management Access network |

The controller went from 80 user-defined policies to 83, split 75 allows to eight blocks. I created the second policy as `Allow ubuntu-dev to Identity RDP` and renamed it when `docker-blue` joined its source list, so the controller now carries the name in the table above.

## Verification

From `ubuntu-dev` at `192.168.40.179`, TCP 3389 was refused on all four identity hosts before the policies existed and accepted on all five hosts afterward. `ObiPC` accepted before the policies were added, which is consistent with both endpoints sitting in Internal.

The first negative control was `docker-blue` at `192.168.40.39`, on the same VLAN as `ubuntu-dev` and not then in the allow list. It was refused on `HQ-DC01`, `HQ-MGT01`, and `ObiPC`. The `ObiPC` refusal is the useful one: the VLAN path from Personal-A to Secure Client is open, so the host firewall scope is what stopped it. Both layers hold independently.

Adding `docker-blue` to the allow list retired that control, so I repeated it from `ansible-01` at `192.168.40.36`, a third Personal-A host that is not in the list. After the change `docker-blue` and `ubuntu-dev` both reached all five machines on TCP 3389, and `ansible-01` was refused on all five. The scoping still holds at both layers.

I read `SeRemoteInteractiveLogonRight` on `HQ-DC01`, `HQ-MGT01`, and `ObiPC`. The controller grants it to `BUILTIN\Administrators` only. `HQ-MGT01` and `ObiPC` grant it to `BUILTIN\Administrators` and `BUILTIN\Remote Desktop Users`. DK-user became a domain and server administrator on 2026-09-12 and a workstation administrator on 2026-09-11, so it holds the right on all five through `Administrators` without any group change. See [Owner Domain Administration](Owner%20Domain%20Administration%20-%202026-09-12.md).

I completed an interactive RDP sign-on to `HQ-WS001` at `192.168.65.20` from Windows App on a Windows client on 2026-09-12, which proves the path end to end on that machine. The first attempt failed with error `0x104` because the connection named the host as `HQ-WS001`. The client resolves DNS through the UniFi gateway, whose 28 local records include `hq-mgt01.ad.alphasecunited.com` and no other domain machine, so the short name never resolved and the attempt did not reach the network. Addressing the target by IP succeeded. I chose not to add gateway DNS records for the other four machines.

The remaining four are verified to the port and logon-right level only. I have not signed in interactively to `HQ-DC01`, `HQ-DC02`, `HQ-MGT01`, or `ObiPC`.

## Remaining work

An interactive sign-on to the four machines other than `HQ-WS001` confirms the part this record does not. RDP connections address these hosts by IP, because the gateway holds a local DNS record for `HQ-MGT01` only. `ObiPC` takes its address by DHCP, so a fixed DNS record for it would want a reservation first.

`ObiPC` and `HQ-WS001` run Windows 11 Pro and allow one session at a time, so an RDP connection displaces whoever is signed in at the physical machine. That matters for `ObiPC`, where `IK-user` has a restricted account with sign-in hours. If a non-administrator ever needs one specific machine, that wants a dedicated group such as `RDP-ObiPC-Users` granted on that host rather than a broader tier membership.

These machines do not appear in Windows App and cannot be made to. Windows App populates itself only from Azure Virtual Desktop, Windows 365, and Microsoft Dev Box, and its own remote PC entries are manual and still in preview on Windows. Azure Virtual Desktop Hybrid would produce real tiles for Arc-enabled session hosts, but it excludes personal PCs such as `ObiPC` and carries per-user licensing. Distributing `.rdp` shortcuts through Group Policy, targeted by group membership, is the option that fits these five machines, and it remains open.

I created no snapshot and no configuration backup. Nothing was copied off a host.
