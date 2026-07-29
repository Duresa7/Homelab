# Fleet Maintenance Evidence

**Created:** 2026-07-28  
**Last updated:** 2026-07-29

This folder retains the Ansible and SSH readback logs for the fleet maintenance job that began on 2026-07-28 local time & finished on 2026-07-29. The associated [change record](../../Documentation/Change%20Records/Fleet%20Maintenance%20-%202026-07-28.md) maps each artifact to the step it proves.

| Artifact | What it demonstrates |
|---|---|
| [S01-preflight.log](Logs/S01-preflight.log) | The validator counted 11 OS hosts, 6 Compose hosts, & 22 projects. Both check-mode playbooks exited 0, and the Compose check exposed the local teamspeak-monitor pull warning. |
| [S02a-remote-guest-os-updates.log](Logs/S02a-remote-guest-os-updates.log) | The live update covered 10 remote Linux guests, excluded ansible-01 and kasm-01, & completed with no failed or unreachable host. |
| [S02b-controller-os-update.log](Logs/S02b-controller-os-update.log) | The separate ansible-01 update changed packages, required no reboot, & exited 0. |
| [S03-compose-updates.log](Logs/S03-compose-updates.log) | The live one-host-at-a-time Compose run completed 22 projects across 6 hosts; 9 projects changed & 13 were current. |
| [S03b-cadvisor-compose-updates.log](Logs/S03b-cadvisor-compose-updates.log) | All 8 pinned cAdvisor projects completed `pull` and `up -d`; the owning playbook then matched named cAdvisor containers to Docker's running count on every host. |
| [S04a-os-idempotency.log](Logs/S04a-os-idempotency.log) | The repeated OS play finished with zero failed or unreachable targets; 3 apt tasks still reported cache or cleanup changes. S07 contains the final empty package queues. |
| [S04b-compose-idempotency.log](Logs/S04b-compose-idempotency.log) | The repeated Compose play reported `changed=False` for all 22 projects. |
| [S04c-compose-health-guard.log](Logs/S04c-compose-health-guard.log) | The first project-state and container-health guard passed on all 6 managed Compose hosts. Later review replaced it because it could miss one exited service inside a partially running project. |
| [S04d-compose-final-review.log](Logs/S04d-compose-final-review.log) | The corrected full-service guard passed check mode and live mode across all 22 projects; the live pull applied one later media-stack image change. |
| [S04e-media-compose-idempotency.log](Logs/S04e-media-compose-idempotency.log) | The immediate media-01 follow-up reported `changed=False` for media-stack and its Edge Agent, with both full-service assertions passing. |
| [S05-system-and-container-health.log](Logs/S05-system-and-container-health.log) | The first readback found four degraded systemd states while Docker projects remained running without unhealthy or restarting containers. |
| [S06-systemd-cleanup.log](Logs/S06-systemd-cleanup.log) | The stale timers were reset, fwupd refresh succeeded, unsupported mcelog was disabled, & all 4 affected guests returned to `system_state=running`. |
| [S07-final-service-verification.log](Logs/S07-final-service-verification.log) | All apt simulations and the dnf update check were clean, all 11 guests had zero failed units, 48 of 48 Prometheus targets were up, & Wazuh, Splunk, SC4S, TeamSpeak, Grafana, Prometheus, and Coolify passed their named checks. |

All timestamps inside the logs are UTC. S05 and S06 retain complete results with summarized command labels; the exact ad hoc command strings were not retained. No command in this evidence set updates a Proxmox node or touches `kasm-01`.
