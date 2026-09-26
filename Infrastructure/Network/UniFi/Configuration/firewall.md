# UniFi Firewall Policies

**Created:** 2026-07-09  
**Last updated:** 2026-09-25

Ahsoka Gateway runs UniFi's zone-based firewall. The controller holds 89 user-defined policies, 81 allows and eight blocks, counted after `Allow App Portal to Identity LDAPS` on 2026-09-20. The table below lists all 89. Generated zone defaults and response companions are not listed.

**Last verified against the controller:** 2026-09-24, for the 13 policies that name Nginx Proxy Manager (`Allow NPM to media-01 web UIs` carries 5055, 7878, 8080, 8096, 8989 and 9696, with no 18080). The last full policy readback was 2026-09-16.

## Recent changes

- 2026-09-24: TCP 18080 was no longer in `Allow NPM to media-01 web UIs`; I added it for Weebarr on 2026-09-21 and have no record of its removal. [Weebarr Retirement](../../../../Archive/Platforms/Weebarr/Documentation/Change%20Records/Retirement%20-%202026-09-25.md).
- 2026-09-20: `Allow App Portal to Identity LDAPS`, TCP 636 from `docker-main` to both domain controllers. [Directory Sign-In for the Portal](../../../../Platforms/App%20Portal/Documentation/Change%20Records/Directory%20Sign-In%20for%20the%20Portal%20-%202026-09-20.md).
- 2026-09-19: `Allow HQ-WS001 to NPM HTTPS` replaced `Allow Identity to App Portal`, and TCP 3004 joined `Allow NPM to docker-main web UIs`. [Internal HTTPS record](../../../../Platforms/App%20Portal/Documentation/Change%20Records/Internal%20HTTPS%2C%20ObiPC%20Enrollment%20and%20the%20First%20Self-Update%20-%202026-09-19.md).

## Policy Inventory

Every custom policy uses the `Always` schedule. The Source and Destination columns name the live zone and selector. Policy names keep their original wording after a zone rename, so seven still read `AlphSec` or `A-Servers` while the zones they point at read `AlphaSec`.

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
| `Allow Secure and Secure Client to WAC HTTPS` | Yes | ALLOW | 10003 | TCP | Internal / Secure and Secure Client networks | `AlphaSec-Identity` / 192.168.65.12 / 443 |
| `Allow MacBook Air and Pixel to WAC HTTPS` | Yes | ALLOW | 10004 | TCP | Internal / MacBook Air M3 and Pixel device selectors | `AlphaSec-Identity` / 192.168.65.12 / 443 |
| `Allow WAC to Secure Client WinRM` | Yes | ALLOW | 10000 | TCP | `AlphaSec-Identity` / 192.168.65.12 | Internal / Secure Client network / 5985,5986 |
| `Allow Action1 Deployer to Secure Client` | Yes | ALLOW | 10001 | TCP (IPv4) | `AlphaSec-Identity` / 192.168.65.12 | Internal / Secure Client network / 135,139,445,49152-65535 |
| `Allow Admin Networks to Identity RDP` | Yes | ALLOW | 10005 | TCP+UDP (IPv4) | Internal / Trusted and Secure networks | `AlphaSec-Identity` / 192.168.65.10, .11, .12, .20 / 3389 |
| `Allow Personal-A Hosts to Identity RDP` | Yes | ALLOW | 10006 | TCP+UDP (IPv4) | Internal / 192.168.40.179, 192.168.40.39 | `AlphaSec-Identity` / 192.168.65.10, .11, .12, .20 / 3389 |
| `Allow VPN to Identity RDP` | Yes | ALLOW | 10000 | TCP+UDP (IPv4) | Vpn / Management Access network | `AlphaSec-Identity` / 192.168.65.10, .11, .12, .20 / 3389 |
| `Allow Identity to MeshCentral` | Yes | ALLOW | 10002 | TCP (IPv4) | `AlphaSec-Identity` / 192.168.65.12, 192.168.65.20 | Internal / 192.168.40.39 / 443 |
| `Allow HQ-WS001 to NPM HTTPS` | Yes | ALLOW | 10001 | TCP (IPv4) | `AlphaSec-Identity` / 192.168.65.20 | `AlphaSec-Access` / 192.168.85.2 / 443 |
| `Allow App Portal to Identity LDAPS` | Yes | ALLOW | 10008 | TCP (IPv4) | Internal / 192.168.40.35 | `AlphaSec-Identity` / 192.168.65.10, .11 / 636 |
| `Allow Secure to HQ-WS001 SSH` | Yes | ALLOW | 10007 | TCP (IPv4) | Internal / Secure (VLAN 50) | `AlphaSec-Identity` / 192.168.65.20 / 22 |
| `Allow NPM to docker-blue MeshCentral` | Yes | ALLOW | 10006 | TCP (IPv4) | `AlphaSec-Access` / 192.168.85.2 | Internal / 192.168.40.39 / 443 |
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
| `Allow NPM to docker-main web UIs` | Yes | ALLOW | 10002 | TCP | `AlphaSec-Access` / `AG-Reverse-Proxy` | Internal / 192.168.40.35 / 2283, 3000, 3001, 3002, 3003, 3004, 6060 |
| `Allow alpha-prod-01 Hawser to NPM HTTPS` | Yes | ALLOW | 10000 | TCP (IPv4) | `AlphaSec-Servers` / 192.168.80.118 | `AlphaSec-Access` / 192.168.85.2 / 443 |
| `Allow security-01 Hawser to NPM HTTPS` | Yes | ALLOW | 10001 | TCP (IPv4) | `AlphaSec-Observability` / 192.168.72.2 | `AlphaSec-Access` / 192.168.85.2 / 443 |
| `Allow NPM to docker-main CLI Proxy API` | Yes | ALLOW | 10004 | TCP | `AlphaSec-Access` / 192.168.85.2 | Internal / 192.168.40.35 / 8317 |
| `Allow NPM to docker-blue Executor` | Yes | ALLOW | 10005 | TCP | `AlphaSec-Access` / 192.168.85.2 | Internal / 192.168.40.39 / 4788 |
| `Allow docker-blue SSH Manager to Proxmox` | Yes | ALLOW | 10004 | TCP | Internal / 192.168.40.39 | `AlphaSec-Mgmt` / .10, .11, .12, .13, .14 / 22 |
| `Allow ubuntu-dev to Proxmox` | Yes | ALLOW | 10003 | All | Internal / 192.168.40.179 | `AlphaSec-Mgmt` / Any / `Proxmox GUI+SSH` port group |
| `Allow Surface SSH replies to Automation` | Yes | ALLOW | 10000 | TCP (IPv4) | Internal / 192.168.10.211 / source port 22 | Internal / 192.168.40.179, 192.168.40.39 |
| `Allow NPM to alpha-prod-01 TS3 Manager` | Yes | ALLOW | 10000 | TCP | `AlphaSec-Access` / 192.168.85.2 | `AlphaSec-Servers` / 192.168.80.118 / 9000 |
| `Allow NPM to security-01 Wazuh` | Yes | ALLOW | 10001 | TCP | `AlphaSec-Access` / `AG-Reverse-Proxy` | `AlphaSec-Observability` / 192.168.72.2 / 443 |
| `Allow NPM to splunk-siem web UI` | Yes | ALLOW | 10002 | TCP | `AlphaSec-Access` / `AG-Reverse-Proxy` | `AlphaSec-Observability` / 192.168.72.3 / 8000 |
| `Allow Monitor to Personal-A monitoring` | Yes | ALLOW | 10000 | TCP | `AlphaSec-Observability` / `AG-Monitor-Collector` | Internal / .35, .36, .39, .42, .179 / `PG-Node-Exporter` |
| `Allow Monitor to A-Servers monitoring` | Yes | ALLOW | 10000 | TCP | `AlphaSec-Observability` / `AG-Monitor-Collector` | `AlphaSec-Servers` / .10, .118 / `PG-Node-Exporter` |
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
| `Allow Workstations to AD` | Yes | ALLOW | 10000 | TCP+UDP | Internal / Secure, Secure Client | `AlphaSec-Identity` / `AG-Domain-Controllers` / `PG-AD-Client` |
| `Allow PAW to Windows Admin` | Yes | ALLOW | 10001 | TCP | Internal / `AG-PAW` | `AlphaSec-Identity` / `AG-Identity-Servers` / `PG-Windows-Admin` |
| `Allow Identity DNS to Gateway` | Yes | ALLOW | 10000 | TCP+UDP | `AlphaSec-Identity` / Any | Gateway / Any / 53 |
| `Allow Identity NTP to Gateway` | Yes | ALLOW | 10001 | UDP | `AlphaSec-Identity` / Any | Gateway / Any / 123 |
| `Allow Identity to Wazuh - Security-A` | Yes | ALLOW | 10000 | TCP | `AlphaSec-Identity` / Any | `AlphaSec-Observability` / 192.168.72.2 / `Wazuh Ports` |
| `Allow Identity Web Egress` | Yes | ALLOW | 10000 | TCP | `AlphaSec-Identity` / Any | External / Any / 80, 443 |
| `Allow Monitor to Windows Exporter` | Yes | ALLOW | 10000 | TCP | `AlphaSec-Observability` / `AG-Monitor-Collector` | `AlphaSec-Identity` / `AG-Identity-Servers` / `PG-Windows-Exporter` |
| `Allow Identity NTP Egress` | Yes | ALLOW | 10001 | UDP | `AlphaSec-Identity` / Any | External / Any / 123 |
| `Block Identity Other External Egress` | Yes | BLOCK | 10002 | All | `AlphaSec-Identity` / Any | External / Any |
| `Allow Identity to Splunk - Security-A` | Yes | ALLOW | 10001 | TCP+UDP | `AlphaSec-Identity` / Any | `AlphaSec-Observability` / 192.168.72.3 / 514 |
| `Allow Automation to Identity SSH` | Yes | ALLOW | 10002 | TCP | Internal / `AG-Automation-Hosts` | `AlphaSec-Identity` / `AG-Identity-Servers` / 22 |

## Order-Sensitive Policy Sets

The Access-to-External trio and Observability-to-External trio use indexes 10000, 10001, and 10002:

1. Allow web egress to `PG-Egress-Web`.
2. Allow NTP.
3. Block every other IPv4 destination.

Automatic respond-policy generation is disabled for all six. The observability trio uses `AG-Observability-Hosts`, `PG-Egress-Web`, and `PG-NTP`. The final controller ordering readback matched those indexes.

The monitoring, NPM, break-glass, Wazuh and automation paths keep response companions where they need them.

## Enforcement Boundaries

A UniFi policy is not sufficient for traffic landing on a Proxmox node. The [Galaxy Datacenter firewall](../../../Compute/Galaxy/Configuration/Datacenter-Firewall.md) enforces independently. I test from the source host after changing a path.

The UniFi zone endpoint still returns no network membership. I read `firewall_zone_id` from each network instead, as recorded in [UniFi zone membership is absent from the zone-matrix endpoint](../Documentation/Troubleshooting/Zone%20Membership%20Absent%20From%20Zone-Matrix%20Endpoint%20-%202026-07-27.md).

`Allow Internal to AlphSec-Servers` admits every Internal network to SERVERS-A on every port. That includes Management, Server-Provision and Personal-A.

## Operating notes

- An interrupted create still creates. On 2026-09-19 a cancelled creation call left two identical policies one millisecond apart; I read the live list and deleted the second.
- A deleted policy is not enforced at once. On 2026-09-19 a probe still connected right after a delete and was refused about a minute later, so I repeat a refusal test before recording it.
- A policy update can drop its description without failing. I verify selectors, action, enabled state, index, protocol and response behavior, not the description.

## Records

Every policy change has a dated record with its before-and-after tests:

| Date | Change | Record |
| --- | --- | --- |
| 2026-09-21 | TCP 18080 added to `Allow NPM to media-01 web UIs` for Weebarr; absent by 2026-09-24 | [Weebarr Deployment](../../../../Archive/Platforms/Weebarr/Documentation/Change%20Records/Deployment%20-%202026-09-21.md), [Weebarr Retirement](../../../../Archive/Platforms/Weebarr/Documentation/Change%20Records/Retirement%20-%202026-09-25.md) |
| 2026-09-20 | `Allow App Portal to Identity LDAPS` | [Directory Sign-In for the Portal](../../../../Platforms/App%20Portal/Documentation/Change%20Records/Directory%20Sign-In%20for%20the%20Portal%20-%202026-09-20.md) |
| 2026-09-19 | `Allow HQ-WS001 to NPM HTTPS` replaced `Allow Identity to App Portal`; TCP 3004 added to `Allow NPM to docker-main web UIs` | [Internal HTTPS record](../../../../Platforms/App%20Portal/Documentation/Change%20Records/Internal%20HTTPS%2C%20ObiPC%20Enrollment%20and%20the%20First%20Self-Update%20-%202026-09-19.md), [App Portal test path](../../../../Platforms/App%20Portal/Documentation/Change%20Records/Credential%2C%20Catalog%20Verification%20and%20Self-Update%20-%202026-09-19.md) |
| 2026-09-19 | `Allow Secure to HQ-WS001 SSH` | [HQ-WS001 SSH Enablement](../../../../Platforms/Active%20Directory/Documentation/Change%20Records/HQ-WS001%20SSH%20Enablement%20-%202026-09-19.md) |
| 2026-09-16 | Portainer policies removed; two unrecorded policies added to this table | [Policy and DNS Readback](../Documentation/Change%20Records/Policy%20and%20DNS%20Readback%20-%202026-09-16.md), [Portainer Retirement](../../../../Archive/Platforms/Portainer/Documentation/Change%20Records/Retirement%20-%202026-09-16.md) |
| 2026-09-15 | Dockhand port 3003 and the two Hawser-to-NPM allows | [Dockge Replacement](../../../../Platforms/Dockhand/Documentation/Change%20Records/Dockge%20Replacement%20-%202026-09-15.md) |
| 2026-09-13 | `Allow NPM to docker-blue MeshCentral` | [MeshCentral Internal HTTPS](../../../../Platforms/MeshCentral/Documentation/Change%20Records/Internal%20HTTPS%20Through%20Nginx%20Proxy%20Manager%20-%202026-09-13.md) |
| 2026-09-12 | `Allow Identity to MeshCentral` | [MeshCentral Deployment](../../../../Platforms/MeshCentral/Documentation/Change%20Records/Deployment%20-%202026-09-12.md) |
| 2026-09-12 | Three identity RDP allows | [Domain Machine RDP Enablement](../../../../Platforms/Active%20Directory/Documentation/Change%20Records/Domain%20Machine%20RDP%20Enablement%20-%202026-09-12.md) |
| 2026-09-12 | Game 01 policies removed | [Game 01 Retirement](../../../../Archive/Platforms/Game%20Servers/Documentation/Change%20Records/Game%2001%20Retirement%20-%202026-09-12.md) |
| 2026-09-12 | `Allow Action1 Deployer to Secure Client` | [AD Deployer Preparation](../../../../Platforms/Action1/Documentation/Change%20Records/AD%20Deployer%20Preparation%20-%202026-09-12.md), [alert investigation](../../../../Security/Incidents/UniFi/Action1%20Remote%20Service%20Control%20Alert%20-%202026-09-12.md) |
| 2026-09-12 | Three Windows Admin Center allows | [WAC Deployment](../../../../Platforms/Windows%20Admin%20Center/Documentation/Change%20Records/Deployment%20-%202026-09-12.md) |
| 2026-09-09 | Identity NTP egress and its order | [Identity NTP and Client DNS](../Documentation/Change%20Records/Identity%20NTP%20and%20Client%20DNS%20-%202026-09-09.md) |
| 2026-09-07 | Identity policies verified; `Allow Identity to Splunk - Security-A` | [Identity Plane Network Preparation](../Documentation/Change%20Records/Identity%20Plane%20Network%20Preparation%20-%202026-09-07.md) |
| 2026-09-06 | Seven policy names matched to the controller spelling | [Documentation Staleness Audit](../../../../Operations/Maintenance/Documentation%20Staleness%20Audit%20-%202026-09-06.md) |
| 2026-09-02 | `Allow splunk-siem to alert bot`; port 9102 for What's Up Docker | [Monitoring Ports](../Documentation/Change%20Records/Monitoring%20Ports%20for%20What's%20Up%20Docker%20and%20the%20Alert%20Bot%20-%202026-09-02.md) |
| 2026-08-31 | `Allow docker-blue SSH Manager to Proxmox` | [SSH Manager Fleet Reach Completion](../../../../Platforms/Docker%20MCP%20Gateway/Documentation/Change%20Records/SSH%20Manager%20Fleet%20Reach%20Completion%20-%202026-08-31.md) |
| 2026-08-30 | `Allow NPM to docker-blue Executor` | [Executor Initial Deployment](../../../../Platforms/Executor/Documentation/Change%20Records/Initial%20Deployment%20-%202026-08-30.md) |
| 2026-08-19 | 68 Kasm and LAB-MGMT policies deleted; CLI Proxy API policy moved to `docker-main` | [Kasm Workspaces Decommission](../../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspaces%20Decommission%20-%202026-08-19.md), [CLI Proxy API Relocation](../../../../Platforms/CLI%20Proxy%20API/Documentation/Change%20Records/Relocation%20to%20docker-main%20-%202026-08-19.md) |
| 2026-08-13 | Workstation access moved to `ubuntu-dev` | [ubuntu-dev Workstation Access](../Documentation/Change%20Records/ubuntu-dev%20Workstation%20Access%20-%202026-08-13.md) |
| 2026-08-10 | CLI Proxy API policy created | [CLI Proxy API Internal HTTPS](../../../../Platforms/CLI%20Proxy%20API/Documentation/Change%20Records/Internal%20HTTPS%20-%202026-08-10.md) |
| 2026-08-08 | `Allow VPN Management Access to DMZ` | [VPN Management Access to DMZ](../Documentation/Change%20Records/VPN%20Management%20Access%20to%20DMZ%20-%202026-08-08.md) |
| 2026-07-27 | Zone and object consolidation: 431 policies to 361, 16 zones to 14 | [Zone and Object Consolidation](../Documentation/Change%20Records/Zone%20and%20Object%20Consolidation%20-%202026-07-27.md), [evidence](../Evidence/Zone%20and%20Object%20Consolidation%20-%202026-07-27/Evidence-Index.md), [pre-consolidation inventory](../../../../Archive/Infrastructure/Network/UniFi/Configuration/Firewall/Firewall%20Policies%20-%20Pre-Consolidation%20-%202026-07-27.md) |
| 2026-07-27 | MGMT-A lockdown | [MGMT-A Final Lockdown](../Documentation/Change%20Records/MGMT-A%20Final%20Lockdown%20-%202026-07-27.md) |
