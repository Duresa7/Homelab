# Galaxy Cluster-Net Corosync Link Addition

**Created:** 2026-07-10  
**Last updated:** 2026-07-18

**Date:** 2026-07-10  
**System:** Proxmox VE 9.2.2 cluster `Galaxy` and UniFi Network 10.4.57  
**Status:** Complete; S-09 follow-up verified

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

I completed read-only verification through the SSH manager and the UniFi controller on 2026-07-10:

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

No UniFi mutation was required.

## Evidence Captured Before Change

I captured both starting-state screenshots from my open Chrome dashboards before touching any node.

<details>
<summary>Pre-change screenshot: UniFi dashboard starting state</summary>

![UniFi dashboard starting state](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Network-Segmentation-Cluster-Net-Prechange-UniFi-Dashboard-2026-07-10.png)

</details>

<details>
<summary>Pre-change screenshot: Proxmox cluster starting state</summary>

![Proxmox cluster starting state](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-Prechange-Proxmox-Cluster-2026-07-10.png)

</details>

## Step Evidence

I ran this change with step-based evidence rather than only a task-level before/after pair: each live step got paired UI captures where the state is visible in Proxmox or UniFi, and I verified the outcome before moving to the next step.

### S-01: controller, trunk, host, and cluster preflight

Read-only preflight of the UniFi controller, trunk ports, hosts, and cluster. The pre-change captures above show the starting state; nothing mutated, so no separate after capture was needed.

### S-02: add `vmbr0.71` on `grey-server`

After the apply, `vmbr0.71` was up, the gateway ping showed 0% loss, the GUI returned HTTP 200, and quorum stayed intact.

<details>
<summary>Step S-02 screenshot: grey-server Network view before</summary>

![Before Network view on grey-server](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-02-grey-server-Network-Before-2026-07-10.png)

</details>

<details>
<summary>Step S-02 screenshot: grey-server Network view after</summary>

![After Network view on grey-server](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-02-grey-server-Network-After-2026-07-10.png)

</details>

### S-03: add `vmbr0.71` on `purple-server`

This step included failed attempts and a rollback before the final apply passed. Afterward `vmbr0.71` was up, the gateway ping showed 0% loss, the grey neighbor was reachable, the GUI returned HTTP 200, and quorum stayed intact.

<details>
<summary>Step S-03 screenshot: purple-server Network view before</summary>

![Before Network view on purple-server](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-03-purple-server-Network-Before-2026-07-10.png)

</details>

<details>
<summary>Step S-03 screenshot: purple-server Network view after</summary>

![After Network view on purple-server](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-03-purple-server-Network-After-2026-07-10.png)

</details>

### S-04: add `vmbr0.71` on `blue-server`

Afterward `vmbr0.71` was up, the gateway ping showed 0% loss, the grey and purple neighbors were reachable, the GUI returned HTTP 200, and quorum stayed intact.

<details>
<summary>Step S-04 screenshot: blue-server Network view before</summary>

![Before Network view on blue-server](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-04-blue-server-Network-Before-2026-07-10.png)

</details>

<details>
<summary>Step S-04 screenshot: blue-server Network view after</summary>

![After Network view on blue-server](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-04-blue-server-Network-After-2026-07-10.png)

</details>

### S-05: allow VLAN 71 and add `vmbr0.71` on `red-server`

Afterward the bridge admitted VLAN 71, `vmbr0.71` was up, all three peers were reachable at Layer 2, the GUI returned HTTP 200, and quorum stayed intact.

<details>
<summary>Step S-05 screenshot: red-server Network view before</summary>

![Before Network view on red-server](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-05-red-server-Network-Before-2026-07-10.png)

</details>

<details>
<summary>Step S-05 screenshot: red-server Network view after</summary>

![After Network view on red-server](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-05-red-server-Network-After-2026-07-10.png)

</details>

### S-06: validate Cluster-Net

Full-mesh validation over the S-02 through S-05 results: all four `vmbr0.71` interfaces and connected routes were present, every gateway ping succeeded, and every peer resolved to a direct VLAN 71 MAC address. General peer ICMP remained blocked by the existing Proxmox host firewall policy.

### S-07: add Corosync `link1`

I validated the candidate configuration before applying it. Afterward the cluster ran config version 8 with four nodes quorate and all peers connected on both links.

<details>
<summary>Step S-07 screenshot: Corosync cluster view before</summary>

![Before Cluster view](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-07-Corosync-Cluster-Before-2026-07-10.png)

</details>

<details>
<summary>Step S-07 screenshot: Corosync cluster view after</summary>

![After Cluster view](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-07-Corosync-Cluster-After-2026-07-10.png)

</details>

### S-08: final management-path verification

The final Proxmox dashboard showed Galaxy quorate with four nodes online, the final UniFi dashboard showed the controller operational, and every original MGMT-A GUI returned HTTP 200.

<details>
<summary>Step S-08 screenshot: final Proxmox dashboard</summary>

![Final Proxmox dashboard](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-08-Final-Proxmox-Dashboard-2026-07-10.png)

</details>

<details>
<summary>Step S-08 screenshot: final UniFi dashboard</summary>

![Final UniFi dashboard](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Network-Segmentation-Cluster-Net-Postchange-UniFi-Dashboard-2026-07-10.png)

</details>

### S-09: normalize `red-server` bridge VLAN range

I applied the change guarded, with verification after `ifreload`. Afterward `bridge-vids 2-4094` matched grey and blue, quorum and both Corosync links remained healthy, and no rollback triggered.

<details>
<summary>Step S-09 screenshot: red-server bridge VLANs before</summary>

![Before bridge dialog on red-server](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-09-red-server-Bridge-VLANs-Before-2026-07-10.png)

</details>

<details>
<summary>Step S-09 screenshot: red-server bridge VLANs after</summary>

![After bridge dialog on red-server](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-09-red-server-Bridge-VLANs-After-2026-07-10.png)

</details>

## Completed Implementation

1. I saved a timestamped copy of `/etc/network/interfaces` on every node under `/root/`.
2. I added VLAN 71 to `red-server`'s bridge admission policy, then normalized the bridge to `bridge-vids 2-4094` in S-09 so it matches grey-server and blue-server.
3. I added `vmbr0.71` as a static, no-gateway interface on every node using the addresses in the scope table.
4. I applied one node at a time and verified that MGMT-A SSH/GUI access and cluster quorum remained healthy after each node.
5. I verified all-to-all Layer-2 reachability over `192.168.71.10` through `192.168.71.13` before changing Corosync.
6. I saved a timestamped copy of `/etc/pve/corosync.conf` under `/root/` on every node.
7. I built and validated the candidate Corosync configuration with `corosync -c /tmp/cluster-net-S07-corosync.conf -t`.
8. I added `ring1_addr` for every node, added `interface { linknumber: 1 }`, and incremented `config_version` from `7` to `8`; every `ring0_addr` and `linknumber: 0` entry was preserved.
9. I verified four-node quorum, all peers connected on both Corosync links, and original MGMT-A GUI/SSH access.

## Rollback Status

I deleted the timestamped interface and Corosync rollback copies on 2026-07-11 after the implementation passed final verification. A second read-only scan returned no files matching `interfaces.bak.pre-cluster-net-*`, `interfaces.bak.pre-vlan-range-*`, or `corosync.conf.bak.pre-link1-*` on grey-server, purple-server, blue-server, or red-server.

- The on-node copies are no longer available for direct restoration.
- Any future reversal must be planned as a new guarded change validated against current live state.
- The implementation remains additive: no existing MGMT-A address, default gateway, Corosync `ring0_addr`, or `link0` entry was removed.

## Verification Status

Implementation and final verification are complete. VLAN 71 is active on all four nodes, gateway reachability succeeds from each node, and all-to-all direct neighbor resolution proves the Layer-2 path. Corosync configuration version 8 is live; every node reports all peers connected on both `link0` and `link1`, quorum stayed intact, and the scoped core services stayed active. All four original MGMT-A Proxmox endpoints returned HTTP 200, the final Proxmox dashboard reported four nodes online and zero offline, and the UniFi API reported all five adopted infrastructure devices online.

S-09 normalized `red-server` from the enumerated bridge VLAN list to `bridge-vids 2-4094`. Persistent configuration, live bridge state, and the 4,093 tagged VLAN-entry count now match grey-server and blue-server. VLAN 71 gateway reachability, four-node quorum, both Corosync links, all scoped core services, and the original red-server management GUI passed after `ifreload`; no rollback was triggered.

The final failed-unit inventory also exposed pre-existing conditions outside this change: `pvestatd` on `blue-server` had been failed since 2026-07-05, and `grey-server` had a failed `hddpool` import plus a stale root-session scope. These did not prevent quorum, dual-link connectivity, or management access, and I took no unrelated recovery action.
