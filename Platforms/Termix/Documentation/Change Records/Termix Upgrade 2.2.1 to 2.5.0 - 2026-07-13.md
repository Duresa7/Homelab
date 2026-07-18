# Termix Upgrade 2.2.1 to 2.5.0

**Created:** 2026-07-13  
**Last updated:** 2026-07-13

**Date:** 2026-07-13  
**Target:** `docker-main`, Compose project `/opt/docker/termix`  
**Status:** Completed

## Scope

Upgrade the existing Termix Compose project from package version 2.2.1 to 2.5.0 to correct the password-reset logger that generated but did not display the reset code. Retain the existing Compose definition and named data volume.

## Starting State

- `termix` and `guacd` were running and healthy.
- Termix reported package version 2.2.1.
- The local mutable `latest` image used repository digest `sha256:577c0e7024fa7767ffbd00e19a1e0ce28fb0027aab37c3f7d49e2c18bc001210`.
- Persistent data was mounted from named volume `termix_termix-data` at `/app/data`.
- The compiled 2.2.1 reset route omitted the reset value from its logger template.

## Decisions

- The operator explicitly directed that no backup be taken. This accepted the risk of performing a multi-version application/database migration without a new recovery copy.
- The operator requested the simple full-project sequence `docker compose pull`, `docker compose down`, and `docker compose up -d`, so both Termix and its `guacd` companion were cycled together.
- No password reset was initiated during verification. The corrected code path was verified statically in the deployed artifact, and the operator retains control of when to generate a fresh recovery code.
- The Compose file was not edited or pinned during this bounded change; it continues to reference `ghcr.io/lukegus/termix:latest`.

## Actions and Results

1. Verified the project contained `guacd` and `termix`, Termix 2.2.1 was healthy, and the named data volume was mounted read-write.
2. Ran `docker compose pull`. Both image pulls completed with exit code zero.
3. Ran `docker compose down`. Both containers and the project network were removed cleanly; the named data volume was not removed.
4. Ran `docker compose up -d`. The network and both containers were recreated and started with exit code zero.
5. Waited for configured health checks and performed application, image, HTTP, log, and inter-container checks.

## Resulting State

| Item | Result |
|---|---|
| Termix package | 2.5.0 |
| Termix repository digest | `sha256:4d3371311087d6757aa9d1c94117e854d749b1c5e8fd07bd36e7a99e0686d26c` |
| Termix health | `healthy`, restart count 0 |
| Termix HTTP | Port 8080 returned `200` |
| Startup error scan | 0 matching errors |
| Password-reset logger artifact | `${resetCode}` variable present |
| `guacd` health | `healthy`, first scheduled probe exit 0, restart count 0 |
| Termix-to-`guacd` path | TCP 4822 connected |
| Persistent volume | Existing `termix_termix-data` retained |

## Verification Notes

The first combined verification reached its two-minute limit while `guacd` still reported `starting`. This was not a service failure: its configured health interval is five minutes and no health probe had run. The equivalent `nc -z 127.0.0.1 4822` check passed immediately, the daemon log reported that it was listening, and Termix connected to TCP 4822.

The first Termix-to-`guacd` Node probe printed `connected` but exited 2 because its timeout was not cleared after a successful connection. The corrected probe cleared the timeout and exited 0. Docker's first scheduled `guacd` probe then exited 0 at 23:46:21 UTC and set the container to `healthy`.

No reset code, password, token, encryption key, environment value, or decrypted database content was printed or retained.

## Rollback

The previous image ID `sha256:7c98e47c2fbb6becb786914a76e1ba6c90a5402346cbdf5a0170360fd8e5f3c0` remained available locally after the upgrade. However, because the operator declined a backup and Termix may have migrated its persistent database, an application downgrade is not guaranteed safe and was not attempted. Any rollback should first inspect 2.5.0 migration compatibility and current data state.

## Remaining Work

The operator must initiate a fresh password reset when ready and retrieve the newly logged code directly from the live Termix logs. The pre-upgrade code was invalidated by the full Compose restart.

## Step Evidence

| Step | Evidence | Verification |
|---|---|---|
| S01 | [Runtime and image inspection](../../Evidence/Password%20Reset%20Code%20Missing%20-%202026-07-13/Logs/S01-Runtime-And-Image-Inspection-2026-07-13.md) | Confirmed healthy Termix 2.2.1 and stale image digest |
| S02 | [Reset path inspection](../../Evidence/Password%20Reset%20Code%20Missing%20-%202026-07-13/Logs/S02-Reset-Path-Inspection-2026-07-13.md) | Confirmed defective logger template |
| S03 | [Feedback-loop verification](../../Evidence/Password%20Reset%20Code%20Missing%20-%202026-07-13/Logs/S03-Feedback-Loop-Verification-2026-07-13.md) | Repeated the assertion twice against the observed missing-code event |
| S04 | [Compose upgrade](../../Evidence/Password%20Reset%20Code%20Missing%20-%202026-07-13/Logs/S04-Compose-Upgrade-2026-07-13.md) | Pull, down, and up each exited zero |
| S05 | [Post-upgrade verification](../../Evidence/Password%20Reset%20Code%20Missing%20-%202026-07-13/Logs/S05-Post-Upgrade-Verification-2026-07-13.md) | Both containers healthy; Termix 2.5.0; HTTP 200; corrected logger deployed |
