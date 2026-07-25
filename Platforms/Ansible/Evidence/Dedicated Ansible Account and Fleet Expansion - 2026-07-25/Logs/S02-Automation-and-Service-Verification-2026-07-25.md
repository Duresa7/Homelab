# S02 Automation and Service Verification

**Created:** 2026-07-25  
**Last updated:** 2026-07-25

## Static and Inventory Checks

| Check | Observed result |
|---|---|
| Fleet validator | 9 OS-update hosts, 5 Compose hosts, 16 projects |
| SSH identity validator | 4 identities, 16 supported hosts, 2 unknown hosts, 18 Semaphore templates |
| Fleet syntax | OS and Compose playbooks passed |
| SSH identity syntax | Audit, onboard, stage, verify, & retire playbooks passed |
| Controller project modes | Both project roots `0755`; live identity directory `0700`; identity files `0600` |

The `ansible-control` audit reported the current key present at `/home/ansible/.ssh/authorized_keys` on all nine targets. Every recap had `unreachable=0` and `failed=0`.

## Fleet Checks

- `ansible os_update_targets -m ping` returned `pong` from all nine hosts.
- The become UID command returned `0` from all nine hosts.
- `os-update.yml --check` completed with `failed=0` on eight apt hosts and one dnf host. No reboot task ran.
- The first Compose check exposed protected project files. After the play began using passwordless sudo, `docker-compose-update.yml --check` completed all 16 projects across all 5 hosts with `failed=0`.
- Check mode predicted changes but installed no package, pulled no image, & recreated no container.

## Service Checks

| Workload | Observed result |
|---|---|
| RustDesk | `hbbs` and `hbbr` both running |
| Media services | flaresolverr, gluetun, jellyfin, jellyseerr, prowlarr, qbittorrent, radarr, & sonarr all running |
| Media health | Jellyfin `healthy`; Gluetun `healthy` |
| Exposed media endpoints | Seerr, Radarr, Jellyfin, Sonarr, Prowlarr, & qBittorrent returned HTTP 200 |
| Internal media endpoint | FlareSolverr health returned HTTP 200 from the media network |
| qBittorrent VPN path | Runtime network mode points to the exact Gluetun container ID; `tun0` is visible; external reachability passed without printing the exit address |
| Port forwarding | Gluetun's forwarded-port status file exists and is non-empty |

The complete service check ran after both playbooks, so it also confirms that check mode left the running workloads available.
