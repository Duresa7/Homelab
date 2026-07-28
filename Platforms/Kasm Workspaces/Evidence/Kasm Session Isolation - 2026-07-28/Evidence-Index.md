# Kasm Session Isolation Evidence

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

I retained the exact final verification commands, structured requests, complete outputs, and concise result summaries. I did not retain authentication output, VPN keys, or API tokens.

| Evidence | Purpose |
| --- | --- |
| [S00 Compute and Storage Final Verification](Logs/S00%20Compute%20and%20Storage%20Final%20Verification%20-%202026-07-28.md) | Cluster quorum, VM placement, pool state, snapshots, and SMART counters |
| [S01 UniFi Final State Verification](Logs/S01%20UniFi%20Final%20State%20Verification%20-%202026-07-28.md) | LAB-MGMT, VLAN 77 DNS state, critical policy order, Proton route, VPN client, trunk, and policy residue |
| [S02 Guest and Kasm Final Verification](Logs/S02%20Guest%20and%20Kasm%20Final%20Verification%20-%202026-07-28.md) | Shim persistence, Docker networks, service health, image residue, and API health |
| [S03 Firewall and Source-Path Verification](Logs/S03%20Firewall%20and%20Source-Path%20Verification%20-%202026-07-28.md) | Final policy order plus allowed and denied source-path checks |
| [S04 DNS and Proton Verification](Logs/S04%20DNS%20and%20Proton%20Verification%20-%202026-07-28.md) | VLAN 77 DNS state, Proton route state, lane egress, and failure-test handling |
| [S05 Lab Sessions Policy Verification](Logs/S05%20Lab%20Sessions%20Policy%20Verification%20-%202026-07-28.md) | Group identity, member count, and the seven effective policy settings |
| [S06 Containment and Cleanup Verification](Logs/S06%20Containment%20and%20Cleanup%20Verification%20-%202026-07-28.md) | Exact lane, DNS, Internet, protected-target, and post-test cleanup results |
| [S06 Host and Direct-IP Acceptance Verification](Logs/S06%20Host%20and%20Direct-IP%20Acceptance%20Verification%20-%202026-07-28.md) | Host pull and protected-target checks, direct-IP lane egress, and cleanup |
| [S07 Documentation and Local Access Verification](Logs/S07%20Documentation%20and%20Local%20Access%20Verification%20-%202026-07-28.md) | Mission Control harness, SSH alias, local links, and secret-output non-retention |
| [S08 Kasm Disk Expansion Verification](Logs/S08%20Kasm%20Disk%20Expansion%20Verification%20-%202026-07-28.md) | Proxmox disk size, guest partition and filesystem size, Kasm storage paths, container health, and API health |
| [Implementation Results](Logs/Implementation%20Results.md) | Migration, service health, network state, containment, Proton failure, and cleanup results |
| [Purple 850 EVO SMART Baseline](Logs/Purple%20850%20EVO%20SMART%20Baseline.md) | Before and after storage-health counters |

The unchanged raw `smartctl -a` capture is stored with the [drive inventory](../../../../Infrastructure/Hardware/Components/Drives/SSD/smartctl-a_Samsung-SSD-850-EVO-250GB_S21NNXAH105252T_2026-07-28.txt). The [change record](../../Documentation/Change%20Records/Kasm%20Session%20Isolation%20-%202026-07-28.md) maps each material step to its retained evidence.
