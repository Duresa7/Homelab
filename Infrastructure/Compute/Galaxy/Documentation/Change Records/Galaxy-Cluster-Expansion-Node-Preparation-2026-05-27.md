# Galaxy Cluster Expansion: Node Preparation and Pre-Join Remediation

**Created:** 2026-05-27  
**Last updated:** 2026-07-17

**Author:** REDACTED_NAME_001
**Date:** 2026-05-27
**Status:** In progress
**Classification:** Internal IT Documentation

**Historical note:** This document records the preparation work for the original
May 2026 cluster expansion. The current four-node state after adding
`red-server` on 2026-07-07 is documented in
`Galaxy Cluster Red Server Expansion - 2026-07-07.md`.

---

## 1. Purpose

This document records the work performed to prepare the existing Proxmox VE environment for the addition of two new cluster nodes, and to bring the existing node into a clean, join-ready state. It captures the current environment, the remediation steps executed on the existing node, the configuration standards defined for the new nodes, and the remaining tasks required to complete the cluster expansion.

## 2. Scope

In scope:

- Assessment of the existing Proxmox node (grey-server) and the single-node cluster named Galaxy.
- Remediation of stale configuration left over from a prior cluster topology.
- Consolidation of the cluster identity onto the current management network.
- Definition of installation and network standards for the two new nodes.

Out of scope (tracked as future work in Section 9):

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
| grey-server | Existing primary | 192.168.70.10 | REDACTED_INTERNAL_DOMAIN_002 |
| purple-server | New node | 192.168.70.11 | REDACTED_INTERNAL_FQDN_002 |
| blue-server | New node | 192.168.70.12 | REDACTED_INTERNAL_FQDN_001 |

A three-node cluster provides an odd vote count, which satisfies corosync quorum requirements and allows the cluster to remain operational if a single node is lost.

## 5. Findings Prior to Remediation

1. **Duplicate APT repository entries.** The file /etc/apt/sources.list.d/proxmox.sources contained three identical pve-no-subscription stanzas, of which only one was active. Functionally correct, but untidy.
2. **Decommissioned node remnants.** A previously removed cluster member, sith-server (192.168.40.60), still had firewall rules, security groups, and a hosts entry referencing it.
3. **Stale cluster identity.** The Galaxy cluster identity (corosync ring address, hosts file, firewall rules, login banner, and known_hosts) was still anchored to the old VLAN 40 address 192.168.40.10, even though the live management address had been moved to VLAN 70 (192.168.70.10). The old address was not bound to any active interface. This would have caused new node joins to fail, because joining nodes would attempt to reach the existing node at an address that no longer exists.

## 6. Remediation Performed on grey-server

All changes were preceded by file backups stored under /root. The Proxmox firewall remained enabled and running throughout, and no running virtual machines or containers were interrupted.

### 6.1 APT repository cleanup

- Reduced /etc/apt/sources.list.d/proxmox.sources to a single active pve-no-subscription stanza.
- Confirmed repository state: Debian trixie, trixie-updates, and trixie-security enabled; pve-no-subscription enabled; pve-enterprise disabled; ceph no-subscription enabled; pve-test disabled.
- Verified with apt-get update (five repository hits, no errors).
- Backup: /etc/apt/sources.list.d/proxmox.sources.bak.20260525-183548

### 6.2 Removal of decommissioned node (sith-server)

Removed all sith-server references from the firewall and hosts configuration:

- cluster.fw: removed the cluster_allow_sith group reference and definition, the orphaned gui_access_sith group, the sith-server GUI rule, and two SSH allow rules (192.168.40.60 and 192.168.50.164).
- host.fw: removed the cluster_allow_sith group reference.
- /etc/hosts: removed the 192.168.40.60 sith-server entry.

Verification:

- pve-firewall compile reported no errors or warnings.
- pve-firewall status confirmed enabled and running.
- A recursive search for "sith" across /etc returned no results.
- Backup: /root/sith-cleanup-backup-20260525-193347

### 6.3 Cluster identity consolidation to VLAN 70

Repointed every reference to the old address 192.168.40.10 to the live management address 192.168.70.10:

| File | Change |
| --- | --- |
| /etc/pve/corosync.conf and /etc/corosync/corosync.conf | ring0_addr set to 192.168.70.10; config_version incremented from 3 to 4 |
| /etc/hosts | grey-server record updated to 192.168.70.10 |
| /etc/pve/firewall/cluster.fw | all self and destination rules updated to 192.168.70.10 |
| /etc/issue | login banner URL updated to https://192.168.70.10:8006/ |
| /etc/pve/priv/known_hosts | stale 192.168.40.10 host key entry removed |
| /etc/pve/.members | auto-updated by the cluster file system to 192.168.70.10 |

Procedure for the corosync change:

1. Staged the new configuration to a temporary file and reviewed the diff (only ring0_addr and config_version changed).
2. Moved the file into place to trigger propagation.
3. Restarted corosync, then pve-cluster.
4. Verified quorum.

Verification:

- pvecm status reported Config Version 4, ring member 192.168.70.10 (local), and Quorate: Yes.
- Services corosync, pve-cluster, pvedaemon, pveproxy, and pve-firewall all reported active.
- pve-firewall compile reported no errors.
- A recursive search for 192.168.40.10 across /etc returned no results.
- No virtual machine or container configuration referenced the old address; none were affected.
- Backup: /root/consolidate-70.10-backup-20260526-195529

## 7. New Node Build Standard

### 7.1 Installer parameters

| Field | purple-server | blue-server |
| --- | --- | --- |
| Hostname / FQDN | REDACTED_INTERNAL_FQDN_002 | REDACTED_INTERNAL_FQDN_001 |
| IP address | 192.168.70.11 | 192.168.70.12 |
| Netmask | 255.255.255.0 (/24) | 255.255.255.0 (/24) |
| Gateway | 192.168.70.1 | 192.168.70.1 |
| DNS server | 192.168.70.1 | 192.168.70.1 |
| Root file system | ext4 | ext4 |

The ext4 layout was chosen for simplicity and to match the existing node. The implication is that cross-node migration will rely on shared storage or offline migration rather than ZFS replication. This can be revisited if replication or high availability becomes a requirement.

### 7.2 Post-install network configuration

Because the switch ports use a trunk profile with no native VLAN, the Proxmox installer default (an untagged IP directly on vmbr0) does not provide connectivity. After the first boot, the network configuration must be edited at the node console to use a VLAN-aware bridge with the management IP on the tagged sub-interface vmbr0.70.

Reference configuration for /etc/network/interfaces (substitute the actual NIC name and the correct address per node):

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

Notes:

- The bridge VLAN list is restricted to the VLANs in use (40, 60, 65, 70, 80, 90) rather than the full range, as a defense-in-depth measure.
- Apply with ifreload -a, then validate connectivity with ping to 192.168.70.1 and 192.168.70.10.
- A host sub-interface is only required for a VLAN where the host itself needs an IP. Virtual machines use VLANs by setting the VLAN tag on their own virtual network device.

## 8. Security Baseline (Reference)

The existing node demonstrates the following baseline, which the new nodes should match before or shortly after joining the cluster.

### 8.1 SSH server configuration on grey-server

| Setting | Value |
| --- | --- |
| Port | 22 |
| PermitRootLogin | prohibit-password (key only) |
| PasswordAuthentication | no |
| PubkeyAuthentication | yes |
| KbdInteractiveAuthentication | no |
| PermitEmptyPasswords | no |
| Key exchange | Modern algorithms, including post-quantum mlkem768x25519-sha256 |

Authorized keys present for root: mac-air3-REDACTED_USER_001, REDACTED_SSH_KEY_LABEL_001-nopass, ansible-control, and a legacy root@REDACTED_NAME_003 RSA key.

### 8.2 Firewall posture

- The Proxmox firewall is enabled at both the data center and node level.
- Access to the management interface (TCP 8006) and SSH (TCP 22) is restricted by source address allow lists, with explicit drop rules for all other sources.
- The management VLAN (70) is permitted, and specific trusted administrative devices are individually allowed.

### 8.3 Network security notes

- The trunk port profile with native VLAN set to none is a deliberate hardening choice that reduces VLAN hopping risk by ensuring all frames are explicitly tagged.
- Recommended follow-up: confirm at the gateway that other VLANs cannot initiate connections into the management VLAN, as a complement to the host-level firewall.

## 9. Remaining Tasks

1. Complete the console network edit on purple-server and blue-server and confirm connectivity to grey-server.
2. Verify health of both new nodes over SSH.
3. Replicate the APT repository configuration on both new nodes (pve-enterprise disabled, pve-no-subscription enabled, pve-test disabled).
4. Confirm time synchronization is active on all three nodes, since corosync is sensitive to clock drift.
5. Join purple-server and blue-server to the Galaxy cluster from the Proxmox web interface.
6. Verify cluster status shows three nodes with quorum of two.
7. Apply the SSH and firewall baseline from Section 8 to the new nodes.
8. Decide on a shared storage or replication strategy if live migration or high availability is required.

## 10. Optional Cleanup Items (Non-Blocking)

- Remove the stale truenas entry from /etc/hosts on grey-server.
- Remove the empty node directories Grey-Server and REDACTED_NAME_003 under /etc/pve/nodes.
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

---

*End of document.*
