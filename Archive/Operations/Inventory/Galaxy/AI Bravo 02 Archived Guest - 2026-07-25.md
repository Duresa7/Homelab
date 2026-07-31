# ai-bravo-02 Archived Guest

**Created:** 2026-07-25  
**Last updated:** 2026-07-31

**Asset:** Galaxy LXC 105 `ai-bravo-02`  
**Node:** `grey-server`  
**Archive date:** 2026-07-25  
**Status:** Stopped with autostart disabled; deletion scheduled for 2026-08-15

## Archived Configuration

I copied the former active inventory tables without dropping the storage, network, backup, high-availability, or NVIDIA device fields.

### Configuration

| Setting | Value |
| --- | --- |
| Node | grey-server |
| High availability | disabled |
| OS | ubuntu |
| Architecture | amd64 |
| vCPU | 6 |
| Memory | 23.81 GiB |
| Swap | 8 GiB |
| Unprivileged | yes |
| Features | nesting=1,keyctl=1,fuse=1 |
| On boot | disabled during archival |

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
| eth0 | vmbr0 | 40 | 192.168.40.38/24 | 192.168.40.1 | enabled | `<YOUR_AI_BRAVO_MAC>` |

### Account & Workload

| Setting | Value |
| --- | --- |
| Administrative account | `<YOUR_DEPLOYMENT_USER>` |
| Workload | TNIO lore retrieval & Discord bot |
| Former project path | `/home/<YOUR_DEPLOYMENT_USER>/lore-rag` |

The guest configuration & disk still exist on `grey-server`. This record doesn't replace a guest backup.

## Archival Verification

I queried CT 105 through `grey-server` before archiving it. Proxmox reported the guest stopped. I changed `onboot` from `1` to `0`, then confirmed the guest remained stopped. The [Galaxy change record](../../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/AI%20Bravo%2002%20Archival%20and%20Autostart%20Disablement%20-%202026-07-25.md) records the command, result, decision, evidence, verification, rollback, & remaining work.

## Preserved Records

- [TNIO platform archive](../../../Platforms/TNIO%20AI%20Bot/README.md)
- [TNIO walkthrough archive](../../../Guides/TNIO-AI-Bot.md)
- [SSH identity automation record](../../../../Platforms/Ansible/Documentation/Change%20Records/SSH%20Identity%20Automation%20-%202026-07-14.md)
- [Termix SSH host onboarding record](../../../Platforms/Termix/Documentation/Change%20Records/Termix%20SSH%20Host%20Onboarding%20-%202026-07-14.md)

## Current-State Cleanup

I removed `ai-bravo-02` from the active Galaxy LXC table, guide index, Ansible host inventory, Termix candidate group, three live identity allowlists, local SSH alias, & known-host files. I left the dated Ansible, Termix, TNIO, & governance records unchanged.

The SSH Manager server definition remains available for deletion-day cleanup. CT 105 is stopped, so the record doesn't provide a live connection.

## Deletion Gate

The [Galaxy backlog](../../../../Infrastructure/Compute/Galaxy/Documentation/TODO.md) schedules deletion for 2026-08-15. Before deleting CT 105, I will confirm it is stopped, verify the archived record & TNIO tree are readable, identify any retained backup outside this repository, & capture the final `pct config 105` output without private data.

After deletion I will confirm that guest ID 105, hostname `ai-bravo-02`, disk `vm-105-disk-0`, address `192.168.40.38`, & every active automation or SSH entry are absent. I will then update this record from archived to retired.
