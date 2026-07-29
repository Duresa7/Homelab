# Local Compose image triggered a registry pull warning

**Created:** 2026-07-28  
**Last updated:** 2026-07-29

**Investigated:** 2026-07-28 to 2026-07-29

## Symptom

The Compose check returned `[WARNING]: Docker compose: image teamspeak-monitor:local: authorization failed` for alpha-prod-01. The project itself stayed up & the Ansible item returned `changed=False`.

## Failed attempt

The first inventory used the playbook-wide `pull: always` policy for every project. That policy sent a registry request for `teamspeak-monitor:local`, even though the image is built and stored only on alpha-prod-01.

## Hypothesis and test

The `:local` image tag and the authorization warning pointed to a registry pull, not a failed container start. The same check showed the teamspeak-monitor project remained present and unchanged.

I kept the project in the managed list so the playbook would still verify its running state. I changed only its image-pull behavior.

## Root cause

The playbook had no project-level pull override. `pull: always` was correct for registry-backed images but wrong for one image with no registry source.

## Corrective action

I added an optional pull value to each project definition & set teamspeak-monitor to `pull: never`. Every project without an override still uses `pull: always`.

## Verification

The live Compose run completed all 22 projects with exit code 0 and no teamspeak-monitor authorization warning. Its follow-up pass reported `changed=False` for all 22 projects, and the health-guard pass found no unhealthy or restarting container on the 6 managed hosts.

Prometheus later returned 3 TeamSpeak series for each public, local, DNS SRV, & query check; every minimum was 1.0.

Evidence: [preflight warning](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S01-preflight.log), [live Compose update](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S03-compose-updates.log), [Compose idempotency](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S04b-compose-idempotency.log), & [final TeamSpeak checks](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S07-final-service-verification.log)
