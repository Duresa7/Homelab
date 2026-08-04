# Galaxy VMs Post-Kasm Build-Out Snapshot

**Created:** 2026-07-28  
**Last updated:** 2026-07-29  
**Snapshot date:** 2026-07-28

I recorded 10 Galaxy QEMU VMs and two templates. This snapshot includes each guest's CPU, memory, storage, firmware, network, VLAN, firewall, TPM, and QEMU-agent state.

I captured the live cluster after the Kasm workspace build-out. VM 122 had its 200G disk, VLAN 75 NIC, and four session lanes. The cluster resource API listed 10 QEMU VMs and two templates.

VM 111 `fedora-dev` was missing from this file until 2026-07-26. I found it in the PVE API while building the Grafana guest-inventory panel, which reads every guest the hypervisor knows about rather than every guest I had written down. It has been stopped since 2026-07-15 and holds 80 GiB on `ssd-lvm1`. I decided to keep it on 2026-07-27.

## Virtual Machines
| VMID | Name | Node | OS | vCPU | Memory | Disk | IPv4 | Gateway | VLAN | HA |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 102 | db-13-dev | grey-server | Debian GNU/Linux 13.6 (trixie), GNOME 48 | 4 | 4 GiB | 60G | 192.168.40.135/24 | 192.168.40.1 | 40 | disabled |
| 106 | kali-pen | grey-server | Kali Linux | 4 | 5.86 GiB | 50G | 192.168.40.226/24 | 192.168.40.1 | none | disabled |
| 109 | splunk-siem | grey-server | Rocky Linux 10.2 (Red Quartz) | 6 | 12 GiB | 150G | 192.168.72.3/24 | 192.168.72.1 | 72 | disabled |
| 111 | fedora-dev | grey-server | Fedora (l26 ostype; release not captured while stopped) | 6 | 8 GiB | 80G | none recorded, stopped since 2026-07-15 | 192.168.40.1 | 40 | disabled |
| 116 | app-01 | grey-server | Debian GNU/Linux 13 (trixie) | 6 | 24 GiB | 200G | 192.168.80.10/24 | 192.168.80.1 | 80 | disabled |
| 117 | supabase-01 | grey-server | Debian 13 | 4 | 12.60 GiB | 100G | 192.168.80.20/24 | 192.168.80.1 | 80 | disabled |
| 121 | edge-01 | grey-server | Debian GNU/Linux 13 (trixie) | 2 | 6.53 GiB | 30G | 192.168.90.10/24 | 192.168.90.1 | 90 | disabled |
| 122 | kasm-01 | purple-server | Ubuntu 24.04.4 LTS | 4 | 8 GiB | 200G | 192.168.78.10/24 | 192.168.78.1 | 78 control, 74/75/77/79 sessions | disabled |
| 200 | security-01 | grey-server | Ubuntu 24.04.4 LTS | 4 | 12 GiB | 100G | 192.168.72.2/24 | 192.168.72.1 | 72 | disabled |
| 401 | alpha-prod-01 | grey-server | Debian GNU/Linux 13 (trixie) | 6 | 16 GiB | 60G | 192.168.80.118/24 | 192.168.80.1 | 80 | disabled |

## Templates
| VMID | Name | Node | OS | vCPU | Memory | Disk | IPv4 | Gateway | VLAN | HA |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 101 | debian13-template | grey-server | Debian 13 | 4 | 4 GiB | 60G | none | none | 40 | disabled |
| 9000 | ubuntu-cloud-template | grey-server | Ubuntu 24.04.4 LTS | 2 | 2 GiB | 20G | none | none | 80 | disabled |

## VM Details

### VM 102 - db-13-dev

#### Identity
| Setting | Value |
| --- | --- |
| Node | grey-server |
| Guest hostname | debian-dev |
| Role | GNOME development workstation and database test VM |
| High availability | disabled |
| Template | no |
| OS family | Linux |
| Guest OS | Debian GNU/Linux 13.6 (trixie), GNOME Shell 48.7 |
| IPv4 | 192.168.40.135/24 |
| Gateway | 192.168.40.1 |

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
| scsi0 | scsi | ssd-lvm1 | vm-102-disk-1 | 60G | disk | discard, I/O thread, SSD emulation |
| efidisk0 | efidisk | ssd-lvm1 | vm-102-disk-0 | 4M | disk | default |

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 40 | 192.168.40.135/24 | 192.168.40.1 | enabled | `<REDACTED_DEBIAN_DEV_MAC>` |

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

### VM 111 - fedora-dev

Recorded on 2026-07-26 after the PVE API surfaced it and this inventory did not. Created 2026-07-14 16:42:59 UTC, first booted successfully at 16:47:09 the same day after two failed starts that ended `QEMU exited with code 1`, and last started 2026-07-15 13:22:07 UTC. Stopped since.

No `onboot` flag, so it does not come up with the node. The IPv4 address is unrecorded because the QEMU agent only reports one while the guest runs, and I did not start it to find out. Its 80 GiB disk is 4.2% of `ssd-lvm1`, which sits at 18.99% used, so it costs capacity but nothing urgent.

I decided to retain this VM on 2026-07-27. Its exact development workload still isn't documented, so I left the technical inventory unchanged instead of inventing a role from its name.

#### Identity
| Setting | Value |
| --- | --- |
| Node | grey-server |
| High availability | disabled |
| Template | no |
| OS family | Linux |
| Guest OS | `ostype: l26`; Fedora per the guest name, release not captured while stopped |
| IPv4 | none recorded |
| Gateway | 192.168.40.1 |
| Power state | stopped since 2026-07-15 |
| Retention decision | Keep; confirmed 2026-07-27 |

#### Hardware
| Setting | Value |
| --- | --- |
| vCPU | 6 |
| CPU type | host |
| Memory | 8 GiB |
| BIOS | ovmf |
| Machine | q35 |
| SCSI controller | virtio-scsi-single |
| Display | virtio |
| QEMU agent | enabled |
| TPM | disabled |
| Created by | QEMU 11.0.0 |

#### Storage
| Device | Bus | Storage | Volume | Size | Media | Options |
| --- | --- | --- | --- | --- | --- | --- |
| scsi0 | scsi | ssd-lvm1 | vm-111-disk-1 | 80G | disk | discard, I/O thread, SSD emulation |
| efidisk0 | efidisk | ssd-lvm1 | vm-111-disk-0 | 4M | disk | efitype 4m, pre-enrolled keys, ms-cert 2023k |

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 40 | none recorded | 192.168.40.1 | enabled | `<REDACTED_FEDORA_DEV_MAC>` |

### VM 116 - app-01

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
| vCPU | 6 |
| CPU type | host |
| Memory | 24 GiB |
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
| IPv4 | 192.168.90.10/24 |
| Gateway | 192.168.90.1 |

#### Hardware
| Setting | Value |
| --- | --- |
| vCPU | 2 |
| CPU type | host |
| Memory | 6.53 GiB |
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
| net0 | virtio | vmbr0 | 90 | 192.168.90.10/24 | 192.168.90.1 | enabled | `<REDACTED_EDGE_HOST_MAC>` |

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
| vCPU | 4 |
| CPU type | host |
| Memory | 8 GiB |
| BIOS | ovmf |
| Machine | q35 |
| SCSI controller | virtio-scsi-single |
| Display | default |
| QEMU agent | enabled |
| TPM | disabled |

#### Storage
| Device | Bus | Storage | Volume | Size | Media | Options |
| --- | --- | --- | --- | --- | --- | --- |
| scsi0 | scsi | ssd-lvm2 | vm-122-disk-1 | 200G | disk | I/O thread, SSD emulation |
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

Cloned from template 9000 on 2026-07-24. Boots with `onboot=1`. A 4 GiB swap file at `/mnt/Kasm.swap` satisfies Kasm's swap requirement. I moved it to Purple, attached four session NICs, and expanded `scsi0` from 100G through 150G to 200G on 2026-07-28. The guest reports a 193G root partition and ext4 filesystem. The parents carry no host address; Docker networks `lab74`, `lab75`, `lab77`, and `lab79` own the session ranges.

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
| Memory | 12 GiB |
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
| Memory | 16 GiB |
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
