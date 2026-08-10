# Prometheus Remained Stopped After monitor-01 Restart

**Created:** 2026-08-10  
**Last updated:** 2026-08-10

**Issue date:** 2026-08-10  
**Affected system:** CT 104 `monitor-01`  
**Status:** Resolved

## Symptom

After I restarted `monitor-01`, Grafana and the exporters returned but `https://prometheus.alphasecunited.com` did not. The Prometheus container was `exited`, its local readiness endpoint returned HTTP `000`, and TCP 9090 was not listening.

## What I checked

Docker reported exit code `0`, `OOMKilled=false`, an empty error field, and a clean `SIGTERM` shutdown at 11:10:46 AM EDT when systemd stopped Docker. Its restart count remained zero and its start timestamp still pointed to August 7, proving Docker had not attempted a post-boot start.

The effective Compose service had `restart: unless-stopped` with no profile or deployment scale that could disable it. Docker's current boot journal showed the other monitoring containers joining their networks while Prometheus was absent. Grafana's persisted `HasBeenManuallyStopped` value was `false`; Prometheus held `HasBeenManuallyStopped=true`.

I found no systemd unit, timer, cron entry, or retained shell-history command that identified the caller that set the flag. The exact earlier GUI or Docker API action could not be reconstructed from the surviving logs.

## Root cause

Docker remembered Prometheus as intentionally stopped. The `unless-stopped` policy honored that persisted state and skipped the container when Docker started after the LXC reboot. Prometheus did not crash, run out of memory, or fail during an attempted start.

## Correction

I changed the deployed Prometheus Compose service from `restart: unless-stopped` to `restart: always`, applied the same policy to the existing container, and started it. The `always` policy makes Docker start Prometheus on a later daemon or LXC boot even if a prior stop had been recorded as manual.

Before editing, I copied the deployed Compose file. I checked the full copy for credentials, tokens, keys, WAN data, MAC addresses, serial numbers, and tunnel or relay identifiers and found none. The retained copy is [monitor-01-docker-compose-2026-08-10.yml](../../../../Backups/monitor-01-docker-compose-2026-08-10.yml). The host-side copy was removed after the repository commit captured it.

## Verification

The effective Compose policy and live container policy both read `always`. Docker reported the container `running` with `HasBeenManuallyStopped=false`. The local and public readiness paths both returned HTTP `200`.

After Prometheus completed its first scrape cycle, its target API reported 52 active targets and zero unhealthy targets. The blackbox query reported zero failed probes across all 20 service endpoints. This also closed the only failed endpoint found during the post-resize service audit.

I did not reboot CT 104 a second time solely to test this change. The persisted Compose definition and live Docker restart policy independently read `always`, and the running service passed local, public, target, and probe checks.

No standalone terminal transcript was retained. The values above are the direct post-change readbacks captured on 2026-08-10.

## What remains open

The action that originally set Docker's manual-stop flag is unknown because the retained logs do not identify the API caller. The restart-policy correction removes that flag's ability to keep Prometheus down after a future reboot.
