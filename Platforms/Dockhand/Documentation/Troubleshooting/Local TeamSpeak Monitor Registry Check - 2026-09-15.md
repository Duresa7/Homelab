# Local TeamSpeak Monitor Registry Check

**Created:** 2026-09-15  
**Last updated:** 2026-09-15

**Status:** Fixed and verified.

## Symptom and reproduction

I clicked Check for updates in Dockhand and received `Could not query registry` for `teamspeak-monitor` on `alpha-prod-01`. I reproduced it twice through authenticated `POST /api/containers/check-updates?env=6`, with `Accept: application/json`. The other eight containers returned no registry errors. This check does not pull images or restart containers.

The monitor row returned image `teamspeak-monitor:local`, `hasUpdate: false`, `updateDisabled: false`, and the exact error above. I retained a local reproduction script at `.scratch/dockhand/check-teamspeak-update.py`; it exits 1 while that error remains and will exit 0 when the container is explicitly excluded and returns no error.

## Cause

The live Compose file at `/home/dkadi/teamspeak-monitor/docker-compose.yml` declares `build: .` and `image: teamspeak-monitor:local`. This is my own collector, built from the [versioned source](../../../Teamspeak%20Hosting/Source/teamspeak-monitor/), not a published registry image. Docker reports a nonempty `RepoDigests` entry, `teamspeak-monitor@sha256:c66a4ccad13865da18765ff45ceff1def9fb92ee48b4f9e187afa9e3c80ce8e3`.

In the inspected Dockhand source, `checkImageUpdateAvailable` treats a nonempty repository digest as a reason to query the registry. That lookup fails for the local image and produces the reported message. I considered a wrong repository reference and registry authentication failure; the live build declaration and local source establish why this image has no upstream update target. The monitor container itself is running.

## Change

I added the supported `dockhand.update: "false"` container label to the repository's Compose definition. Dockhand checks this label before attempting the registry query. The [upstream label documentation](https://dockhand.pro/manual/#container-labels) also states that it disables update checks and automatic or batch updates for that container. Updating this collector remains a source rebuild operation.

I validated the same proposed change in a temporary Compose file beside the live definition: `docker compose config --quiet` returned exit code 0. I removed that temporary file. After approval I applied the same change to the live file and recreated only `teamspeak-monitor` using the existing image. No full remote command transcript is retained; the validation result and the two API reproduction results are summarized here.

Applying a Docker label requires recreating the container. I ran the following command from `/home/dkadi/teamspeak-monitor`: `docker compose up -d --no-deps --no-build --pull never teamspeak-monitor` after applying the label. This uses the existing image and affects only the monitoring collector. I requested approval because monitoring pauses during recreation, under the workspace's disruptive-change rule.

## Verification

The original reproduction now exits 0: `updateDisabled: true`, no registry error. The recreated monitor uses the same image ID and is running. Its metrics file was written after the restart and was 29.7 seconds old at verification. Both TeamSpeak voice containers retain their pre-change IDs and start timestamps. Compose validation and the recreate command both returned exit code 0. No voice container was restarted.
