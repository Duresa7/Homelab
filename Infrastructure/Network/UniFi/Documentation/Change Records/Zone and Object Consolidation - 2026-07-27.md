# Zone and Object Consolidation

**Created:** 2026-07-27  
**Last updated:** 2026-07-28

## Date

I completed this change on 2026-07-27.

## Scope

I reduced the UniFi zone matrix, moved repeated host and port selectors into reusable groups, removed Secure-V and its route, corrected two zone names and one disabled WLAN binding, and cleaned unreferenced client groups.

I kept KASM-BROWSER, MALWARE-OFFLINE, and EVIDENCE-QUARANTINE separate. I also kept `AlphaSec`-Access separate from observability because its reverse proxy accepts internet traffic.

The [Windows Servers retirement](../../../../../Platforms/Windows%20Servers/README.md) ran between S01 and S02. S01 therefore captured the controller before that plan changed its remaining UniFi, Proxmox, Ansible, Termix, and credential state.

## Starting State

The S01 readback returned:

| Measure | Starting value |
|---|---:|
| Firewall policies | 431 |
| Custom policies | 61 |
| Controller-generated policies | 370 |
| Firewall zones | 16 |
| Network objects | 26 |
| Firewall groups | 5 port groups, 0 IPv4 address groups |
| Client groups | 14 |
| OON policies | 4 |
| Traffic routes | 3 |
| WLANs | 4 |
| Proxmox-Trunk exclusions | 6 |

The policy stop condition passed at exactly 61 custom policies. I made no S02 change until the Active Directory decommission finished.

The repeated selectors were maintenance debt rather than distinct policy intent. `monitor-01` appeared in 15 policies, the reverse proxy in nine, the security pair in seven, and node-exporter ports in several policy bodies.

## Actions

### Step 1: Capture the rollback baseline

I exported all 431 policies, all 16 zones, all 26 networks with one detail read per network, all five firewall groups, all 14 client groups, all four OON policies, and the client-group reference inventory.

The only client-group reference was the enabled `QoS for D` OON policy targeting `D_devices`.

Evidence: [S01 snapshot and reference inventory](../../Evidence/Zone%20and%20Object%20Consolidation%20-%202026-07-27/Logs/S01-Snapshot-and-Reference-Inventory.md)

### Step 2: Create the reusable groups

I added five IPv4 address groups and three port groups one at a time:

- `OBJ-Monitor-Collector`
- `OBJ-Reverse-Proxy`
- `OBJ-Security-Stack`
- `OBJ-Proxmox-Nodes`
- `OBJ-Observability-Hosts`
- `PG-Node-Exporter`
- `PG-Egress-Web`
- `PG-NTP`

Nothing referenced a new group during creation. The custom policy and zone counts stayed at 61 and 16 after every addition.

Evidence: [S02 firewall group creation](../../Evidence/Zone%20and%20Object%20Consolidation%20-%202026-07-27/Logs/S02-Firewall-Group-Creation.md)

### Step 3: Move exact selectors onto groups

I replaced 35 exact selectors across 24 policies with group references. I read every policy back after its update and compared the non-selector fields against the before snapshot.

I left 11 partial, mixed, or intentionally broader selectors inline. Replacing those with one of the new groups would have changed the allowed host or port set.

Evidence: [S03 policy selector migration](../../Evidence/Zone%20and%20Object%20Consolidation%20-%202026-07-27/Logs/S03-Policy-Selector-Migration.md)

### Step 4: Correct the zone names

I corrected both shortened organisation prefixes in the controller UI. Each before-and-after comparison changed one zone name and no other zone field.

Evidence: [S04 zone name corrections](../../Evidence/Zone%20and%20Object%20Consolidation%20-%202026-07-27/Logs/S04-Zone-Name-Corrections.md)

### Step 5: Merge Cluster-Net into the management zone

I moved Cluster-Net/VLAN 71 into `AlphaSec`-Mgmt, then deleted the empty cluster zone. Cluster-Net retained `dhcpd_enabled: false` and `internet_access_enabled: false`.

`pvecm status` returned four nodes, four votes, and quorum after the move. GUI and SSH remained available on 192.168.70.10 through 192.168.70.13.

Evidence: [S05 cluster zone merge](../../Evidence/Zone%20and%20Object%20Consolidation%20-%202026-07-27/Logs/S05-Cluster-Net-Zone-Merge.md)

### Step 6: Build the observability zone

I repointed nine security-zone policy references before moving Security-A/VLAN 72. I moved Security-A into the monitor zone, created `Allow Monitor to Security monitoring` for the collector-to-security node-exporter path, removed the obsolete cross-zone rule, deleted the empty security zone, and renamed the survivor `AlphaSec`-Observability.

I collapsed five overlapping egress policies into an ordered three-policy set sourced from `OBJ-Observability-Hosts`:

1. `Allow Observability Web Egress` at index 10000
2. `Allow Observability NTP Egress` at index 10001
3. `Block Observability Other External Egress` at index 10002

The required service gate passed before either redundant allow was removed and again after the final order was restored. Prometheus returned 46 of 46 targets up. Wazuh agent ports, five NPM backends, Jedi PC break-glass access, Ansible SSH, DNS, HTTPS, NTP, and the terminal egress block all passed.

Evidence: [S06 observability zone merge](../../Evidence/Zone%20and%20Object%20Consolidation%20-%202026-07-27/Logs/S06-Observability-Zone-Merge.md)

### Step 7: Remove Secure-V

I deleted `Non-tracking` before deleting Secure-V/VLAN 100. The final readback returned 25 network objects, two traffic routes, no WLAN reference to the deleted network, and five Proxmox-Trunk exclusions.

I also rebound the disabled `AlphaSec`-IoT WLAN from the untagged Management network to IoT/VLAN 20. It remained disabled and no other WLAN field changed.

Evidence: [S07 Secure-V removal](../../Evidence/Zone%20and%20Object%20Consolidation%20-%202026-07-27/Logs/S07-Secure-V-Removal.md)

### Step 8: Clean the client groups

I renamed `server` to `docker-blue` and `grey-server` to `grey-node-and-guests`. Both readbacks retained every member.

I deleted the empty `IOT` group and the obsolete `Game Servers` group after fresh firewall, OON, UniFi history, repository, and four-node Proxmox checks found no dependency or current host. The enabled `QoS for D` policy still targets `D_devices`.

I left `VM`, `Admin_Device`, `D_devices`, and the four inline MACs on `Device Access --> Proxmox` unchanged. The V2 policy schema has no client-group selector.

Evidence: [S08 client group hygiene](../../Evidence/Zone%20and%20Object%20Consolidation%20-%202026-07-27/Logs/S08-Client-Group-Hygiene.md)

### Step 9: Replace stale records and archive completed plans

I updated the live VLAN, zone, firewall, object, route, WLAN, client-group, VPN, and port-profile records from the final controller readback. I archived the pre-consolidation 61-policy inventory and the completed plans under their original categories.

The plan estimated 13 final zones. The measured result is 14 because the implementation deleted two zones, not three. I recorded the controller result and archived the estimate with the plan.

Evidence: [S09 final verification](../../Evidence/Zone%20and%20Object%20Consolidation%20-%202026-07-27/Logs/S09-Final-Verification.md)

## Decisions

- I kept the three Kasm zones separate.
- I kept `AlphaSec`-Access separate from observability.
- I preserved Cluster-Net as its own VLAN while sharing the management trust zone.
- I repointed policies before moving Security-A so a stale block could not stop matching.
- I kept mixed or partial selectors inline when a group would widen access.
- I retained the mixed `VM` client group because it includes `kasm-01`, which is outside this project.
- I deleted `Game Servers` only after the current host and reference checks were all negative.
- I treated the live count of 14 zones as authoritative over the plan's estimate of 13.

## Resulting Configuration

| Measure | Result |
|---|---:|
| Firewall policies | 361 |
| Custom policies | 59 |
| Enabled custom policies | 58 |
| Controller-generated policies | 302 |
| Firewall zones | 14 |
| Custom zones | 7 |
| Network objects | 25 |
| Routed LAN networks | 17 |
| Firewall groups | 13 |
| IPv4 address groups | 5 |
| Port groups | 8 |
| Client groups | 12 |
| OON policies | 4 |
| Traffic routes | 2 |
| WLANs | 4 |
| Proxmox-Trunk exclusions | 5 |

Security-A and MONITOR-A share `AlphaSec`-Observability. MGMT-A and Cluster-Net share `AlphaSec`-Mgmt. Their VLAN boundaries remain separate.

The project reduced the policy set by 70: two custom policies and 68 controller-generated policies.

## Verification

| Check | Observed result |
|---|---|
| Final controller count | 361 policies, 59 custom, 14 zones |
| Final network count | 25 objects, 17 routed LAN networks |
| Cluster-Net settings | DHCP disabled, Internet access disabled |
| Secure-V and Non-tracking | Both absent |
| `AlphaSec`-IoT | Disabled and bound to IoT/VLAN 20 |
| Proxmox-Trunk | Five exclusions |
| Client groups | 12; deleted IDs absent |
| `QoS for D` | Enabled and still targets `D_devices` |
| Proxmox cluster | Four nodes, four votes, quorate |
| Prometheus | 46 active targets, 46 up |
| Wazuh agent ports | TCP 1514 and 1515 opened from `app-01` |
| NPM backend paths | Wazuh, Splunk, Grafana, PeaNUT, and Prometheus returned HTTP 200 |
| Ansible to monitor-01 | TCP 22 opened |
| SIEM approved egress | DNS and HTTPS passed from both hosts |
| SIEM unapproved egress | TCP 22 denied from both hosts |
| Mission Control | Harness passed after S08 and again at completion |

The [evidence index](../../Evidence/Zone%20and%20Object%20Consolidation%20-%202026-07-27/Evidence-Index.md) maps every retained before-and-after export, policy ledger, service gate, and stated historical evidence boundary.

## Rollback

The S01 exports are the full controller baseline. S02 through S08 retain before-and-after snapshots around every material mutation.

I can restore policy selectors, group membership, names, and order from those exports. Recreating a deleted zone or network is a controller UI operation. A full rollback of S06 requires recreating the old security zone, moving Security-A back, and restoring the S01 policy bodies in their original order. A rollback of S07 requires recreating Secure-V and `Non-tracking` from the S07 before snapshot.

The Active Directory decommission has no rollback because the owner explicitly chose no backups and the three guests were destroyed. Its retained evidence is separate from this network rollback.

## Remaining Work

No consolidation step remains.

The unidentified 192.168.74.49 host and the mixed `VM` client group remain with the Kasm relocation. They were out of scope and neither weakened nor blocked this change.
