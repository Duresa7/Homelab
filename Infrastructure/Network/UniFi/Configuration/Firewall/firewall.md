# UniFi Firewall Policies

**Created:** 2026-07-09  
**Last updated:** 2026-07-31

I verified both Galaxy PXE callback policies against the live controller on 2026-07-31. The full baseline remains the 2026-07-28 Kasm readback.

The gateway runs UniFi's zone-based V2 firewall. It has 121 user-defined policies after the two Galaxy PXE callback additions on 2026-07-31. The list below contains the durable custom policy inventory, including 56 LAB-MGMT and Kasm isolation policies.

## Recorded Custom Policy Inventory

Every custom policy uses the `Always` schedule. Three stateful isolation blocks use `NEW, INVALID`; the rest use connection state `ALL`. The source and destination columns name the live zone and selector. Policy names retain their historical wording even when a target zone has been consolidated.

| Policy | Enabled | Action | Index | Protocol | Source | Destination |
|---|---|---|---:|---|---|---|
| `Block DMZ to Internal` | Yes | BLOCK | 40000 | All | Dmz / Any | Internal / Any |
| `DMZ Allow List` | Yes | ALLOW | 10001 | All | Internal / 3 MACs | Dmz / Any |
| `Block DMZ to LAN` | Yes | BLOCK | 40001 | All | Dmz / Any | Internal / Any |
| `Allow VPN to <YOUR_ORG_NAME>-Mgmt` | Yes | ALLOW | 10000 | All | Vpn / Any | `<YOUR_ORG_NAME>`-Mgmt / Any |
| `Allow VPN to <YOUR_ORG_NAME>-Servers` | Yes | ALLOW | 10000 | All | Vpn / Any | `<YOUR_ORG_NAME>`-Servers / Any |
| `Allow <YOUR_ORG_NAME>-Mgmt to <YOUR_ORG_NAME>-Servers` | Yes | ALLOW | 10000 | All | `<YOUR_ORG_NAME>`-Mgmt / Any | `<YOUR_ORG_NAME>`-Servers / Any |
| `Allow Proxmox Nodes to Galaxy PXE` | Yes | ALLOW | 10000 | TCP | `<YOUR_ORG_NAME>`-Mgmt / `OBJ-Proxmox-Nodes` | Internal / 192.168.40.36 / 8080 |
| `Allow Server-Provision callbacks to Galaxy PXE` | Yes | ALLOW | 10005 | TCP | Internal / `Server-Provision` | Internal / 192.168.40.36 / 8080 |
| `Allow Internal to <YOUR_ORG_NAME>-Mgmt` | No | ALLOW | 10000 | All | Internal / Any | `<YOUR_ORG_NAME>`-Mgmt / Any |
| `Allow Internal to <YOUR_ORG_NAME>-Servers` | Yes | ALLOW | 10000 | All | Internal / Any | `<YOUR_ORG_NAME>`-Servers / Any |
| `Allow edge-01 to app-01 Web` | Yes | ALLOW | 10000 | TCP | Dmz / `edge-01` MAC | `<YOUR_ORG_NAME>`-Servers / 192.168.80.10 / `App Access` |
| `Allow Devices to Personal-A` | Yes | ALLOW | 10001 | All | Internal / 9 MACs | Internal / Personal-A |
| `Block Trusted to Personal-A` | Yes | BLOCK | 10002 | All | Internal / Trusted | Internal / Personal-A |
| `Device Access --> Proxmox` | Yes | ALLOW | 10001 | All | Internal / 4 MACs | `<YOUR_ORG_NAME>`-Mgmt / `Proxmox-Admin-Ports` |
| `Allow <YOUR_ORG_NAME>-Servers to Portainer Edge` | Yes | ALLOW | 10000 | All | `<YOUR_ORG_NAME>`-Servers / Any | Internal / 192.168.40.35 / `Portainer Edge Agents` |
| `Allow Identity Sync Service Connection` | Yes | ALLOW | 10000 | All | External / Any | Gateway / TCP 9543 group |
| `VPN: Temp Ban` | Yes | BLOCK | 10000 | All | Vpn / Temp | Internal / Personal-A, Secure, Secure Client, Management |
| `VPN: Temp #2` | Yes | BLOCK | 10001 | All | Vpn / Temp | `<YOUR_ORG_NAME>`-Servers / Any |
| `Docker-main Allowed -> Server` | Yes | ALLOW | 10002 | TCP | Internal / `docker-main` MAC | `<YOUR_ORG_NAME>`-Mgmt / MGMT-A / 8006 |
| `Docker -> Jedi PC` | Yes | ALLOW | 10003 | All | Internal / `docker-main` MAC | Internal / Secure |
| `Allow Internal to <YOUR_ORG_NAME>-Access` | Yes | ALLOW | 10000 | All | Internal / Any | `<YOUR_ORG_NAME>`-Access / Any |
| `Allow VPN to <YOUR_ORG_NAME>-Access` | Yes | ALLOW | 10000 | All | Vpn / Any | `<YOUR_ORG_NAME>`-Access / Any |
| `Allow Internal to <YOUR_ORG_NAME>-Security` | Yes | ALLOW | 10003 | All | Internal / Any | `<YOUR_ORG_NAME>`-Observability / Any |
| `Allow VPN to <YOUR_ORG_NAME>-Security` | Yes | ALLOW | 10001 | All | Vpn / Any | `<YOUR_ORG_NAME>`-Observability / Any |
| `Allow Access Services Web Egress` | Yes | ALLOW | 10000 | TCP | `<YOUR_ORG_NAME>`-Access / .2, .3, .6 | External / `PG-Egress-Web` |
| `Allow Access Services NTP Egress` | Yes | ALLOW | 10001 | UDP | `<YOUR_ORG_NAME>`-Access / .2, .3, .6 | External / `PG-NTP` |
| `Block <YOUR_ORG_NAME>-Access Other External Egress` | Yes | BLOCK | 10002 | All | `<YOUR_ORG_NAME>`-Access / Any | External / Any |
| `Block Observability Other External Egress` | Yes | BLOCK | 10002 | All | `<YOUR_ORG_NAME>`-Observability / `OBJ-Observability-Hosts` | External / Any |
| `Allow <YOUR_ORG_NAME>-Servers to Wazuh - Security-A` | Yes | ALLOW | 10000 | TCP | `<YOUR_ORG_NAME>`-Servers / Any | `<YOUR_ORG_NAME>`-Observability / 192.168.72.2 / `Wazuh Ports` |
| `Allow DMZ to Wazuh - Security-A` | Yes | ALLOW | 10000 | TCP | Dmz / `edge-01` MAC | `<YOUR_ORG_NAME>`-Observability / 192.168.72.2 / `Wazuh Ports` |
| `Allow VPN --> Internal Zone` | Yes | ALLOW | 10001 | All | Vpn / Management Access | Internal / Any |
| `Allow Device --> media-01` | Yes | ALLOW | 10004 | All | Internal / 2 MACs | Internal / Personal-A |
| `Allow NPM to media-01 web UIs` | Yes | ALLOW | 10000 | TCP | `<YOUR_ORG_NAME>`-Access / `OBJ-Reverse-Proxy` | Internal / 192.168.40.42 / 5055, 7878, 8080, 8096, 8989, 9696 |
| `Allow NPM to ansible-01 Semaphore` | Yes | ALLOW | 10001 | TCP | `<YOUR_ORG_NAME>`-Access / `OBJ-Reverse-Proxy` | Internal / 192.168.40.36 / 3000 |
| `Allow NPM to docker-main web UIs` | Yes | ALLOW | 10002 | TCP | `<YOUR_ORG_NAME>`-Access / `OBJ-Reverse-Proxy` | Internal / 192.168.40.35 / 2283, 3000, 3001, 6060, 8080, 8384, 9443 |
| `Allow docker-network to Portainer Edge` | Yes | ALLOW | 10003 | TCP | `<YOUR_ORG_NAME>`-Access / 192.168.85.2 | Internal / 192.168.40.35 / `Portainer Edge Agents` |
| `Allow NPM to alpha-prod-01 TS3 Manager` | Yes | ALLOW | 10000 | TCP | `<YOUR_ORG_NAME>`-Access / 192.168.85.2 | `<YOUR_ORG_NAME>`-Servers / 192.168.80.118 / 9000 |
| `Allow NPM to kasm-01 web UI` | Yes | ALLOW | 10000 | TCP | `<YOUR_ORG_NAME>`-Access / 192.168.85.2 | LAB-MGMT / 192.168.78.10 / 443 |
| `Allow NPM to security-01 Wazuh` | Yes | ALLOW | 10001 | TCP | `<YOUR_ORG_NAME>`-Access / `OBJ-Reverse-Proxy` | `<YOUR_ORG_NAME>`-Observability / 192.168.72.2 / 443 |
| `Allow NPM to splunk-siem web UI` | Yes | ALLOW | 10002 | TCP | `<YOUR_ORG_NAME>`-Access / `OBJ-Reverse-Proxy` | `<YOUR_ORG_NAME>`-Observability / 192.168.72.3 / 8000 |
| `KASM Allow KASM-BROWSER DHCP to Gateway` | Yes | ALLOW | 10000 | UDP | KASM-BROWSER / 68 | Gateway / 67 |
| `KASM Allow KASM-BROWSER NTP to Gateway` | Yes | ALLOW | 10002 | UDP | KASM-BROWSER / Any | Gateway / 123 |
| `KASM Block KASM-BROWSER Other Gateway` | Yes | BLOCK | 10003 | All | KASM-BROWSER / Any | Gateway / Any |
| `KASM Allow KASM-TRUSTED DHCP to Gateway` | Yes | ALLOW | 10000 | UDP | KASM-TRUSTED / 68 | Gateway / 67 |
| `KASM Allow KASM-TRUSTED NTP to Gateway` | Yes | ALLOW | 10001 | UDP | KASM-TRUSTED / Any | Gateway / 123 |
| `KASM Block KASM-TRUSTED Other Gateway` | Yes | BLOCK | 10002 | All | KASM-TRUSTED / Any | Gateway / Any |
| `KASM Allow MALWARE-OFFLINE DHCP to Gateway` | Yes | ALLOW | 10000 | UDP | MALWARE-OFFLINE / 68 | Gateway / 67 |
| `KASM Block MALWARE-OFFLINE Other Gateway` | Yes | BLOCK | 10001 | All | MALWARE-OFFLINE / Any | Gateway / Any |
| `KASM Allow EVIDENCE-QUARANTINE DHCP to Gateway` | Yes | ALLOW | 10000 | UDP | EVIDENCE-QUARANTINE / 68 | Gateway / 67 |
| `KASM Block EVIDENCE-QUARANTINE Other Gateway` | Yes | BLOCK | 10001 | All | EVIDENCE-QUARANTINE / Any | Gateway / Any |
| `KASM Block MALWARE-OFFLINE External` | Yes | BLOCK | 10000 | All | MALWARE-OFFLINE / Any | External / Any |
| `KASM Block EVIDENCE-QUARANTINE External` | Yes | BLOCK | 10000 | All | EVIDENCE-QUARANTINE / Any | External / Any |
| `KASM Allow KASM-TRUSTED to External` | Yes | ALLOW | 10000 | All | KASM-TRUSTED / Any | External / Any |
| `LABMGMT Allow Trusted and Personal-A to kasm-01` | Yes | ALLOW | 10000 | TCP | Internal / Trusted, Personal-A | LAB-MGMT / 192.168.78.10 / 22, 443 |
| `LABMGMT Allow Management Access to kasm-01` | Yes | ALLOW | 10000 | TCP | Vpn / Management Access | LAB-MGMT / 192.168.78.10 / 22, 443 |
| `LABMGMT Allow Jedi PC to kasm-01` | Yes | ALLOW | 10001 | TCP | Internal / 192.168.50.241 | LAB-MGMT / 192.168.78.10 / 22, 443 |
| `LABMGMT Allow monitor-01 to kasm-01 node_exporter` | Yes | ALLOW | 10000 | TCP | `<YOUR_ORG_NAME>`-Observability / 192.168.73.2 | LAB-MGMT / 192.168.78.10 / 9100 |
| `LABMGMT Block Other Internal to LAB-MGMT` | Yes | BLOCK | 10002 | All | Internal / Any | LAB-MGMT / Any |
| `LABMGMT Block Other VPN to LAB-MGMT` | Yes | BLOCK | 10001 | All | Vpn / Any | LAB-MGMT / Any |
| `LABMGMT Block to Internal` | Yes | BLOCK | 10000 | All / `NEW, INVALID` | LAB-MGMT / Any | Internal / Any |
| `LABMGMT Block to <YOUR_ORG_NAME>-Servers` | Yes | BLOCK | 10000 | All | LAB-MGMT / Any | `<YOUR_ORG_NAME>`-Servers / Any |
| `LABMGMT Block to <YOUR_ORG_NAME>-Mgmt` | Yes | BLOCK | 10000 | All | LAB-MGMT / Any | `<YOUR_ORG_NAME>`-Mgmt / Any |
| `LABMGMT Block to <YOUR_ORG_NAME>-Access` | Yes | BLOCK | 10000 | All / `NEW, INVALID` | LAB-MGMT / Any | `<YOUR_ORG_NAME>`-Access / Any |
| `LABMGMT Block to <YOUR_ORG_NAME>-Observability` | Yes | BLOCK | 10000 | All / `NEW, INVALID` | LAB-MGMT / Any | `<YOUR_ORG_NAME>`-Observability / Any |
| `LABMGMT Block to Gateway` | Yes | BLOCK | 10000 | All | LAB-MGMT / Any | Gateway / Any |
| `LABMGMT Block to KASM-BROWSER` | Yes | BLOCK | 10000 | All | LAB-MGMT / Any | KASM-BROWSER / Any |
| `LABMGMT Block to KASM-TRUSTED` | Yes | BLOCK | 10000 | All | LAB-MGMT / Any | KASM-TRUSTED / Any |
| `LABMGMT Block to MALWARE-OFFLINE` | Yes | BLOCK | 10000 | All | LAB-MGMT / Any | MALWARE-OFFLINE / Any |
| `LABMGMT Block to EVIDENCE-QUARANTINE` | Yes | BLOCK | 10000 | All | LAB-MGMT / Any | EVIDENCE-QUARANTINE / Any |
| `LABMGMT Allow to External` | Yes | ALLOW | 10000 | All | LAB-MGMT / Any | External / Any |
| `KASM Allow KASM-BROWSER to MALWARE-OFFLINE` | Yes | ALLOW | 10000 | All | KASM-BROWSER / Any | MALWARE-OFFLINE / Any |
| `KASM Block MALWARE-OFFLINE to KASM-BROWSER` | Yes | BLOCK | 10000 | All / `NEW, INVALID` | MALWARE-OFFLINE / Any | KASM-BROWSER / Any |
| `KASM Block KASM-BROWSER to EVIDENCE-QUARANTINE` | Yes | BLOCK | 10000 | All | KASM-BROWSER / Any | EVIDENCE-QUARANTINE / Any |
| `KASM Block MALWARE-OFFLINE to EVIDENCE-QUARANTINE` | Yes | BLOCK | 10000 | All | MALWARE-OFFLINE / Any | EVIDENCE-QUARANTINE / Any |
| `KASM Block EVIDENCE-QUARANTINE to KASM-BROWSER` | Yes | BLOCK | 10000 | All | EVIDENCE-QUARANTINE / Any | KASM-BROWSER / Any |
| `KASM Block EVIDENCE-QUARANTINE to MALWARE-OFFLINE` | Yes | BLOCK | 10000 | All | EVIDENCE-QUARANTINE / Any | MALWARE-OFFLINE / Any |
| `KASM Block KASM-BROWSER to LAB-MGMT` | Yes | BLOCK | 10000 | All | KASM-BROWSER / Any | LAB-MGMT / Any |
| `KASM Block KASM-BROWSER to KASM-TRUSTED` | Yes | BLOCK | 10000 | All | KASM-BROWSER / Any | KASM-TRUSTED / Any |
| `KASM Block KASM-BROWSER to Internal` | Yes | BLOCK | 10000 | All | KASM-BROWSER / Any | Internal / Any |
| `KASM Block KASM-BROWSER to <YOUR_ORG_NAME>-Servers` | Yes | BLOCK | 10000 | All | KASM-BROWSER / Any | `<YOUR_ORG_NAME>`-Servers / Any |
| `KASM Block KASM-BROWSER to <YOUR_ORG_NAME>-Mgmt` | Yes | BLOCK | 10000 | All | KASM-BROWSER / Any | `<YOUR_ORG_NAME>`-Mgmt / Any |
| `KASM Block KASM-BROWSER to <YOUR_ORG_NAME>-Access` | Yes | BLOCK | 10000 | All | KASM-BROWSER / Any | `<YOUR_ORG_NAME>`-Access / Any |
| `KASM Block KASM-BROWSER to <YOUR_ORG_NAME>-Observability` | Yes | BLOCK | 10000 | All | KASM-BROWSER / Any | `<YOUR_ORG_NAME>`-Observability / Any |
| `KASM Block MALWARE-OFFLINE to LAB-MGMT` | Yes | BLOCK | 10000 | All | MALWARE-OFFLINE / Any | LAB-MGMT / Any |
| `KASM Block MALWARE-OFFLINE to KASM-TRUSTED` | Yes | BLOCK | 10000 | All | MALWARE-OFFLINE / Any | KASM-TRUSTED / Any |
| `KASM Block MALWARE-OFFLINE to Internal` | Yes | BLOCK | 10000 | All | MALWARE-OFFLINE / Any | Internal / Any |
| `KASM Block MALWARE-OFFLINE to <YOUR_ORG_NAME>-Servers` | Yes | BLOCK | 10000 | All | MALWARE-OFFLINE / Any | `<YOUR_ORG_NAME>`-Servers / Any |
| `KASM Block MALWARE-OFFLINE to <YOUR_ORG_NAME>-Mgmt` | Yes | BLOCK | 10000 | All | MALWARE-OFFLINE / Any | `<YOUR_ORG_NAME>`-Mgmt / Any |
| `KASM Block MALWARE-OFFLINE to <YOUR_ORG_NAME>-Access` | Yes | BLOCK | 10000 | All | MALWARE-OFFLINE / Any | `<YOUR_ORG_NAME>`-Access / Any |
| `KASM Block MALWARE-OFFLINE to <YOUR_ORG_NAME>-Observability` | Yes | BLOCK | 10000 | All | MALWARE-OFFLINE / Any | `<YOUR_ORG_NAME>`-Observability / Any |
| `KASM Block EVIDENCE-QUARANTINE to LAB-MGMT` | Yes | BLOCK | 10000 | All | EVIDENCE-QUARANTINE / Any | LAB-MGMT / Any |
| `KASM Block EVIDENCE-QUARANTINE to KASM-TRUSTED` | Yes | BLOCK | 10000 | All | EVIDENCE-QUARANTINE / Any | KASM-TRUSTED / Any |
| `KASM Block EVIDENCE-QUARANTINE to Internal` | Yes | BLOCK | 10000 | All | EVIDENCE-QUARANTINE / Any | Internal / Any |
| `KASM Block EVIDENCE-QUARANTINE to <YOUR_ORG_NAME>-Servers` | Yes | BLOCK | 10000 | All | EVIDENCE-QUARANTINE / Any | `<YOUR_ORG_NAME>`-Servers / Any |
| `KASM Block EVIDENCE-QUARANTINE to <YOUR_ORG_NAME>-Mgmt` | Yes | BLOCK | 10000 | All | EVIDENCE-QUARANTINE / Any | `<YOUR_ORG_NAME>`-Mgmt / Any |
| `KASM Block EVIDENCE-QUARANTINE to <YOUR_ORG_NAME>-Access` | Yes | BLOCK | 10000 | All | EVIDENCE-QUARANTINE / Any | `<YOUR_ORG_NAME>`-Access / Any |
| `KASM Block EVIDENCE-QUARANTINE to <YOUR_ORG_NAME>-Observability` | Yes | BLOCK | 10000 | All | EVIDENCE-QUARANTINE / Any | `<YOUR_ORG_NAME>`-Observability / Any |
| `KASM Block KASM-TRUSTED to KASM-BROWSER` | Yes | BLOCK | 10000 | All | KASM-TRUSTED / Any | KASM-BROWSER / Any |
| `KASM Block KASM-TRUSTED to MALWARE-OFFLINE` | Yes | BLOCK | 10000 | All | KASM-TRUSTED / Any | MALWARE-OFFLINE / Any |
| `KASM Block KASM-TRUSTED to EVIDENCE-QUARANTINE` | Yes | BLOCK | 10000 | All | KASM-TRUSTED / Any | EVIDENCE-QUARANTINE / Any |
| `KASM Block KASM-TRUSTED to LAB-MGMT` | Yes | BLOCK | 10000 | All | KASM-TRUSTED / Any | LAB-MGMT / Any |
| `KASM Block KASM-TRUSTED to Internal` | Yes | BLOCK | 10000 | All | KASM-TRUSTED / Any | Internal / Any |
| `KASM Block KASM-TRUSTED to <YOUR_ORG_NAME>-Servers` | Yes | BLOCK | 10000 | All | KASM-TRUSTED / Any | `<YOUR_ORG_NAME>`-Servers / Any |
| `KASM Block KASM-TRUSTED to <YOUR_ORG_NAME>-Mgmt` | Yes | BLOCK | 10000 | All | KASM-TRUSTED / Any | `<YOUR_ORG_NAME>`-Mgmt / Any |
| `KASM Block KASM-TRUSTED to <YOUR_ORG_NAME>-Access` | Yes | BLOCK | 10000 | All | KASM-TRUSTED / Any | `<YOUR_ORG_NAME>`-Access / Any |
| `KASM Block KASM-TRUSTED to <YOUR_ORG_NAME>-Observability` | Yes | BLOCK | 10000 | All | KASM-TRUSTED / Any | `<YOUR_ORG_NAME>`-Observability / Any |
| `Allow Monitor to Personal-A monitoring` | Yes | ALLOW | 10000 | TCP | `<YOUR_ORG_NAME>`-Observability / `OBJ-Monitor-Collector` | Internal / .35, .36, .39, .42 / `PG-Node-Exporter` |
| `Allow Monitor to <YOUR_ORG_NAME>-Servers monitoring` | Yes | ALLOW | 10000 | TCP | `<YOUR_ORG_NAME>`-Observability / `OBJ-Monitor-Collector` | `<YOUR_ORG_NAME>`-Servers / .10, .118 / `PG-Node-Exporter` |
| `Allow Monitor to <YOUR_ORG_NAME>-Access monitoring` | Yes | ALLOW | 10000 | TCP | `<YOUR_ORG_NAME>`-Observability / `OBJ-Monitor-Collector` | `<YOUR_ORG_NAME>`-Access / `OBJ-Reverse-Proxy` / 9100, 9101, 443 |
| `Allow Monitor to DMZ monitoring` | Yes | ALLOW | 10000 | TCP | `<YOUR_ORG_NAME>`-Observability / `OBJ-Monitor-Collector` | Dmz / 192.168.90.10 / 9100 |
| `Allow Monitor to Proxmox monitoring` | Yes | ALLOW | 10000 | TCP | `<YOUR_ORG_NAME>`-Observability / `OBJ-Monitor-Collector` | `<YOUR_ORG_NAME>`-Mgmt / `OBJ-Proxmox-Nodes` / 9100, 8006 |
| `Allow Monitor to Proxmox NUT` | Yes | ALLOW | 10001 | TCP | `<YOUR_ORG_NAME>`-Observability / `OBJ-Monitor-Collector` | `<YOUR_ORG_NAME>`-Mgmt / .10, .13 / 3493 |
| `Allow Observability Web Egress` | Yes | ALLOW | 10000 | TCP | `<YOUR_ORG_NAME>`-Observability / `OBJ-Observability-Hosts` | External / `PG-Egress-Web` |
| `Allow Observability NTP Egress` | Yes | ALLOW | 10001 | UDP | `<YOUR_ORG_NAME>`-Observability / `OBJ-Observability-Hosts` | External / `PG-NTP` |
| `Allow NPM to monitor-01 web UIs` | Yes | ALLOW | 10000 | TCP | `<YOUR_ORG_NAME>`-Access / `OBJ-Reverse-Proxy` | `<YOUR_ORG_NAME>`-Observability / `OBJ-Monitor-Collector` / 3000, 8090, 9090 |
| `Allow Secure to monitor-01 break-glass` | Yes | ALLOW | 10000 | TCP | Internal / 192.168.50.241 | `<YOUR_ORG_NAME>`-Observability / `OBJ-Monitor-Collector` / 3000, 8090, 9090 |
| `Allow Automation to monitor-01 SSH` | Yes | ALLOW | 10001 | TCP | Internal / 192.168.40.36 | `<YOUR_ORG_NAME>`-Observability / `OBJ-Monitor-Collector` / 22 |
| `Allow Monitor DNS to Gateway` | Yes | ALLOW | 10000 | All | `<YOUR_ORG_NAME>`-Observability / `OBJ-Monitor-Collector` | Gateway / 53 |
| `Allow VPN Management Access to PeaNUT` | Yes | ALLOW | 10000 | TCP | Vpn / Management Access | `<YOUR_ORG_NAME>`-Observability / `OBJ-Monitor-Collector` / 8090 |
| `Allow <YOUR_ADMIN_USERNAME> MacBook Air M3 to PeaNUT` | Yes | ALLOW | 10002 | TCP | Internal / 192.168.10.27 | `<YOUR_ORG_NAME>`-Observability / `OBJ-Monitor-Collector` / 8090 |
| `Allow Monitor to Security monitoring` | Yes | ALLOW | 10000 | TCP | `<YOUR_ORG_NAME>`-Observability / `OBJ-Monitor-Collector` | `<YOUR_ORG_NAME>`-Observability / `OBJ-Security-Stack` / `PG-Node-Exporter` |

## Order-Sensitive Policy Sets

The Access-to-External trio and Observability-to-External trio use indexes 10000, 10001, and 10002:

1. Allow approved web egress.
2. Allow NTP.
3. Block every other IPv4 destination.

Automatic respond-policy generation is disabled for all six. The observability trio uses `OBJ-Observability-Hosts`, `PG-Egress-Web`, and `PG-NTP`. The final controller ordering readback matched those indexes.

The KASM-TRUSTED gateway set uses DHCP at 10000, NTP at 10001, and the gateway catchall block at 10002. I read those indexes back from the controller after creation. The external allow and every inter-zone block use index 10000 within their separate source and destination zone pairs.

The monitoring, NPM, break-glass, Wazuh, and automation paths retain response companions where required. A policy update can drop its description without failing, so I verify selectors, action, enabled state, index, protocol, and response behavior rather than treating a description as enforcement.

The two LAB-MGMT inbound allow rules precede their zone-wide catchall blocks. The LAB-MGMT-to-Internal and MALWARE-OFFLINE-to-KASM-BROWSER blocks match only new and invalid connections so established replies to an allowed inbound connection survive. The original source tests and order-sensitive state choices are retained in [Kasm Session Isolation](../../../../../Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Session%20Isolation%20-%202026-07-28.md). The KASM-TRUSTED policy verification and source tests are retained in [Kasm Workspace Build-Out](../../../../../Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspace%20Build-Out%20-%202026-07-28.md).

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

A UniFi policy is not sufficient for traffic landing on a Proxmox node. The [Galaxy Datacenter firewall](../../../../Compute/Galaxy/Configuration/Firewall/Galaxy%20Data%20Center%20Firewall.md) enforces independently. I test from the source host after changing a path.

The UniFi zone endpoint still returns no network membership. I read `firewall_zone_id` from each network instead, as recorded in [UniFi zone membership is absent from the zone-matrix endpoint](../../Documentation/Troubleshooting/UniFi%20Zone%20Membership%20Absent%20From%20Zone-Matrix%20Endpoint%20-%202026-07-27.md).

The exact policy bodies, per-step diffs, rollback exports, and final service gate are indexed in the [consolidation evidence](../../Evidence/Zone%20and%20Object%20Consolidation%20-%202026-07-27/Evidence-Index.md).

The retired 61-policy inventory is archived at [Firewall Policies - Pre-Consolidation - 2026-07-27](../../../../../Archive/Infrastructure/Network/UniFi/Configuration/Firewall/Firewall%20Policies%20-%20Pre-Consolidation%20-%202026-07-27.md).
