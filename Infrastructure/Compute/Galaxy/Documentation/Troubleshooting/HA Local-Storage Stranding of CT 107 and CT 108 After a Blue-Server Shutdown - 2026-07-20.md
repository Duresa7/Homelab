# HA Local-Storage Stranding of CT 107 and CT 108 After a Blue-Server Shutdown

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Investigated:** 2026-07-20  
**Owner:** Galaxy / Proxmox HA  
**Status:** Resolved

## Symptom and impact

CT 107 `docker-network` & CT 108 `docker-blue` were both down and both sat in the HA `error` state on purple-server. `ha-manager migrate ct:107 blue-server` returned exit code 255, so I couldn't move either one back to blue where it started. NetBird, Nginx Proxy Manager (CT 107), & the RustDesk relay `hbbs`/`hbbr` (CT 108) were offline from 16:30 to 17:04 EDT, about 34 minutes.

## What I found

The two config files had moved to `/etc/pve/nodes/purple-server/lxc/`, but purple had no disks for them: `pct list` showed both `stopped`, and `lvs` on purple carried only `data`, `root`, & `swap`. blue still held the real disks, `pve/vm-107-disk-0` (32 GiB) & `pve/vm-108-disk-0` (15 GiB), inactive because the configs weren't on blue. The purple task log spelled it out: `vzstart` failing with `no such logical volume pve/vm-107-disk-0`, `vzmigrate ... migration aborted`, and `ha-manager migrate ct:107 blue-server' failed: exit code 255`.

## Root cause

Both containers are HA-managed and put their rootfs on `local-lvm`, node-local LVM-thin with no shared copy on any other node. The trigger was planned maintenance: I was moving blue, purple, red, & grey onto a UPS and shut blue down. `datacenter.cfg` sets no HA `shutdown_policy`, so it defaults to `conditional`, which relocates HA services on a node shutdown rather than freezing them, and blue's LRM logged `got shutdown request with shutdown policy 'conditional'` at 16:30:14. `last` confirms `shutdown system down Mon Jul 20 16:30 - 16:36`, a power-down, not a reboot. The shutdown made the CRM relocate 107 & 108 off blue; the configs went to purple, the node-local disks couldn't follow, and every start looped into `error`. A migrate command against a service already in `error` is refused (`service 'ct:107' in error state, must be disabled and fixed first`), which is why the exit 255 attempts never had a chance.

## Corrective action

The data was safe on blue, so this was a config-and-disk reunion, not a restore. I removed both from HA (`ha-manager remove ct:107` & `ct:108`) to clear the error state, moved each config from `purple-server/lxc/` back to `blue-server/lxc/`, and started them with `pct start`. The disks reactivated (`Vwi-aotz--`) and both workloads came up: `netbird-server`, `netbird-dashboard`, & a healthy `nginx-proxy-manager` on 107; `hbbs` & `hbbr` on 108. I then re-added both to HA and applied a strict node-affinity rule, `pin-blue-local-storage`, limiting `ct:107,ct:108` to `blue-server` so the HA manager can't relocate them to a diskless node again.

## Verification

- `ha-manager status` reports `service ct:107 (blue-server, started)` & `service ct:108 (blue-server, started)`.
- `ha-manager rules list` shows `pin-blue-local-storage`; `pct list` on blue shows both `running`.
- SSH reached 192.168.85.2 with NetBird & NPM healthy; CT 108 held 192.168.40.39/24 with its gateway reachable and both relay containers up.
- purple's `lxc` directory is empty of 107/108, and red carried no stale `vm-107`/`vm-108` volumes.

## Related records

- Full write-up, screenshots, & log transcripts in the [Galaxy HA Local-Storage Stranding Incident report](../../../../../Security/Incidents/Galaxy-HA-Local-Storage-Stranding-2026-07-20/Galaxy-HA-Local-Storage-Stranding-Incident-2026-07-20.md).
- The [Docker-Network LXC deployment record](../Change%20Records/Galaxy%20Docker-Network%20LXC%20Deployment%20-%202026-07-10.md) documented the no-failover caveat this incident exercised.
- blue's back-to-back reboot & shutdown may relate to the [recurring pvestatd failure on blue-server](#1-recurring-pvestatd-failure-on-blue-server).
