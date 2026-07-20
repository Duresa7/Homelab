# Galaxy Cluster Expansion: Node Preparation and Pre-Join Remediation

**Created:** 2026-05-27  
**Last updated:** 2026-07-20

**Author:** Duresa7  
**Date:** 2026-05-27  
**Status:** In progress  
**Classification:** Internal IT Documentation

**Historical note:** This document records the preparation work for the original
May 2026 cluster expansion. The current four-node state after adding
`red-server` on 2026-07-07 is documented in
[Galaxy Cluster Red Server Expansion](Galaxy%20Cluster%20Red%20Server%20Expansion%20-%202026-07-07.md).

## 1. Work Recorded Here

This record covers the work I did to prepare my existing Proxmox VE environment for two new cluster nodes and to bring the existing node into a clean, join-ready state. It captures the environment as I found it, the remediation I ran on the existing node, the configuration standards I defined for the new nodes, and the remaining tasks to complete the cluster expansion.

## 2. Boundaries

I covered:

- Assessment of my existing Proxmox node (grey-server) and the single-node cluster named Galaxy.
- Remediation of stale configuration left over from a prior cluster topology.
- Consolidation of the cluster identity onto the current management network.
- Definition of installation and network standards for the two new nodes.

I left these items for the expansion work that followed:

- The actual cluster join of the new nodes.
- Shared storage or replication design for live migration and high availability.
- Switch-side VLAN profile changes beyond the items noted.

## 3. Environment Overview

### 3.1 Existing node

| Attribute | Value |
| --- | --- |
| Hostname | grey-server |
| Proxmox VE version | 9.2.2 (kernel 6.17.13-2-pve) |
| Base OS | Debian 13 (trixie) |
| CPU | AMD Ryzen 7 3700X (8 cores, 16 threads) |
| Memory | 62 GB |
| Cluster name | Galaxy |
| Management address | 192.168.70.10/24 (VLAN 70) |
| Default gateway | 192.168.70.1 |
| DNS server | 192.168.70.1 |

### 3.2 Network architecture

- A single Ubiquiti switch connects all nodes.
- Node switch ports use a Proxmox trunk port profile with native VLAN set to none and tagged VLANs 40, 60, 65, 70, 80, and 90.
- The management plane operates on VLAN 70.
- Each node uses a VLAN-aware Linux bridge (vmbr0) with the management IP placed on the tagged sub-interface vmbr0.70.

### 3.3 Storage on grey-server

| Storage ID | Type | Capacity | Scope |
| --- | --- | --- | --- |
| local | Directory (ISO, templates, backups) | 96 GB | All nodes |
| local-lvm | LVM-thin (NVMe) | 794 GB | Per node |
| ssd-lvm1 | LVM-thin (SATA SSD) | 1.8 TB | grey-server only |
| hddpool | ZFS | 3.6 TB | grey-server only |

## 4. Target Cluster Topology

| Node | Role | Management IP | FQDN |
| --- | --- | --- | --- |
| grey-server | Existing primary | 192.168.70.10 | `<YOUR_INTERNAL_DOMAIN>` |
| purple-server | New node | 192.168.70.11 | `<YOUR_PURPLE_SERVER_FQDN>` |
| blue-server | New node | 192.168.70.12 | `<YOUR_BLUE_SERVER_FQDN>` |

I targeted three nodes. That gave Corosync an odd vote count and allowed the cluster to retain quorum after losing one node.

## 5. Findings Before Remediation

1. `/etc/apt/sources.list.d/proxmox.sources` contained three identical `pve-no-subscription` stanzas, although only one was active.
2. Removed member `sith-server` at `192.168.40.60` still appeared in firewall rules, security groups, & `/etc/hosts`.
3. Corosync, `/etc/hosts`, firewall rules, the login banner, & `known_hosts` still pointed at old VLAN 40 address `192.168.40.10`. The live management address was `192.168.70.10` on VLAN 70, and no interface held the old address. A joining node would therefore have tried to reach an address that didn't exist.

## 6. Remediation Performed on grey-server

I saved the affected files under `/root` before changing them. The Proxmox firewall stayed enabled, and no VM or container stopped.

### 6.1 APT repository cleanup

- I reduced `/etc/apt/sources.list.d/proxmox.sources` to one active `pve-no-subscription` stanza.
- Debian trixie, trixie-updates, trixie-security, `pve-no-subscription`, & Ceph no-subscription remained enabled. `pve-enterprise` and `pve-test` remained disabled.
- `apt-get update` returned five repository hits and no errors.
- Backup: `/etc/apt/sources.list.d/proxmox.sources.bak.20260525-183548`

### 6.2 Remove `sith-server` remnants

I removed every `sith-server` reference from the firewall and host configuration:

- `cluster.fw`: removed the `cluster_allow_sith` group reference and definition, orphaned `gui_access_sith` group, `sith-server` GUI rule, & SSH allow rules for `192.168.40.60` and `192.168.50.164`.
- `host.fw`: removed the `cluster_allow_sith` group reference.
- `/etc/hosts`: removed the `192.168.40.60 sith-server` entry.

Verification:

- `pve-firewall compile` reported no errors or warnings.
- `pve-firewall status` reported enabled and running.
- A recursive search for `sith` under `/etc` returned no results.
- Backup: `/root/sith-cleanup-backup-20260525-193347`

### 6.3 Cluster identity consolidation to VLAN 70

I repointed every reference to the old address 192.168.40.10 to the live management address 192.168.70.10:

| File | Change |
| --- | --- |
| /etc/pve/corosync.conf and /etc/corosync/corosync.conf | ring0_addr set to 192.168.70.10; config_version incremented from 3 to 4 |
| /etc/hosts | grey-server record updated to 192.168.70.10 |
| /etc/pve/firewall/cluster.fw | all self and destination rules updated to 192.168.70.10 |
| /etc/issue | login banner URL updated to https://192.168.70.10:8006/ |
| /etc/pve/priv/known_hosts | stale 192.168.40.10 host key entry removed |
| /etc/pve/.members | auto-updated by the cluster file system to 192.168.70.10 |

I changed Corosync in four steps:

1. I staged the new configuration in a temporary file. The diff changed only `ring0_addr` and `config_version`.
2. I moved the file into place to trigger propagation.
3. I restarted `corosync`, then `pve-cluster`.
4. I checked quorum.

Verification:

- `pvecm status` reported configuration version 4, local ring member `192.168.70.10`, & `Quorate: Yes`.
- `corosync`, `pve-cluster`, `pvedaemon`, `pveproxy`, & `pve-firewall` all reported active.
- `pve-firewall compile` reported no errors.
- A recursive search for `192.168.40.10` under `/etc` returned no results.
- No virtual machine or container configuration referenced the old address; none were affected.
- Backup: `/root/consolidate-70.10-backup-20260526-195529`

## 7. New Node Build Standard

### 7.1 Installer parameters

| Field | purple-server | blue-server |
| --- | --- | --- |
| Hostname / FQDN | `<YOUR_PURPLE_SERVER_FQDN>` | `<YOUR_BLUE_SERVER_FQDN>` |
| IP address | 192.168.70.11 | 192.168.70.12 |
| Netmask | 255.255.255.0 (/24) | 255.255.255.0 (/24) |
| Gateway | 192.168.70.1 | 192.168.70.1 |
| DNS server | 192.168.70.1 | 192.168.70.1 |
| Root file system | ext4 | ext4 |

I chose ext4 to match the existing node. Cross-node migration would therefore require shared storage or an offline move instead of ZFS replication.

### 7.2 Post-install network configuration

The switch ports use a trunk profile with no native VLAN, so the Proxmox installer's untagged address on `vmbr0` can't reach the network. After the first boot, I have to use the node console to create a VLAN-aware bridge and place the management address on `vmbr0.70`.

Reference `/etc/network/interfaces` configuration, using the node's NIC name and assigned address:

```
auto lo
iface lo inet loopback

iface nic0 inet manual

iface nic1 inet manual

auto vmbr0
iface vmbr0 inet manual
        bridge-ports nic0
        bridge-stp off
        bridge-fd 0
        bridge-vlan-aware yes
        bridge-vids 40 60 65 70 80 90

auto vmbr0.70
iface vmbr0.70 inet static
        address 192.168.70.11/24
        gateway 192.168.70.1

source /etc/network/interfaces.d/*
```

What matters here:

- I limited the bridge to VLANs 40, 60, 65, 70, 80, & 90 instead of admitting the full range.
- Apply the configuration with `ifreload -a`, then ping `192.168.70.1` and `192.168.70.10`.
- A host sub-interface is only required for a VLAN where the host itself needs an IP. Virtual machines use VLANs by setting the VLAN tag on their own virtual network device.

## 8. Security Baseline (Reference)

I used grey-server's settings as the baseline for the two new nodes.

### 8.1 SSH server configuration on grey-server

| Setting | Value |
| --- | --- |
| Port | 22 |
| PermitRootLogin | prohibit-password (key only) |
| PasswordAuthentication | no |
| PubkeyAuthentication | yes |
| KbdInteractiveAuthentication | no |
| PermitEmptyPasswords | no |
| Key exchange | Includes `mlkem768x25519-sha256` |

Authorized keys present for root: mac-air3-`<YOUR_ADMIN_USERNAME>`, `<RETIRED_ROOT_KEY_LABEL>`-nopass, ansible-control, and a legacy root@`<YOUR_RETIRED_NODE_NAME>` RSA key.

### 8.2 Firewall posture

- The Proxmox firewall is enabled at both the data center and node level.
- Access to the management interface (TCP 8006) and SSH (TCP 22) is restricted by source address allow lists, with explicit drop rules for all other sources.
- The management VLAN (70) is permitted, and specific trusted administrative devices are individually allowed.

### 8.3 Network checks

- I set the trunk port profile's native VLAN to none, so every frame must carry a VLAN tag.
- The remaining gateway check was to confirm that other VLANs couldn't open new connections into management VLAN 70.

## 9. Tasks Remaining at the Time

1. Complete the console network edit on purple-server and blue-server and confirm connectivity to grey-server.
2. Verify health of both new nodes over SSH.
3. Replicate the APT repository configuration on both new nodes (pve-enterprise disabled, pve-no-subscription enabled, pve-test disabled).
4. Confirm time synchronization is active on all three nodes, since corosync is sensitive to clock drift.
5. Join purple-server and blue-server to the Galaxy cluster from the Proxmox web interface.
6. Verify cluster status shows three nodes with quorum of two.
7. Apply the SSH and firewall baseline from Section 8 to the new nodes.
8. Decide on a shared storage or replication strategy if live migration or high availability is required.

## 10. Cleanup Left Open

- Remove the stale truenas entry from /etc/hosts on grey-server.
- Remove the empty node directories Grey-Server and `<YOUR_RETIRED_NODE_NAME>` under /etc/pve/nodes.
- Tighten bridge-vids on grey-server from 2-4094 to the in-use set (40, 60, 65, 70, 80, 90).
- Align grey-server FQDN domain to .galaxy for consistency with the new nodes.

## 11. Backup and Rollback Locations

| Backup | Contents |
| --- | --- |
| /root/sith-cleanup-backup-20260525-193347 | cluster.fw, host.fw, hosts (pre sith removal) |
| /root/consolidate-70.10-backup-20260526-195529 | corosync.conf, cluster.fw, hosts, issue, known_hosts (pre VLAN 70 consolidation) |
| /etc/apt/sources.list.d/proxmox.sources.bak.20260525-183548 | Original repository file |

## 12. Verification Summary

| Item | Result |
| --- | --- |
| APT repositories | Clean, five hits, no errors |
| sith-server references in /etc | None |
| 192.168.40.10 references in /etc | None |
| Cluster quorum | Quorate, Config Version 4, member 192.168.70.10 |
| Core services | corosync, pve-cluster, pvedaemon, pveproxy, pve-firewall all active |
| Firewall compile | No errors or warnings |
| Running workloads | Unaffected |

