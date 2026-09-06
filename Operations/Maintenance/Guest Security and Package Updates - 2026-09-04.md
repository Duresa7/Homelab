# Guest Security and Package Updates

**Created:** 2026-09-04  
**Last updated:** 2026-09-04

**Implementation date:** 2026-09-04  
**Status:** Complete  
**Affected systems:** `alpha-prod-01`, `ansible-01`, `app-01`, `docker-blue`, `docker-main`, `docker-network`, `edge-01`, `game-01`, `media-01`, `monitor-01`, `splunk-siem`

## Outcome

I updated the eleven guests named by the security-update alert through the deployed [fleet update workflow](../../Platforms/Ansible/Source/fleet-updates/README.md). The opening alert reported 105 security updates across the eleven guests. The playbook applied every eligible safe APT upgrade on the ten Debian-family guests and every eligible DNF upgrade on `splunk-siem`.

The ten-host run and the isolated `docker-blue` run both exited 0. No host was unreachable and no Ansible task failed. I left the guests online during the package run, then rebooted `splunk-siem` in a separate approved maintenance step later that day.

| Guest | Security updates reported before the run | Reboot required after the run |
|---|---:|---|
| `alpha-prod-01` | 4 | No |
| `ansible-01` | 2 | No |
| `app-01` | 1 | No |
| `docker-blue` | 1 | No |
| `docker-main` | 16 | No |
| `docker-network` | 1 | No |
| `edge-01` | 23 | No |
| `game-01` | 16 | No |
| `media-01` | 1 | No |
| `monitor-01` | 1 | No |
| `splunk-siem` | 39 | Yes |

## What changed

I ran `os-update.yml` from `ansible-01` against ten guests with the normal two-host serial limit. I then ran `docker-blue` by itself because it carries SSH Manager and Executor, the control path used for the work. The playbook refreshed package metadata, upgraded packages, removed unused dependencies, cleaned package caches, and reported reboot state without rebooting a host.

`splunk-siem` installed kernel `6.12.0-211.50.1.el10_2.x86_64`. Its later reboot changed the boot ID from `91d21426-c874-4660-9431-77ff03d17096` to `02213b64-bfdd-42c2-90da-73eb1a82098e` and loaded that kernel.

## Control-path interruption

The Executor endpoint briefly stopped answering while `docker-network` was in its package transaction. The Ansible process continued on `ansible-01` and its final recap covered all ten intended guests with no failure.

Updating `docker-blue` restarted its Docker workloads and temporarily removed `ssh_execute` from the gateway's cached tool catalog. I waited for the existing package run to finish instead of starting it again. After the gateway returned, the isolated run reported exit 0, `changed=1`, `unreachable=0`, and `failed=0`.

## Verification

- The package-update metrics reported zero pending security updates on all eleven guests. `dnf_security_upgrades_pending` was 0 on `splunk-siem`.
- `dpkg --audit` returned no incomplete package state on the ten Debian-family guests. Their reboot metrics were 0.
- `app-01` and `edge-01` each list a newer Wazuh agent from the Wazuh repository. The package is deliberately held on both guests, so APT did not omit a Debian security update.
- `Splunkd` and `sc4s` were active. DNF's security check returned 0, and the reboot metric was 1 because the running and newest installed kernels differ.
- Docker was active on every Docker host. Every container present in the pre-update baseline remained present and running afterward, and every configured container health check reported healthy. SSH Manager and Executor were healthy again on `docker-blue`.
- Semaphore was active on `ansible-01`; Caddy and Cloudflared were active on `edge-01`; and Docker, Wings, and the Minecraft Playit relay were active on `game-01`.
- The seven pre-existing `openipmi.service` failures remained the only failed units on those guests. No new failed unit appeared. The failed Prometheus node exporter unit seen on `docker-main` before the run was clear afterward.
- Ten SSH Manager health checks returned healthy. `docker-main` returned warning only because `/data` was 83 percent full; its CPU, memory, root filesystem, Docker service, and containers were healthy.
- After the approved `splunk-siem` reboot, the running kernel matched the newest installed kernel, systemd returned `running` with zero failed units, and `Splunkd`, `sc4s`, and `node_exporter` were active. Splunk Web returned HTTPS 303, HEC health returned HTTPS 200, management port 8089 listened, and the SC4S container reported healthy.
- SC4S's first Podman health check ran before its control socket was ready and briefly left one failed transient unit. The scheduled 120-second retry returned healthy and cleared the unit, matching the known [SC4S startup behavior](../../Platforms/Ansible/Documentation/Troubleshooting/SC4S%20startup%20health%20check%20briefly%20degraded%20systemd%20-%202026-07-29.md).

I retained no snapshot, backup, transcript, or standalone evidence folder. The results above came from the live Ansible recaps, package-manager checks, update metrics, service checks, container state, and SSH Manager health checks during the maintenance window.

## Open state

The controlled `splunk-siem` reboot is complete, and no update or repair remains from this run.
