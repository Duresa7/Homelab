# Game 01 Archived Guest

**Created:** 2026-09-12  
**Last updated:** 2026-09-12

I retired this guest on 2026-09-12. I subsequently deleted CT 123 and its 80 GiB root volume on Green, including the game data. Proxmox confirms the guest configuration and all CT 123 volumes are absent. The section below preserves the last active inventory, including its former boot policy and management access; those statements are historical. The [retirement record](../../../Platforms/Game%20Servers/Documentation/Change%20Records/Game%2001%20Retirement%20-%202026-09-12.md) holds the verified final state.

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
- SSH Manager reaches the normal administrative account as `dkadi`, which holds `(ALL : ALL) ALL` through the `sudo` group behind a password prompt. `/etc/sudoers.d/00-rootpw` points that prompt at root's password, and the SSH Manager answers it from its configured entry. The `90-dkadi` NOPASSWD drop-in I added on 2026-08-11 came off on 2026-09-07, so the host is no longer a deviation from the [Linux host baseline](../../../../Guides/Linux-Host-Baseline.md). [NOPASSWD Drop-ins Removed on game-01](../../../Operations/Maintenance/NOPASSWD%20Drop-ins%20Removed%20on%20game-01%20-%202026-09-07.md).
- `ansible` keeps its NOPASSWD drop-in. `ai-agent` logs in by key and is not allowed to run sudo since its `90-ai-agent` drop-in was removed the same day, matching the other ten guests. The 2026-08-11 grant is recorded in [Vanilla Keep Inventory and Host Sudo Policy - 2026-08-11](../../../Platforms/Game%20Servers/Documentation/Change%20Records/Vanilla%20Keep%20Inventory%20and%20Host%20Sudo%20Policy%20-%202026-08-11.md).

