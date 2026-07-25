# ai-bravo-02 Archived Guest

**Created:** 2026-07-25  
**Last updated:** 2026-07-25

**Asset:** Galaxy LXC 105 `ai-bravo-02`  
**Node:** `grey-server`  
**Archive date:** 2026-07-25  
**Status:** Stopped with autostart disabled; deletion scheduled for 2026-08-15

## Verified Configuration

I queried CT 105 through `grey-server` before archiving it. Proxmox reported the guest stopped. I changed `onboot` from `1` to `0`, then confirmed the guest remained stopped.

| Setting | Verified value |
|---|---|
| Guest ID | LXC 105 |
| Hostname | `ai-bravo-02` |
| OS type | Ubuntu, amd64 |
| vCPU | 6 |
| Memory | 24,384 MiB |
| Swap | 8,192 MiB |
| Unprivileged | yes |
| Features | nesting, keyctl, fuse |
| Root volume | `ssd-lvm1:vm-105-disk-0`, 100 GiB |
| Address | `192.168.40.38/24` on VLAN 40 |
| Gateway | `192.168.40.1` |
| Firewall | enabled |
| Administrative account | `<YOUR_DEPLOYMENT_USER>` |
| Workload | TNIO lore retrieval and Discord bot under `/home/<YOUR_DEPLOYMENT_USER>/lore-rag` |
| Host devices | Seven NVIDIA device mappings |
| Autostart | disabled during archival |

The guest configuration and disk still exist on `grey-server`. This record doesn't replace a guest backup.

## Preserved Records

- [TNIO platform archive](../../../Platforms/TNIO%20AI%20Bot/README.md)
- [TNIO walkthrough archive](../../../Guides/TNIO-AI-Bot.md)
- [SSH identity automation record](../../../../Platforms/Ansible/Documentation/Change%20Records/SSH%20Identity%20Automation%20-%202026-07-14.md)
- [Termix SSH host onboarding record](../../../../Platforms/Termix/Documentation/Change%20Records/Termix%20SSH%20Host%20Onboarding%20-%202026-07-14.md)

## Deletion Gate

The [Galaxy backlog](../../../../Infrastructure/Compute/Galaxy/Documentation/TODO.md) schedules deletion for 2026-08-15. Before deleting CT 105, I will confirm it is stopped, verify the archived record and TNIO tree are readable, identify any retained backup outside this repository, & capture the final `pct config 105` output without private data.

After deletion I will confirm that guest ID 105, hostname `ai-bravo-02`, disk `vm-105-disk-0`, address `192.168.40.38`, and every active automation or SSH entry are absent. I will then update this record from archived to retired.
