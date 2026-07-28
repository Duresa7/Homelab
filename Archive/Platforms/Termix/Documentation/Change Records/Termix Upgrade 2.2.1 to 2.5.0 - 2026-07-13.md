# Termix Upgrade 2.2.1 to 2.5.0

**Created:** 2026-07-13  
**Last updated:** 2026-07-20

**Date:** 2026-07-13  
**Target:** `docker-main`, Compose project `/opt/docker/termix`  
**Status:** Complete

## Scope

I upgraded the existing Termix Compose project from package version 2.2.1 to 2.5.0 to correct the password-reset logger that generated but did not display the reset code. I retained the existing Compose definition and named data volume.

## Starting State

- `termix` and `guacd` were running and healthy.
- Termix reported package version 2.2.1.
- The local mutable `latest` image used repository digest `sha256:577c0e7024fa7767ffbd00e19a1e0ce28fb0027aab37c3f7d49e2c18bc001210`.
- Persistent data was mounted from named volume `termix_termix-data` at `/app/data`.
- The compiled 2.2.1 reset route omitted the reset value from its logger template.

## Upgrade Choices

- I deliberately took no backup. I accepted the risk of a multi-version application/database migration without a new recovery copy.
- I chose the simple full-project sequence `docker compose pull`, `docker compose down`, and `docker compose up -d`, so both Termix and its `guacd` companion cycled together.
- I verified the corrected reset logger statically without initiating a reset.
- I did not edit or pin the Compose file during this bounded change; it continues to reference `ghcr.io/lukegus/termix:latest`.

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

## Rollback

The previous image ID `sha256:7c98e47c2fbb6becb786914a76e1ba6c90a5402346cbdf5a0170360fd8e5f3c0` remained available locally after the upgrade. Because I declined a backup and Termix may have migrated its persistent database, an application downgrade is not guaranteed safe and I did not attempt it. Any rollback should first inspect 2.5.0 migration compatibility and current data state.

## Remaining Work

Run one password-reset test to confirm the 2.5.0 logger returns the newly generated code. The pre-upgrade code expired with the former process.
