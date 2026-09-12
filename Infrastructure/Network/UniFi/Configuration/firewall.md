# UniFi Firewall Policies

**Created:** 2026-07-09  
**Last updated:** 2026-09-12

On 2026-09-12 I read back three enabled Windows Admin Center policies and their three response companions. `Allow Secure and Secure Client to WAC HTTPS` permits all of VLAN 50 and VLAN 60 to `192.168.65.12` on TCP 443. `Allow MacBook Air and Pixel to WAC HTTPS` permits those two device selectors to the same address and port while they are on VLAN 10. `Allow WAC to Secure Client WinRM` permits only `192.168.65.12` to VLAN 60 on TCP 5985/5986. The enabled local DNS A record `hq-mgt01.ad.alphasecunited.com` resolves to `192.168.65.12`, TTL 300. The [deployment record](../../../../Platforms/Windows%20Admin%20Center/Documentation/Change%20Records/Deployment%20-%202026-09-12.md) retains the scoped readback and endpoint verification; I did not recount all controller policies in this check.

I verified the eight existing identity policies on 2026-09-07 and found no mismatch in their actions, enabled states, protocols, zones, or selectors. I added Allow Identity to Splunk - Security-A after checking SC4S on 192.168.72.3. The controller now returns 351 policies: 77 user-defined policies, split 69 allows to eight blocks, and 274 generated policies. The [final identity readback](../Evidence/Identity%20Plane%20Network%20Preparation%20-%202026-09-07/Final%20Identity%20Policy%20Readback.json) retains all nine custom rules and their response companions.

On 2026-09-06 I read all 68 policies back from the controller during the documentation audit and compared the names. Seven rows in the table carried the corrected zone spelling `AlphaSec` where the controller still names the policy with the original `AlphSec` or `A-Servers` shorthand; the 2026-07-27 consolidation corrected the zone names, not the policy names that mention them. The rows now match the controller character for character, so a search of this file finds the live policy. The count, the 61 to seven split, and every selector I checked were as recorded.

On 2026-09-02 I added `Allow splunk-siem to alert bot`. It admits only `192.168.72.3` to `192.168.73.2` on TCP 8080, both in `AlphaSec-Observability`, logs matches, and permits the response path, so Splunk's webhook alert action can reach the Discord alert bot on `monitor-01`. The same evening `PG-Node-Exporter` gained port 9102 for What's Up Docker, and `Allow Monitor to A-Access monitoring`, which names its ports inline, gained 9102 too. The live controller total increased from 67 to 68 user-defined policies: 61 allows and seven blocks. The table had recorded that inline policy as `Allow Monitor to AlphaSec-Access monitoring`; the controller's name is `Allow Monitor to A-Access monitoring` and the row now matches. See [Monitoring Ports for What's Up Docker and the Alert Bot](../Documentation/Change%20Records/Monitoring%20Ports%20for%20What's%20Up%20Docker%20and%20the%20Alert%20Bot%20-%202026-09-02.md).

On 2026-08-31 I added `Allow docker-blue SSH Manager to Proxmox`. It admits only `192.168.40.39` in Internal to `192.168.70.10` through `192.168.70.14` in `AlphaSec-Mgmt` over TCP 22, logs matches, and permits the response path. The live controller total increased from 66 to 67 user-defined policies: 60 allows and seven blocks. The matching Proxmox Datacenter `pve_admins` member was required before the five nodes answered.

During the same readback I found that this living table omitted the existing `Allow Internal to Printer` policy. It permits Internal to reach `192.168.20.212` in Untrusted through `PG-Printing`. I added the missing row without changing the controller.

On 2026-08-30 I added `Allow NPM to docker-blue Executor`. It admits only `192.168.85.2` in AlphaSec-Access to `192.168.40.39:4788` in Internal over TCP, logs matches, and permits the response path. The live controller total increased from 65 to 66 user-defined policies: 59 allows and seven blocks. I used direct selectors because this rule has one source, one destination, and one port; a reusable Network List would not reduce the edit surface and could make a later membership expansion broaden access unintentionally.

On 2026-08-19 I repointed the dedicated CLI Proxy API policy from `ubuntu-dev` to `docker-main` and renamed it `Allow NPM to docker-main CLI Proxy API`. It now admits only `192.168.85.2` in Access-A to `192.168.40.35:8317` in Personal-A over TCP. The source, port, protocol, action, logging, index, and policy ID stayed in place; the before-and-after policy comparison found no other firewall change.

Also on 2026-08-13 I moved workstation access from `debian-dev` to `ubuntu-dev`. I swapped the client MAC in `Device Access --> Proxmox`, but a MAC entry alone never produced a working rule for the new guest, so I added `Allow ubuntu-dev to Proxmox`, which admits `192.168.40.179` in Internal to the `AlphaSec-Mgmt` zone on the same port group the MAC policy uses. That policy is what carries the access today. I also swapped `192.168.40.135` for `192.168.40.179` in the destination list of `Allow Monitor to Personal-A monitoring`, so `monitor-01` scrapes the new host's exporter. Neither firewall was sufficient by itself here either: the Proxmox cluster firewall needed the new address in `pve_admins` before any of the five nodes answered.

On 2026-08-13 I repointed that policy to `ubuntu-dev` and renamed it `Allow NPM to ubuntu-dev CLI Proxy API`, when CLI Proxy API moved hosts. Only the name and the destination address changed, from `192.168.40.135` to `192.168.40.179`; the source, port, protocol, action, logging, and index are as they were, and the policy kept its 3,694 recorded hits.

On 2026-08-10 I added it as `Allow NPM to debian-dev CLI Proxy API`. It admitted only `192.168.85.2` in Access-A to `192.168.40.135:8317` in Personal-A over TCP, logged matches, and permitted the response path. I verified the route through NPM and the internal HTTPS name.

On 2026-08-08 I made three changes for `debian-dev`, which is now the machine I develop on. I added its MAC to `Device Access --> Proxmox`, taking that policy from four client MACs to five. I added `Allow VPN Management Access to DMZ` so the Management Access VPN reaches `edge-01` from outside the network. Before that policy existed, the controller returned no user rule at all for the VPN-to-DMZ zone pair, which is why the DMZ was the one zone the VPN could not reach. The new rule names the Management Access network rather than the whole `Vpn` zone, so Game-Access still cannot reach the DMZ, and it does not weaken `Block DMZ to Internal`, which governs the opposite direction.

The third change added `192.168.40.135` to the destination list of `Allow Monitor to Personal-A monitoring`, so `monitor-01` can scrape the node_exporter that host now runs. That policy matches specific addresses rather than the whole Internal zone, so a new exporter on Personal-A stays unreachable until its address is named here. Before the edit, TCP 9100 from `192.168.73.2` to `192.168.40.135` timed out while TCP 1514 and 1515 to the Wazuh manager already worked, because `Allow Internal to AlphaSec-Security` covers the whole zone and the monitoring policy does not.

I added three policies for `game-01` on 2026-08-07 and extended one existing monitoring policy to reach it. The remaining narrow Wazuh enrollment paths admit `monitor-01`, `docker-network`, the five Galaxy nodes, the server zone, and `edge-01` to `192.168.72.2` on TCP 1514 and 1515. The Galaxy PXE callback verification also remains current.

The gateway runs UniFi's zone-based V2 firewall. After I deleted the 68 Kasm policies on 2026-08-19, the controller returned 64 user-defined policies: 57 allows and seven blocks. The list below records that audited baseline and later documented service-specific additions.

`game-01` needed no policy for game traffic. `Allow Internal to AlphSec-Servers` already permits every Internal network to that zone on every port, so Trusted, Secure, and Secure Client reach TCP 25565 and the Pelican SFTP port 2022 without a new rule. That also admits Management, Server-Provision, and Personal-A, which is wider than the three networks the host was built for.

What did need policies is the reverse direction. Both the panel and Wings call *out* to `192.168.85.2:443`, because Wings fetches its server list from the panel's published URL and the panel reaches Wings at the node FQDN. Both paths hairpin through NPM. Wings refuses to start without that return path and exits with `dial tcp 192.168.85.2:443: i/o timeout`.

## Recorded Custom Policy Inventory

Every custom policy uses the `Always` schedule. The source and destination columns name the live zone and selector. Policy names retain their historical wording even when a target zone has been consolidated or renamed, which is why seven of them still read `AlphSec` or `A-Servers` while the zones they point at read `AlphaSec`.

| Policy | Enabled | Action | Index | Protocol | Source | Destination |
|---|---|---|---:|---|---|---|
| `Block DMZ to Internal` | Yes | BLOCK | 40000 | All | Dmz / Any | Internal / Any |
| `DMZ Allow List` | Yes | ALLOW | 10001 | All | Internal / 3 MACs | Dmz / Any |
| `Block DMZ to LAN` | Yes | BLOCK | 40001 | All | Dmz / Any | Internal / Any |
| `Allow VPN to AlphSec-Mgmt` | Yes | ALLOW | 10000 | All | Vpn / Any | `AlphaSec-Mgmt` / Any |
| `Allow VPN to AlphSec-Servers` | Yes | ALLOW | 10000 | All | Vpn / Any | `AlphaSec-Servers` / Any |
| `Allow AlphSec-Mgmt to AlphSec-Servers` | Yes | ALLOW | 10000 | All | `AlphaSec-Mgmt` / Any | `AlphaSec-Servers` / Any |
| `Allow Proxmox Nodes to Galaxy PXE` | Yes | ALLOW | 10000 | TCP | `AlphaSec-Mgmt` / `AG-Proxmox-Nodes` | Internal / `AG-Galaxy-PXE-Service` / `PG-Galaxy-PXE-Callback` |
| `Allow Server-Provision callbacks to Galaxy PXE` | Yes | ALLOW | 10005 | TCP | Internal / `Server-Provision` | Internal / `AG-Galaxy-PXE-Service` / `PG-Galaxy-PXE-Callback` |
| `Allow Internal to AlphSec-Mgmt` | No | ALLOW | 10000 | All | Internal / Any | `AlphaSec-Mgmt` / Any |
| `Allow Internal to AlphSec-Servers` | Yes | ALLOW | 10000 | All | Internal / Any | `AlphaSec-Servers` / Any |
| `Allow edge-01 to app-01 Web` | Yes | ALLOW | 10000 | TCP | Dmz / `edge-01` MAC | `AlphaSec-Servers` / 192.168.80.10 / `App Access` |
| `Allow Devices to Personal-A` | Yes | ALLOW | 10001 | All | Internal / 9 MACs | Internal / Personal-A |
| `Block Trusted to Personal-A` | Yes | BLOCK | 10002 | All | Internal / Trusted | Internal / Personal-A |
| `Device Access --> Proxmox` | Yes | ALLOW | 10001 | All | Internal / 5 MACs | `AlphaSec-Mgmt` / `Proxmox-Admin-Ports` |
| `Jedi PC --> Unifi Console SSH` | Yes | ALLOW | 10006 | All | Internal / 1 MAC | Internal / Management |
| `Allow A-Servers to Portainer Edge` | Yes | ALLOW | 10000 | All | `AlphaSec-Servers` / Any | Internal / 192.168.40.35 / `Portainer Edge Agents` |
| `Allow Secure and Secure Client to WAC HTTPS` | Yes | ALLOW | 10003 | TCP | Internal / Secure and Secure Client networks | `AlphaSec-Identity` / 192.168.65.12 / 443 |
| `Allow MacBook Air and Pixel to WAC HTTPS` | Yes | ALLOW | 10004 | TCP | Internal / MacBook Air M3 and Pixel device selectors | `AlphaSec-Identity` / 192.168.65.12 / 443 |
| `Allow WAC to Secure Client WinRM` | Yes | ALLOW | 10000 | TCP | `AlphaSec-Identity` / 192.168.65.12 | Internal / Secure Client network / 5985,5986 |
| `Allow Identity Sync Service Connection` | Yes | ALLOW | 10000 | All | External / Any | Gateway / TCP 9543 group |
| `VPN: Temp Ban` | Yes | BLOCK | 10000 | All | Vpn / Temp | Internal / Personal-A, Secure, Secure Client, Management |
| `VPN: Temp #2` | Yes | BLOCK | 10001 | All | Vpn / Temp | `AlphaSec-Servers` / Any |
| `Docker-main Allowed -> Server` | Yes | ALLOW | 10002 | TCP | Internal / `docker-main` MAC | `AlphaSec-Mgmt` / MGMT-A / 8006 |
| `Docker -> Jedi PC` | Yes | ALLOW | 10003 | All | Internal / `docker-main` MAC | Internal / Secure |
| `Allow Internal to AlphaSec-Access` | Yes | ALLOW | 10000 | All | Internal / Any | `AlphaSec-Access` / Any |
| `Allow Internal to Printer` | Yes | ALLOW | 10000 | All | Internal / Any | Untrusted / 192.168.20.212 / `PG-Printing` |
| `Allow VPN to AlphaSec-Access` | Yes | ALLOW | 10000 | All | Vpn / Any | `AlphaSec-Access` / Any |
| `Allow Internal to AlphaSec-Security` | Yes | ALLOW | 10003 | All | Internal / Any | `AlphaSec-Observability` / Any |
| `Allow VPN to AlphaSec-Security` | Yes | ALLOW | 10001 | All | Vpn / Any | `AlphaSec-Observability` / Any |
| `Allow VPN Management Access to DMZ` | Yes | ALLOW | 10000 | All | Vpn / Management Access | Dmz / Any |
| `Allow Access Services Web Egress` | Yes | ALLOW | 10000 | TCP | `AlphaSec-Access` / .2, .3, .6 | External / `PG-Egress-Web` |
| `Allow Access Services NTP Egress` | Yes | ALLOW | 10001 | UDP | `AlphaSec-Access` / .2, .3, .6 | External / `PG-NTP` |
| `Block AlphaSec-Access Other External Egress` | Yes | BLOCK | 10002 | All | `AlphaSec-Access` / Any | External / Any |
| `Block Observability Other External Egress` | Yes | BLOCK | 10002 | All | `AlphaSec-Observability` / `AG-Observability-Hosts` | External / Any |
| `Allow AlphSec-Servers to Wazuh - Security-A` | Yes | ALLOW | 10000 | TCP | `AlphaSec-Servers` / Any | `AlphaSec-Observability` / 192.168.72.2 / `Wazuh Ports` |
| `Allow DMZ to Wazuh - Security-A` | Yes | ALLOW | 10000 | TCP | Dmz / `edge-01` MAC | `AlphaSec-Observability` / 192.168.72.2 / `Wazuh Ports` |
| `Allow monitor-01 to Wazuh - Security-A` | Yes | ALLOW | 10001 | TCP | `AlphaSec-Observability` / 192.168.73.2 | `AlphaSec-Observability` / 192.168.72.2 / `Wazuh Ports` |
| `Allow docker-network to Wazuh - Security-A` | Yes | ALLOW | 10003 | TCP | `AlphaSec-Access` / 192.168.85.2 | `AlphaSec-Observability` / 192.168.72.2 / `Wazuh Ports` |
| `Allow Galaxy nodes to Wazuh - Security-A` | Yes | ALLOW | 10000 | TCP | `AlphaSec-Mgmt` / .10, .11, .12, .13, .14 | `AlphaSec-Observability` / 192.168.72.2 / `Wazuh Ports` |
| `Allow VPN --> Internal Zone` | Yes | ALLOW | 10001 | All | Vpn / Management Access | Internal / Any |
| `Allow Device --> media-01` | Yes | ALLOW | 10004 | All | Internal / 2 MACs | Internal / Personal-A |
| `Allow NPM to media-01 web UIs` | Yes | ALLOW | 10000 | TCP | `AlphaSec-Access` / `AG-Reverse-Proxy` | Internal / 192.168.40.42 / 5055, 7878, 8080, 8096, 8989, 9696 |
| `Allow NPM to ansible-01 Semaphore` | Yes | ALLOW | 10001 | TCP | `AlphaSec-Access` / `AG-Reverse-Proxy` | Internal / 192.168.40.36 / 3000 |
| `Allow NPM to docker-main web UIs` | Yes | ALLOW | 10002 | TCP | `AlphaSec-Access` / `AG-Reverse-Proxy` | Internal / 192.168.40.35 / 2283, 3000, 3001, 3002, 6060, 9443 |
| `Allow NPM to docker-main CLI Proxy API` | Yes | ALLOW | 10004 | TCP | `AlphaSec-Access` / 192.168.85.2 | Internal / 192.168.40.35 / 8317 |
| `Allow NPM to docker-blue Executor` | Yes | ALLOW | 10005 | TCP | `AlphaSec-Access` / 192.168.85.2 | Internal / 192.168.40.39 / 4788 |
| `Allow docker-blue SSH Manager to Proxmox` | Yes | ALLOW | 10004 | TCP | Internal / 192.168.40.39 | `AlphaSec-Mgmt` / .10, .11, .12, .13, .14 / 22 |
| `Allow ubuntu-dev to Proxmox` | Yes | ALLOW | 10003 | All | Internal / 192.168.40.179 | `AlphaSec-Mgmt` / Any / `Proxmox GUI+SSH` port group |
| `Allow docker-network to Portainer Edge` | Yes | ALLOW | 10003 | TCP | `AlphaSec-Access` / 192.168.85.2 | Internal / 192.168.40.35 / `Portainer Edge Agents` |
| `Allow NPM to alpha-prod-01 TS3 Manager` | Yes | ALLOW | 10000 | TCP | `AlphaSec-Access` / 192.168.85.2 | `AlphaSec-Servers` / 192.168.80.118 / 9000 |
| `Allow NPM to game-01 Panel` | Yes | ALLOW | 10001 | TCP | `AlphaSec-Access` / 192.168.85.2 | `AlphaSec-Servers` / 192.168.80.30 / 80 |
| `Allow NPM to game-01 Wings` | Yes | ALLOW | 10002 | TCP | `AlphaSec-Access` / 192.168.85.2 | `AlphaSec-Servers` / 192.168.80.30 / 8080 |
| `Allow game-01 to NPM HTTPS` | Yes | ALLOW | 10000 | TCP | `AlphaSec-Servers` / 192.168.80.30 | `AlphaSec-Access` / 192.168.85.2 / 443 |
| `Allow NPM to security-01 Wazuh` | Yes | ALLOW | 10001 | TCP | `AlphaSec-Access` / `AG-Reverse-Proxy` | `AlphaSec-Observability` / 192.168.72.2 / 443 |
| `Allow NPM to splunk-siem web UI` | Yes | ALLOW | 10002 | TCP | `AlphaSec-Access` / `AG-Reverse-Proxy` | `AlphaSec-Observability` / 192.168.72.3 / 8000 |
| `Allow Monitor to Personal-A monitoring` | Yes | ALLOW | 10000 | TCP | `AlphaSec-Observability` / `AG-Monitor-Collector` | Internal / .35, .36, .39, .42, .179 / `PG-Node-Exporter` |
| `Allow Monitor to A-Servers monitoring` | Yes | ALLOW | 10000 | TCP | `AlphaSec-Observability` / `AG-Monitor-Collector` | `AlphaSec-Servers` / .10, .30, .118 / `PG-Node-Exporter` |
| `Allow Monitor to A-Access monitoring` | Yes | ALLOW | 10000 | TCP | `AlphaSec-Observability` / `AG-Monitor-Collector` | `AlphaSec-Access` / `AG-Reverse-Proxy` / 9100, 9101, 9102, 443 |
| `Allow Monitor to DMZ monitoring` | Yes | ALLOW | 10000 | TCP | `AlphaSec-Observability` / `AG-Monitor-Collector` | Dmz / 192.168.30.10 / 9100 |
| `Allow Monitor to Proxmox monitoring` | Yes | ALLOW | 10000 | TCP | `AlphaSec-Observability` / `AG-Monitor-Collector` | `AlphaSec-Mgmt` / `AG-Proxmox-Nodes` / 9100, 8006 |
| `Allow Monitor to Proxmox NUT` | Yes | ALLOW | 10001 | TCP | `AlphaSec-Observability` / `AG-Monitor-Collector` | `AlphaSec-Mgmt` / .10, .13 / 3493 |
| `Allow Observability Web Egress` | Yes | ALLOW | 10000 | TCP | `AlphaSec-Observability` / `AG-Observability-Hosts` | External / `PG-Egress-Web` |
| `Allow Observability NTP Egress` | Yes | ALLOW | 10001 | UDP | `AlphaSec-Observability` / `AG-Observability-Hosts` | External / `PG-NTP` |
| `Allow NPM to monitor-01 web UIs` | Yes | ALLOW | 10000 | TCP | `AlphaSec-Access` / `AG-Reverse-Proxy` | `AlphaSec-Observability` / `AG-Monitor-Collector` / 3000, 8090, 9090 |
| `Allow Secure to monitor-01 break-glass` | Yes | ALLOW | 10000 | TCP | Internal / 192.168.50.241 | `AlphaSec-Observability` / `AG-Monitor-Collector` / 3000, 8090, 9090 |
| `Allow Automation to monitor-01 SSH` | Yes | ALLOW | 10001 | TCP | Internal / 192.168.40.36 | `AlphaSec-Observability` / `AG-Monitor-Collector` / 22 |
| `Allow Monitor DNS to Gateway` | Yes | ALLOW | 10000 | All | `AlphaSec-Observability` / `AG-Monitor-Collector` | Gateway / 53 |
| `Allow VPN Management Access to PeaNUT` | Yes | ALLOW | 10000 | TCP | Vpn / Management Access | `AlphaSec-Observability` / `AG-Monitor-Collector` / 8090 |
| `Allow dkadi MacBook Air M3 to PeaNUT` | Yes | ALLOW | 10002 | TCP | Internal / 192.168.10.27 | `AlphaSec-Observability` / `AG-Monitor-Collector` / 8090 |
| `Allow Monitor to Security monitoring` | Yes | ALLOW | 10000 | TCP | `AlphaSec-Observability` / `AG-Monitor-Collector` | `AlphaSec-Observability` / `AG-Security-Stack` / `PG-Node-Exporter` |
| `Allow splunk-siem to alert bot` | Yes | ALLOW | 10002 | TCP | `AlphaSec-Observability` / 192.168.72.3 | `AlphaSec-Observability` / 192.168.73.2 / 8080 |

| `Allow Workstations to AD` | Yes | ALLOW | 10000 | TCP+UDP | Internal / Secure, Secure Client | AlphaSec-Identity / AG-Domain-Controllers / PG-AD-Client |
| `Allow PAW to Windows Admin` | Yes | ALLOW | 10001 | TCP | Internal / AG-PAW | AlphaSec-Identity / AG-Identity-Servers / PG-Windows-Admin |
| `Allow Identity DNS to Gateway` | Yes | ALLOW | 10000 | TCP+UDP | AlphaSec-Identity / Any | Gateway / Any / 53 |
| `Allow Identity NTP to Gateway` | Yes | ALLOW | 10001 | UDP | AlphaSec-Identity / Any | Gateway / Any / 123 |
| `Allow Identity to Wazuh - Security-A` | Yes | ALLOW | 10000 | TCP | AlphaSec-Identity / Any | AlphaSec-Observability / 192.168.72.2 / Wazuh Ports |
| `Allow Identity Web Egress` | Yes | ALLOW | 10000 | TCP | AlphaSec-Identity / Any | External / Any / 80,443 |
| `Allow Monitor to Windows Exporter` | Yes | ALLOW | 10000 | TCP | AlphaSec-Observability / AG-Monitor-Collector | AlphaSec-Identity / AG-Identity-Servers / PG-Windows-Exporter |
| `Allow Identity NTP Egress` | Yes | ALLOW | 10001 | UDP | AlphaSec-Identity / Any | External / Any / 123 |
| `Block Identity Other External Egress` | Yes | BLOCK | 10002 | All | AlphaSec-Identity / Any | External / Any |
| `Allow Identity to Splunk - Security-A` | Yes | ALLOW | 10001 | TCP+UDP | AlphaSec-Identity / Any | AlphaSec-Observability / 192.168.72.3 / 514 |

## Identity Egress Order, 2026-09-09

I verified the saved AlphaSec-Identity-to-External order after reload: Allow Identity Web Egress (10000), Allow Identity NTP Egress (10001), then Block Identity Other External Egress (10002). NTP allows UDP 123 and showed 34 hits. The [change record](../Documentation/Change%20Records/Identity%20NTP%20and%20Client%20DNS%20-%202026-09-09.md) retains the screenshot and client DHCP DNS changes. The following verification describes the earlier 2026-09-07 state.

## Identity Policy Verification

I confirmed that Allow Workstations to AD selects exactly Secure and Secure Client in Internal, with no other source network. All nine identity policies are enabled, use BOTH IP versions and the Always schedule, and have no source port restriction. The table names every bound address and port group; Any and literal destinations have no address group.

I verified Identity-to-External indexes 10000 for Allow Identity Web Egress and 10001 for Block Identity Other External Egress. The ordering endpoint also returned two before-system entries and no after-system entries. The web rule binds explicit TCP ports 80,443, not PG-Egress-Web, following the earlier controller rejection of a port group with an any-in-zone destination. I did not reproduce that earlier failed write.

I found no SERVERS-A-to-Splunk policy in the complete 349-policy pre-change inventory, including generated rules. The only custom rule from AlphaSec-Servers to AlphaSec-Observability targets Wazuh at 192.168.72.2; the pair otherwise has a default block and a monitoring response rule. I left that gap unchanged. The [pattern check and creation readback](../Evidence/Identity%20Plane%20Network%20Preparation%20-%202026-09-07/Splunk%20Policy%20Creation%20and%20Readback.json) retain the result.

I checked splunk_siem through SSH Manager. SC4S was active/running with host networking, syslog-ng was running, and TCP and UDP 514 were listening on 0.0.0.0. CEF-specific listeners use 1514; I used the standard syslog port 514 for this policy. The initial sudo commands failed because a terminal/password was required; an unprivileged follow-up confirmed the listener and service state with exit code 0. The [host capture](../Evidence/Identity%20Plane%20Network%20Preparation%20-%202026-09-07/Splunk%20Listener%20Checks.json) includes the failures and follow-up.

I created Allow Identity to Splunk - Security-A with ID `6a9f71f1f9e5db2485af6cce`: ALLOW, enabled, TCP+UDP, AlphaSec-Identity / Any to AlphaSec-Observability / 192.168.72.3 / 514, index 10001, logging false, and `create_allow_respond: true`. The controller accepted the default and generated an enabled RELATED/ESTABLISHED return rule at index 30001. No address or port group is bound to the new policy.

The workstation AD, PAW administration, Wazuh, exporter, and Splunk rules have `create_allow_respond: true`. DNS, NTP, web egress, and the external block have it false. Only the external block logs matches. All 76 pre-existing custom policies compared unchanged after creation. I left Secure and Secure Client DHCP DNS unchanged and created no VPN access. This verifies controller preparation and the Splunk listener, not event delivery from the future Windows guests.

## Kasm Retirement Result

On 2026-08-19 I deleted 68 Kasm and LAB-MGMT policies one at a time after reviewing each mutation preview. Every before-and-after comparison removed exactly the approved policy and changed nothing else. The final controller readback returned 64 policies and no policy name or selector matching Kasm, LAB-MGMT, KASM-BROWSER, KASM-TRUSTED, MALWARE-OFFLINE, or EVIDENCE-QUARANTINE. The full dependency order and final counts are in [Kasm Workspaces Decommission](../../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspaces%20Decommission%20-%202026-08-19.md).

## Order-Sensitive Policy Sets

The Access-to-External trio and Observability-to-External trio use indexes 10000, 10001, and 10002:

1. Allow approved web egress.
2. Allow NTP.
3. Block every other IPv4 destination.

Automatic respond-policy generation is disabled for all six. The observability trio uses `AG-Observability-Hosts`, `PG-Egress-Web`, and `PG-NTP`. The final controller ordering readback matched those indexes.


The monitoring, NPM, break-glass, Wazuh, and automation paths retain response companions where required. A policy update can drop its description without failing, so I verify selectors, action, enabled state, index, protocol, and response behavior rather than treating a description as enforcement.



## Post-Consolidation Baseline

The controller generated 302 policies for zone defaults, state tracking, return companions, gateway services, & isolation immediately after the 2026-07-27 consolidation. The pre-change count was 370. That project reduced the generated set by 68 & the total set by 70:

| Measure | Before | After | Change |
|---|---:|---:|---:|
| Total policies | 431 | 361 | -70 |
| Custom policies | 61 | 59 | -2 |
| Controller-generated policies | 370 | 302 | -68 |
| Firewall zones | 16 | 14 | -2 |

The plan estimated 13 zones. The controller result is 14 because two zones were deleted: the empty cluster zone and one observability predecessor. The seven built-in zones remained.

## Enforcement Boundaries

A UniFi policy is not sufficient for traffic landing on a Proxmox node. The [Galaxy Datacenter firewall](../../../Compute/Galaxy/Configuration/Datacenter-Firewall.md) enforces independently. I test from the source host after changing a path.

The UniFi zone endpoint still returns no network membership. I read `firewall_zone_id` from each network instead, as recorded in [UniFi zone membership is absent from the zone-matrix endpoint](../Documentation/Troubleshooting/UniFi%20Zone%20Membership%20Absent%20From%20Zone-Matrix%20Endpoint%20-%202026-07-27.md).

The exact policy bodies, per-step diffs, rollback exports, and final service gate are indexed in the [consolidation evidence](../Evidence/Zone%20and%20Object%20Consolidation%20-%202026-07-27/Evidence-Index.md).

The retired 61-policy inventory is archived at [Firewall Policies - Pre-Consolidation - 2026-07-27](../../../../Archive/Infrastructure/Network/UniFi/Configuration/Firewall/Firewall%20Policies%20-%20Pre-Consolidation%20-%202026-07-27.md).
