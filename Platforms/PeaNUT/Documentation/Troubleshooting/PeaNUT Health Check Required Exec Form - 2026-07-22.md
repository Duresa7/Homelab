# PeaNUT Health Check Required Exec Form

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

## Symptom

PeaNUT served its web interface, but Docker marked the container unhealthy and the deployment verification timed out after 90 seconds.

## Exact Error

`OCI runtime exec failed: exec failed: unable to start container process: exec: "/bin/sh": stat /bin/sh: no such file or directory`

## Failed Attempts

The first Compose health check used `CMD-SHELL` to run a Node request against `/api/ping`. The web process was running, but every probe failed before Node started. The [initial deployment transcript](../../Evidence/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22/Logs/S05-Dashboard-Deploy.txt) records the exact Compose command, image pull, container start, 90-second timeout, and exit code 124.

## Hypotheses

I suspected the image was shell-free because its entrypoint was `node entrypoint.mjs` and the runtime couldn't find `/bin/sh`.

## Tests

Docker's health history repeated the missing-shell error. A host-side request to `http://192.168.40.35:8090/api/ping` returned HTTP 200, which separated application health from probe execution.

## Root Cause

Compose implements `CMD-SHELL` through `/bin/sh`. PeaNUT 6.0.0's image doesn't contain that shell.

## Corrective Action

I changed the health check to exec-form `CMD` with `node`, `-e`, and the probe script as separate arguments. I also rotated the authentication secret that the first startup printed and stored the replacement in 1Password before recreating the container.

## Verification

Docker reported `state=running health=healthy`. `/api/ping` returned `pong`, and the authenticated [dashboard capture](../../Evidence/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22/Screenshots/S06-PeaNUT-Dashboard-After.png) showed both UPS devices online.
