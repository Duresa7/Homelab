# Coolify Traefik 3.7 Minor Update

**Created:** 2026-08-09  
**Last updated:** 2026-08-09

## Scope

I updated the Coolify-managed proxy on app-01 from Traefik 3.6.25 to 3.7.10. I changed the proxy's Compose image from `traefik:v3.6` to `traefik:v3.7`, recreated only `coolify-proxy`, refreshed Coolify's detected-version state, & left Coolify 4.1.2 and the other five Coolify containers unchanged.

## Version decision

The Coolify notification identified 3.7.8 as the newest 3.7 patch when it ran. The mutable `traefik:v3.7` tag resolved to 3.7.10 when I pulled it on 2026-08-09. [Traefik 3.7.10](https://github.com/traefik/traefik/releases/tag/v3.7.10) fixes three published advisories and an authentication singleflight-key collision, so I used the current 3.7 patch rather than deliberately installing the stale notification target.

I reviewed the [Traefik v3 migration notes](https://doc.traefik.io/traefik/migrate/v3/) from 3.6.25 through 3.7.10. The required v3.7 configuration work applies to Kubernetes providers. This proxy still enables only the Docker & file providers. It had zero Kubernetes provider arguments, zero running HTTP router-rule labels, & zero bare ``Host(`*`)`` rules affected by the 3.7.7 matcher change. The explicit HTTP/1 CONNECT rejection in 3.7.9 makes an already nonfunctional request method return 501. The 3.7.10 migration items affect the unused Kubernetes Gateway API provider.

## Starting state

Traefik 3.6.25 ran healthy from image ID `sha256:31267173a15b4944e797a76ffd9c419707c8d8b32fe5b610f80cd0cfa05f372d`. All six Coolify containers were healthy, the control panel returned HTTP 302, the unmatched proxy route returned HTTP 404, & Docker exposed API 1.55. The proxy Compose file contained one `traefik:v3.6` image reference and had SHA-256 `5787cd1472ae5aea089b5118f5eb3ac8d48949c81e5e5a595c27613423421d9e`. [The starting-state transcript](../../Evidence/Coolify%20Traefik%203.7%20Minor%20Update%20-%202026-08-09/Logs/S00-Starting-State-2026-08-09.txt) retains the successful preflight command & output.

Two earlier read-only probes did not reach their full check list. The first exited 1 because its image-line expression did not allow the quotes around `traefik:v3.6`. The second exited 3 after BusyBox `find` rejected `-printf` and jq reported `syntax error, unexpected INVALID_CHARACTER` for an over-escaped wildcard-rule expression. Neither command changed the proxy or its configuration. I did not retain those preliminary probe transcripts; the corrected preflight captures every intended check.

## Candidate test

I tagged the running image as `traefik:rollback-v3.6.25-2026-08-09`, pulled `traefik:v3.7`, & received digest `sha256:9c3b91d5fb7770853ca5c1124a23c34bf2d9b47ffaebeab2614cbaf410dcb2ac`. An isolated container with networking disabled reported Traefik 3.7.10, Go 1.26.5, linux/amd64. A temporary copy of the production Compose file with only the image line changed to `traefik:v3.7` passed `docker compose config -q`. The running 3.6.25 proxy stayed healthy throughout the test. [The candidate transcript](../../Evidence/Coolify%20Traefik%203.7%20Minor%20Update%20-%202026-08-09/Logs/S01-Candidate-Test-2026-08-09.txt) retains the pull, version, configuration validation, & unchanged production state.

## Proxy update

I generated a candidate Compose file beside the production file, required exactly one old image reference and one new image reference, validated the candidate, & moved it atomically over the production file. Its new SHA-256 is `09e4e66796084887f110f1687c6b009647e9cf091f0752ded26f336e885d1c06`.

I recreated only the `traefik` service in the `coolify-proxy` Compose project with `--no-deps`, `--force-recreate`, & `--pull never`. The command therefore used the candidate image that had already passed the isolated test. The proxy reached healthy state in 7 seconds, reported 3.7.10, & logged zero error, fatal, or panic entries. All six Coolify containers remained healthy, the control panel returned HTTP 302, & the unmatched proxy route returned HTTP 404. The update command included automatic configuration and container rollback paths for a Compose failure or failed health check, but neither path ran. [The update transcript](../../Evidence/Coolify%20Traefik%203.7%20Minor%20Update%20-%202026-08-09/Logs/S02-Proxy-Update-2026-08-09.txt) retains the edit, recreation, health wait, & immediate checks.

## Coolify state refresh

Because I performed the bounded proxy recreation through Docker, I ran Coolify's `traefik:check-version` command after the proxy was healthy. The queued check stored `detected_traefik_version` as `3.7.10` and cleared `traefik_outdated_info`, which removes the stale upgrade warning. [The Coolify-state transcript](../../Evidence/Coolify%20Traefik%203.7%20Minor%20Update%20-%202026-08-09/Logs/S03-Coolify-State-Refresh-2026-08-09.txt) retains the command and database-backed state.

## Final verification

At 9:42 AM EDT, the proxy still reported 3.7.10, `running|healthy`, the tested image ID, & the `traefik:v3.7` image reference. The Compose checksum matched the post-edit value and no temporary configuration files remained. All six Coolify containers were healthy, no core container was unhealthy or restarting, the control panel returned HTTP 302, the local unmatched route returned HTTP 404, & the proxy had logged zero errors since the update. From edge-01, an unmatched Host request across the VLAN path also returned HTTP 404. [The final-verification transcript](../../Evidence/Coolify%20Traefik%203.7%20Minor%20Update%20-%202026-08-09/Logs/S04-Final-Verification-2026-08-09.txt) retains both host checks.

## Resulting configuration

| Item | Result |
|---|---|
| Coolify | 4.1.2, unchanged |
| Proxy image tag | `traefik:v3.7` |
| Traefik runtime | 3.7.10 |
| Running image ID | `sha256:9c3b91d5fb7770853ca5c1124a23c34bf2d9b47ffaebeab2614cbaf410dcb2ac` |
| Rollback image | `traefik:rollback-v3.6.25-2026-08-09` |
| Compose project / service | `coolify-proxy` / `traefik`, unchanged |
| Providers | Docker & file, unchanged |
| Coolify outdated state | Cleared |

This changed one workload version without adding, moving, or resizing a guest. I updated the living [Galaxy Services inventory](../../../../Operations/Inventory/Galaxy/Services.md) and did not create a dated topology snapshot.

## Rollback

The 3.6.25 image remains on app-01 under the dated rollback tag, and `traefik:v3.6` still references it. To revert, I can change the one Compose image reference back to `traefik:v3.6`, validate the file, & rerun the same single-service recreation with `--pull never`. I would then repeat the six-container, control-panel, local proxy, edge-to-proxy, log, & Coolify detected-version checks.

## Remaining work

None. I left the dated 3.6.25 rollback image in place for the next proxy maintenance window; no running container references it.
