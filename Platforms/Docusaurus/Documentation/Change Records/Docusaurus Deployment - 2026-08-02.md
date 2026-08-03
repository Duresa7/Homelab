# Docusaurus Deployment

**Created:** 2026-08-02  
**Last updated:** 2026-08-02

**Implementation date:** 2026-08-02  
**Target:** Docker Main (`192.168.40.35`)  
**Scope:** Docusaurus 3.10.2 static documentation site

## Starting state

Docker Main ran seven Compose projects and 11 containers. TCP 3010 was unused. The host had Docker Engine 29.6.2, Docker Compose 5.3.1, 24,000 MiB RAM with 3,024 MiB used, & 78 GiB free on `/`.

No Docusaurus source, image, container, or Compose project existed on the host. The deployment added one project without changing another service or guest allocation.

## Decisions

I deployed a new classic Docusaurus site instead of cloning the `facebook/docusaurus` contributor repository. The project repository is the framework's source; `create-docusaurus` is the supported path for a site. I used Docusaurus 3.10.2, which was the current documented version on 2026-08-02.

I built static files with Node.js 24.14.0 and served them with Nginx 1.29.5. This keeps 1,298 npm build packages out of the running image. The container runs as UID 101 with a read-only root filesystem, no Linux capabilities, `no-new-privileges`, & limits of 0.50 CPU, 128 MiB RAM, and 100 PIDs.

## Step 1: Validate the source & Compose definition

I created the source under `Platforms/Docusaurus/Source`, generated `package-lock.json`, & copied the source plus Compose configuration to `/opt/docker/docusaurus`. `docker compose config --quiet` exited `0`; the transcript records SHA256 values for all 12 deployed files.

Evidence: [preflight transcript](../../Evidence/Docusaurus%20Deployment%20-%202026-08-02/Logs/s01-preflight-2026-08-02.log)

## Step 2: Build & start the site

The first Docker build installed 1,298 npm packages, generated the static site in 3.311 seconds, & produced image `sha256:4b452421e71e8c6e37bf547d22e294d600fc034525b0d05fcf751e7074feb19e`. Compose created the container and published host TCP 3010 to container TCP 8080.

Evidence: [build & deployment transcript](../../Evidence/Docusaurus%20Deployment%20-%202026-08-02/Logs/s02-build-deploy-2026-08-02.log)

## Step 3: Check the runtime controls & restart path

The container reported `healthy`. `docker inspect` returned `user=nginx`, `readonly=true`, all capabilities dropped, `no-new-privileges=true`, a 128 MiB memory limit, a 0.50 CPU limit, a 100-PID limit, & `unless-stopped` restart behavior.

The runtime image had no `node` executable. A write beneath `/usr/share/nginx/html` failed with `Read-only file system`, the home page returned HTTP `200`, `/healthz` returned HTTP `200`, & the container returned to `healthy` after a controlled restart.

Evidence: [runtime verification transcript](../../Evidence/Docusaurus%20Deployment%20-%202026-08-02/Logs/s03-runtime-verification-2026-08-02.log)

## Step 4: Correct the Compose project name

Compose initially derived the project name `configuration` from the file's directory. I set the top-level name to `docusaurus`, recreated the stateless container, & confirmed `docker compose ls` reported eight projects with `docusaurus` running.

Evidence: [project-name correction transcript](../../Evidence/Docusaurus%20Deployment%20-%202026-08-02/Logs/s04-project-name-correction-2026-08-02.log)

## Step 5: Correct directory redirects

The first redirect-following test exposed a bad Nginx redirect. `/docs/intro` returned HTTP `301` toward `127.0.0.1:8080`, so the follow-up connection failed because only host TCP 3010 is published.

I added `absolute_redirect off` to the Nginx server block and rebuilt the image as `sha256:431580f0dc29c1aa52e5b16983ca6c24df0dfd2778863fd343e09ddf169c5ad4`. The corrected response carried `Location: /docs/intro/`; curl followed one redirect through host TCP 3010 and received HTTP `200` with 10,251 bytes.

Evidence: [failed final-state check](../../Evidence/Docusaurus%20Deployment%20-%202026-08-02/Logs/s05-final-state-2026-08-02.log), [corrective build & verification](../../Evidence/Docusaurus%20Deployment%20-%202026-08-02/Logs/s06-relative-redirect-fix-2026-08-02.log), & [troubleshooting record](../Troubleshooting/Nginx%20Directory%20Redirect%20Used%20Container%20Port%20-%202026-08-02.md)

## Step 6: Verify access from outside Docker Main

From Jedi PC, I requested the home page, the documentation route with and without a trailing slash, & `/healthz`. All four requests returned HTTP `200`; the no-slash request finished at `/docs/intro/` after the corrected relative redirect.

Evidence: [LAN reachability transcript](../../Evidence/Docusaurus%20Deployment%20-%202026-08-02/Logs/s07-lan-reachability-2026-08-02.log)

## Step 7: Converge the deployed source & final image

I added the repository's required `Created` and `Last updated` metadata to the site's introductory Markdown, deployed that final source, & rebuilt the image. The published page contained the metadata, the no-slash route followed one redirect to HTTP `200`, Docker reported `healthy`, & Nginx logged zero error-level lines.

That metadata rebuild produced image `sha256:1cbeee7666b9849dba2d4815b2ed6b4da14e4fb17647290de73daf489371592e`. The next step replaced it after correcting missing-route status handling.

Evidence: [final convergence transcript](../../Evidence/Docusaurus%20Deployment%20-%202026-08-02/Logs/s08-final-convergence-2026-08-02.log)

## Step 8: Return HTTP 404 for unknown routes

The first Nginx configuration sent an unknown path to `/404.html` as a successful internal redirect. I changed `try_files` to end with `=404` and configured `/404.html` as the error page, so a missing route keeps HTTP `404` while showing the Docusaurus page.

The host-side matrix returned HTTP `200` for home, docs with and without a trailing slash, & health. The missing route returned HTTP `404`, the slash redirect stayed relative, Docker reported `healthy`, & Nginx logged zero error-level lines. Jedi PC repeated the published-route checks with the same status values.

Evidence: [final route matrix](../../Evidence/Docusaurus%20Deployment%20-%202026-08-02/Logs/s09-final-route-matrix-2026-08-02.log), [final LAN matrix](../../Evidence/Docusaurus%20Deployment%20-%202026-08-02/Logs/s10-final-lan-route-matrix-2026-08-02.log), & [troubleshooting record](../Troubleshooting/Unknown%20Routes%20Returned%20HTTP%20200%20-%202026-08-02.md)

## Resulting configuration

| Item | Result |
| --- | --- |
| Site | `http://192.168.40.35:3010` |
| Health | `http://192.168.40.35:3010/healthz`, HTTP `200` |
| Compose project | `docusaurus`, one healthy container |
| Final image | `sha256:af4a28807ed90bc9345a65c644da77e6f2ec63aa5ca83339b28fe079947c656b` |
| Image size | 62,720,008 bytes |
| Observed idle use | 0.00 percent CPU, 4.621 MiB RAM, 5 PIDs |
| Persistence | Versioned source only; no database or writable volume |

## Rollback points

The service is additive. I can stop and remove its one container plus its default Docker network with `docker compose down`; the other seven Compose projects use separate networks and files.

The deployed source remains under `/opt/docker/docusaurus`, and the authoritative copy remains in this repository. Rebuilding from the lockfile recreates the static site.

## Remaining work

The site is reachable by direct LAN address only. I did not add internal DNS, Nginx Proxy Manager, public ingress, or authentication because the request covered deployment on Docker Main.

The Docusaurus build graph retains 18 moderate npm advisories in packages discarded before runtime. A future Docusaurus upgrade should retest the lockfile and remove the override when upstream no longer needs it.
