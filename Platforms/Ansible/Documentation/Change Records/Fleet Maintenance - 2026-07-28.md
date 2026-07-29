# Fleet Maintenance

**Created:** 2026-07-28  
**Last updated:** 2026-07-29

**Started:** 2026-07-28  
**Status:** Package, Compose, repair, & verification phases complete; 2 guest reboots pending

I ran the first live fleet maintenance job from `ansible-01`. The job updated OS packages on 11 running Linux guests, refreshed 22 fleet-managed Compose projects, reconciled 8 pinned cAdvisor projects through their owning automation, repaired four failed systemd states found during verification, & left two guests waiting for planned reboots.

## Scope

The OS scope was ansible-01, monitor-01, docker-network, docker-blue, splunk-siem, docker-main, app-01, edge-01, security-01, alpha-prod-01, & media-01. I excluded `kasm-01` as requested.

I did not run package updates on grey-server, purple-server, blue-server, or red-server. Those four Proxmox nodes were inventory sources only. Powered-off guests were also outside this job.

The main Compose scope covered 22 projects on docker-main, docker-network, docker-blue, media-01, alpha-prod-01, & monitor-01. A second pass used the monitoring-exporters inventory to pull and reconcile the pinned cAdvisor project on those 6 hosts plus app-01 & security-01. I left Coolify's generated projects on app-01 under Coolify control and excluded every Compose project on `kasm-01`.

## Starting state

The deployed inventory covered 9 OS targets, 5 Compose hosts, & 18 Compose projects. It omitted the running ansible-01 and monitor-01 guests from OS maintenance, plus syncthing, teamspeak-monitor, and monitor-01's monitoring and PeaNUT projects from Compose maintenance.

The normal OS play used full-fleet concurrency. That setting caused the first live package run to contend on grey-server's shared SATA SSD. The Compose play also applied `pull: always` to the locally built `teamspeak-monitor:local` image, which produced an authorization warning during check mode.

## Step 1: Validate the target set

I expanded the inventory to 11 OS targets, 6 Compose hosts, & 22 Compose projects. The validator returned `Validation passed: 11 OS-update hosts, 6 compose hosts, 22 projects.` Both playbooks completed check mode with exit code 0.

The Compose check exposed one warning: `Docker compose: image teamspeak-monitor:local: authorization failed`. I corrected that before the live Compose run by adding a per-project pull policy & setting teamspeak-monitor to `pull: never`.

Evidence: [S01 preflight](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S01-preflight.log)

## Step 2: Update OS packages

I ran the OS play against 10 remote guests, then updated ansible-01 through the playbook's local connection. Nine remote guests changed, monitor-01 was already current, & ansible-01 changed. Both runs finished with exit code 0 and no unreachable or failed host.

The first remote run continued after the calling SSH tool reached its five-minute timeout. I did not kill `apt`, `dpkg`, or Ansible. Read-only process and disk checks showed the package transaction was progressing under shared-storage contention, and the retained Ansible transcript ended with exit code 0.

Evidence: [remote guest updates](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S02a-remote-guest-os-updates.log) & [controller update](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S02b-controller-os-update.log)

## Step 3: Update Compose projects

I ran the Compose play one host at a time. Nine projects changed: forgejo, portainer, netbird, rustdesk, media-stack, teamspeak, teamspeak-02, teamspeak-03, & ts3-manager. The other 13 projects were already current.

The run finished with exit code 0 across all 6 hosts. teamspeak-monitor remained on its local image without a registry authorization warning.

I then used the separate monitoring-exporters project to run `docker compose pull` and `docker compose up -d` for all 8 cAdvisor projects. The image remained on the pinned `ghcr.io/google/cadvisor:v0.60.5` release. The owning playbook returned HTTP 200 from every exporter & matched cAdvisor's named-container count to Docker's running-container count on every host.

Evidence: [Compose updates](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S03-compose-updates.log) & [cAdvisor Compose updates](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S03b-cadvisor-compose-updates.log)

## Step 4: Repeat the maintenance checks

I changed the normal OS batch size from full-fleet concurrency to 2 guests. The existing automatic-reboot path remains limited to 1 guest, and this job kept the default report-only reboot policy.

The second OS pass finished with zero failed or unreachable hosts. Its apt task still reported `changed=True` on alpha-prod-01, app-01, & edge-01 because cache cleanup can change state. The later direct apt simulations proved that all 10 apt queues held zero upgrades, and Rocky Linux returned `dnf_check_update_rc=0`.

The second Compose pass reported `changed=False` for all 22 projects. A review found that the first health guard could pass a partial project when one service ran and another had exited. I replaced it with Compose's bounded `--wait` behavior and an assertion over the module's full `ps --all` result. The first final dry run hit one GHCR TLS handshake timeout, so I added three bounded pull attempts. The clean rerun passed check mode and live mode across all 22 projects. media-stack received one later image change during that final live pull; an immediate focused pass returned `changed=False` for both media-01 projects.

Evidence: [OS idempotency](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S04a-os-idempotency.log), [Compose idempotency](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S04b-compose-idempotency.log), [first Compose health guard](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S04c-compose-health-guard.log), [final Compose review](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S04d-compose-final-review.log), & [media-01 idempotency](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S04e-media-compose-idempotency.log)

## Step 5: Repair systemd state

The first post-update readback found four degraded guests. docker-network & monitor-01 retained a failed `wtmpdb-rotate.timer` after its unit vanished; security-01 had a failed `fwupd-refresh.service`; splunk-siem had a nonfunctional `mcelog.service` on AMD processor family 23.

I reset the two stale timer failures, reran the fwupd refresh successfully, & disabled the unsupported mcelog service. These were state repairs, not guest or Proxmox-node reboots.

Evidence: [initial health readback](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S05-system-and-container-health.log), [systemd cleanup](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S06-systemd-cleanup.log), & [systemd troubleshooting record](../Troubleshooting/Failed%20systemd%20units%20remained%20after%20package%20maintenance%20-%202026-07-28.md)

The S05 & S06 files retain complete results but summarized command labels. The exact ad hoc command strings were not retained, so I treat them as result records rather than exact command transcripts.

## Decisions

I left reboots in report-only mode. security-01 reports a pending reboot for `libc6`; splunk-siem has kernel `6.12.0-211.39.1.el10_2.x86_64` installed while `6.12.0-211.32.1.el10_2.x86_64` remains running.

I did not treat every visible Compose file as independently managed. Coolify owns app-01's generated source and proxy projects, so I verified its `ghcr.io/coollabsio/coolify:4.1.2` container instead of running a second reconciler over its files. GitHub's official latest-release endpoints listed [Coolify v4.1.2](https://github.com/coollabsio/coolify/releases/tag/v4.1.2) & [cAdvisor v0.60.5](https://github.com/google/cadvisor/releases/tag/v0.60.5) on 2026-07-29. I reconciled cAdvisor through its separate owner automation without changing that pinned version.

I kept teamspeak-monitor in the managed project list but disabled pulls for that one local image. Removing the project would also remove health verification; pulling it would keep sending a registry request for an image that exists only on alpha-prod-01.

## Resulting configuration

The fleet update project now defines 11 OS targets, 6 Compose hosts, & 22 Compose projects. Normal OS maintenance runs 2 guests at a time. The local ansible-01 entry has a hostname guard. Compose maintenance runs one host at a time, accepts a per-project pull policy, retries transient registry failures up to 3 times, waits up to 180 seconds for each project, & checks the complete service list for stopped or unhealthy containers.

The deployed project on ansible-01 passed its validator and both Ansible syntax checks after these changes. A pre-maintenance backup remains under `/home/ansible/fleet-update-backups/2026-07-28-pre-maintenance/`.

## Verification

Direct package simulation returned `0 upgraded, 0 newly installed, 0 to remove and 0 not upgraded` on all 10 apt guests. Rocky Linux returned `dnf_check_update_rc=0`.

All 11 guests returned `system_state=running` with `failed_units=0`. Wazuh manager, indexer, & dashboard were active at package version `4.14.6-1`; its dashboard returned HTTP 302 & API returned the expected unauthenticated HTTP 401. Splunkd and SC4S were active; Splunk returned HTTPS 303 & the SC4S container reported healthy.

Prometheus reported 48 of 48 targets up. Prometheus and Grafana each returned HTTP 200. The TeamSpeak public, local, DNS SRV, & query checks each returned 3 series with a minimum value of 1.0. Coolify 4.1.2 remained running and healthy.

Evidence: [final service verification](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S07-final-service-verification.log)

## Rollback points

The controller backup can restore the pre-maintenance inventory, playbooks, validator, README, & Semaphore template. The serial and pull-policy edits can also be reverted independently because they do not alter target data.

The OS and image updates changed installed packages and container images. Their rollback depends on each package repository or service-specific backup; I did not force a package downgrade or image rollback because the post-change service checks passed.

I can re-enable mcelog with `systemctl enable mcelog.service`, but it failed on this guest's AMD processor before this maintenance. The two vanished timer units cannot be restarted because the package update removed their unit files; resetting their failed state was the correct cleanup.

## Remaining work

security-01 and splunk-siem still need controlled reboots. I left both online because the job used report-only reboot policy. After each reboot, I need to verify Wazuh or Splunk and SC4S, confirm zero failed units, & confirm that the pending reboot or old-kernel condition cleared.

The storage contention, local-image warning, & registry timeout are recorded separately in [Shared SSD contention slowed the fleet package run](../Troubleshooting/Shared%20SSD%20contention%20slowed%20the%20fleet%20package%20run%20-%202026-07-28.md), [Local Compose image triggered a registry pull warning](../Troubleshooting/Local%20Compose%20image%20triggered%20a%20registry%20pull%20warning%20-%202026-07-28.md), & [Transient registry timeout interrupted the Compose dry run](../Troubleshooting/Transient%20registry%20timeout%20interrupted%20the%20Compose%20dry%20run%20-%202026-07-29.md).
