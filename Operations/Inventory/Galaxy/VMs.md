# Galaxy VMs

**Created:** 2026-07-08  
**Last updated:** 2026-08-14  

Galaxy currently has 9 QEMU VMs & two templates. This inventory records each guest's CPU, memory, storage, firmware, network, VLAN, firewall, TPM, & QEMU-agent state.

I captured the live cluster after moving VM 122 to Purple on 2026-07-28, then recaptured its storage after expanding `scsi0` from 100G to 200G in two steps later that day. On 2026-07-30 I corrected VM 122's detail block to its live six vCPUs and 12 GiB, added `discard=on`, and recorded its one replacement snapshot. The cluster resource API listed 10 QEMU VMs and two templates. On 2026-08-08 I recaptured after confirming VM 111's deletion and correcting VM 102 to its live size, and the API now lists 9 QEMU VMs and two templates.

On 2026-08-10 I recaptured the active VMs after the [guest resource efficiency change](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Guest%20Resource%20Efficiency%20Tuning%20-%202026-08-10.md). Five VMs now use a maximum and a lower ballooning minimum, while Splunk and Kasm remain fixed. The table and hardware blocks below show the post-restart state.

On 2026-08-13 I added VM 105 `ubuntu-dev`, which had been running since 2026-08-12 without an entry here. I found the gap while moving CLI Proxy API onto it, so this file was one guest short of the cluster for a day.

VM 111 `fedora-dev` is gone, and I deleted it deliberately. I added it to this file on 2026-07-26 after the PVE API surfaced a guest I had never written down, and I decided to keep it on 2026-07-27. I reversed that decision: `debian-dev` (VM 102) is the machine I develop on, so a second development guest that had been stopped since 2026-07-15 was paying for nothing. I confirmed the deletion against the cluster on 2026-08-08. `pvesh get /cluster/resources` returns no VMID 111, `/etc/pve/qemu-server/111.conf` does not exist, and `pvesm list ssd-lvm1` holds no `vm-111-*` volume, so its 80 GiB is back.

`debian-dev` (VM 102) is also gone now. `ubuntu-dev` (VM 105) took over as the machine I develop on when CLI Proxy API moved across on 2026-08-13, and VM 102 sat idle from that point. I shut it down cleanly on 2026-08-14 and destroyed it with `qm destroy 102 --purge`. It carried no snapshot, backup job, HA resource, or replication job, so there was nothing to reconcile first. `pvesh get /cluster/resources` returns no VMID 102, `/etc/pve/qemu-server/102.conf` does not exist, and `pvesm list ssd-lvm1` holds no `vm-102-*` volume; its 120 GiB is back. The full decommission record, including the documentation archival, is [debian-dev Decommission - 2026-08-14](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/debian-dev%20Decommission%20-%202026-08-14.md), and the final configuration snapshot is [Debian Dev Archived Guest - 2026-08-14](../../../Archive/Operations/Inventory/Galaxy/Debian%20Dev%20Archived%20Guest%20-%202026-08-14.md).

## Virtual Machines
| VMID | Name | Node | OS | vCPU | Memory | Disk | IPv4 | Gateway | VLAN | HA |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 105 | ubuntu-dev | grey-server | Ubuntu 26.04 LTS, GNOME 50 | 6 | 16 GiB | 150G | 192.168.40.179/24 | 192.168.40.1 | 40 | disabled |
| 106 | kali-pen | grey-server | Kali Linux | 4 | 5.86 GiB | 50G | 192.168.40.226/24 | 192.168.40.1 | none | disabled |
| 109 | splunk-siem | grey-server | Rocky Linux 10.2 (Red Quartz) | 6 | 12 GiB | 150G | 192.168.72.3/24 | 192.168.72.1 | 72 | disabled |
| 116 | app-01 | grey-server | Debian GNU/Linux 13 (trixie) | 4 | 8 GiB maximum / 4 GiB minimum | 200G | 192.168.80.10/24 | 192.168.80.1 | 80 | disabled |
| 117 | supabase-01 | grey-server | Debian 13 | 4 | 12.60 GiB | 100G | 192.168.80.20/24 | 192.168.80.1 | 80 | disabled |
| 121 | edge-01 | grey-server | Debian GNU/Linux 13 (trixie) | 2 | 4 GiB maximum / 2 GiB minimum | 30G | 192.168.30.10/24 | 192.168.30.1 | 30 | disabled |
| 122 | kasm-01 | purple-server | Ubuntu 24.04.4 LTS | 6 | 12 GiB | 200G | 192.168.78.10/24 | 192.168.78.1 | 78 control, 74/75/77/79 sessions | disabled |
| 200 | security-01 | grey-server | Ubuntu 24.04.4 LTS | 4 | 10 GiB maximum / 8 GiB minimum | 100G | 192.168.72.2/24 | 192.168.72.1 | 72 | disabled |
| 401 | alpha-prod-01 | grey-server | Debian GNU/Linux 13 (trixie) | 6 | 4 GiB maximum / 2 GiB minimum | 60G | 192.168.80.118/24 | 192.168.80.1 | 80 | disabled |

## Templates
| VMID | Name | Node | OS | vCPU | Memory | Disk | IPv4 | Gateway | VLAN | HA |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 101 | debian13-template | grey-server | Debian 13 | 4 | 4 GiB | 60G | none | none | 40 | disabled |
| 9000 | ubuntu-cloud-template | grey-server | Ubuntu 24.04.4 LTS | 2 | 2 GiB | 20G | none | none | 80 | disabled |

## VM Details

### VM 105 - ubuntu-dev

This is the Ubuntu development workstation that takes over from `debian-dev`. I created it on 2026-08-12 and added it to this inventory on 2026-08-13, when CLI Proxy API moved onto it; it ran undocumented in between.

It has 16 GiB with ballooning off, which is deliberate. The running instance predates that setting and has not been restarted to pick it up, so until it is the QEMU monitor reports `actual=12630` against `max_mem=16384` and the guest sees 11.4 GiB. The tables below record the configured end state; the restart is outstanding.

I applied the [Linux Host Baseline Standard](../../../Security/Hardening/Linux-Host-Baseline-Standard.md) on 2026-08-13, following the single-account exception this workstation role carries. It joined fleet monitoring the same day as Wazuh agent `020` and as a node_exporter target.

#### Identity
| Setting | Value |
| --- | --- |
| Node | grey-server |
| Guest hostname | ubuntu-dev |
| Role | GNOME development workstation and Docker host |
| High availability | disabled |
| Template | no |
| OS family | Linux |
| Guest OS | Ubuntu 26.04 LTS, GNOME Shell 50.1 |
| IPv4 | 192.168.40.179/24 |
| Gateway | 192.168.40.1 |
| Login account | `ai-agent` |
| Snapshot | none |

#### Hardware
| Setting | Value |
| --- | --- |
| vCPU | 6 |
| CPU type | host |
| Memory | 16 GiB |
| Ballooning | disabled (`balloon: 0`); pending a guest restart to take effect |
| BIOS | ovmf |
| Machine | q35 |
| SCSI controller | virtio-scsi-single |
| Display | qxl |
| QEMU agent | enabled |
| TPM | disabled |

#### Storage
| Device | Bus | Storage | Volume | Size | Media | Options |
| --- | --- | --- | --- | --- | --- | --- |
| scsi0 | scsi | ssd-lvm1 | vm-105-disk-1 | 150G | disk | discard, I/O thread, SSD emulation |
| efidisk0 | efidisk | ssd-lvm1 | vm-105-disk-0 | 4M | disk | efitype 4m |

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 40 | 192.168.40.179/24 | 192.168.40.1 | enabled | `<REDACTED_UBUNTU_DEV_MAC>` |

### VM 106 - kali-pen

#### Identity
| Setting | Value |
| --- | --- |
| Node | grey-server |
| High availability | disabled |
| Template | no |
| OS family | Linux |
| Guest OS | Kali Linux |
| IPv4 | 192.168.40.226/24 |
| Gateway | 192.168.40.1 |

#### Hardware
| Setting | Value |
| --- | --- |
| vCPU | 4 |
| CPU type | host |
| Memory | 5.86 GiB |
| BIOS | ovmf |
| Machine | q35 |
| SCSI controller | virtio-scsi-single |
| Display | default |
| QEMU agent | not set |
| TPM | disabled |

#### Storage
| Device | Bus | Storage | Volume | Size | Media | Options |
| --- | --- | --- | --- | --- | --- | --- |
| scsi0 | scsi | local-lvm | vm-106-disk-1 | 50G | disk | I/O thread |
| ide2 | ide | local | iso/kali-linux-2025.2-installer-amd64.iso | 4373964K | cdrom | default |
| efidisk0 | efidisk | local-lvm | vm-106-disk-0 | 4M | disk | default |

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | none | 192.168.40.226/24 | 192.168.40.1 | enabled | `<REDACTED_KALI_VM_MAC>` |

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

I stopped and started this guest on 2026-08-10, which cleared the stale 24 GiB QEMU allocation. Its active and configured maximum is now 8 GiB, with a 4 GiB ballooning minimum.

#### Identity
| Setting | Value |
| --- | --- |
| Node | grey-server |
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
| scsi0 | scsi | ssd-lvm1 | vm-116-disk-1 | 200G | disk | I/O thread, SSD emulation |
| efidisk0 | efidisk | ssd-lvm1 | vm-116-disk-0 | 4M | disk | default |

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 80 | 192.168.80.10/24 | 192.168.80.1 | enabled | `<REDACTED_APP_HOST_MAC>` |

### VM 117 - supabase-01

#### Identity
| Setting | Value |
| --- | --- |
| Node | grey-server |
| High availability | disabled |
| Template | no |
| OS family | Linux |
| Guest OS | Debian 13 |
| IPv4 | 192.168.80.20/24 |
| Gateway | 192.168.80.1 |

#### Hardware
| Setting | Value |
| --- | --- |
| vCPU | 4 |
| CPU type | host |
| Memory | 12.60 GiB |
| BIOS | ovmf |
| Machine | q35 |
| SCSI controller | virtio-scsi-single |
| Display | default |
| QEMU agent | enabled |
| TPM | disabled |

#### Storage
| Device | Bus | Storage | Volume | Size | Media | Options |
| --- | --- | --- | --- | --- | --- | --- |
| scsi0 | scsi | ssd-lvm1 | vm-117-disk-1 | 100G | disk | I/O thread, SSD emulation |
| ide2 | ide | local | iso/debian-13.0.0-amd64-netinst.iso | 754M | cdrom | default |
| efidisk0 | efidisk | ssd-lvm1 | vm-117-disk-0 | 4M | disk | default |

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 80 | 192.168.80.20/24 | 192.168.80.1 | enabled | `<REDACTED_SUPABASE_HOST_MAC>` |

### VM 121 - edge-01

#### Identity
| Setting | Value |
| --- | --- |
| Node | grey-server |
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
| scsi0 | scsi | ssd-lvm1 | vm-121-disk-1 | 30G | disk | I/O thread, SSD emulation |
| efidisk0 | efidisk | ssd-lvm1 | vm-121-disk-0 | 4M | disk | default |

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 30 | 192.168.30.10/24 | 192.168.30.1 | enabled | `<REDACTED_EDGE_HOST_MAC>` |

### VM 122 - kasm-01

#### Identity
| Setting | Value |
| --- | --- |
| Node | purple-server |
| Guest hostname | kasm-01 |
| Role | Kasm Workspaces 1.19.0 Community Edition control plane |
| High availability | disabled |
| Template | no |
| OS family | Linux |
| Guest OS | Ubuntu 24.04.4 LTS |
| IPv4 | 192.168.78.10/24 |
| Gateway | 192.168.78.1 |

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
| scsi0 | scsi | ssd-lvm2 | vm-122-disk-1 | 200G | disk | discard, I/O thread, SSD emulation |
| ide2 | ide | ssd-lvm2 | vm-122-cloudinit | 4M | cdrom | default |
| efidisk0 | efidisk | ssd-lvm2 | vm-122-disk-0 | 4M | disk | default |

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 78 | 192.168.78.10/24 | 192.168.78.1 | enabled | <REDACTED_KASM_HOST_MAC> |
| net1 | virtio | vmbr0 | 74 | none | none | disabled | <REDACTED_KASM_LANE_74_MAC> |
| net2 | virtio | vmbr0 | 77 | none | none | disabled | <REDACTED_KASM_LANE_77_MAC> |
| net3 | virtio | vmbr0 | 79 | none | none | disabled | <REDACTED_KASM_LANE_79_MAC> |
| net4 | virtio | vmbr0 | 75 | none | none | disabled | <REDACTED_KASM_LANE_75_MAC> |

Cloned from template 9000 on 2026-07-24. Boots with `onboot=1`. A 4 GiB swap file at `/mnt/Kasm.swap` satisfies Kasm's swap requirement. I moved it to Purple, attached four session NICs, expanded `scsi0` from 100G through 150G to 200G on 2026-07-28, and enabled discard on 2026-07-29. The guest reports a 193G root partition and ext4 filesystem. `baseline-parrot-2026-07-30` is the only VM snapshot. The parents carry no host address; Docker networks `lab74`, `lab75`, `lab77`, and `lab79` own the session ranges.

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

### VM 401 - alpha-prod-01

#### Identity
| Setting | Value |
| --- | --- |
| Node | grey-server |
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
| scsi0 | scsi | ssd-lvm1 | vm-401-disk-1 | 60G | disk | discard, I/O thread, SSD emulation |
| efidisk0 | efidisk | ssd-lvm1 | vm-401-disk-0 | 4M | disk | default |

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
