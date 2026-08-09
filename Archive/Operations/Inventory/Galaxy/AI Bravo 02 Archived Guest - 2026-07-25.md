# ai-bravo-02 Archived Guest

**Created:** 2026-07-25  
**Last updated:** 2026-08-09

**Asset:** Galaxy LXC 105 `ai-bravo-02`  
**Node:** `grey-server`  
**Archive date:** 2026-07-25  
**Status:** Retired; CT 105 and its root volume were deleted on 2026-08-09

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
| eth0 | vmbr0 | 40 | 192.168.40.38/24 | 192.168.40.1 | enabled | `<REDACTED_AI_BRAVO_MAC>` |

### Account & Workload

| Setting | Value |
| --- | --- |
| Administrative account | `aibravo` |
| Workload | TNIO lore retrieval & Discord bot with an OpenClaw-backed inference layer |
| Former project path | `/home/aibravo/lore-rag` |

This final configuration snapshot survives in the archive. It is not a restorable guest backup; no restorable guest backup existed when I retired the machine.

## Archival Verification

I queried CT 105 through `grey-server` before archiving it. Proxmox reported the guest stopped. I changed `onboot` from `1` to `0`, then confirmed the guest remained stopped. The [Galaxy change record](../../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/AI%20Bravo%2002%20Archival%20and%20Autostart%20Disablement%20-%202026-07-25.md) records the command, result, decision, evidence, verification, rollback, & remaining work.

## Retirement Verification

I completed the deletion gate early on 2026-08-09. CT 105 was still stopped with autostart disabled, the archived TNIO platform tree, OpenClaw-related records, walkthrough, and diagrams were readable, and Proxmox held no snapshot, HA resource, replication job, or configured backup for the guest. I captured the final redacted configuration, deleted CT 105 with its unreferenced 100 GiB root volume, and confirmed the guest ID, configuration file, and storage volume were absent while Galaxy remained quorate with five votes.

UniFi held no matching client record, fixed address, local DNS record, firewall object, policy target, client group, content filter, ACL, or traffic route. Ansible, monitoring, Wazuh, local SSH configuration, and known-host files had no active dependency. The generated documentation host page was removed from the live site; its retired route returns HTTP `404`. The [retirement record](../../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/AI%20Bravo%2002%20Retirement%20-%202026-08-09.md) holds the deletion and cleanup evidence.

## Preserved Records

- [TNIO platform archive](../../../Platforms/TNIO%20AI%20Bot/README.md)
- [TNIO walkthrough archive](../../../Guides/TNIO-AI-Bot.md)
- [OpenClaw walkthrough archive](../../../Guides/OpenClaw.md)
- [TNIO OpenClaw integration and fixes record](../../../Platforms/TNIO%20AI%20Bot/Documentation/Change%20Records/tnio-bot-fixes-report-2026-05-11.md)
- [SSH identity automation record](../../../../Platforms/Ansible/Documentation/Change%20Records/SSH%20Identity%20Automation%20-%202026-07-14.md)
- [Termix SSH host onboarding record](../../../Platforms/Termix/Documentation/Change%20Records/Termix%20SSH%20Host%20Onboarding%20-%202026-07-14.md)

## Current-State Cleanup

I removed `ai-bravo-02` from the active Galaxy LXC table, guide index, Ansible host inventory, Termix candidate group, three live identity allowlists, local SSH alias, known-host files, and the durable SSH Manager configuration. I left dated Ansible, Termix, TNIO, OpenClaw, and governance records unchanged as history.

The already-running SSH Manager process retains its startup-time copy of the server definition until that process restarts. The durable source entry is gone, and there is no active session, tunnel, alias, group membership, or pooled connection for it.

## Retirement Complete

I completed every item in the [Galaxy backlog checklist](../../../../Infrastructure/Compute/Galaxy/Documentation/TODO.md) on 2026-08-09. The archive is the retained record; the guest and its root volume are not recoverable from a Proxmox backup.
