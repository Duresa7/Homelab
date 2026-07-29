# Transient registry timeout interrupted the Compose dry run

**Created:** 2026-07-29  
**Last updated:** 2026-07-29

**Investigated:** 2026-07-29

## Symptom

The first final Compose dry run stopped on alpha-prod-01 while checking `ghcr.io/playit-cloud/playit-agent:0.17`. Docker returned `net/http: TLS handshake timeout`. The running playit-agent container stayed up.

## Failed attempt

The playbook made one registry request per project and failed the item after one network timeout. That behavior was too brittle for a fleet run even though it correctly surfaced the failed pull.

## Hypothesis and test

The error came from the GHCR HTTPS handshake, not Compose parsing, authentication, or a stopped container. A later request for the same image completed, and the full project assertion passed.

## Root cause

The retained output proves a transient registry handshake timeout. It does not identify whether the delay occurred at GHCR, the WAN path, or the guest. I did not assign a narrower cause without evidence.

## Corrective action

I added three bounded attempts with a 10-second delay around each Compose project update. The play still fails after the third unsuccessful attempt.

## Verification

The repeated whole-fleet dry run & live run completed with zero failed or unreachable hosts. The corrected guard checked all 22 project service lists. media-stack received one later image change during the live pull, then its immediate follow-up returned `changed=False`.

The failed attempt did not receive a retained transcript before the clean rerun replaced that job log. The exact error above comes from the observed Ansible result. The retained clean result is [S04d-compose-final-review.log](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S04d-compose-final-review.log), followed by [S04e-media-compose-idempotency.log](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S04e-media-compose-idempotency.log).
