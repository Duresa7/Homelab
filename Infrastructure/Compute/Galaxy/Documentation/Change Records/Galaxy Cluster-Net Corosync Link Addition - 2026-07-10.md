# Galaxy Cluster-Net Corosync Link Addition

**Created:** 2026-07-10  
**Last updated:** 2026-07-20

**Date:** 2026-07-10  
**System:** Proxmox VE 9.2.2 cluster `Galaxy` and UniFi Network 10.4.57  
**Status:** Complete; S-09 follow-up verified

## Scope

I added an IP-only Cluster-Net interface on VLAN 71 to each Galaxy node, then used those four addresses for redundant Corosync `link1`. I left the MGMT-A addresses and Corosync `link0` unchanged.

During the S-09 follow-up, I changed `red-server`'s VLAN-aware `vmbr0` bridge from an enumerated VLAN list to `bridge-vids 2-4094`. That brought it in line with grey-server and blue-server without changing host addressing, routing, or Corosync.

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
- No node has a `vmbr0.71` interface or a `<YOUR_PREVIOUS_MANAGEMENT_SUBNET>` address.
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

## Walkthrough

### Step 1: Verify the controller, trunks, hosts, and cluster

**Action:** I performed read-only checks of the UniFi controller, the four Proxmox trunk ports, every node's bridge state, and the Corosync configuration before changing a host.

**Observed result:** All four nodes were online and quorate on Corosync `link0`. VLAN 71 was admitted on grey, purple, and blue, but not in red's live bridge table. No node had `vmbr0.71`.

**Verification:** UniFi reported all five adopted infrastructure devices online, all four switch ports used the Proxmox-Trunk profile, & the Proxmox cluster showed four votes with quorum three.

**Evidence:**

![UniFi dashboard starting state](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Network-Segmentation-Cluster-Net-Prechange-UniFi-Dashboard-2026-07-10.png)

![Proxmox cluster starting state](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-Prechange-Proxmox-Cluster-2026-07-10.png)

### Step 2: Add `vmbr0.71` on grey-server

**Action:** I saved a timestamped copy of `/etc/network/interfaces`, added static no-gateway interface `vmbr0.71` at `192.168.71.10/24`, and applied the network change on `grey-server`.

**Observed result:** `vmbr0.71` came up without disturbing the existing MGMT-A interface.

**Verification:** The VLAN 71 gateway ping had 0% loss, the original management GUI returned HTTP 200, and cluster quorum stayed intact.

**Evidence:**

![Before Network view on grey-server](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-02-grey-server-Network-Before-2026-07-10.png)

![After Network view on grey-server](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-02-grey-server-Network-After-2026-07-10.png)

### Step 3: Add `vmbr0.71` on purple-server

**Action:** I saved the interfaces file and added static no-gateway interface `vmbr0.71` at `192.168.71.11/24`. Failed apply attempts triggered a rollback before the final apply passed.

**Observed result:** The final configuration brought `vmbr0.71` up while preserving MGMT-A access.

**Verification:** The gateway ping had 0% loss, the grey neighbor was reachable, the GUI returned HTTP 200, and quorum stayed intact.

**Evidence:**

![Before Network view on purple-server](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-03-purple-server-Network-Before-2026-07-10.png)

![After Network view on purple-server](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-03-purple-server-Network-After-2026-07-10.png)

### Step 4: Add `vmbr0.71` on blue-server

**Action:** I saved the interfaces file, added static no-gateway interface `vmbr0.71` at `192.168.71.12/24`, and applied the change on `blue-server`.

**Observed result:** `vmbr0.71` came up without changing the original management path.

**Verification:** The gateway ping had 0% loss, the grey and purple neighbors were reachable, the GUI returned HTTP 200, and quorum stayed intact.

**Evidence:**

![Before Network view on blue-server](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-04-blue-server-Network-Before-2026-07-10.png)

![After Network view on blue-server](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-04-blue-server-Network-After-2026-07-10.png)

### Step 5: Admit VLAN 71 and add `vmbr0.71` on red-server

**Action:** I saved the interfaces file, added VLAN 71 to red's bridge admission policy, created static no-gateway interface `vmbr0.71` at `192.168.71.13/24`, and applied the network change.

**Observed result:** The bridge admitted VLAN 71 and `vmbr0.71` came up.

**Verification:** All three Cluster-Net peers were directly reachable at Layer 2, the management GUI returned HTTP 200, and quorum stayed intact.

**Evidence:**

![Before Network view on red-server](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-05-red-server-Network-Before-2026-07-10.png)

![After Network view on red-server](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-05-red-server-Network-After-2026-07-10.png)

### Step 6: Validate the Cluster-Net mesh

**Action:** I checked all four `vmbr0.71` interfaces, their connected routes, gateway reachability, and peer neighbor resolution before touching Corosync.

**Observed result:** Every interface and route was present, every gateway ping succeeded, and every peer resolved to a direct VLAN 71 MAC address. General peer ICMP remained blocked by the existing Proxmox host firewall policy.

**Verification:** Direct neighbor resolution proved the full Layer-2 mesh despite the intentional ICMP restriction.

**Evidence:** The local S-06 transcript holds the terminal validation. Steps 2 through 5 show the four before-and-after interface pairs used by the mesh checks.

### Step 7: Add Corosync link1

**Action:** I saved `/etc/pve/corosync.conf`, added each node's `ring1_addr`, added `interface { linknumber: 1 }`, preserved every `ring0_addr` and `linknumber: 0` entry, and incremented `config_version` from 7 to 8.

**Command retained for candidate validation:**

```sh
corosync -c /tmp/cluster-net-S07-corosync.conf -t
```

**Observed result:** The candidate passed validation and the live cluster adopted configuration version 8.

**Verification:** All four nodes remained quorate and every peer connected on both Corosync links.

**Evidence:**

![Before Cluster view](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-07-Corosync-Cluster-Before-2026-07-10.png)

![After Cluster view](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-07-Corosync-Cluster-After-2026-07-10.png)

### Step 8: Verify the original management paths

**Action:** I reopened the Proxmox and UniFi dashboards and probed every original MGMT-A Proxmox endpoint after the Corosync change.

**Observed result:** Proxmox showed Galaxy quorate with four nodes online, and UniFi remained operational.

**Verification:** Every original MGMT-A GUI returned HTTP 200 and no node reported offline.

**Evidence:**

![Final Proxmox dashboard](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-08-Final-Proxmox-Dashboard-2026-07-10.png)

![Final UniFi dashboard](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Network-Segmentation-Cluster-Net-Postchange-UniFi-Dashboard-2026-07-10.png)

### Step 9: Normalize red-server's bridge VLAN range

**Action:** I guarded the follow-up change, replaced red's enumerated VLAN list with `bridge-vids 2-4094`, and applied the bridge configuration with `ifreload`.

**Observed result:** Red's persistent and live bridge state matched grey and blue with 4,093 tagged VLAN entries.

**Verification:** VLAN 71 gateway reachability, four-node quorum, both Corosync links, scoped services, and the original red-server management GUI all passed. No rollback triggered.

**Evidence:**

![Before bridge dialog on red-server](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-09-red-server-Bridge-VLANs-Before-2026-07-10.png)

![After bridge dialog on red-server](../../Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-09-red-server-Bridge-VLANs-After-2026-07-10.png)

## Rollback Status

I deleted the timestamped interface and Corosync rollback copies on 2026-07-11 after the implementation passed final verification. A second read-only scan returned no files matching `interfaces.bak.pre-cluster-net-*`, `interfaces.bak.pre-vlan-range-*`, or `corosync.conf.bak.pre-link1-*` on grey-server, purple-server, blue-server, or red-server.

- The on-node copies are no longer available for direct restoration.
- Any future reversal must be planned as a new guarded change validated against current live state.
- The implementation remains additive: no existing MGMT-A address, default gateway, Corosync `ring0_addr`, or `link0` entry was removed.

## Final Cluster Verification

VLAN 71 is active on all four nodes. Each node reached the gateway, and all-to-all neighbor resolution confirmed the Layer-2 path. Corosync configuration version 8 is live, with every peer connected on `link0` and `link1`. Quorum stayed at four votes, all four MGMT-A Proxmox endpoints returned HTTP 200, the Proxmox dashboard showed four nodes online and none offline, & the UniFi API showed all five adopted infrastructure devices online.

After S-09, `red-server` reported `bridge-vids 2-4094` in both persistent and live state. The bridge held 4,093 tagged VLAN entries, matching grey-server and blue-server. Gateway reachability, four-node quorum, both Corosync links, the scoped services, and the original management GUI all passed after `ifreload`.

The final failed-unit inventory also exposed pre-existing conditions outside this change: `pvestatd` on `blue-server` had been failed since 2026-07-05, and `grey-server` had a failed `hddpool` import plus a stale root-session scope. These didn't prevent quorum, dual-link connectivity, or management access, and I took no unrelated recovery action.
