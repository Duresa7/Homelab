# Coolify Traefik 3.6 Patch Update

**Created:** 2026-08-02  
**Last updated:** 2026-08-02

## Scope

I updated the Coolify-managed proxy on app-01 from Traefik 3.6.11 to 3.6.25. I kept the existing 3.6 minor line, the `traefik:v3.6` image tag, the Compose project, & every proxy setting unchanged.

## Starting state

Coolify 4.1.2 reported that localhost ran Traefik 3.6.11 while 3.6.23 was available. The `coolify-proxy` container used image ID `sha256:acfc80650104f0194a15f73dc1648f517561bc1645391a15705332a064cfc33c` & reported `running|healthy`. All six Coolify containers were healthy, the control panel returned HTTP 302 on port 8000, & Traefik returned its expected HTTP 404 for an unmatched request on port 80. [The starting-state transcript](../../Evidence/Coolify%20Traefik%203.6%20Patch%20Update%20-%202026-08-02/Logs/S00-Starting-State-2026-08-02.txt) retains the command & output.

The proxy uses the Docker & file providers. It doesn't use a Kubernetes provider. Docker exposed API 1.55, above the API 1.40 minimum introduced in Traefik 3.6.16.

## Version decision

I didn't move to Traefik 3.7. The alert called for a patch update, & the [Traefik 3.6.23 release](https://github.com/traefik/traefik/releases/tag/v3.6.23) fixed two published security advisories without requiring a minor-version migration.

The mutable `traefik:v3.6` tag resolved to [3.6.25](https://github.com/traefik/traefik/releases/tag/v3.6.25) when I pulled it on 2026-08-02. I reviewed the [Traefik v3 migration notes](https://doc.traefik.io/traefik/migrate/v3/) from 3.6.11 through 3.6.25. The Docker API floor is satisfied. The BasicAuth, ForwardAuth, StripPrefix, & StripPrefixRegex settings called out by the intervening notes had zero references in this proxy configuration, & `underscoreHeadersStrategy` keeps its prior behavior by default. Traefik 3.6.24 returns an explicit HTTP 501 for CONNECT requests that were already nonfunctional; 3.6.25 changes generated Kubernetes Gateway API names, which doesn't apply to this Docker & file-provider proxy.

I tested the candidate binary with networking disabled & validated the current Compose file before I recreated the production proxy. This was a binary & configuration smoke test, not a parallel traffic test. The running containers had zero application router labels, so there wasn't a routed application to duplicate on alternate ports.

## Step 1: Preserve 3.6.11 & test 3.6.25

I tagged the running image as `traefik:rollback-v3.6.11-2026-08-02` before pulling anything. The pull changed `traefik:v3.6` to digest `sha256:31267173a15b4944e797a76ffd9c419707c8d8b32fe5b610f80cd0cfa05f372d`, & an isolated `docker run --rm --network none` reported Traefik 3.6.25, Go 1.26.5, linux/amd64.

The running container stayed on 3.6.11 & remained healthy during this test. [The candidate transcript](../../Evidence/Coolify%20Traefik%203.6%20Patch%20Update%20-%202026-08-02/Logs/S01-Preflight-and-Candidate-2026-08-02.txt) retains the command, pull result, candidate version, & rollback image ID.

The separate [Compose-validation transcript](../../Evidence/Coolify%20Traefik%203.6%20Patch%20Update%20-%202026-08-02/Logs/S01B-Compose-Validation-2026-08-02.txt) records Docker Compose 5.3.1 accepting the current file. That preflight command exited 1 only after validation, when its optional routed-host probe found no application router label.

## Step 2: Recreate only the proxy

The SSH account can control Docker but can't traverse `/data/coolify`, which is mode 0700 & owned by Coolify's UID 9999. I mounted `/data/coolify/proxy` read-only at the same absolute path inside an ephemeral `docker:cli` container, validated the Compose file, & addressed the existing `coolify-proxy` project by its explicit project & service names.

I ran `docker compose -p coolify-proxy up -d --no-deps --force-recreate --pull never traefik` through that container. `--pull never` forced Compose to use the 3.6.25 image I had already tested. The command recreated only `coolify-proxy`, which reached healthy state 7 seconds after the command started. [The recreation transcript](../../Evidence/Coolify%20Traefik%203.6%20Patch%20Update%20-%202026-08-02/Logs/S02-Proxy-Recreation-2026-08-02.txt) records the old & new image IDs & immediate checks.

## Step 3: Verify the ingress path

At 2026-08-02T09:00:37Z, `coolify-proxy` reported Traefik 3.6.25, `running|healthy`, & the new image ID. All six Coolify containers were healthy, none were unhealthy or restarting, the control panel still returned HTTP 302, & the proxy had logged zero error, fatal, or panic entries since recreation.

The unmatched-route check returned HTTP 404 from app-01 & from edge-01 across the VLAN 90-to-80 path. A count-only inspection found zero application router labels on running containers & zero references to the four middleware settings affected by the intervening migration notes. [The final verification transcript](../../Evidence/Coolify%20Traefik%203.6%20Patch%20Update%20-%202026-08-02/Logs/S03-Final-Verification-2026-08-02.txt) retains the provider, configuration, & host checks without recording a live public domain.

## Resulting configuration

| Item | Result |
|---|---|
| Coolify | 4.1.2, unchanged |
| Proxy image tag | `traefik:v3.6`, unchanged |
| Traefik runtime | 3.6.25 |
| Running image ID | `sha256:31267173a15b4944e797a76ffd9c419707c8d8b32fe5b610f80cd0cfa05f372d` |
| Rollback image | `traefik:rollback-v3.6.11-2026-08-02` |
| Compose project / service | `coolify-proxy` / `traefik`, unchanged |
| Providers | Docker & file, unchanged |

The change altered one workload version without adding, moving, or resizing a guest. I updated the living [Galaxy Services inventory](../../../../Operations/Inventory/Galaxy/Services.md) with Traefik 3.6.25; I didn't create a dated topology snapshot because all 13 guest assignments & workload memberships stayed unchanged.

## Rollback

The 3.6.11 image remains on app-01 under the dated rollback tag. To revert, I can retag it as `traefik:v3.6` & rerun the same single-service Compose recreation:

```sh
docker tag traefik:rollback-v3.6.11-2026-08-02 traefik:v3.6
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /data/coolify/proxy:/data/coolify/proxy:ro \
  -w /data/coolify/proxy \
  docker:cli docker compose -p coolify-proxy \
  up -d --no-deps --force-recreate --pull never traefik
```

I would then repeat the six-container, port 8000, port 80, edge-01, & proxy-log checks from Step 3.

## Remaining work

None. I left the dated 3.6.11 rollback image in place for the next proxy maintenance window; it isn't referenced by a running container.
