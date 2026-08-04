# S02 UniFi Changes

**Created:** 2026-07-27  
**Last updated:** 2026-07-27

I previewed and applied one mutation at a time.

| Policy | Before | After | Result |
|---|---|---|---|
| `Allow Internal to AlphaSec-Mgmt` | Enabled, all Internal clients | Disabled | Only explicit exceptions now pass the zone default block |
| `Docker-main Allowed -> Server` | All protocols, Proxmox ports 22 and 8006 | TCP 8006 only | Dashboard API retained; SSH removed |

The after snapshots, both retained on my workstation outside this repository, are:

- `firewall_20260727T122457Z_after-internal-disable.json`
- `firewall_20260727T122558Z_after-docker-narrow.json`

The structural diffs showed only the intended policy in each mutation.
