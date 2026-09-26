# Deployment

**Created:** 2026-09-21  
**Last updated:** 2026-09-21

**Implementation date:** 2026-09-21  
**Status:** Complete

I added Weebarr 0.2.0 to `media-01` at `https://weebarr.alphasecunited.com`. It uses Seerr's existing anime route, profile 7 `[Anime] Remux-1080p`, and `/data/media/anime`. The [upstream deployment instructions](https://deepdaddyttv.github.io/weebarr/Deployment-Other-Options/) supplied the image, port, persistent mount, and public-URL setting.

## Deployment and access

I added only the `weebarr` service to `/opt/media-stack/compose.yml` and started it with `--no-deps`. It runs as `1000:1000`, joins `media`, publishes `18080:8888`, and mounts `/opt/media-stack/config/weebarr` at `/config`. The host directory is mode 0700. The deployed image ID is `sha256:761ec55c65634c1425f87be870d6576dc7e13e6fc058e21a2cace9de4d382a14`.

I created local login `dkadi` and saved its generated password in the Weebarr administrator item. The backend key came from the existing Seerr configuration without appearing in output. I initially supplied it through a mode-0600 environment file, then persisted it through Weebarr's settings store, removed the environment-file dependency, recreated only Weebarr, and shredded the temporary file. Fresh login and the Seerr connection test passed after recreation. All four automatic-request buckets remain disabled and the content filter retains its default.

I added Weebarr to Dockhand's imported media-stack definition on `docker-main`. Both definitions pass Compose validation, the imported file remains mode 0600, and Hawser can read the live Compose path. Docker labels identify the container as project `media-stack`, service `weebarr`.

I created NPM proxy host 33 with upstream `192.168.40.42:18080`, certificate 1, Force SSL, HTTP/2, WebSockets, and exploit blocking. I added UniFi local A record `6ab17b2625574794b91d2402`, TTL 300, pointing to NPM `192.168.85.2`. Policy `6a60fd2c2d027bb05525a86d`, `Allow NPM to media-01 web UIs`, retains its source and destination selectors and now includes TCP 18080 alongside its six existing ports. I added no public DNS record or WAN ingress.

## Verification

| Check | Observed result |
| --- | --- |
| Container | Running, healthy, zero restarts after recreation; version 0.2.0 |
| HTTPS | HTTP redirects with 301; TLS validation succeeds; fresh authenticated login returns 200 |
| Access control | Unauthenticated settings API returns 401 |
| Health | `/api/health` returns `healthy`, backend `seerr`, and both backend-configured flags true |
| Backend test | HTTP 200, success true, one Sonarr server; server 0, profile 7, anime root and series type resolved |
| Seasonal data | Summer 2026 lookup returns 48 titles: 43 requestable, 2 requested, 1 available, 1 partial, 3 missing mappings |
| Sonarr | Zero health messages; both root folders accessible; anime profile 7 present |
| Downstream configuration | Enabled qBittorrent client through Proton VPN; enabled 1337x, EZTV, and Nyaa.si indexers from Prowlarr |
| Existing services | Eight existing media services retain their running state; Jellyfin and Gluetun remain healthy |
| NPM | `nginx -t` passes; 25 enabled proxy hosts |
| DNS | Internal name resolves through NPM; public Cloudflare resolver returns NXDOMAIN |
| Monitoring | Weebarr target is up with `probe_success=1`; approved-target assertion passes for all 58 targets |

I added the root HTTPS URL to `/home/dkadi/monitoring/prometheus-config/prometheus.yml`, validated with `promtool`, and reloaded Prometheus with SIGHUP. The live file and versioned reference share SHA-256 `118c7009aaacddf9822bd27f45530fa1da7452f533e9864a8a238b786a7d73d1`. I updated the approved-target assertion and the media, service, DNS, proxy, firewall, and Dockhand records.

I did not submit an acquisition request or start a download. Verification covers live authentication, discovery, existing-library availability, backend defaults, downstream configuration, and monitoring. It does not establish that every AniList title maps to Seerr; three of the sampled titles lacked mappings.

I retained no separate terminal transcript or screenshot for these steps. Results were read back from the live application APIs, SSH Manager, and UniFi during this session. Temporary local API-token and session files were removed. I created no snapshot or retained backup.

## Setup corrections

An initial Compose read as `dkadi` could not read the root-owned `.env`. I used the configured SSH Manager sudo path. A heredoc placed directly after sudo consumed the password input and failed before any change; wrapping the script in `bash -c` fixed the invocation. A Dockhand inspection tried unavailable PyYAML; Docker Compose's JSON output supplied the readback instead.

My first login probe posted to `/login` and returned 405. The documented source exposes `/api/auth/login`, which returned 200 with a persistent session. The pre-recreation session subsequently returned 401; a fresh login passed and the saved backend key, anime defaults, and disabled automation remained intact.

## Password alignment after deployment

On 2026-09-21 I replaced the generated Weebarr password with the password from my selected shared login, keeping username `dkadi`. I used the authenticated `/api/settings/access/local` endpoint and updated the Weebarr administrator item through stdin. Its saved password matched the shared login in an in-memory digest comparison. A fresh HTTPS login and the Seerr connection test both passed. No secret value or temporary credential file was written during this change; I retained no separate transcript.

## Removal path

Remove only Weebarr from both media-stack definitions, stop and remove its container, and remove NPM host 33, the local DNS record, TCP 18080 from the NPM-to-media policy, and its Prometheus target. Retain the persistent config unless intentionally deleting its login and request history. The existing Seerr and downstream media services do not depend on Weebarr.
