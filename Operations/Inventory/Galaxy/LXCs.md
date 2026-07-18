# Galaxy LXCs

**Created:** 2026-07-08  
**Last updated:** 2026-07-18

This is my configuration inventory of the LXC containers on the Galaxy cluster.

## Summary
| CTID | Name | Node | HA | OS | vCPU | Memory | IP | Gateway | VLAN |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 100 | ansible-01 | grey-server | disabled | Debian GNU/Linux 13 (trixie) | 1 | 1 GiB | 192.168.40.36/24 | 192.168.40.1 | 40 |
| 104 | ai-alpha-01 | grey-server | disabled | debian | 2 | 4 GiB | 192.168.40.37/24 | 192.168.40.1 | 40 |
| 105 | ai-bravo-02 | grey-server | disabled | ubuntu | 6 | 23.81 GiB | 192.168.40.38/24 | 192.168.40.1 | 40 |
| 107 | docker-network | blue-server | enabled (`started`) | Debian GNU/Linux 13 (trixie) | 2 | 4 GiB | 192.168.85.2/24 | 192.168.85.1 | 85 |
| 108 | docker-blue | blue-server | enabled | Debian GNU/Linux 13 (trixie) | 2 | 4 GiB | 192.168.40.39/24 | 192.168.40.1 | 40 |
| 110 | docker-main | grey-server | disabled | Debian GNU/Linux 12 (bookworm) | 10 | 23.44 GiB | 192.168.40.35/24 | 192.168.40.1 | 40 |
| 842 | media-01 | red-server | disabled | Debian GNU/Linux 13 (trixie) | 4 | 8 GiB | 192.168.40.42 | 192.168.40.1 | 40 |

## LXC 100 - ansible-01

### Overview
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
| eth0 | vmbr0 | 40 | 192.168.40.36/24 | 192.168.40.1 | enabled | REDACTED_MAC_015 |

## LXC 104 - ai-alpha-01

### Overview
| Setting | Value |
| --- | --- |
| Node | grey-server |
| High availability | disabled |
| OS | debian |
| vCPU | 2 |
| Memory | 4 GiB |
| Swap | 2 GiB |
| Unprivileged | yes |
| Features | nesting=1 |

### Storage
| Device | Mount | Storage | Volume | Size | Backup |
| --- | --- | --- | --- | --- | --- |
| rootfs | / | ssd-lvm1 | vm-104-disk-0 | 40G | default |

### Network
| Interface | Bridge | VLAN | IP | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- |
| eth0 | vmbr0 | 40 | 192.168.40.37/24 | 192.168.40.1 | enabled | REDACTED_MAC_008 |

## LXC 105 - ai-bravo-02

### Overview
| Setting | Value |
| --- | --- |
| Node | grey-server |
| High availability | disabled |
| OS | ubuntu |
| vCPU | 6 |
| Memory | 23.81 GiB |
| Swap | 8 GiB |
| Unprivileged | yes |
| Features | nesting=1,keyctl=1,fuse=1 |

### Storage
| Device | Mount | Storage | Volume | Size | Backup |
| --- | --- | --- | --- | --- | --- |
| rootfs | / | ssd-lvm1 | vm-105-disk-0 | 100G | default |

### Host Devices
| Entry | Host device | Mode |
| --- | --- | --- |
| dev0 | /dev/nvidia0 | 0666 |
| dev1 | /dev/nvidiactl | 0666 |
| dev2 | /dev/nvidia-modeset | 0666 |
| dev3 | /dev/nvidia-uvm | 0666 |
| dev4 | /dev/nvidia-uvm-tools | 0666 |
| dev5 | /dev/nvidia-caps/nvidia-cap1 | 0666 |
| dev6 | /dev/nvidia-caps/nvidia-cap2 | 0666 |

### Network
| Interface | Bridge | VLAN | IP | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- |
| eth0 | vmbr0 | 40 | 192.168.40.38/24 | 192.168.40.1 | enabled | REDACTED_MAC_004 |

## LXC 107 - docker-network

### Overview
| Setting | Value |
| --- | --- |
| Node | blue-server |
| High availability | enabled; desired/runtime state `started` |
| OS | Debian GNU/Linux 13 (trixie) |
| vCPU | 2 |
| Memory | 4 GiB |
| Swap | 1 GiB |
| Unprivileged | yes |
| Features | nesting=1,keyctl=1 |
| On boot | yes |
| Tags | docker-network |

### Storage
| Device | Mount | Storage | Volume | Size | Backup |
| --- | --- | --- | --- | --- | --- |
| rootfs | / | local-lvm | vm-107-disk-0 | 32G | default |

The HA resource uses node-local `local-lvm`; it does not have shared-storage failover to another node.

### Network
| Interface | Bridge | VLAN | IP | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- |
| eth0 | vmbr0 | 85 | 192.168.85.2/24 | 192.168.85.1 | enabled | REDACTED_MAC_013 |

### Administrative Access

- SSH is public-key only as `REDACTED_USER_001`; I installed the three approved administrative keys.
- `REDACTED_USER_001` has NOPASSWD sudo. Root SSH, password SSH, and keyboard-interactive SSH are disabled.
- Root and `REDACTED_USER_001` password records remain locked pending protected console entry; this does not affect key-based SSH.

## LXC 108 - docker-blue

### Overview
| Setting | Value |
| --- | --- |
| Node | blue-server |
| High availability | enabled |
| OS | Debian GNU/Linux 13 (trixie) |
| vCPU | 2 |
| Memory | 4 GiB |
| Swap | 1 GiB |
| Unprivileged | yes |
| Features | nesting=1 |

### Storage
| Device | Mount | Storage | Volume | Size | Backup |
| --- | --- | --- | --- | --- | --- |
| rootfs | / | local-lvm | vm-108-disk-0 | 15G | default |

### Network
| Interface | Bridge | VLAN | IP | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- |
| eth0 | vmbr0 | 40 | 192.168.40.39/24 | 192.168.40.1 | enabled | REDACTED_MAC_002 |

## LXC 110 - docker-main

### Overview
| Setting | Value |
| --- | --- |
| Node | grey-server |
| High availability | disabled |
| OS | Debian GNU/Linux 12 (bookworm) |
| vCPU | 10 |
| Memory | 23.44 GiB |
| Swap | 15.71 GiB |
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
| eth0 | vmbr0 | 40 | 192.168.40.35/24 | 192.168.40.1 | enabled | REDACTED_MAC_014 |

## LXC 842 - media-01

### Overview

| Setting | Value |
| --- | --- |
| Node | red-server |
| High availability | disabled |
| OS | Debian GNU/Linux 13 (trixie) |
| vCPU | 4 |
| Memory | 8 GiB |
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

### Host Devices

| Entry | Host device | Mode | Purpose |
| --- | --- | --- | --- |
| dev0 | /dev/dri/renderD128 | 0666 | Jellyfin Intel Quick Sync |
| dev1 | /dev/net/tun | 0666 | Gluetun WireGuard tunnel |

### Network

| Interface | Bridge | VLAN | IP | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- |
| eth0 | vmbr0 | 40 | 192.168.40.42 | 192.168.40.1 | enabled | REDACTED_MAC_021 |

### Administrative Access

- SSH is public-key only as `REDACTED_USER_001`; I installed the approved administrative keys.
- `REDACTED_USER_001` has NOPASSWD sudo. Root SSH, password SSH, and keyboard-interactive SSH are disabled.
- Root is locked. The administrative account retains a protected console password outside the repository.
