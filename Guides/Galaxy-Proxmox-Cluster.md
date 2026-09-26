# Galaxy Proxmox Cluster Walkthrough

**Created:** 2026-07-20  
**Last updated:** 2026-09-25

## What This Guide Covers

Galaxy is a five-node Proxmox VE cluster. It grew from one node to three on 2026-05-30; I added `red-server` on 2026-07-07 and `green-server` on 2026-07-31. This walkthrough covers joining a node, the dedicated Corosync link on VLAN 71, the Datacenter firewall objects, and the first Docker LXC, `docker-network`.

## Current Status and Verified Versions

Verified against the cluster on 2026-09-24. All five nodes run `pve-manager/9.2.11`. Four run kernel `7.0.14-8-pve`; `blue-server` runs `7.0.14-15-pve`. `pvecm status` reports five of five votes and quorate. The cluster holds 21 guest records: 18 guests (12 VMs, 6 LXCs) and 3 templates. 16 guests were running; `kali-pen` and `HQ-WS001` were stopped. `green-server` holds no guests.

Corosync `link0` runs on MGMT-A (`192.168.70.0/24`, VLAN 70) and `link1` on Cluster-Net (`192.168.71.0/24`, VLAN 71), one address per node from `.10` to `.14`. `ha-manager config` returns nothing: no guest is an HA resource.

The original four-node build ran `pve-manager/9.2.2` and kernel `7.0.2-6-pve`. Earlier versions of this guide built VM 102 `debian-dev` as a sixth step. I destroyed that VM on 2026-08-14 when `ubuntu-dev` (VM 105) replaced it; its retirement is in the [archived decommission record](../Archive/Infrastructure/Compute/Galaxy/Documentation/Change%20Records/debian-dev%20Decommission%20-%202026-08-14.md).

## What You Need

- Proxmox nodes on matching package versions, with working name resolution between them.
- A management network that already carries the initial Corosync traffic. Mine is MGMT-A, VLAN 70.
- A tagged VLAN for the second Corosync link. I used VLAN 71.
- Console access to each node before changing cluster networking.
- A copy of `/etc/pve/corosync.conf`, `/etc/network/interfaces`, and the Datacenter firewall files taken before each edit.

## How the Pieces Fit Together

![Galaxy: five Proxmox nodes, Corosync link0 on VLAN 70 and link1 on VLAN 71, and the guests on each node](../Assets/Diagrams/galaxy-cluster.svg)

## Walkthrough

### Step 1: Verify the Starting Cluster

I checked package parity, node time, SSH reachability, quorum, and the current Corosync ring before changing a node.

```sh
pveversion -v
pvecm status
pvecm nodes
corosync-cfgtool -s
```

On 2026-07-10 the starting view showed four online nodes using `link0`.

![Proxmox cluster before Corosync link1](../Infrastructure/Compute/Galaxy/Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-Prechange-Proxmox-Cluster-2026-07-10.png)

### Step 2: Join a New Node

I installed the same Proxmox release on the joining node, aligned `/etc/hosts`, authorized the joining root key on the founder, and opened the required cluster traffic before running `pvecm add <YOUR_FOUNDER_IP>` from the joiner.

A join isn't finished when the command returns. I counted it done once `pvecm nodes` listed the new node, quorum held, `/etc/pve/nodes/<YOUR_NEW_NODE>` existed, and the web UI showed the same member count. `green-server` joined this way on 2026-07-31, installed through [Galaxy PXE](../Platforms/Galaxy%20PXE/README.md).

### Step 3: Add the Dedicated Corosync Link

I created `vmbr0.71` on grey, purple, blue, and red with one address per node in `192.168.71.0/24`, `.10` to `.13`. I applied one node at a time, checked reachability to the other link addresses, then added `link1` to `corosync.conf` with a new `config_version`. `green-server` took `192.168.71.14` when it joined.

![red-server network after vmbr0.71](../Infrastructure/Compute/Galaxy/Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-05-red-server-Network-After-2026-07-10.png)

The completed cluster view showed both Corosync links.

![Proxmox cluster after Corosync link1](../Infrastructure/Compute/Galaxy/Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Cluster-Net-Corosync-Link1-S-07-Corosync-Cluster-After-2026-07-10.png)

### Step 4: Apply the Datacenter Firewall Objects

I kept management sources in the `pve_admins` IPSet and verified live SSH before, during, and after the restructure on 2026-07-13. The final test covered the current admin source, a permitted management source, and a source outside the set.

### Step 5: Build the Docker Network LXC

I created CT 107 `docker-network` on VLAN 85 on 2026-07-10 with 2 vCPU, 4 GiB memory, a 32 GiB root disk, nesting, key-only SSH, Docker Engine 29.6.1, and Docker Compose 5.3.1. It became the shared host for Nginx Proxy Manager and NetBird. I cut its memory to 2 GiB on 2026-08-10, which is what it runs today.

![docker-network LXC after creation](../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S02-Docker-Network-LXC-Created-2026-07-10.jpg)

## What I Checked After Each Step

- `pvecm status` remained quorate after every cluster change.
- `corosync-cfgtool -s` showed both rings.
- Management SSH stayed connected while firewall objects changed.
- CT 107 passed Docker, SSH, DNS, web, NTP, and restart checks.

## Troubleshooting and Recovery

Stop if quorum drops, a node loses both management paths, or the edited `corosync.conf` fails to replicate. Restore the last versioned Corosync file from a quorate node. For one failed network change, use the node console to restore `/etc/network/interfaces` before touching another member.

## Known Limits

Galaxy has no shared storage. Every guest disk sits on its node's own storage, so a failed node takes its guests down until it returns. CT 107 and CT 108 were once HA resources pinned to `blue-server`; on 2026-09-24 `ha-manager config` was empty. ([HA removal record](../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/CT%20107%20and%20CT%20108%20HA%20Removal%20-%202026-09-24.md)) The [2026-07-20 stranding incident](../Security/Incidents/Galaxy/HA%20Local%20Storage%20Stranding%20-%202026-07-20.md) shows what HA does with node-local disks.

`green-server` has unresolved memory errors from 2026-09-20 and runs no guests. The [memory failure record](../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/win11-dev%20Provisioning%20and%20Green%20Memory%20Failure%20-%202026-09-20.md) holds the test results.

## Source Records

- [Cluster setup](../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Three-Node%20Cluster%20Formation%20-%202026-05-30.md)
- [red-server expansion](../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Red%20Server%20Expansion%20-%202026-07-07.md)
- [Corosync link1 change](../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10.md)
- [Docker network LXC](../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Docker-Network%20LXC%20Deployment%20-%202026-07-10.md)
- [Debian development VM (archived; VM decommissioned 2026-08-14)](../Archive/Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Debian%20Dev%20GNOME%20Installation%20-%202026-07-15.md)
- [green-server provisioning](../Platforms/Galaxy%20PXE/Documentation/Change%20Records/Provisioning%20Service%20-%202026-07-30.md)
- [Datacenter firewall IPSet restructure](../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Datacenter%20Firewall%20IPSet%20Restructure%20-%202026-07-13.md)
- [PVE 9.2.11 package update](../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/PVE%209.2.11%20Package%20Update%20-%202026-09-04.md)
- [Galaxy inventory](../Operations/Inventory/Galaxy/Galaxy%20Inventory.md), the living current-state view
