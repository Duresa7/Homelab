# Galaxy LXCs

**Created:** 2026-07-08  
**Last updated:** 2026-09-25

Galaxy has six LXCs, all running, on blue-server, grey-server and red-server. I read them back from `pvesh get /cluster/resources` and each container's configuration on 2026-09-24. Together they hold 13 vCPUs, 27 GiB of memory and 8.5 GiB of swap. No container is an HA resource: `ha-manager config` and `ha-manager rules config` return nothing.

## Recent changes

- 2026-09-24: I found monitor-01's rootfs at 20G and the HA resources for CT 107 and CT 108 removed. [monitor-01 Rootfs at 20 GiB](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/monitor-01%20Rootfs%20at%2020%20GiB%20-%202026-09-24.md), [CT 107 and CT 108 HA Removal](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/CT%20107%20and%20CT%20108%20HA%20Removal%20-%202026-09-24.md).
- 2026-09-12: I moved CT 100 `ansible-01` to Blue's `local-lvm`. [Migration record](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/ansible-01%20Blue%20Migration%20-%202026-09-12.md).
- 2026-09-12: I retired `game-01` and deleted CT 123 with its 80 GiB volume on `green-server`. [Archived guest record](../../../Archive/Operations/Inventory/Galaxy/Game%2001%20Archived%20Guest%20-%202026-09-12.md).

## LXC Summary
| CTID | Name | Node | HA | OS | vCPU | Memory | IP | Gateway | VLAN |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 100 | ansible-01 | blue-server | disabled | Debian GNU/Linux 13 (trixie) | 1 | 1 GiB | 192.168.40.36/24 | 192.168.40.1 | 40 |
| 104 | monitor-01 | blue-server | disabled | Debian GNU/Linux 13 (trixie) | 2 | 2 GiB | 192.168.73.2/24 | 192.168.73.1 | 73 |
| 107 | docker-network | blue-server | disabled | Debian GNU/Linux 13 (trixie) | 2 | 2 GiB | 192.168.85.2/24 | 192.168.85.1 | 85 |
| 108 | docker-blue | blue-server | disabled | Debian GNU/Linux 13 (trixie) | 2 | 2 GiB | 192.168.40.39/24 | 192.168.40.1 | 40 |
| 110 | docker-main | grey-server | disabled | Debian GNU/Linux 12 (bookworm) | 4 | 16 GiB | 192.168.40.35/24 | 192.168.40.1 | 40 |
| 842 | media-01 | red-server | disabled | Debian GNU/Linux 13 (trixie) | 2 | 4 GiB | 192.168.40.42 | 192.168.40.1 | 40 |

## LXC 100 - ansible-01

### Configuration
| Setting | Value |
| --- | --- |
| Node | blue-server |
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
| rootfs | / | local-lvm | vm-100-disk-0 | 16G | default |

### Network
| Interface | Bridge | VLAN | IP | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- |
| eth0 | vmbr0 | 40 | 192.168.40.36/24 | 192.168.40.1 | enabled | `<REDACTED_ANSIBLE_CONTROLLER_MAC>` |

I removed the stale `net1` VLAN 74 interface on 2026-08-19 after retiring the Kasm lab lane that needed it. The container has only `eth0` and no `192.168.74.0/24` route.

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
| rootfs | / | local-lvm | vm-104-disk-0 | 20G | default |

### Network

| Interface | Bridge | VLAN | IP | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- |
| eth0 | vmbr0 | 73 | 192.168.73.2/24 | 192.168.73.1 | enabled | `<REDACTED_MONITOR_HOST_MAC>` |

The LXC keeps its address static in the Proxmox network configuration. UniFi DHCP remains enabled for `MONITOR-A` from 192.168.73.6 through 192.168.73.254.

### Administrative Access

- SSH is public-key only as `dkadi` and `ansible`; I installed my administrative keys. SSH Manager reaches it through a ProxyJump.
- `dkadi` holds `(ALL : ALL) ALL` through the `sudo` group behind a password prompt that `/etc/sudoers.d/00-rootpw` points at root's password. Its `90-dkadi` NOPASSWD drop-in came off on 2026-09-07. `ansible` keeps NOPASSWD; `ai-agent` cannot run sudo. [NOPASSWD Drop-ins Removed on docker-network, monitor-01 and media-01](../../Maintenance/NOPASSWD%20Drop-ins%20Removed%20on%20docker-network,%20monitor-01%20and%20media-01%20-%202026-09-07.md).
- Root and `dkadi` carry known passwords since 2026-08-15, for the console and the sudo prompt only.

### Workload

Prometheus, Grafana, the Proxmox exporter, `blackbox_exporter`, the NUT exporter, and cAdvisor run from `/home/dkadi/monitoring`. The build and verification are in [Monitoring Relocation to monitor-01 - 2026-07-26](../../../Platforms/Prometheus/Documentation/Change%20Records/Monitoring%20Relocation%20to%20monitor-01%20-%202026-07-26.md).

## LXC 107 - docker-network

### Configuration
| Setting | Value |
| --- | --- |
| Node | blue-server |
| High availability | disabled; the HA resource was removed between 2026-09-06 and 2026-09-23 |
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

The rootfs is on node-local `local-lvm`, so there is no shared-storage failover. After the [2026-07-20 stranding incident](../../../Security/Incidents/Galaxy/HA%20Local%20Storage%20Stranding%20-%202026-07-20.md) I kept CT 107 and CT 108 as HA resources pinned to blue-server by the strict node-affinity rule `pin-blue-local-storage`. Both resources and the rule were present on 2026-09-06 and absent by 2026-09-23. Neither container is HA-managed now: a Blue outage stops both until Blue returns. [CT 107 and CT 108 HA Removal](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/CT%20107%20and%20CT%20108%20HA%20Removal%20-%202026-09-24.md).

### Network
| Interface | Bridge | VLAN | IP | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- |
| eth0 | vmbr0 | 85 | 192.168.85.2/24 | 192.168.85.1 | enabled | `<REDACTED_DOCKER_NETWORK_MAC>` |

### Administrative Access

- SSH is public-key only as `dkadi`; I installed my three administrative keys. Root SSH, password SSH, and keyboard-interactive SSH are disabled.
- `dkadi` holds `(ALL : ALL) ALL` through the `sudo` group behind a password prompt that `/etc/sudoers.d/00-rootpw` points at root's password. Its `90-dkadi` NOPASSWD drop-in came off on 2026-09-07. `ansible` keeps NOPASSWD; `ai-agent` cannot run sudo. [NOPASSWD Drop-ins Removed on docker-network, monitor-01 and media-01](../../Maintenance/NOPASSWD%20Drop-ins%20Removed%20on%20docker-network,%20monitor-01%20and%20media-01%20-%202026-09-07.md).
- Root and `dkadi` carry known passwords since 2026-08-15; password SSH stays disabled, so they serve the console and the sudo prompt only.

## LXC 108 - docker-blue

### Configuration
| Setting | Value |
| --- | --- |
| Node | blue-server |
| High availability | disabled; the HA resource was removed between 2026-09-06 and 2026-09-23 |
| OS | Debian GNU/Linux 13 (trixie) |
| vCPU | 2 |
| Memory | 2 GiB |
| Swap | 1 GiB |
| Unprivileged | yes |
| Features | nesting=1 |
| On boot | yes |

### Storage
| Device | Mount | Storage | Volume | Size | Backup |
| --- | --- | --- | --- | --- | --- |
| rootfs | / | local-lvm | vm-108-disk-0 | 15G | default |

### Network
| Interface | Bridge | VLAN | IP | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- |
| eth0 | vmbr0 | 40 | 192.168.40.39/24 | 192.168.40.1 | enabled | `<REDACTED_DOCKER_BLUE_MAC>` |

### Administrative Access

- SSH is public-key only as `dkadi`, with `(ALL : ALL) ALL` through the `sudo` group behind a prompt that `/etc/sudoers.d/00-rootpw` points at root's password. `ansible` keeps NOPASSWD; `ai-agent` cannot run sudo. Root login is disabled.
- The host clock moved from `Etc/UTC` to `America/New_York` on 2026-09-07. The SSH Manager restart timer names its zone explicitly and still fires at 4 AM Eastern; no container on the host mounts the host's zone file.

## LXC 110 - docker-main

### Configuration
| Setting | Value |
| --- | --- |
| Node | grey-server |
| High availability | disabled |
| OS | Debian GNU/Linux 12 (bookworm) |
| vCPU | 4 |
| Memory | 16 GiB |
| Swap | 4 GiB |
| Unprivileged | yes |
| Features | nesting=1 |
| Tags | docker |
| GPU devices | GTX 1080 Ti via `/dev/nvidia0`, `nvidiactl`, `nvidia-modeset`, both UVM nodes, and both NVIDIA capability nodes |

### Storage
| Device | Mount | Storage | Volume | Size | Backup |
| --- | --- | --- | --- | --- | --- |
| rootfs | / | local-lvm | vm-110-disk-0 | 100G | default |
| mp0 | /data | hddpool-1 | subvol-110-disk-0 | 2900G | enabled |

Until 2026-09-06 the configuration also carried `unused0: hddpool:subvol-110-disk-0`, a reference to a storage ID that no longer exists; the pool is `hddpool-1`, and the one volume on it is the `subvol-110-disk-0` that `mp0` mounts. Proxmox showed it as a phantom unused disk. I removed the line by editing the pmxcfs file directly rather than through `pct set --delete`, which would have tried to free the named volume, and the container kept running with `/data` mounted throughout. [CT 110 Phantom Unused Volume Removed](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/CT%20110%20Phantom%20Unused%20Volume%20Removed%20-%202026-09-06.md) has the verification.

### Network
| Interface | Bridge | VLAN | IP | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- |
| eth0 | vmbr0 | 40 | 192.168.40.35/24 | 192.168.40.1 | enabled | `<REDACTED_DOCKER_MAIN_MAC>` |

### Administrative Access

- Root-login only, keyed. I keep this host outside the three-account model, so it has no `dkadi` account.
- The host clock moved from `Etc/UTC` to `America/New_York` on 2026-09-07. Immich and Forgejo mount the host's zone file; Immich already ran on Eastern through its own `TZ` variable, and Forgejo keeps reporting UTC until its next restart. The CLI Proxy API container carries `TZ=Asia/Shanghai` from its upstream image.

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

- SSH is public-key only as `dkadi`; I installed my administrative keys. Root SSH, password SSH, and keyboard-interactive SSH are disabled, and sshd carries an `AllowUsers dkadi ansible ai-agent` list, the only one in the fleet.
- `dkadi` holds `(ALL : ALL) ALL` through the `sudo` group behind a password prompt that `/etc/sudoers.d/00-rootpw` points at root's password. Its NOPASSWD drop-in, named `dkadi` rather than `90-dkadi`, came off on 2026-09-07. `ansible` keeps NOPASSWD; `ai-agent` cannot run sudo. [NOPASSWD Drop-ins Removed on docker-network, monitor-01 and media-01](../../Maintenance/NOPASSWD%20Drop-ins%20Removed%20on%20docker-network,%20monitor-01%20and%20media-01%20-%202026-09-07.md).
- Root and `dkadi` carry known passwords since 2026-08-15, for the console and the sudo prompt only. The host clock moved from `Etc/UTC` to `America/New_York` on 2026-09-07, matching the other guests and the baseline.

## Archived and Retired LXCs

CT 104 `ai-alpha-01` no longer exists in Galaxy. I preserved its last recorded configuration, OpenClaw deployment records, and retirement verification in the [2026-07-25 retired guest record](../../../Archive/Operations/Inventory/Galaxy/AI%20Alpha%2001%20Retired%20Guest%20-%202026-07-25.md).

CT 105 `ai-bravo-02` no longer exists in Galaxy. I deleted it and its 100 GiB root volume on 2026-08-09 after preserving its TNIO source, tests, configuration, records, walkthrough, diagrams, OpenClaw-backed inference records, and final configuration in the [retired guest record](../../../Archive/Operations/Inventory/Galaxy/AI%20Bravo%2002%20Archived%20Guest%20-%202026-07-25.md). The [retirement record](../../../Archive/Infrastructure/Compute/Galaxy/Documentation/Change%20Records/AI%20Bravo%2002%20Retirement%20-%202026-08-09.md) records the deletion and external cleanup.
