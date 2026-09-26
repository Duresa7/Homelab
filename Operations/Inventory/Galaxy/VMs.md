# Galaxy VMs

**Created:** 2026-07-08  
**Last updated:** 2026-09-25

Galaxy has 12 QEMU VMs and three templates. I read every figure below back from `pvesh get /cluster/resources` and the guest configuration files on 2026-09-24. Ten VMs were running; `kali-pen` and `HQ-WS001` were stopped. No VM is an HA resource: `ha-manager config` returns nothing. This file records each guest's CPU, memory, storage, firmware, network, VLAN, firewall, TPM, and QEMU-agent state.

## Recent changes

- 2026-09-24: I found `HQ-WS001` at 8 GiB and stopped, and `ubuntu-dev` running on its 12 GiB setting. [HQ-WS001 Memory at 8 GiB](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/HQ-WS001%20Memory%20at%208%20GiB%20-%202026-09-24.md), [ubuntu-dev 12 GiB Applied](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/ubuntu-dev%2012%20GiB%20Applied%20-%202026-09-24.md).
- 2026-09-23: I moved VM 103 `win11-dev` from Green to Grey's `local-lvm`. [Migration record](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/win11-dev%20Grey%20Migration%20-%202026-09-23.md).
- 2026-09-21: I completed VM 103 `win11-dev` as a standalone Windows 11 Pro 25H2 workstation. [Completion record](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/win11-dev%20Completion%20-%202026-09-21.md).

## Virtual Machines
| VMID | Name | Node | State | OS | vCPU | Memory | Disk | IPv4 | Gateway | VLAN | HA |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 102 | kali-pen | grey-server | stopped | Kali Linux 2026.2 | 6 | 8 GiB | 100G | Not captured | 192.168.40.1 | 40 | disabled |
| 103 | win11-dev | grey-server | running | Windows 11 Pro 25H2 | 4 | 8 GiB | 120G | 192.168.40.117/24 | 192.168.40.1 | 40 | disabled |
| 105 | ubuntu-dev | grey-server | running | Ubuntu 26.04.1 LTS, GNOME 50 | 6 | 12 GiB | 150G | 192.168.40.179/24 | 192.168.40.1 | 40 | disabled |
| 109 | splunk-siem | grey-server | running | Rocky Linux 10.2 (Red Quartz) | 6 | 12 GiB | 150G | 192.168.72.3/24 | 192.168.72.1 | 72 | disabled |
| 116 | app-01 | purple-server | running | Debian GNU/Linux 13 (trixie) | 4 | 8 GiB maximum / 4 GiB minimum | 64G | 192.168.80.10/24 | 192.168.80.1 | 80 | disabled |
| 121 | edge-01 | purple-server | running | Debian GNU/Linux 13 (trixie) | 2 | 4 GiB maximum / 2 GiB minimum | 30G | 192.168.30.10/24 | 192.168.30.1 | 30 | disabled |
| 200 | security-01 | grey-server | running | Ubuntu 24.04.4 LTS | 4 | 10 GiB maximum / 8 GiB minimum | 100G | 192.168.72.2/24 | 192.168.72.1 | 72 | disabled |
| 301 | HQ-DC01 | grey-server | running | Windows Server 2025 Standard | 4 | 4 GiB | 80G | 192.168.65.10/24 | 192.168.65.1 | 65 | disabled |
| 302 | HQ-DC02 | grey-server | running | Windows Server 2025 Standard | 4 | 4 GiB | 80G | 192.168.65.11/24 | 192.168.65.1 | 65 | disabled |
| 303 | HQ-MGT01 | grey-server | running | Windows Server 2025 Standard | 2 | 6 GiB | 100G | 192.168.65.12/24 | 192.168.65.1 | 65 | disabled |
| 310 | HQ-WS001 | grey-server | stopped | Windows 11 Pro 25H2 | 4 | 8 GiB | 80G | 192.168.65.20/24 | 192.168.65.1 | 65 | disabled |
| 401 | alpha-prod-01 | purple-server | running | Debian GNU/Linux 13 (trixie) | 6 | 4 GiB maximum / 2 GiB minimum | 60G | 192.168.80.118/24 | 192.168.80.1 | 80 | disabled |

## Templates
| VMID | Name | Node | OS | vCPU | Memory | Disk | IPv4 | Gateway | VLAN | HA |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 101 | debian13-template | grey-server | Debian 13 | 4 | 4 GiB | 60G | none | none | 40 | disabled |
| 300 | ws2025-template | grey-server | Windows Server 2025 Standard | 4 | 4 GiB | 80G | none | none | 65 | disabled |
| 9000 | ubuntu-cloud-template | grey-server | Ubuntu 24.04.4 LTS | 2 | 2 GiB | 20G | none | none | 80 | disabled |

## VM Details

### VM 103 - win11-dev

I built this guest on Green between 2026-09-20 and 2026-09-21 and moved it to Grey on 2026-09-23 after Green's memory test failures. It runs standalone in `WORKGROUP` with local `dkadi`, and SSH Manager reaches it as `win11_dev`. Windows activation is still open. [Completion record](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/win11-dev%20Completion%20-%202026-09-21.md), [migration record](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/win11-dev%20Grey%20Migration%20-%202026-09-23.md).

OVMF with pre-enrolled Secure Boot keys, TPM 2.0, `virtio-scsi-single`, and `vmbr0` VLAN 40. Disks: `local-lvm:vm-103-disk-0` (4 MiB EFI), `vm-103-disk-1` (120 GiB system), and `vm-103-disk-2` (4 MiB TPM). `onboot=1`; no installation discs remain attached. Secure Boot is enabled and TPM is ready. `sshd` and `QEMU-GA` start automatically; the final device query reports no unresolved drivers. No development tools are installed.

### VM 102 - kali-pen

I rebuilt this VM on 2026-08-26. The earlier `kali-pen` was VM 106, a 4 vCPU, 5.86 GiB guest with a 50G disk, no VLAN tag, and the Kali 2025.2 installer; I destroyed it at 10:42 EDT and created this one at 10:52 EDT under VMID 102. The new guest is tagged VLAN 40, carries the Kali 2026.2 installer, and has the QEMU agent and a QXL display enabled. It was stopped on 2026-09-06 and again on 2026-09-24, so its address has never been read back; the previous VM held 192.168.40.226.

#### Identity
| Setting | Value |
| --- | --- |
| Node | grey-server |
| High availability | disabled |
| Template | no |
| OS family | Linux |
| Guest OS | Kali Linux, 2026.2 installer |
| IPv4 | Not captured; the VM was stopped at every readback |
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

This is the Ubuntu development workstation that took over from `debian-dev`. I created it on 2026-08-12 and added it here on 2026-08-13. On 2026-09-08 I moved both disks to Grey's NVMe-backed `local-lvm`. [Storage move record](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/ubuntu-dev%20NVMe%20Storage%20Move%20-%202026-09-08.md).

It runs with 12 GiB and ballooning off. I set 12 GiB on 2026-09-10 without a restart; the guest's uptime of 192,960 seconds on the evening of 2026-09-24 puts the restart that applied it at about 1:50 PM Eastern on 2026-09-22. [Memory assessment](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/ubuntu-dev%20Memory%20Assessment%20-%202026-09-10.md), [12 GiB applied](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/ubuntu-dev%2012%20GiB%20Applied%20-%202026-09-24.md).

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
| Memory | 12 GiB (`memory: 12288`), applied at the restart of about 2026-09-22 |
| Ballooning | disabled (`balloon: 0`) |
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

On 2026-09-11 I replaced its 200 GiB system disk with a 64 GiB disk and then moved both disks to Purple's NVMe-backed `local-lvm`. [Replacement record](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/app-01%2064%20GiB%20Boot%20Disk%20Replacement%20-%202026-09-11.md), [migration record](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/app-01%20and%20edge-01%20Purple%20Migration%20-%202026-09-11.md). A stop and start on 2026-08-10 cleared a stale 24 GiB QEMU allocation. [Resource tuning record](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Guest%20Resource%20Efficiency%20Tuning%20-%202026-08-10.md).

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

I moved both disks to Purple's NVMe-backed `local-lvm` on 2026-09-11. [Migration record](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/app-01%20and%20edge-01%20Purple%20Migration%20-%202026-09-11.md).

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

I built it with 4 GiB because `grey-server` was carrying 51 GiB of its 62 GiB at the time. On 2026-09-24 the configuration read `memory: 8192`, `balloon: 0`, `onboot: 0`, and the VM was stopped. [HQ-WS001 Memory at 8 GiB](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/HQ-WS001%20Memory%20at%208%20GiB%20-%202026-09-24.md).

OpenSSH Server has been enabled on this machine since 2026-09-19, and `Allow Secure to HQ-WS001 SSH` admits VLAN 50 to it. It is not enrolled in SSH Manager. [SSH enablement record](../../../Platforms/Active%20Directory/Documentation/Change%20Records/HQ-WS001%20SSH%20Enablement%20-%202026-09-19.md).

#### Identity
| Setting | Value |
| --- | --- |
| Node | grey-server |
| Guest hostname | HQ-WS001 |
| Role | Windows 11 test workstation for tiered policy and LAPS validation |
| State | stopped, `onboot: 0`, on 2026-09-24 |
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
| Memory | 8 GiB |
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

## Retired VMs

| VMID | Name | Removed | Record |
| --- | --- | --- | --- |
| 111 | fedora-dev | Deleted; absent from the cluster, its config and `ssd-lvm1` on 2026-08-08 | No separate record |
| 102 | debian-dev | Destroyed 2026-08-14; VMID 102 was reused for `kali-pen` on 2026-08-26 | [debian-dev Decommission](../../../Archive/Infrastructure/Compute/Galaxy/Documentation/Change%20Records/debian-dev%20Decommission%20-%202026-08-14.md), [archived guest](../../../Archive/Operations/Inventory/Galaxy/Debian%20Dev%20Archived%20Guest%20-%202026-08-14.md) |
| 106 | kali-pen (first build) | Destroyed 10:42 AM Eastern 2026-08-26 and rebuilt as VM 102 | Detail block above |
| 122 | kasm-01 | Destroyed 2026-08-19 with all volumes | [Kasm Workspaces Decommission](../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspaces%20Decommission%20-%202026-08-19.md) |
| 117 | supabase-01 | Confirmed deleted 2026-08-20 | [Supabase 01 Retirement](../../../Archive/Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Supabase%2001%20Retirement%20-%202026-08-20.md) |
