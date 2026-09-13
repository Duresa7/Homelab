# Galaxy VMs

**Created:** 2026-07-08  
**Last updated:** 2026-09-12  

Galaxy currently has 11 QEMU VMs & three templates. This inventory records each guest's CPU, memory, storage, firmware, network, VLAN, firewall, TPM, & QEMU-agent state.

I captured the live cluster after moving VM 122 to Purple on 2026-07-28, then recaptured its storage after expanding `scsi0` from 100G to 200G in two steps later that day. On 2026-07-30 I corrected VM 122's detail block to its live six vCPUs and 12 GiB, added `discard=on`, and recorded its one replacement snapshot. The cluster resource API listed 10 QEMU VMs and two templates. On 2026-08-08 I recaptured after confirming VM 111's deletion and correcting VM 102 to its live size, and the API now lists 9 QEMU VMs and two templates.

On 2026-08-10 I recaptured the active VMs after the [guest resource efficiency change](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Guest%20Resource%20Efficiency%20Tuning%20-%202026-08-10.md). Five VMs now use a maximum and a lower ballooning minimum, while Splunk remains fixed. The table and hardware blocks below show the post-restart state.

On 2026-08-13 I added VM 105 `ubuntu-dev`, which had been running since 2026-08-12 without an entry here. I found the gap while moving CLI Proxy API onto it, so this file was one guest short of the cluster for a day.

On 2026-09-06 I audited this file against `pvesh get /cluster/resources` and every `qemu-server/*.conf` on the cluster. `kali-pen` had been rebuilt without a record: grey-server's task log shows `qmdestroy 106` at 10:42 EDT on 2026-08-26 and `qmcreate 102` ten minutes later, so the new Kali VM reused VMID 102, the number `debian-dev` carried until 2026-08-14. It is a 6 vCPU, 8 GiB guest with a 100G `local-lvm` disk, the Kali 2026.2 installer attached, tagged VLAN 40 without the Proxmox firewall flag, and it was stopped when I read it. Its detail block below replaces the retired VM 106 block. The same pass confirmed the other six VMs and both templates match their configuration files, and it closed the `ubuntu-dev` restart note. The audit is recorded in [Documentation Staleness Audit - 2026-09-06](../../Maintenance/Documentation%20Staleness%20Audit%20-%202026-09-06.md).

VM 111 `fedora-dev` is gone, and I deleted it deliberately. I added it to this file on 2026-07-26 after the PVE API surfaced a guest I had never written down, and I decided to keep it on 2026-07-27. I reversed that decision: `debian-dev` (VM 102) is the machine I develop on, so a second development guest that had been stopped since 2026-07-15 was paying for nothing. I confirmed the deletion against the cluster on 2026-08-08. `pvesh get /cluster/resources` returns no VMID 111, `/etc/pve/qemu-server/111.conf` does not exist, and `pvesm list ssd-lvm1` holds no `vm-111-*` volume, so its 80 GiB is back.

`debian-dev` (VM 102) is also gone now. `ubuntu-dev` (VM 105) took over as the machine I develop on when CLI Proxy API moved across on 2026-08-13, and VM 102 sat idle from that point. I shut it down cleanly on 2026-08-14 and destroyed it with `qm destroy 102 --purge`. It carried no snapshot, backup job, HA resource, or replication job, so there was nothing to reconcile first. At that point `pvesh get /cluster/resources` returned no VMID 102, `/etc/pve/qemu-server/102.conf` did not exist, and `pvesm list ssd-lvm1` held no `vm-102-*` volume; its 120 GiB was back. VMID 102 has been in use again since 2026-08-26, when I rebuilt `kali-pen` under it on `local-lvm`, so a `102.conf` exists today and describes the Kali VM rather than `debian-dev`. The full decommission record, including the documentation archival, is [debian-dev Decommission - 2026-08-14](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/debian-dev%20Decommission%20-%202026-08-14.md), and the final configuration snapshot is [Debian Dev Archived Guest - 2026-08-14](../../../Archive/Operations/Inventory/Galaxy/Debian%20Dev%20Archived%20Guest%20-%202026-08-14.md).

`kasm-01` (VM 122) is gone. On 2026-08-19 I shut it down cleanly and destroyed it with its cloud-init, EFI, 200 GiB system, and baseline snapshot volumes. The cluster resource API returns no VMID 122 and `pvesm list ssd-lvm2 --vmid 122` returns no volumes. The [decommission record](../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspaces%20Decommission%20-%202026-08-19.md) records the completed monitoring, proxy, automation, security-agent, and UniFi cleanup.

`supabase-01` (VM 117) is also gone. On 2026-08-20 I confirmed I had already deleted it: the Proxmox configuration and cluster-resource entry are absent, `pvesm list ssd-lvm1 --vmid 117` returns no volume, and the local LVM inventory has no VM 117 logical volume. The [retirement record](../../../Archive/Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Supabase%2001%20Retirement%20-%202026-08-20.md) records the remaining automation, SSH, monitoring, diagram, and documentation cleanup.

On 2026-09-09 I added the three Windows Server 2025 guests and the template they came from. VM 300 `ws2025-template` was built on 2026-09-08 and cloned into VM 301 `HQ-DC01`, VM 302 `HQ-DC02`, and VM 303 `HQ-MGT01`, all on IDENTITY-A, VLAN 65. The two controllers hold the `ad.alphasecunited.com` forest and `HQ-MGT01` is its member server. All four run OVMF firmware with a TPM 2.0 device, which Windows Server 2025 expects, and each carries the virtio driver ISO on `ide0`. The [forest build record](../../../Platforms/Active%20Directory/Documentation/Change%20Records/Forest%20Build%20-%202026-09-09.md) holds the verification.

On 2026-09-10 I added VM 310 `HQ-WS001`, a Windows 11 Pro test workstation on IDENTITY-A, VLAN 65. It is a fresh unattended install rather than a clone of the Windows Server template, and it is the client that proves the Tier 2 local-administrator policy and Windows LAPS reach a workstation. The [join record](../../../Platforms/Active%20Directory/Documentation/Change%20Records/HQ-WS001%20Workstation%20Join%20-%202026-09-10.md) holds the verification and the installer traps.

## Virtual Machines
| VMID | Name | Node | OS | vCPU | Memory | Disk | IPv4 | Gateway | VLAN | HA |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 102 | kali-pen | grey-server | Kali Linux 2026.2 | 6 | 8 GiB | 100G | Not captured; stopped on 2026-09-06 | 192.168.40.1 | 40 | disabled |
| 105 | ubuntu-dev | grey-server | Ubuntu 26.04.1 LTS, GNOME 50 | 6 | 12 GiB pending / 16 GiB running | 150G | 192.168.40.179/24 | 192.168.40.1 | 40 | disabled |
| 109 | splunk-siem | grey-server | Rocky Linux 10.2 (Red Quartz) | 6 | 12 GiB | 150G | 192.168.72.3/24 | 192.168.72.1 | 72 | disabled |
| 116 | app-01 | purple-server | Debian GNU/Linux 13 (trixie) | 4 | 8 GiB maximum / 4 GiB minimum | 64G | 192.168.80.10/24 | 192.168.80.1 | 80 | disabled |
| 121 | edge-01 | purple-server | Debian GNU/Linux 13 (trixie) | 2 | 4 GiB maximum / 2 GiB minimum | 30G | 192.168.30.10/24 | 192.168.30.1 | 30 | disabled |
| 200 | security-01 | grey-server | Ubuntu 24.04.4 LTS | 4 | 10 GiB maximum / 8 GiB minimum | 100G | 192.168.72.2/24 | 192.168.72.1 | 72 | disabled |
| 301 | HQ-DC01 | grey-server | Windows Server 2025 Standard | 4 | 4 GiB | 80G | 192.168.65.10/24 | 192.168.65.1 | 65 | disabled |
| 302 | HQ-DC02 | grey-server | Windows Server 2025 Standard | 4 | 4 GiB | 80G | 192.168.65.11/24 | 192.168.65.1 | 65 | disabled |
| 303 | HQ-MGT01 | grey-server | Windows Server 2025 Standard | 2 | 6 GiB | 100G | 192.168.65.12/24 | 192.168.65.1 | 65 | disabled |
| 310 | HQ-WS001 | grey-server | Windows 11 Pro 25H2 | 4 | 4 GiB | 80G | 192.168.65.20/24 | 192.168.65.1 | 65 | disabled |
| 401 | alpha-prod-01 | purple-server | Debian GNU/Linux 13 (trixie) | 6 | 4 GiB maximum / 2 GiB minimum | 60G | 192.168.80.118/24 | 192.168.80.1 | 80 | disabled |

## Templates
| VMID | Name | Node | OS | vCPU | Memory | Disk | IPv4 | Gateway | VLAN | HA |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 101 | debian13-template | grey-server | Debian 13 | 4 | 4 GiB | 60G | none | none | 40 | disabled |
| 300 | ws2025-template | grey-server | Windows Server 2025 Standard | 4 | 4 GiB | 80G | none | none | 65 | disabled |
| 9000 | ubuntu-cloud-template | grey-server | Ubuntu 24.04.4 LTS | 2 | 2 GiB | 20G | none | none | 80 | disabled |

## VM Details

### VM 102 - kali-pen

I rebuilt this VM on 2026-08-26. The earlier `kali-pen` was VM 106, a 4 vCPU, 5.86 GiB guest with a 50G disk, no VLAN tag, and the Kali 2025.2 installer; I destroyed it at 10:42 EDT and created this one at 10:52 EDT under VMID 102. The new guest is tagged VLAN 40, carries the Kali 2026.2 installer, and has the QEMU agent and a QXL display enabled. It was stopped when I captured it on 2026-09-06, so its address is not recorded here; the previous VM held 192.168.40.226 and the rebuilt one has not been read back.

#### Identity
| Setting | Value |
| --- | --- |
| Node | grey-server |
| High availability | disabled |
| Template | no |
| OS family | Linux |
| Guest OS | Kali Linux, 2026.2 installer |
| IPv4 | Not captured; the VM was stopped on 2026-09-06 |
| Gateway | 192.168.40.1 |

#### Hardware
| Setting | Value |
| --- | --- |
| vCPU | 6 |
| CPU type | host |
| Memory | 8 GiB |
| Ballooning | default; no `balloon` key, so the minimum equals the maximum |
| BIOS | ovmf |
| Machine | q35 |
| SCSI controller | virtio-scsi-single |
| Display | qxl |
| QEMU agent | enabled |
| TPM | disabled |

#### Storage
| Device | Bus | Storage | Volume | Size | Media | Options |
| --- | --- | --- | --- | --- | --- | --- |
| scsi0 | scsi | local-lvm | vm-102-disk-1 | 100G | disk | discard, I/O thread, SSD emulation |
| ide2 | ide | local | iso/kali-linux-2026.2-installer-amd64.iso | 4689972K | cdrom | default |
| efidisk0 | efidisk | local-lvm | vm-102-disk-0 | 4M | disk | efitype 4m |

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 40 | Not captured | 192.168.40.1 | disabled | `<REDACTED_KALI_VM_MAC>` |

### VM 105 - ubuntu-dev

On 2026-09-08 I moved both disks to Grey's M.2 NVMe-backed `local-lvm` and deleted the two unused `ssd-lvm1` source volumes. The VM remained running and its guest agent responded after cleanup. The [storage move record](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/ubuntu-dev%20NVMe%20Storage%20Move%20-%202026-09-08.md) holds the verification and reclaimed-space figures.

This is the Ubuntu development workstation that takes over from `debian-dev`. I created it on 2026-08-12 and added it to this inventory on 2026-08-13, when CLI Proxy API moved onto it; it ran undocumented in between.

It is configured for a pending reduction to 12 GiB, while the running instance retains 16 GiB with ballooning off. The running instance predated that setting until the guest restarted on 2026-08-19, and the setting has been in force since: on 2026-09-06 the guest reported 15,408 MiB of total memory, where the pre-restart instance had been capped at `actual=12630` against `max_mem=16384` and saw 11.4 GiB.

On 2026-09-10 I assessed 15 days of guest memory history. Usage averaged 5.44 GiB but peaked at 10.37 GiB with another 4.00 GiB in swap. I then chose 12 GiB and applied `qm set 105 --memory 12288` without restarting anything. Proxmox shows 12,288 MiB pending against 16,384 MiB running; the reduction will take effect on a future full VM stop/start. The [memory assessment](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/ubuntu-dev%20Memory%20Assessment%20-%202026-09-10.md) records the initial recommendation and the subsequent decision, change, and verification.

I applied the Linux Host Baseline Standard on 2026-08-13, following the single-account exception this workstation role carries. It joined fleet monitoring the same day as Wazuh agent `020` and as a node_exporter target.

#### Identity
| Setting | Value |
| --- | --- |
| Node | grey-server |
| Guest hostname | ubuntu-dev |
| Role | GNOME development workstation and Docker host |
| High availability | disabled |
| Template | no |
| OS family | Linux |
| Guest OS | Ubuntu 26.04.1 LTS, GNOME Shell 50.1 |
| IPv4 | 192.168.40.179/24 |
| Gateway | 192.168.40.1 |
| Login account | `ai-agent` |
| Snapshot | none |

#### Hardware
| Setting | Value |
| --- | --- |
| vCPU | 6 |
| CPU type | host |
| Memory | 12 GiB pending / 16 GiB running; no restart performed |
| Ballooning | disabled (`balloon: 0`); in effect since the 2026-08-19 restart |
| BIOS | ovmf |
| Machine | q35 |
| SCSI controller | virtio-scsi-single |
| Display | qxl |
| QEMU agent | enabled |
| TPM | disabled |

#### Storage
| Device | Bus | Storage | Volume | Size | Media | Options |
| --- | --- | --- | --- | --- | --- | --- |
| scsi0 | scsi | local-lvm | vm-105-disk-0 | 150G | disk | discard, I/O thread, SSD emulation |
| efidisk0 | efidisk | local-lvm | vm-105-disk-1 | 4M | disk | efitype 4m |

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 40 | 192.168.40.179/24 | 192.168.40.1 | enabled | `<REDACTED_UBUNTU_DEV_MAC>` |

### VM 109 - splunk-siem

#### Identity
| Setting | Value |
| --- | --- |
| Node | grey-server |
| High availability | disabled |
| Template | no |
| OS family | Linux |
| Guest OS | Rocky Linux 10.2 (Red Quartz) |
| IPv4 | 192.168.72.3/24 |
| Gateway | 192.168.72.1 |

#### Hardware
| Setting | Value |
| --- | --- |
| vCPU | 6 |
| CPU type | host |
| Memory | 12 GiB |
| Ballooning | off; fixed memory |
| BIOS | ovmf |
| Machine | q35 |
| SCSI controller | virtio-scsi-single |
| Display | default |
| QEMU agent | enabled |
| TPM | disabled |

#### Storage
| Device | Bus | Storage | Volume | Size | Media | Options |
| --- | --- | --- | --- | --- | --- | --- |
| scsi0 | scsi | ssd-lvm1 | vm-109-disk-1 | 150G | disk | discard, I/O thread, SSD emulation |
| ide2 | ide | local | iso/Rocky-10.2-x86_64-boot.iso | 1024940K | cdrom | default |
| efidisk0 | efidisk | ssd-lvm1 | vm-109-disk-0 | 4M | disk | default |

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 72 | 192.168.72.3/24 | 192.168.72.1 | enabled | `<REDACTED_SPLUNK_VM_MAC>` |

### VM 116 - app-01

On 2026-09-11 I replaced its 200 GiB system disk with a verified 64 GiB disk on Grey and removed the original volume. Root has about 44 GiB available. The [replacement record](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/app-01%2064%20GiB%20Boot%20Disk%20Replacement%20-%202026-09-11.md) holds boot, service, and cleanup checks.

I subsequently moved both disks to Purple's NVMe-backed `local-lvm` on 2026-09-11. Boot, containers, PostgreSQL, dashboard reachability, node exporter, and Wazuh connection checks passed.

I stopped and started this guest on 2026-08-10, which cleared the stale 24 GiB QEMU allocation. Its active and configured maximum is now 8 GiB, with a 4 GiB ballooning minimum.

#### Identity
| Setting | Value |
| --- | --- |
| Node | purple-server |
| High availability | disabled |
| Template | no |
| OS family | Linux |
| Guest OS | Debian GNU/Linux 13 (trixie) |
| IPv4 | 192.168.80.10/24 |
| Gateway | 192.168.80.1 |

#### Hardware
| Setting | Value |
| --- | --- |
| vCPU | 4 |
| CPU type | host |
| Memory | 8 GiB maximum; 4 GiB minimum |
| Ballooning | on (`balloon: 4096`) |
| BIOS | ovmf |
| Machine | q35 |
| SCSI controller | virtio-scsi-single |
| Display | default |
| QEMU agent | enabled |
| TPM | disabled |

#### Storage
| Device | Bus | Storage | Volume | Size | Media | Options |
| --- | --- | --- | --- | --- | --- | --- |
| scsi0 | scsi | local-lvm | vm-116-disk-2 | 64G | disk | I/O thread, SSD emulation |
| efidisk0 | efidisk | local-lvm | vm-116-disk-0 | 4M | disk | Configuration reports 528K; allocated volume is 4 MiB |

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 80 | 192.168.80.10/24 | 192.168.80.1 | enabled | `<REDACTED_APP_HOST_MAC>` |

#### Administrative Access

- SSH is public-key only. Root login, password authentication, and keyboard-interactive authentication are disabled; `PermitRootLogin no` since 2026-09-07, when Coolify stopped managing the host as root.
- `dkadi` holds `(ALL : ALL) ALL` through the `sudo` group behind a prompt that `/etc/sudoers.d/00-rootpw` points at root's password. `ansible` keeps its NOPASSWD drop-in. `ai-agent` cannot run sudo.
- `coolify`, uid 9999, is Coolify's own key-only service account with `NOPASSWD` sudo and `docker` group membership; the uid matches the container's internal user so `/data/coolify` needs no ownership change. [Non-Root Server Account and Root SSH Disabled](../../../Platforms/Coolify/Documentation/Change%20Records/Non-Root%20Server%20Account%20and%20Root%20SSH%20Disabled%20-%202026-09-07.md).

### VM 121 - edge-01

I moved both disks to Purple's NVMe-backed `local-lvm` on 2026-09-11. The migration completed at 3:28:25 AM Eastern; boot, ingress services, monitoring, and Wazuh connection checks passed.

#### Identity
| Setting | Value |
| --- | --- |
| Node | purple-server |
| High availability | disabled |
| Template | no |
| OS family | Linux |
| Guest OS | Debian GNU/Linux 13 (trixie) |
| IPv4 | 192.168.30.10/24 |
| Gateway | 192.168.30.1 |

#### Hardware
| Setting | Value |
| --- | --- |
| vCPU | 2 |
| CPU type | host |
| Memory | 4 GiB maximum; 2 GiB minimum |
| Ballooning | on (`balloon: 2048`) |
| BIOS | ovmf |
| Machine | q35 |
| SCSI controller | virtio-scsi-single |
| Display | default |
| QEMU agent | enabled |
| TPM | disabled |

#### Storage
| Device | Bus | Storage | Volume | Size | Media | Options |
| --- | --- | --- | --- | --- | --- | --- |
| scsi0 | scsi | local-lvm | vm-121-disk-1 | 30G | disk | I/O thread, SSD emulation |
| efidisk0 | efidisk | local-lvm | vm-121-disk-0 | 4M | disk | Configuration reports 528K; allocated volume is 4 MiB |

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 30 | 192.168.30.10/24 | 192.168.30.1 | enabled | `<REDACTED_EDGE_HOST_MAC>` |

### VM 200 - security-01

#### Identity
| Setting | Value |
| --- | --- |
| Node | grey-server |
| High availability | disabled |
| Template | no |
| OS family | Linux |
| Guest OS | Ubuntu 24.04.4 LTS |
| IPv4 | 192.168.72.2/24 |
| Gateway | 192.168.72.1 |

#### Hardware
| Setting | Value |
| --- | --- |
| vCPU | 4 |
| CPU type | host |
| Memory | 10 GiB maximum; 8 GiB minimum |
| Ballooning | on (`balloon: 8192`) |
| BIOS | ovmf |
| Machine | q35 |
| SCSI controller | virtio-scsi-single |
| Display | default |
| QEMU agent | enabled |
| TPM | disabled |

#### Storage
| Device | Bus | Storage | Volume | Size | Media | Options |
| --- | --- | --- | --- | --- | --- | --- |
| scsi0 | scsi | ssd-lvm1 | vm-200-disk-1 | 100G | disk | cache=writeback, discard, I/O thread, SSD emulation |
| efidisk0 | efidisk | ssd-lvm1 | vm-200-disk-0 | 4M | disk | default |

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 72 | 192.168.72.2/24 | 192.168.72.1 | enabled | `<REDACTED_SECURITY_HOST_MAC>` |

### VM 301 - HQ-DC01

Cloned from VM 300 on 2026-09-09 and promoted the same day. This guest holds the schema, domain naming, PDC emulator, RID, and infrastructure master roles for `ad.alphasecunited.com`, and is the forest's external time source through `time.cloudflare.com`.

#### Identity
| Setting | Value |
| --- | --- |
| Node | grey-server |
| Guest hostname | HQ-DC01 |
| Role | First domain controller; all five operations master roles, global catalog, AD-integrated DNS |
| High availability | disabled |
| Template | no |
| OS family | Windows |
| Guest OS | Windows Server 2025 Standard, build 26100 |
| IPv4 | 192.168.65.10/24 |
| Gateway | 192.168.65.1 |
| Login account | `Administrator` |
| Snapshot | none |

#### Hardware
| Setting | Value |
| --- | --- |
| vCPU | 4 |
| CPU type | host |
| Memory | 4 GiB |
| Ballooning | disabled |
| BIOS | ovmf |
| Machine | q35 |
| SCSI controller | virtio-scsi-single |
| Display | default |
| QEMU agent | enabled |
| TPM | enabled, version 2.0 |

#### Storage
| Device | Bus | Storage | Volume | Size | Media | Options |
| --- | --- | --- | --- | --- | --- | --- |
| scsi0 | scsi | ssd-lvm1 | vm-301-disk-1 | 80G | disk | discard, I/O thread, SSD emulation |
| efidisk0 | efidisk | ssd-lvm1 | vm-301-disk-0 | 4M | disk | efitype 4m, pre-enrolled keys |
| tpmstate0 | tpmstate | ssd-lvm1 | vm-301-disk-2 | 4M | disk | version 2.0 |
| ide0 | ide | local | virtio-win-0.1.285.iso | 771138K | cdrom | virtio driver media |

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 65 | 192.168.65.10/24 | 192.168.65.1 | disabled | `<REDACTED_HQ_DC01_MAC>` |

### VM 302 - HQ-DC02

Cloned from VM 300 on 2026-09-09 and promoted into the existing domain. It holds no operations master role and synchronises time from `HQ-DC01`.

#### Identity
| Setting | Value |
| --- | --- |
| Node | grey-server |
| Guest hostname | HQ-DC02 |
| Role | Second domain controller; global catalog, AD-integrated DNS |
| High availability | disabled |
| Template | no |
| OS family | Windows |
| Guest OS | Windows Server 2025 Standard, build 26100 |
| IPv4 | 192.168.65.11/24 |
| Gateway | 192.168.65.1 |
| Login account | `Administrator` |
| Snapshot | none |

#### Hardware
| Setting | Value |
| --- | --- |
| vCPU | 4 |
| CPU type | host |
| Memory | 4 GiB |
| Ballooning | disabled |
| BIOS | ovmf |
| Machine | q35 |
| SCSI controller | virtio-scsi-single |
| Display | default |
| QEMU agent | enabled |
| TPM | enabled, version 2.0 |

#### Storage
| Device | Bus | Storage | Volume | Size | Media | Options |
| --- | --- | --- | --- | --- | --- | --- |
| scsi0 | scsi | ssd-lvm1 | vm-302-disk-1 | 80G | disk | discard, I/O thread, SSD emulation |
| efidisk0 | efidisk | ssd-lvm1 | vm-302-disk-0 | 4M | disk | efitype 4m, pre-enrolled keys |
| tpmstate0 | tpmstate | ssd-lvm1 | vm-302-disk-2 | 4M | disk | version 2.0 |
| ide0 | ide | local | virtio-win-0.1.285.iso | 771138K | cdrom | virtio driver media |

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 65 | 192.168.65.11/24 | 192.168.65.1 | disabled | `<REDACTED_HQ_DC02_MAC>` |

### VM 303 - HQ-MGT01

Cloned from VM 300 on 2026-09-09 and joined to the domain, where it sits in `OU=Management,OU=Servers`. Its local `Administrator` password is managed by Windows LAPS, so the directory holds the authoritative value. Extending `C:` on this guest required removing the trailing recovery partition first; the recovery partition GPT type is `de94bba4-06d1-4d40-a16a-bfd50179d6ac`.

#### Identity
| Setting | Value |
| --- | --- |
| Node | grey-server |
| Guest hostname | HQ-MGT01 |
| Role | Member server for management tooling and Entra Cloud Sync |
| High availability | disabled |
| Template | no |
| OS family | Windows |
| Guest OS | Windows Server 2025 Standard, build 26100 |
| IPv4 | 192.168.65.12/24 |
| Gateway | 192.168.65.1 |
| Login account | `Administrator` |
| Snapshot | none |

#### Hardware
| Setting | Value |
| --- | --- |
| vCPU | 2 |
| CPU type | host |
| Memory | 6 GiB |
| Ballooning | disabled |
| BIOS | ovmf |
| Machine | q35 |
| SCSI controller | virtio-scsi-single |
| Display | default |
| QEMU agent | enabled |
| TPM | enabled, version 2.0 |

#### Storage
| Device | Bus | Storage | Volume | Size | Media | Options |
| --- | --- | --- | --- | --- | --- | --- |
| scsi0 | scsi | ssd-lvm1 | vm-303-disk-1 | 100G | disk | discard, I/O thread, SSD emulation |
| efidisk0 | efidisk | ssd-lvm1 | vm-303-disk-0 | 4M | disk | efitype 4m, pre-enrolled keys |
| tpmstate0 | tpmstate | ssd-lvm1 | vm-303-disk-2 | 4M | disk | version 2.0 |
| ide0 | ide | local | virtio-win-0.1.285.iso | 771138K | cdrom | virtio driver media |

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 65 | 192.168.65.12/24 | 192.168.65.1 | disabled | `<REDACTED_HQ_MGT01_MAC>` |

### VM 310 - HQ-WS001

Installed on 2026-09-10 from `Win11_25H2_English_x64.iso` with an unattended answer file, then joined to `ad.alphasecunited.com` with an offline domain join so no domain administrator password was needed anywhere. It sits in `OU=Standard,OU=Workstations`.

Its local `Administrator` password is managed by Windows LAPS, so the directory holds the authoritative value and any password manager entry for this machine is stale. `ALPHASEC\ADM-T2-WorkstationAdmins` is in its local `Administrators` group, placed there by the `C-WKS-LocalAdmins` policy.

Memory is 4 GiB rather than 8 because `grey-server` was carrying 51 GiB of its 62 GiB when this guest was built. OpenSSH Server would not install on this machine, so it is not in SSH Manager; the QEMU guest agent is the management channel.

#### Identity
| Setting | Value |
| --- | --- |
| Node | grey-server |
| Guest hostname | HQ-WS001 |
| Role | Windows 11 test workstation for tiered policy and LAPS validation |
| High availability | disabled |
| Template | no |
| OS family | Windows |
| Guest OS | Windows 11 Pro, 25H2, build 26200 |
| Windows activation | Licensed, retail channel, activated 2026-09-10 |
| IPv4 | 192.168.65.20/24 |
| Gateway | 192.168.65.1 |
| Login account | `Administrator`, LAPS-managed |
| Snapshot | none |

#### Hardware
| Setting | Value |
| --- | --- |
| vCPU | 4 |
| CPU type | host |
| Memory | 4 GiB |
| Ballooning | disabled (`balloon: 0`) |
| BIOS | ovmf |
| Machine | q35 |
| SCSI controller | virtio-scsi-single |
| Display | default |
| QEMU agent | enabled |
| TPM | enabled, version 2.0 |

#### Storage
| Device | Bus | Storage | Volume | Size | Media | Options |
| --- | --- | --- | --- | --- | --- | --- |
| scsi0 | scsi | ssd-lvm1 | vm-310-disk-1 | 80G | disk | discard, I/O thread, SSD emulation |
| efidisk0 | efidisk | ssd-lvm1 | vm-310-disk-0 | 4M | disk | efitype 4m, pre-enrolled keys |
| tpmstate0 | tpmstate | ssd-lvm1 | vm-310-disk-2 | 4M | disk | version 2.0 |

No optical drive is attached. The installation and answer-file media were detached and deleted after the build.

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 65 | 192.168.65.20/24 | 192.168.65.1 | disabled | `<REDACTED_HQ_WS001_MAC>` |

### VM 401 - alpha-prod-01

I moved both disks to Purple on 2026-09-12. The [migration record](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/alpha-prod-01%20Purple%20Migration%20-%202026-09-12.md) holds startup and service verification.

#### Identity
| Setting | Value |
| --- | --- |
| Node | purple-server |
| High availability | disabled |
| Template | no |
| OS family | Linux |
| Guest OS | Debian GNU/Linux 13 (trixie) |
| IPv4 | 192.168.80.118/24 |
| Gateway | 192.168.80.1 |

#### Hardware
| Setting | Value |
| --- | --- |
| vCPU | 6 |
| CPU type | host |
| Memory | 4 GiB maximum; 2 GiB minimum |
| Ballooning | on (`balloon: 2048`) |
| BIOS | ovmf |
| Machine | q35 |
| SCSI controller | virtio-scsi-single |
| Display | default |
| QEMU agent | enabled |
| TPM | disabled |

#### Storage
| Device | Bus | Storage | Volume | Size | Media | Options |
| --- | --- | --- | --- | --- | --- | --- |
| scsi0 | scsi | local-lvm | vm-401-disk-1 | 60G | disk | discard, I/O thread, SSD emulation |
| efidisk0 | efidisk | local-lvm | vm-401-disk-0 | 4M | disk | default |

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 80 | 192.168.80.118/24 | 192.168.80.1 | enabled | `<REDACTED_TEAMSPEAK_HOST_MAC>` |

## Template Details

### Template 101 - debian13-template

#### Identity
| Setting | Value |
| --- | --- |
| Node | grey-server |
| High availability | disabled |
| Template | yes |
| OS family | Linux |
| Guest OS | Debian 13 |
| IPv4 | none |
| Gateway | none |

#### Hardware
| Setting | Value |
| --- | --- |
| vCPU | 4 |
| CPU type | host |
| Memory | 4 GiB |
| BIOS | ovmf |
| Machine | q35 |
| SCSI controller | virtio-scsi-single |
| Display | default |
| QEMU agent | enabled |
| TPM | disabled |

#### Storage
| Device | Bus | Storage | Volume | Size | Media | Options |
| --- | --- | --- | --- | --- | --- | --- |
| scsi0 | scsi | ssd-lvm1 | base-101-disk-1 | 60G | disk | discard, I/O thread, SSD emulation |
| efidisk0 | efidisk | ssd-lvm1 | base-101-disk-0 | 4M | disk | default |

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 40 | none | none | enabled | `<REDACTED_DEBIAN_TEMPLATE_MAC>` |

### Template 300 - ws2025-template

Built on 2026-09-08 as the source for the three Windows Server 2025 guests. It carries the QEMU guest agent, OpenSSH Server, and the virtio driver media, and sysprep has been run. Sysprep does not regenerate SSH host keys, so every clone taken from this template presents the template's fingerprint until the keys under `C:\ProgramData\ssh` are deleted and `sshd` is restarted.

#### Identity
| Setting | Value |
| --- | --- |
| Node | grey-server |
| High availability | disabled |
| Template | yes |
| OS family | Windows |
| Guest OS | Windows Server 2025 Standard, build 26100 |
| IPv4 | none |
| Gateway | none |

#### Hardware
| Setting | Value |
| --- | --- |
| vCPU | 4 |
| CPU type | host |
| Memory | 4 GiB |
| BIOS | ovmf |
| Machine | q35 |
| SCSI controller | virtio-scsi-single |
| Display | default |
| QEMU agent | enabled |
| TPM | enabled, version 2.0 |

#### Storage
| Device | Bus | Storage | Volume | Size | Media | Options |
| --- | --- | --- | --- | --- | --- | --- |
| scsi0 | scsi | ssd-lvm1 | base-300-disk-1 | 80G | disk | discard, I/O thread, SSD emulation |
| efidisk0 | efidisk | ssd-lvm1 | base-300-disk-0 | 4M | disk | efitype 4m, pre-enrolled keys |
| tpmstate0 | tpmstate | ssd-lvm1 | base-300-disk-2 | 4M | disk | version 2.0 |
| ide0 | ide | local | virtio-win-0.1.285.iso | 771138K | cdrom | virtio driver media |

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 65 | none | none | disabled | `<REDACTED_WS2025_TEMPLATE_MAC>` |

### Template 9000 - ubuntu-cloud-template

#### Identity
| Setting | Value |
| --- | --- |
| Node | grey-server |
| High availability | disabled |
| Template | yes |
| OS family | Linux |
| Guest OS | Ubuntu 24.04.4 LTS |
| IPv4 | none |
| Gateway | none |

#### Hardware
| Setting | Value |
| --- | --- |
| vCPU | 2 |
| CPU type | host |
| Memory | 2 GiB |
| BIOS | ovmf |
| Machine | q35 |
| SCSI controller | virtio-scsi-single |
| Display | default |
| QEMU agent | enabled |
| TPM | disabled |

#### Storage
| Device | Bus | Storage | Volume | Size | Media | Options |
| --- | --- | --- | --- | --- | --- | --- |
| scsi0 | scsi | ssd-lvm1 | base-9000-disk-0 | 20G | disk | I/O thread, SSD emulation |
| ide2 | ide | ssd-lvm1 | vm-9000-cloudinit | - | cdrom | default |
| efidisk0 | efidisk | ssd-lvm1 | base-9000-disk-1 | 4M | disk | default |

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 80 | none | none | disabled | `<REDACTED_UBUNTU_TEMPLATE_MAC>` |
