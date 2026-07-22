# Syncthing Container Restarted After Capability Drop

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Date:** 2026-07-22  
**Affected system:** `docker-main`  
**Status:** Resolved

## Symptom

The first `syncthing/syncthing:2.1.2` container entered a restart loop before it opened TCP 8384 or 22000. Docker reported restart count 7 and health `unhealthy`.

## Cause

The Compose file dropped every Linux capability. The image entrypoint changes ownership under `/var/syncthing` and then switches to UID/GID 1000. Without the required capability set, each attempt logged `chown: /var/syncthing: Operation not permitted` followed by `su-exec: setgroups(1000): Operation not permitted`.

Syncthing never started, so the failed container didn't scan or modify the vault directory.

## Failed Attempt

I first deployed the container with `cap_drop: ALL`. It reached restart count 7 and never opened its GUI or synchronization listeners. I didn't retain the exact terminal transcript from this failed attempt; the two error lines above came from the live container logs I inspected during the failure.

## Hypothesis

I expected the entrypoint to succeed if it retained the image's default capability set because the failure occurred during its ownership change & group setup, before Syncthing started.

## Test

I removed only `cap_drop: ALL`, kept `security_opt: no-new-privileges:true`, & recreated the same 2.1.2 image. The service then opened its listeners and reached `healthy` with restart count 0, which supported the capability hypothesis.

## Resolution

I removed `cap_drop: ALL`, retained `security_opt: no-new-privileges:true`, & recreated the container from the same 2.1.2 image. I did not grant privileged mode or add host devices.

## Verification

- The recreated container reported `running` & `healthy` with restart count 0.
- TCP 22000, UDP 22000, & UDP 21027 opened for synchronization and discovery.
- The GUI bound only to `127.0.0.1:8384`.
- The no-auth health endpoint returned `{"status":"OK"}`.
- A later Compose restart returned healthy and restored the direct Windows peer connection.

The [deployment verification summary](../../Evidence/Syncthing%20Deployment%20-%202026-07-22/Logs/Syncthing-Deployment-Verification-2026-07-22.txt) includes a fresh exact command transcript for the resolved container state. It doesn't reconstruct the missing failure transcript.
