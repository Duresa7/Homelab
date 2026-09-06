# docker-blue Firewall Grant Narrowed to pve_ssh_manager

**Created:** 2026-09-06  
**Last updated:** 2026-09-06

**Implementation date:** 2026-09-06  
**Status:** Complete  
**Affected systems:** `/etc/pve/firewall/cluster.fw` on all five Galaxy nodes; the SSH Manager on `docker-blue`

## Why

The [2026-09-06 audit](../../../../../Operations/Maintenance/Documentation%20Staleness%20Audit%20-%202026-09-06.md) found `192.168.40.39` admitted twice in the Datacenter firewall: as a member of `pve_admins`, which accepts TCP 22, 8006, and 3128, and as the only member of `pve_ssh_manager`, which accepts TCP 22 alone. Both landed on 2026-08-31 and only the first was recorded. The SSH Manager needs port 22 to the five nodes and nothing else, and the UniFi policy `Allow docker-blue SSH Manager to Proxmox` already limits it to that, so the `pve_admins` membership granted two ports on the Proxmox side that the host has no use for.

## What I did

I copied the file before editing; the redacted copy is [grey-server-pve-cluster.fw-2026-09-06](../../../../../Backups/grey-server-pve-cluster.fw-2026-09-06) and the host keeps no copy. On `grey-server` I deleted the single line `192.168.40.39 # docker-blue SSH Manager` from the `[IPSET pve_admins]` section with `sed`, leaving the `pve_ssh_manager` set and its rule as they were. The file went from 52 lines to 51. `pve-firewall compile` exited 0, and `pve-firewall` picked the change up on its own within its ten-second cycle.

## Verification

- All five nodes read the edited file through pmxcfs: each reports one remaining `192.168.40.39` line, the `pve_ssh_manager` member, and `pve-firewall status` of `enabled/running`.
- The live sets on every node agree: `PVEFW-0-pve_admins-v4` holds four members and no `192.168.40.39`; `PVEFW-0-pve_ssh_manager-v4` holds `192.168.40.39`.
- From `docker-blue`, TCP 22 opens to all five node addresses and TCP 8006 is closed on all five. The SSH Manager gateway that runs on `docker-blue` then executed commands as root on all five nodes, which is the path this rule exists for.

## Result

`pve_admins` now holds the four personal administration sources: the Mac, the Pixel, `ubuntu-dev`, and Jedi PC. `docker-blue` reaches the nodes on port 22 only, through a set named for what it is. The configuration reference is updated in [Datacenter-Firewall.md](../../Configuration/Datacenter-Firewall.md).
