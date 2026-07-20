# Galaxy VMs

**Created:** 2026-07-08  
**Last updated:** 2026-07-20

This is my configuration inventory of the QEMU VMs and templates on the Galaxy cluster.

## Virtual Machines
| VMID | Name | Node | OS | vCPU | Memory | Disk | IPv4 | Gateway | VLAN | HA |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 102 | db-13-dev | grey-server | Debian GNU/Linux 13.6 (trixie), GNOME 48 | 4 | 4 GiB | 60G | 192.168.40.135/24 | 192.168.40.1 | 40 | disabled |
| 103 | W11-Test-1 | grey-server | Windows 11 Pro | 4 | 8 GiB | 80G | 192.168.65.112/24 | 192.168.65.1 | 65 | disabled |
| 106 | kali-pen | grey-server | Kali Linux | 4 | 5.86 GiB | 50G | 192.168.40.226/24 | 192.168.40.1 | none | disabled |
| 109 | splunk-siem | grey-server | Rocky Linux 10.2 (Red Quartz) | 6 | 12 GiB | 150G | 192.168.72.3/24 | 192.168.72.1 | 72 | disabled |
| 116 | app-01 | grey-server | Debian GNU/Linux 13 (trixie) | 6 | 24 GiB | 200G | 192.168.80.10/24 | 192.168.80.1 | 80 | disabled |
| 117 | supabase-01 | grey-server | Debian 13 | 4 | 12.60 GiB | 100G | 192.168.80.20/24 | 192.168.80.1 | 80 | disabled |
| 121 | edge-01 | grey-server | Debian GNU/Linux 13 (trixie) | 2 | 6.53 GiB | 30G | 192.168.90.10/24 | 192.168.90.1 | 90 | disabled |
| 200 | security-01 | grey-server | Ubuntu 24.04.4 LTS | 4 | 12 GiB | 100G | 192.168.72.2/24 | 192.168.72.1 | 72 | disabled |
| 300 | ws-dc-1 | grey-server | Windows Server 2025 | 4 | 12 GiB | 100G | 192.168.65.10/24 | 192.168.65.1 | 65 | disabled |
| 301 | ws-dc-2 | grey-server | Windows Server 2025 | 4 | 8 GiB | 100G | 192.168.65.45/24 | 192.168.65.1 | 65 | disabled |
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
| net0 | virtio | vmbr0 | 40 | 192.168.40.135/24 | 192.168.40.1 | enabled | `<YOUR_DEBIAN_DEV_MAC>` |

### VM 103 - W11-Test-1

#### Identity
| Setting | Value |
| --- | --- |
| Node | grey-server |
| High availability | disabled |
| Template | no |
| OS family | Windows |
| Guest OS | Windows 11 Pro |
| IPv4 | 192.168.65.112/24 |
| Gateway | 192.168.65.1 |

#### Hardware
| Setting | Value |
| --- | --- |
| vCPU | 4 |
| CPU type | host |
| Memory | 8 GiB |
| BIOS | ovmf |
| Machine | pc-q35-10.1 |
| SCSI controller | virtio-scsi-single |
| Display | default |
| QEMU agent | enabled |
| TPM | enabled (ssd-lvm1, v2.0) |

#### Storage
| Device | Bus | Storage | Volume | Size | Media | Options |
| --- | --- | --- | --- | --- | --- | --- |
| scsi0 | scsi | ssd-lvm1 | vm-103-disk-1 | 80G | disk | discard, I/O thread, SSD emulation |
| ide0 | ide | local | iso/virtio-win-0.1.285.iso | 771138K | cdrom | default |
| efidisk0 | efidisk | ssd-lvm1 | vm-103-disk-0 | 4M | disk | default |
| tpmstate0 | tpmstate | ssd-lvm1 | vm-103-disk-2 | 4M | disk | default |

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 65 | 192.168.65.112/24 | 192.168.65.1 | enabled | `<YOUR_WINDOWS_TEST_VM_MAC>` |

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
| net0 | virtio | vmbr0 | none | 192.168.40.226/24 | 192.168.40.1 | enabled | `<YOUR_KALI_VM_MAC>` |

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
| net0 | virtio | vmbr0 | 72 | 192.168.72.3/24 | 192.168.72.1 | enabled | `<YOUR_SPLUNK_VM_MAC>` |

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
| net0 | virtio | vmbr0 | 80 | 192.168.80.10/24 | 192.168.80.1 | enabled | `<YOUR_APP_HOST_MAC>` |

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
| net0 | virtio | vmbr0 | 80 | 192.168.80.20/24 | 192.168.80.1 | enabled | `<YOUR_SUPABASE_HOST_MAC>` |

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
| net0 | virtio | vmbr0 | 90 | 192.168.90.10/24 | 192.168.90.1 | enabled | `<YOUR_EDGE_HOST_MAC>` |

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
| net0 | virtio | vmbr0 | 72 | 192.168.72.2/24 | 192.168.72.1 | enabled | `<YOUR_SECURITY_HOST_MAC>` |

### VM 300 - ws-dc-1

#### Identity
| Setting | Value |
| --- | --- |
| Node | grey-server |
| High availability | disabled |
| Template | no |
| OS family | Windows |
| Guest OS | Windows Server 2025 |
| IPv4 | 192.168.65.10/24 |
| Gateway | 192.168.65.1 |

#### Hardware
| Setting | Value |
| --- | --- |
| vCPU | 4 |
| CPU type | host |
| Memory | 12 GiB |
| BIOS | ovmf |
| Machine | pc-q35-10.1 |
| SCSI controller | virtio-scsi-single |
| Display | default |
| QEMU agent | enabled |
| TPM | enabled (ssd-lvm1, v2.0) |

#### Storage
| Device | Bus | Storage | Volume | Size | Media | Options |
| --- | --- | --- | --- | --- | --- | --- |
| scsi0 | scsi | ssd-lvm1 | vm-300-disk-1 | 100G | disk | discard, I/O thread, SSD emulation |
| ide0 | ide | local | iso/virtio-win-0.1.285.iso | 771138K | cdrom | default |
| efidisk0 | efidisk | ssd-lvm1 | vm-300-disk-0 | 4M | disk | default |
| tpmstate0 | tpmstate | ssd-lvm1 | vm-300-disk-2 | 4M | disk | default |

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 65 | 192.168.65.10/24 | 192.168.65.1 | disabled | `<YOUR_FIRST_DOMAIN_CONTROLLER_MAC>` |

### VM 301 - ws-dc-2

#### Identity
| Setting | Value |
| --- | --- |
| Node | grey-server |
| High availability | disabled |
| Template | no |
| OS family | Windows |
| Guest OS | Windows Server 2025 |
| IPv4 | 192.168.65.45/24 |
| Gateway | 192.168.65.1 |

#### Hardware
| Setting | Value |
| --- | --- |
| vCPU | 4 |
| CPU type | host |
| Memory | 8 GiB |
| BIOS | ovmf |
| Machine | pc-q35-10.1 |
| SCSI controller | virtio-scsi-single |
| Display | default |
| QEMU agent | enabled |
| TPM | enabled (ssd-lvm1, v2.0) |

#### Storage
| Device | Bus | Storage | Volume | Size | Media | Options |
| --- | --- | --- | --- | --- | --- | --- |
| scsi0 | scsi | ssd-lvm1 | vm-301-disk-1 | 100G | disk | discard, I/O thread, SSD emulation |
| ide0 | ide | local | iso/virtio-win-0.1.285.iso | 771138K | cdrom | default |
| efidisk0 | efidisk | ssd-lvm1 | vm-301-disk-0 | 4M | disk | default |
| tpmstate0 | tpmstate | ssd-lvm1 | vm-301-disk-2 | 4M | disk | default |

#### Network
| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 65 | 192.168.65.45/24 | 192.168.65.1 | disabled | `<YOUR_SECOND_DOMAIN_CONTROLLER_MAC>` |

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
| net0 | virtio | vmbr0 | 80 | 192.168.80.118/24 | 192.168.80.1 | enabled | `<YOUR_TEAMSPEAK_HOST_MAC>` |

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
| net0 | virtio | vmbr0 | 40 | none | none | enabled | `<YOUR_DEBIAN_TEMPLATE_MAC>` |

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
| net0 | virtio | vmbr0 | 80 | none | none | disabled | `<YOUR_UBUNTU_TEMPLATE_MAC>` |
