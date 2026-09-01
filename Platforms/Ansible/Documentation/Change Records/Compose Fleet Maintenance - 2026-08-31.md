# Compose Fleet Maintenance

**Created:** 2026-09-01  
**Last updated:** 2026-09-01

**Implementation date:** 2026-08-31  
**Final verification:** 2026-09-01  
**Status:** Complete  
**Primary owner:** Ansible  
**Affected systems:** `docker-main`, `docker-network`, `docker-blue`, `media-01`, `alpha-prod-01`, `monitor-01`

## Scope

I reconciled the fleet-update inventory with the running Compose projects, ran the 24-project update, and checked the services that received new images. The inventory remains bounded to six Docker hosts. Coolify-owned projects on `app-01`, the matched Pelican Panel and Wings pair on `game-01`, and the separately managed cAdvisor projects remain outside this play.

The same maintenance run advanced Portainer, NetBird, Forgejo, Prometheus, Grafana, the Proxmox exporter, and five media-stack containers. I did not run OS package updates or reboot a host.

## Inventory Reconciliation

The deployed inventory held 21 projects before this pass. I added four running projects that the automation did not own yet:

- `cli-proxy-api` and the local-image `docusaurus` project on `docker-main`
- `docker-mcp-gateway` and `executor` on `docker-blue`

I removed the retired `teamspeak` project from `alpha-prod-01` so a future run cannot recreate TeamSpeak server 01. `docusaurus` joins `teamspeak-monitor` with `pull: never` because both images are built locally and have no registry source. The resulting inventory has 12 OS-update hosts, six Compose hosts, and 24 Compose projects.

I deployed the inventory and validator to `/home/ansible/fleet-updates` on `ansible-01`. The local and deployed validators both returned `12 OS-update hosts, 6 compose hosts, 24 projects`, both playbooks passed syntax checks, and all 12 OS targets answered Ansible `ping`.

## Observed Changes

The live run recreated these containers from newer images between 11:43 PM and 11:49 PM Eastern on 2026-08-31:

| Host | Recreated containers | Verified version or state |
|---|---|---|
| `docker-main` | `portainer_ce`, `forgejo` | Portainer 2.45.0; Forgejo 15.0.7 |
| `docker-network` | `netbird-server`, `netbird-dashboard`, `portainer_edge_agent` | NetBird management 0.77.1, dashboard 2.91.1, Edge Agent 2.45.0; HTTPS `200` |
| `docker-blue` | `portainer_edge_agent` | Edge Agent 2.45.0 |
| `media-01` | `qbittorrent`, `radarr`, `sonarr`, `gluetun`, `prowlarr`, `portainer_edge_agent` | All project containers running; Edge Agent 2.45.0 |
| `alpha-prod-01` | `portainer_edge_agent` | Edge Agent 2.45.0 |
| `monitor-01` | `prometheus`, `grafana`, `pve-exporter` | Prometheus 3.14.0 ready; Grafana 13.2.0 with database `ok` |

The Portainer server and all four Edge Agent endpoints reported operational state. The dedicated [Portainer upgrade record](../../../Portainer/Documentation/Change%20Records/Portainer%202.45.0%20Upgrade%20-%202026-08-31.md) holds that platform's version and endpoint verification.

## Verification

- Check mode reached all 24 project paths and passed the running and health assertions.
- The live play completed with `unreachable=0` and `failed=0` on all six hosts.
- A foreground rerun on 2026-09-01 reported `changed=0` for all 24 projects and passed every running and health assertion again.
- Prometheus reported 49 active targets with all 49 `up` after UPS-01 left the target set.
- The NetBird HTTPS path returned `200` after both NetBird containers changed addresses.
- The Portainer API reported endpoint status 1 for `alpha-prod-01`, `docker-blue`, `docker-network`, and `media-01`.

I first tried to detach the idempotency rerun. Shell grouping created only a PID marker; no Ansible process or log existed. I removed that marker and ran the same command in the foreground, which produced the authoritative zero-change recap above.

## Remaining Work

The Grafana recreation did not close the inert WAL-setting backlog. The versioned Compose file no longer carries `GF_DATABASE_WAL`, but the live Compose file still does, so Grafana 13.2.0 inherited the variable again. Deploying the versioned file and recreating Grafana remains an explicit item in the [Prometheus backlog](../../../Prometheus/Documentation/TODO.md).

I created no snapshot or backup. The play retained each project's existing volumes and configuration, and the final idempotency run is the post-change recovery check. I retained no standalone command or API capture; the verification bullets above record the live results I observed.
