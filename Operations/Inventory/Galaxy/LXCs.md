# Galaxy LXCs

**Created:** 2026-07-08  
**Last updated:** 2026-08-11

Galaxy currently has seven active LXCs on grey, blue, red, or green for automation, Docker, monitoring, remote access, media, & game hosting. Retired CT 105 `ai-bravo-02` was deleted from grey on 2026-08-09; its final configuration and TNIO/OpenClaw-backed records remain in the archive.

I recaptured all seven containers after the [2026-08-10 resource efficiency change](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Guest%20Resource%20Efficiency%20Tuning%20-%202026-08-10.md). The active LXC allocation now totals 18 vCPUs, 30 GiB of memory, and 10 GiB of swap. The values below are the live post-restart settings.

## LXC Summary
| CTID | Name | Node | HA | OS | vCPU | Memory | IP | Gateway | VLAN |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 100 | ansible-01 | grey-server | disabled | Debian GNU/Linux 13 (trixie) | 1 | 1 GiB | 192.168.40.36/24 | 192.168.40.1 | 40 |
| 104 | monitor-01 | blue-server | disabled | Debian GNU/Linux 13 (trixie) | 2 | 2 GiB | 192.168.73.2/24 | 192.168.73.1 | 73 |
| 107 | docker-network | blue-server | enabled (`started`) | Debian GNU/Linux 13 (trixie) | 2 | 2 GiB | 192.168.85.2/24 | 192.168.85.1 | 85 |
| 108 | docker-blue | blue-server | enabled | Debian GNU/Linux 13 (trixie) | 1 | 1 GiB | 192.168.40.39/24 | 192.168.40.1 | 40 |
| 110 | docker-main | grey-server | disabled | Debian GNU/Linux 12 (bookworm) | 4 | 8 GiB | 192.168.40.35/24 | 192.168.40.1 | 40 |
| 123 | game-01 | green-server | disabled | Debian GNU/Linux 13 (trixie) | 6 | 12 GiB | 192.168.80.30/24 | 192.168.80.1 | 80 |
| 842 | media-01 | red-server | disabled | Debian GNU/Linux 13 (trixie) | 2 | 4 GiB | 192.168.40.42 | 192.168.40.1 | 40 |

## LXC 100 - ansible-01

### Configuration
| Setting | Value |
| --- | --- |
| Node | grey-server |
| High availability | disabled |
| OS | Debian GNU/Linux 13 (trixie) |
| vCPU | 1 |
| Memory | 1 GiB |
| Swap | 0.50 GiB |
| Unprivileged | yes |
| Features | nesting=1 |
| On boot | yes |

### Storage
| Device | Mount | Storage | Volume | Size | Backup |
| --- | --- | --- | --- | --- | --- |
| rootfs | / | ssd-lvm1 | vm-100-disk-0 | 16G | default |

### Network
| Interface | Bridge | VLAN | IP | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- |
| eth0 | vmbr0 | 40 | 192.168.40.36/24 | 192.168.40.1 | enabled | `<REDACTED_ANSIBLE_CONTROLLER_MAC>` |

## LXC 104 - monitor-01

### Configuration

| Setting | Value |
| --- | --- |
| Node | blue-server |
| High availability | disabled |
| OS | Debian GNU/Linux 13 (trixie) |
| vCPU | 2 |
| Memory | 2 GiB |
| Swap | 1 GiB |
| Unprivileged | yes |
| Features | nesting=1,keyctl=1 |
| On boot | yes |

### Storage

| Device | Mount | Storage | Volume | Size | Backup |
| --- | --- | --- | --- | --- | --- |
| rootfs | / | local-lvm | vm-104-disk-0 | 16G | default |

### Network

| Interface | Bridge | VLAN | IP | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- |
| eth0 | vmbr0 | 73 | 192.168.73.2/24 | 192.168.73.1 | enabled | `<REDACTED_MONITOR_HOST_MAC>` |

The LXC keeps its address static in the Proxmox network configuration. UniFi DHCP remains enabled for `MONITOR-A` from 192.168.73.6 through 192.168.73.254.

### Administrative Access

- SSH is public-key only as `dkadi` and `ansible`; I installed the approved keys.
- Both accounts have their recorded recovery credentials. Root is locked.

### Workload

Prometheus, Grafana, the Proxmox exporter, `blackbox_exporter`, the NUT exporter, and cAdvisor run from `/home/dkadi/monitoring`. The build and verification are in [Monitoring Relocation to monitor-01 - 2026-07-26](../../../Platforms/Prometheus/Documentation/Change%20Records/Monitoring%20Relocation%20to%20monitor-01%20-%202026-07-26.md).

## LXC 107 - docker-network

### Configuration
| Setting | Value |
| --- | --- |
| Node | blue-server |
| High availability | enabled; desired/runtime state `started` |
| OS | Debian GNU/Linux 13 (trixie) |
| vCPU | 2 |
| Memory | 2 GiB |
| Swap | 1 GiB |
| Unprivileged | yes |
| Features | nesting=1,keyctl=1 |
| On boot | yes |
| Tags | docker-network |

### Storage
| Device | Mount | Storage | Volume | Size | Backup |
| --- | --- | --- | --- | --- | --- |
| rootfs | / | local-lvm | vm-107-disk-0 | 32G | default |

The HA resource uses node-local `local-lvm`, so it has no shared-storage failover. After the [2026-07-20 stranding incident](../../../Security/Incidents/Galaxy/HA%20Local%20Storage%20Stranding%20-%202026-07-20.md) I pinned it to blue-server with the strict node-affinity rule `pin-blue-local-storage` (covering CT 107 & CT 108) so HA can't relocate it to a node without its disk.

### Network
| Interface | Bridge | VLAN | IP | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- |
| eth0 | vmbr0 | 85 | 192.168.85.2/24 | 192.168.85.1 | enabled | `<REDACTED_DOCKER_NETWORK_MAC>` |

### Administrative Access

- SSH is public-key only as `dkadi`; I installed the three approved administrative keys.
- `dkadi` has NOPASSWD sudo. Root SSH, password SSH, and keyboard-interactive SSH are disabled.
- Root and `dkadi` password records are locked; public-key SSH remains available.

## LXC 108 - docker-blue

### Configuration
| Setting | Value |
| --- | --- |
| Node | blue-server |
| High availability | enabled; pinned to blue-server via strict node-affinity rule `pin-blue-local-storage` |
| OS | Debian GNU/Linux 13 (trixie) |
| vCPU | 1 |
| Memory | 1 GiB |
| Swap | 0.50 GiB |
| Unprivileged | yes |
| Features | nesting=1 |

### Storage
| Device | Mount | Storage | Volume | Size | Backup |
| --- | --- | --- | --- | --- | --- |
| rootfs | / | local-lvm | vm-108-disk-0 | 15G | default |

### Network
| Interface | Bridge | VLAN | IP | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- |
| eth0 | vmbr0 | 40 | 192.168.40.39/24 | 192.168.40.1 | enabled | `<REDACTED_DOCKER_BLUE_MAC>` |

## LXC 110 - docker-main

### Configuration
| Setting | Value |
| --- | --- |
| Node | grey-server |
| High availability | disabled |
| OS | Debian GNU/Linux 12 (bookworm) |
| vCPU | 4 |
| Memory | 8 GiB |
| Swap | 4 GiB |
| Unprivileged | yes |
| Features | nesting=1 |
| Tags | docker |

### Storage
| Device | Mount | Storage | Volume | Size | Backup |
| --- | --- | --- | --- | --- | --- |
| rootfs | / | local-lvm | vm-110-disk-0 | 100G | default |
| mp0 | /data | hddpool-1 | subvol-110-disk-0 | 2900G | enabled |

### Network
| Interface | Bridge | VLAN | IP | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- |
| eth0 | vmbr0 | 40 | 192.168.40.35/24 | 192.168.40.1 | enabled | `<REDACTED_DOCKER_MAIN_MAC>` |

## LXC 123 - game-01

### Configuration
| Setting | Value |
| --- | --- |
| Node | green-server |
| High availability | disabled |
| OS | Debian GNU/Linux 13 (trixie) |
| vCPU | 6 |
| Memory | 12 GiB |
| Swap | 2 GiB |
| Unprivileged | yes |
| Features | nesting=1,keyctl=1 |
| On boot | yes |

### Storage
| Device | Mount | Storage | Volume | Size | Backup |
| --- | --- | --- | --- | --- | --- |
| rootfs | / | local-lvm | vm-123-disk-0 | 80G | default |

### Network
| Interface | Bridge | VLAN | IP | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- |
| eth0 | vmbr0 | 80 | 192.168.80.30/24 | 192.168.80.1 | enabled | `<REDACTED_GAME_01_MAC>` |

### Administrative Access

- SSH is public-key only. Root login, password authentication, and keyboard-interactive authentication are disabled.
- SSH Manager reaches the normal administrative account as `dkadi`. `/etc/sudoers.d/90-dkadi` has granted it NOPASSWD sudo since 2026-08-11; the complete sudoers configuration parsed successfully, and `sudo -n` worked through the normal SSH path. This is a deliberate deviation from the [Linux host baseline](../../../Guides/Linux-Host-Baseline.md) awaiting the fleet sudo decision, not baseline-conforming state.
- `ansible` and `ai-agent` retain their separate NOPASSWD drop-ins. `ai-agent` has no authorized SSH key and cannot use the key-only SSH path. The policy change is recorded with the game-rule work in [Vanilla Keep Inventory and Host Sudo Policy - 2026-08-11](../../../Platforms/Game%20Servers/Documentation/Change%20Records/Vanilla%20Keep%20Inventory%20and%20Host%20Sudo%20Policy%20-%202026-08-11.md).

## LXC 842 - media-01

### Configuration

| Setting | Value |
| --- | --- |
| Node | red-server |
| High availability | disabled |
| OS | Debian GNU/Linux 13 (trixie) |
| vCPU | 2 |
| Memory | 4 GiB |
| Swap | 1 GiB |
| Unprivileged | yes |
| Features | nesting=1,keyctl=1 |
| On boot | yes |
| Startup | order=40, up delay=30 seconds |
| Tags | media |

### Storage

| Device | Mount | Storage | Volume | Size | Backup |
| --- | --- | --- | --- | --- | --- |
| rootfs | / | local-lvm | vm-842-disk-0 | 100G | default |
| mp0 | /data | host ext4 bind mount | /mnt/bindmounts/media-01-hdd/data | 931.5G raw, 916G usable | disabled |

The host mounts ext4 UUID `289788f9-52a4-4e49-885b-000e8d565c8b` with systemd automount. The `data` child exists only on that filesystem; CT 842 refuses startup when the HDD isn't mounted.

### Host Devices

| Entry | Host device | Mode | Purpose |
| --- | --- | --- | --- |
| dev0 | /dev/dri/renderD128 | 0666 | Jellyfin Intel Quick Sync |
| dev1 | /dev/net/tun | 0666 | Gluetun WireGuard tunnel |

### Network

| Interface | Bridge | VLAN | IP | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- |
| eth0 | vmbr0 | 40 | 192.168.40.42 | 192.168.40.1 | enabled | `<REDACTED_MEDIA_HOST_MAC>` |

### Administrative Access

- SSH is public-key only as `dkadi`; I installed the approved administrative keys.
- `dkadi` has NOPASSWD sudo. Root SSH, password SSH, and keyboard-interactive SSH are disabled.
- Root is locked; the administrative account uses the recorded public-key SSH path.

## Archived & Retired LXCs

CT 104 `ai-alpha-01` no longer exists in Galaxy. I preserved its last recorded configuration, OpenClaw deployment records, & retirement verification in the [2026-07-25 retired guest record](../../../Archive/Operations/Inventory/Galaxy/AI%20Alpha%2001%20Retired%20Guest%20-%202026-07-25.md).

CT 105 `ai-bravo-02` no longer exists in Galaxy. I deleted it and its 100 GiB root volume on 2026-08-09 after preserving its TNIO source, tests, configuration, records, walkthrough, diagrams, OpenClaw-backed inference records, and final configuration in the [retired guest record](../../../Archive/Operations/Inventory/Galaxy/AI%20Bravo%2002%20Archived%20Guest%20-%202026-07-25.md). The [retirement record](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/AI%20Bravo%2002%20Retirement%20-%202026-08-09.md) records the deletion and external cleanup.
