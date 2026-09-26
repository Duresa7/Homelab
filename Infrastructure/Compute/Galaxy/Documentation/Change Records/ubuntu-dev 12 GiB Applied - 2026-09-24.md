# ubuntu-dev 12 GiB Applied

**Created:** 2026-09-25  
**Last updated:** 2026-09-25

**Observed on:** 2026-09-24  
**Status:** Recorded after the fact; completes the 2026-09-10 memory change  
**Affected systems:** VM 105 `ubuntu-dev` on `grey-server`

## What changed

The 12 GiB setting I applied on 2026-09-10 is now in force. On that day I ran `qm set 105 --memory 12288` without a restart, so Proxmox showed 12,288 MiB pending against 16,384 MiB running. [ubuntu-dev Memory Assessment](ubuntu-dev%20Memory%20Assessment%20-%202026-09-10.md).

On 2026-09-24 `qm config 105` returned `memory: 12288`, `qm pending 105` showed `cur memory: 12288` with nothing pending, and the runtime `maxmem` was 12,884,901,888 bytes (12 GiB). The guest's uptime was 192,960 seconds at about 7:27 PM Eastern, which puts its last full stop and start at about 1:50 PM Eastern on 2026-09-22. I made no record of that restart.

## Current state

- 6 vCPUs, 12 GiB, ballooning off (`balloon: 0`).
- The 4 GiB reduction is released on Grey: Grey used 51.61 of 62.72 GiB on 2026-09-24.

## Verification

The [VM inventory](../../../../../Operations/Inventory/Galaxy/VMs.md) and [Galaxy inventory](../../../../../Operations/Inventory/Galaxy/Galaxy%20Inventory.md) no longer describe the change as pending. I did not check the guest's own memory report (`free -m`) after the restart.
