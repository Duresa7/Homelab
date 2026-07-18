# Galaxy Cluster-Net Corosync Link Addition

**Created:** 2026-07-10  
**Last updated:** 2026-07-17

**Date:** 2026-07-10  
**System:** Proxmox VE 9.2.2 cluster `Galaxy` and UniFi Network 10.4.57  
**Status:** Complete — S-09 follow-up verified

## Scope

Add an IP-only VLAN interface for Cluster-Net (VLAN 71) to each Galaxy node and add the resulting addresses to Corosync as redundant `link1`. The existing MGMT-A addresses and Corosync `link0` remain unchanged.

The S-09 follow-up also normalizes `red-server`'s VLAN-aware `vmbr0` bridge from the enumerated VLAN list to `bridge-vids 2-4094`, matching grey-server and blue-server without changing host addressing, routing, or Corosync configuration.

| Node | Existing MGMT-A / link0 | Current Cluster-Net / link1 |
|---|---|---|
| `grey-server` | `192.168.70.10/24` | `192.168.71.10/24` |
| `purple-server` | `192.168.70.11/24` | `192.168.71.11/24` |
| `blue-server` | `192.168.70.12/24` | `192.168.71.12/24` |
| `red-server` | `192.168.70.13/24` | `192.168.71.13/24` |

## Starting State

Read-only verification completed through SSH Manager MCP and UniFi Network MCP on 2026-07-10:

- All four nodes run `pve-manager/9.2.2` with Corosync `knet` transport.
- The cluster is quorate with four votes, quorum three, and Corosync configuration version `7`.
- Only Corosync `link0` exists, using `192.168.70.10` through `192.168.70.13`.
- No node has a `vmbr0.71` interface or a `REDACTED_PRIVATE_SUBNET` address.
- `grey-server`, `purple-server`, and `blue-server` persist `bridge-vids 2-4094`; VLAN 71 also appears in each live bridge VLAN table.
- `red-server` persists `bridge-vids 40 60 65 70 80 90`; VLAN 71 is absent from its live bridge VLAN table.
- UniFi health reports all inspected subsystems `ok`.

### UniFi Port Verification

| Node | Switch | Port | Port profile | VLAN 71 result |
|---|---|---:|---|---|
| `grey-server` | Bane Switch POE | 14 | Proxmox-Trunk | Tagged by profile |
| `purple-server` | Bane Switch POE | 2 | Proxmox-Trunk | Tagged by profile |
| `blue-server` | Bane Switch POE | 3 | Proxmox-Trunk | Tagged by profile |
| `red-server` | Jango Switch | 3 | Proxmox-Trunk | Tagged by profile |

No UniFi mutation is required.

## Evidence Captured Before Change

- [UniFi dashboard starting state](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Network-Segmentation-Cluster-Net-Prechange-UniFi-Dashboard-2026-07-10.png)
- [Proxmox cluster starting state](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-Prechange-Proxmox-Cluster-2026-07-10.png)

Both screenshots were captured from the open Chrome dashboards through the Windows computer-control integration.

## Step Evidence Procedure

This change uses step-based evidence rather than only a task-level before/after pair. Each live step will include its exact SSH commands and complete results in a linked transcript plus paired UI captures when the state is visible in Proxmox or UniFi.

| Step | Before evidence | Action transcript | After evidence and verification |
|---|---|---|---|
| S-01: controller, trunk, host, and cluster preflight | Existing UniFi and Proxmox screenshots above | [Exact SSH command and output transcript](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Logs/Cluster-Net-Corosync-Link1-S-01-Preflight-2026-07-10.md) | Read-only result; no state mutation, so no separate after capture is required |
| S-02: add `vmbr0.71` on `grey-server` | [Before Network view](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-02-grey-server-Network-Before-2026-07-10.png) and [before interface export](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Exports/Cluster-Net-Corosync-Link1-S-02-grey-server-interfaces-Before-2026-07-10.txt) | [Exact deployment transcript](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Logs/Cluster-Net-Corosync-Link1-S-02-grey-server-2026-07-10.md) | [After Network view](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-02-grey-server-Network-After-2026-07-10.png); `vmbr0.71` up, gateway ping 0% loss, GUI HTTP 200, quorum intact |
| S-03: add `vmbr0.71` on `purple-server` | [Before Network view](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-03-purple-server-Network-Before-2026-07-10.png) and [before interface export](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Exports/Cluster-Net-Corosync-Link1-S-03-purple-server-interfaces-Before-2026-07-10.txt) | [Exact transcript, including failed attempts and rollback](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Logs/Cluster-Net-Corosync-Link1-S-03-purple-server-2026-07-10.md) | [After Network view](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-03-purple-server-Network-After-2026-07-10.png); `vmbr0.71` up, gateway ping 0% loss, grey neighbor reachable, GUI HTTP 200, quorum intact |
| S-04: add `vmbr0.71` on `blue-server` | [Before Network view](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-04-blue-server-Network-Before-2026-07-10.png) and [before interface export](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Exports/Cluster-Net-Corosync-Link1-S-04-blue-server-interfaces-Before-2026-07-10.txt) | [Exact deployment transcript](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Logs/Cluster-Net-Corosync-Link1-S-04-blue-server-2026-07-10.md) | [After Network view](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-04-blue-server-Network-After-2026-07-10.png); `vmbr0.71` up, gateway ping 0% loss, grey and purple neighbors reachable, GUI HTTP 200, quorum intact |
| S-05: allow VLAN 71 and add `vmbr0.71` on `red-server` | [Before Network view](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-05-red-server-Network-Before-2026-07-10.png) and [before interface export](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Exports/Cluster-Net-Corosync-Link1-S-05-red-server-interfaces-Before-2026-07-10.txt) | [Exact deployment transcript](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Logs/Cluster-Net-Corosync-Link1-S-05-red-server-2026-07-10.md) | [After Network view](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-05-red-server-Network-After-2026-07-10.png); bridge admits VLAN 71, `vmbr0.71` up, all three peers reachable at Layer 2, GUI HTTP 200, quorum intact |
| S-06: validate Cluster-Net | S-02 through S-05 after captures | [Exact full-mesh validation transcript](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Logs/Cluster-Net-Corosync-Link1-S-06-Full-Mesh-Validation-2026-07-10.md) | All four `vmbr0.71` interfaces and connected routes are present; all gateway pings succeed; every peer resolves to a direct VLAN 71 MAC address. General peer ICMP remains blocked by the existing Proxmox host firewall policy. |
| S-07: add Corosync `link1` | [Before Cluster view](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-07-Corosync-Cluster-Before-2026-07-10.png) and [before Corosync export](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Exports/Cluster-Net-Corosync-Link1-S-07-corosync-Before-2026-07-10.conf) | [Exact validated configuration-change transcript](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Logs/Cluster-Net-Corosync-Link1-S-07-Corosync-Change-2026-07-10.md) | [After Cluster view](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-07-Corosync-Cluster-After-2026-07-10.png) and [deployed configuration](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Exports/Cluster-Net-Corosync-Link1-S-07-corosync-After-2026-07-10.conf); config version 8, four nodes quorate, and all peers connected on both links |
| S-08: final management-path verification | S-07 after state | [Exact four-node and UniFi verification transcript](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Logs/Cluster-Net-Corosync-Link1-S-08-Final-Verification-2026-07-10.md) | [Final Proxmox dashboard](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-08-Final-Proxmox-Dashboard-2026-07-10.png) shows Galaxy quorate with four nodes online; [final UniFi dashboard](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Network-Segmentation-Cluster-Net-Postchange-UniFi-Dashboard-2026-07-10.png) shows the controller operational; every original MGMT-A GUI returned HTTP 200 |
| S-09: normalize `red-server` bridge VLAN range | [Before bridge dialog](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-09-red-server-Bridge-VLANs-Before-2026-07-10.png) and [before interface export](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Exports/Cluster-Net-Corosync-Link1-S-09-red-server-interfaces-Before-2026-07-10.txt) | [Exact guarded apply and verification transcript](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Logs/Cluster-Net-Corosync-Link1-S-09-red-server-Bridge-VLAN-Normalization-2026-07-10.md) | [After bridge dialog](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-09-red-server-Bridge-VLANs-After-2026-07-10.png) and [deployed interface export](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Exports/Cluster-Net-Corosync-Link1-S-09-red-server-interfaces-After-2026-07-10.txt); `bridge-vids 2-4094` matches grey/blue, quorum and both Corosync links remained healthy, and no rollback triggered |

## Completed Implementation

1. Saved a timestamped copy of `/etc/network/interfaces` on every node under `/root/`.
2. Added VLAN 71 to `red-server`'s bridge admission policy, then normalized the bridge to `bridge-vids 2-4094` in S-09 so it matches grey-server and blue-server.
3. Added `vmbr0.71` as a static, no-gateway interface on every node using the addresses in the scope table.
4. Applied one node at a time and verified that MGMT-A SSH/GUI access and cluster quorum remained healthy after each node.
5. Verified all-to-all Layer-2 reachability over `192.168.71.10` through `192.168.71.13` before changing Corosync.
6. Saved a timestamped copy of `/etc/pve/corosync.conf` under `/root/` on every node.
7. Built and validated the candidate Corosync configuration with `corosync -c /tmp/cluster-net-S07-corosync.conf -t`.
8. Added `ring1_addr` for every node, added `interface { linknumber: 1 }`, and incremented `config_version` from `7` to `8`; every `ring0_addr` and `linknumber: 0` entry was preserved.
9. Verified four-node quorum, all peers connected on both Corosync links, and original MGMT-A GUI/SSH access.

## Rollback Status

The timestamped interface and Corosync rollback copies created for this change were intentionally deleted on 2026-07-11 at the operator's request after the implementation passed final verification. A second read-only scan returned no files matching `interfaces.bak.pre-cluster-net-*`, `interfaces.bak.pre-vlan-range-*`, or `corosync.conf.bak.pre-link1-*` on grey-server, purple-server, blue-server, or red-server.

- The on-node copies are no longer available for direct restoration.
- The before-state interface and Corosync exports remain under the project's versioned `Evidence/` directory for audit and reconstruction.
- Any future reversal must be planned as a new guarded change using those before-state records and current live-state validation.
- The implementation remains additive: no existing MGMT-A address, default gateway, Corosync `ring0_addr`, or `link0` entry was removed.

## Verification Status

Implementation and final verification are complete. VLAN 71 is active on all four nodes, gateway reachability succeeds from each node, and all-to-all direct neighbor resolution proves the Layer-2 path. Corosync configuration version 8 is live; every node reports all peers connected on both `link0` and `link1`, quorum stayed intact, and the scoped core services stayed active. All four original MGMT-A Proxmox endpoints returned HTTP 200, the final Proxmox dashboard reported four nodes online and zero offline, and the UniFi API reported all five adopted infrastructure devices online.

S-09 normalized `red-server` from the enumerated bridge VLAN list to `bridge-vids 2-4094`. Persistent configuration, live bridge state, and the 4,093 tagged VLAN-entry count now match grey-server and blue-server. VLAN 71 gateway reachability, four-node quorum, both Corosync links, all scoped core services, and the original red-server management GUI passed after `ifreload`; no rollback was triggered.

The final failed-unit inventory also exposed pre-existing conditions outside this change: `pvestatd` on `blue-server` had been failed since 2026-07-05, and `grey-server` had a failed `hddpool` import plus a stale root-session scope. These did not prevent quorum, dual-link connectivity, or management access, and no unrelated recovery action was taken.
