# Deployment

**Created:** 2026-10-05  
**Last updated:** 2026-10-05

**Status:** Complete  
**Date:** 2026-10-05

I deployed Sure 0.7.5-hotfix.1, the community fork of Maybe Finance, on CT 110 `docker-main` with Docker Compose and published it internally at `https://sure.alphasecunited.com` through Nginx Proxy Manager.

## Official deployment method

Before deploying I read the [official Docker hosting guide](https://github.com/we-promise/sure/blob/main/docs/hosting/docker.md), its [`compose.example.yml`](https://github.com/we-promise/sure/blob/main/compose.example.yml) and [`.env.example`](https://github.com/we-promise/sure/blob/main/.env.example). The guide's stack is four services: `web` (Rails and Puma on 3000), `worker` (Sidekiq), PostgreSQL 16 and Redis. It requires `SECRET_KEY_BASE` from `openssl rand -hex 64` and a `POSTGRES_PASSWORD`, and says to set `RAILS_ASSUME_SSL` to `true` when Sure sits behind HTTPS.

The `stable` tag pointed to `sha256:3692b3bcf0eae2c7f3154348c6131060bda8127038fc78b0543f15b5166e6074`, the same digest as `0.7.5-hotfix.1`. GitHub had published release `v0.7.5-hotfix.2` at 3:08 UTC that morning, but GHCR returned 404 for its image tag, so I pinned `0.7.5-hotfix.1`. Its source is commit `789883081feda49fcfa8c7bc923cc77c9fe301ad`.

I kept the official service layout, PostgreSQL 16, the health checks, the `dns` override to `8.8.8.8` and `1.1.1.1` that the example sets for Yahoo Finance, and the Sidekiq worker command. My local changes:

| Change | Reason |
|---|---|
| Image pinned to `0.7.5-hotfix.1`; Redis pinned to `redis:8` instead of `latest` | Upgrades happen when I choose to make them |
| Port `192.168.40.35:3005:3000` | TCP 3000 on `docker-main` belongs to Forgejo; 3005 was free |
| `RAILS_ASSUME_SSL: "true"`, `APP_DOMAIN: sure.alphasecunited.com` | NPM terminates TLS; the guide's HTTPS setting |
| `EXCHANGE_RATE_PROVIDER` and `SECURITIES_PROVIDER` set to `yahoo_finance` | The official `.env.example` sets them, but the example Compose file never passes them to the containers. Without them Sure defaults to Twelve Data, which needs an API key |
| Bind mounts under `/opt/docker/sure/data/` instead of named volumes | Matches the other Compose projects on this host |
| Secrets required with `:?` instead of the example's defaults | The example falls back to a published `SECRET_KEY_BASE` and `sure_password` when `.env` is missing |
| Bounded `json-file` logs, explicit container names | Same as Homarr and BookOrbit on this host |
| Backup sidecar omitted | I keep no backups |

## Deployment and access

| Step | Action and observed result |
|---|---|
| Preflight | `docker-main` had 14 GiB of available RAM, 39 GiB free on `/`, Compose v5.5.1 and no listener on 3005. `/opt/docker/sure` did not exist. NPM had 24 live hosts and none for Sure. UniFi held 30 DNS records, 24 pointing at NPM, none for Sure. |
| Project and secrets | I created `/opt/docker/sure` and copied the Compose file across. Its SHA-256 matched the repository copy, `32d22edae388fd0d5e6044005e3c99f212616ebc09eff54537a807e032b56460`. I generated `SECRET_KEY_BASE` (128 hex characters) and `POSTGRES_PASSWORD` (64 hex characters) with `openssl` on the host, writing them straight into `.env` under `umask 077`. The file is mode `0600`, owned by root, and its values never left the host. `docker compose config --quiet` passed. [Log](../../Evidence/Deployment%20-%202026-10-05/Logs/Stage-and-Secrets.log) |
| Containers | `docker compose pull` and `up -d` exited 0. `sure-db` and `sure-redis` turned healthy, then `sure-web` and `sure-worker` started. Pulled digests: `postgres:16` `sha256:1a6ab3f5345eb6dbe04a1349529caabdb0ab09293a09590fad07b2246bfa4b54`, `redis:8` `sha256:6f81e8915c60b065a524e6967e0ad1c639ba6efa84d669f823683ea04d9150ee`. [Log](../../Evidence/Deployment%20-%202026-10-05/Logs/Compose-Up.log) |
| Readiness | At 1:53 PM Eastern, `http://192.168.40.35:3005/up` returned 200 on the second poll. The database showed 446 migrations up and 0 down. The worker had logged a missing `settings` table because it started while migrations were still running, so I restarted `sure-worker`. It came back without that warning. [Log](../../Evidence/Deployment%20-%202026-10-05/Logs/Readiness.log) |
| Firewall | Through UniFi MCP I added TCP 3005 to policy `6a60fd2c2d027bb05525a873`, `Allow NPM to docker-main web UIs`. Readback: destination ports `2283,3000,3002,3003,3004,3005,6060,7575`, with source (`192.168.85.2`) and destination (`192.168.40.35`) unchanged. From `docker-network`, `/up` returned 200. [Export](../../Evidence/Deployment%20-%202026-10-05/Exports/Firewall-Update.json) |
| NPM | I created proxy host 36 for `sure.alphasecunited.com` through the NPM API, forwarding HTTP to `192.168.40.35:3005`. Its settings were copied from Homarr's host 34: certificate 1, Force SSL, HTTP/2, WebSockets and Block Common Exploits on; HSTS and caching off. Readback: `nginx_online=true`, no nginx error, 25 live hosts. [Export](../../Evidence/Deployment%20-%202026-10-05/Exports/NPM-Proxy-Host.json) |
| DNS | Through UniFi MCP I created A record `6ac3e46b25574794b94ddd9b`, `sure.alphasecunited.com` to `192.168.85.2`, TTL 300. `ubuntu-dev` resolved it to `192.168.85.2`, and `1.1.1.1` returned NXDOMAIN. [Export](../../Evidence/Deployment%20-%202026-10-05/Exports/DNS-Record.json) |
| Administrator | I registered the first account through the HTTPS sign-up form using the email and password from the standard application account. The form returned 302 to `/`. Rails readback showed one user with role `super_admin` and one family. I then set `Setting.onboarding_state` to `closed` with `rails runner`, which the guide does through Settings > Self-Hosting > Onboarding. `/registration/new` now redirects to `/sessions/new`. [Log](../../Evidence/Deployment%20-%202026-10-05/Logs/Signup-Closure.log) |

## Verification

At 1:55 PM Eastern, HTTP redirected to HTTPS with a 301, the certificate validated, and `/up` returned 200 through HTTPS. [Log](../../Evidence/Deployment%20-%202026-10-05/Logs/HTTPS-Verification.log)

A fresh HTTPS session with the standard account's email and password returned 302 to `/`. The authenticated root then redirected to `/onboarding`, while an anonymous request redirected to `/sessions/new`. I restarted all four containers with `docker compose restart`. `/up` returned 200 again within 11 seconds, every container's restart count was 0, and the same login test produced the same result. That confirms the account and database survived the restart. Sign-up stayed closed. [Log](../../Evidence/Deployment%20-%202026-10-05/Logs/Login-and-Restart.log), [post-restart checks](../../Evidence/Deployment%20-%202026-10-05/Logs/Post-Restart-Checks.log)

The preview browser on Jedi PC loaded the sign-in form at `https://sure.alphasecunited.com/sessions/new`. No retained capture exists for that step.

The first resource sample showed `sure-web` at 360 MiB, `sure-worker` at 329 MiB, `sure-db` at 40 MiB and `sure-redis` at 6 MiB. The data directory was 56 MB. I did not resize the LXC or touch any other application.

## Findings

**Encryption at rest.** Every boot logs `[SECURITY] ActiveRecord Encryption is NOT configured`. I read `config/initializers/active_record_encryption.rb` at the deployed commit. In self-hosted mode it derives the primary key, deterministic key and salt from `SECRET_KEY_BASE` with SHA-256. The warning fires because the keys were not set explicitly. `ActiveRecordEncryptionConfig.ready?` returned `true` at runtime, so the models that encrypt provider tokens are encrypting. The consequence: changing `SECRET_KEY_BASE` makes every encrypted field unreadable.

**Yahoo Finance is rate-limited.** The Yahoo provider loaded, but a USD to EUR rate fetch failed and `healthy?` returned false. From inside `sure-web`, `query1.finance.yahoo.com` returned HTTP 429. Yahoo is refusing my public address, so this is not a problem with the container's DNS or routing. [Log](../../Evidence/Deployment%20-%202026-10-05/Logs/Yahoo-Finance-Check.log)

## Open

- Finish onboarding in the browser: name, country, currency and locale are my choices, so I left them for the first sign-in.
- Exchange rates and security prices will fail while Yahoo keeps returning 429. A free Twelve Data API key, entered under Settings > Self-Hosting, is the fallback the guide supports.
- No SMTP is configured, so password reset by email does not work.

I created no snapshot or backup. The only file holding secrets is the deployment's own `/opt/docker/sure/.env`. The local working copies of the evidence and the login script under `/tmp` held no credentials, and I deleted them after copying the evidence into the repository. During preflight I tested outbound DNS in throwaway `--rm` containers from `alpine:3.20`. That image is still on the host. I could not tell whether it was already present before the test, so I left it.
