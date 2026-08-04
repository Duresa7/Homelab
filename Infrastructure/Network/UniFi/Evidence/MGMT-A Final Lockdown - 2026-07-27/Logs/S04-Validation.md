# S04 Validation

**Created:** 2026-07-27  
**Last updated:** 2026-07-27

| Source | Test | Result |
|---|---|---|
| Jedi PC | TCP 22 and 8006 to four nodes | 8 of 8 open |
| `ansible-01` | TCP 22 and 8006 to four nodes | 8 of 8 open |
| `docker-main` | TCP 22 to four nodes | 4 of 4 blocked |
| `docker-main` | TCP 8006 to four nodes | 4 of 4 open |
| `docker-main` | Homelab dashboard health | Healthy |
| `monitor-01` | TCP 8006 and 9100 to four nodes | 8 of 8 open |
| `monitor-01` | TCP 3493 to Grey and Red | 2 of 2 open |
| WireGuard | UniFi and Proxmox rule inspection | Both broad MGMT paths retained |
| NetBird | Rule inspection | No MGMT path added |

No WireGuard client was connected for a live packet test. I recorded that as a verification limit instead of claiming a test I did not run.
