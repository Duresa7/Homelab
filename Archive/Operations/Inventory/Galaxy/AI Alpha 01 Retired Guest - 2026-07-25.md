# ai-alpha-01 Retired Guest

**Created:** 2026-07-25  
**Last updated:** 2026-07-31

**Former asset:** Galaxy LXC 104 `ai-alpha-01`  
**Former node:** `grey-server`  
**Verification date:** 2026-07-25  
**Status:** Deleted before verification; exact deletion date wasn't retained

## Recorded Configuration

I preserved the last configuration recorded in the Galaxy LXC inventory. CT 104 ran Debian with 2 vCPU, 4 GiB memory, 2 GiB swap, nesting enabled, & a 40 GiB `ssd-lvm1` root volume.

| Setting | Recorded value |
|---|---|
| Guest ID | LXC 104 |
| Hostname | `ai-alpha-01` |
| Address | `192.168.40.37/24` on VLAN 40 |
| Gateway | `192.168.40.1` |
| Administrative account | `openclaw` |
| Root volume | `ssd-lvm1:vm-104-disk-0`, 40 GiB |
| Workload | OpenClaw 2026.4.25 Discord assistant |

## Retirement Verification

I queried the Galaxy cluster resources on 2026-07-25. No VM or LXC with guest ID 104 or hostname `ai-alpha-01` existed on any of the four nodes. The live SSH endpoint at `192.168.40.37` had also timed out in the 2026-07-14 Ansible and Termix checks.

The cluster no longer holds the guest configuration or disk. This archive is a documentation record, not a backup that can restore CT 104.

## Preserved Records

- [OpenClaw setup overview](../../../Platforms/Openclaw/Documentation/OpenClaw-Setup-Overview.md)
- [OpenClaw 2026-04-27 change record](../../../Platforms/Openclaw/Documentation/OpenClaw-Change-Record-2026-04-27.md)
- [Archived OpenClaw walkthrough](../../../Guides/OpenClaw.md)
- [SSH identity automation record](../../../../Platforms/Ansible/Documentation/Change%20Records/SSH%20Identity%20Automation%20-%202026-07-14.md)
- [Termix SSH host onboarding record](../../../Platforms/Termix/Documentation/Change%20Records/Termix%20SSH%20Host%20Onboarding%20-%202026-07-14.md)

## Current-State Cleanup

I removed `ai-alpha-01` from current Ansible target inventories, the active guide index, the VLAN 40 example list, the controller identity allowlist, & local SSH connection state. I left dated change records, troubleshooting records, maintenance records, sensitive scrub artifacts, & other historical references unchanged.
