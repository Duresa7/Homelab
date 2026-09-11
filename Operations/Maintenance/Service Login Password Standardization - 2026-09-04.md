# Service Login Password Standardization

**Created:** 2026-09-04  
**Last updated:** 2026-09-06

**Implementation date:** 2026-09-04  
**Status:** Complete  
**Affected systems:** `media-01`, `docker-main`, `monitor-01`, `docker-network`, `app-01`, `game-01`, `splunk-siem`

## Outcome

I put every `dkadi` and `<REDACTED_PERSONAL_EMAIL>` web login on one password, the credential stored as `Account dkadi`. Fifteen web logins now authenticate with it. Three already did and needed no change, eleven were changed, and one is new.

The audit that preceded the change found two passwords in circulation rather than one. Seven stored items already held the standard, and a separate cluster of eight shared a different password among themselves. Eleven services with `dkadi` logins had no stored credential at all, so their state could not be compared until I reached each one directly.

Two stored credentials turned out to be wrong rather than merely different. The Nginx Proxy Manager item was already documented as stale, and the qBittorrent item failed the same way once tested. Neither could be used to authenticate, so both services were repaired at the storage layer instead of rotated through their own interfaces.

## Scope

Changed: `dkadi` and `<REDACTED_PERSONAL_EMAIL>` web logins only.

Left alone by instruction: the Jellyfin `IK-user` account, the Portainer `dashboard` account, the Coolify `jkhamdaraphone` account, the Splunk `admin` account, the Wazuh `admin` account, the `unifi-mcp` account, and the NetBird identity that authenticates through Microsoft Entra.

Out of scope entirely: Proxmox, every operating system and sudo credential, and every API token. The `Sudo Splunk-Siem VM`, `splunk-siem VM`, and `docker-network LXC` items sit in the same password cluster as the changed web logins but are host credentials, so they keep the password they had.

Prometheus has no authentication, so there was nothing to set.

## Changes

Each change was driven from the workstation over the service's own interface where the service offered one, so the credential moved from the password manager to the service without passing through the SSH gateway.

| Service | Host | Account | Method |
|---|---|---|---|
| Grafana 13.2.1 | `monitor-01` | `dkadi` | `PUT /api/admin/users/1/password` |
| qBittorrent 5.2.3 | `media-01` | `dkadi` | PBKDF2-SHA512 value written to `qBittorrent.conf` with the container stopped |
| Sonarr | `media-01` | `dkadi` | `PUT /api/v3/config/host` |
| Radarr | `media-01` | `dkadi` | `PUT /api/v3/config/host` |
| Prowlarr | `media-01` | `dkadi` | `PUT /api/v1/config/host` |
| Jellyfin 10.11.11 | `media-01` | `dkadi` | `POST /Users/{id}/Password` under an existing API key |
| Forgejo 16.0.3 | `docker-main` | `dkadi` | `forgejo admin user change-password` |
| Immich 3.1.0 | `docker-main` | `<REDACTED_PERSONAL_EMAIL>` | bcrypt `$2b$10$` written to the `user` table |
| BookLore v2.3.1 | `docker-main` | `dkadi` | bcrypt `$2a$10$` written to `users.password_hash` |
| Open WebUI 0.11.3 | `docker-main` | `<REDACTED_PERSONAL_EMAIL>` | bcrypt written to the `auth` table |
| PeaNUT 6.0.0 | `monitor-01` | `dkadi` | `WEB_PASSWORD` in `/opt/docker/peanut/.env`, then `docker compose up -d` |
| Nginx Proxy Manager 2.15.1 | `docker-network` | `<REDACTED_PERSONAL_EMAIL>` | bcrypt `$2b$13$` written to `auth.secret` |
| NetBird 0.78.0 | `docker-network` | `<REDACTED_PERSONAL_EMAIL>` | bcrypt `$2a$10$` written to the embedded identity provider, management restarted |
| Coolify | `app-01` | `dkadi` | bcrypt `$2y$10$` written to `users` where `id = 0` |
| Pelican Panel v1.0.0-beta38 | `game-01` | `dkadi` | bcrypt `$2y$10$` written to `users` where `id = 1` |

Portainer, Executor, and the Wazuh dashboard already accepted the shared account password. I confirmed each against the live service rather than trusting the stored item, and changed nothing.

Splunk cannot rename a user, so `admin` could not become `dkadi`. I created `dkadi` with the `admin` role and real name Duresa Kadi through `POST /services/authentication/users` on `127.0.0.1:8089`. The existing `admin` account keeps its own password and remains the only other Splunk user.

## Credential Storage

The stored arrangement changed once the rotation was done. Rather than one item per service, the account credential is now centralized in a single `Account dkadi` login holding the username `dkadi`, the password, and the email `<REDACTED_PERSONAL_EMAIL>`. That one item is the answer for every web login covered here.

I first updated the five items that had held stale or divergent values, then renamed them to drop the host suffix, since the hostname was not what identified them and one of them named the wrong host outright. Four of the five were then deleted as redundant against `Account dkadi`: Grafana Administrator, Nginx Proxy Manager, qBittorrent, and Pelican Panel. `PeaNUT Dashboard` was kept. The eleven services that never had an item still have none and do not need one under this arrangement.

`Account Standard` was deleted after `Account dkadi` was created and confirmed to hold the same password, so that two items could not drift apart while claiming to be the same credential.

Service API tokens, machine accounts, and host credentials keep their own items and are unaffected.

## Failed Attempts and Recovery

The first BookLore write corrupted the stored hash. I passed the bcrypt string through a double-quoted remote shell, so `$2a$10$` was read as positional parameters and the row ended up holding `a0/XLuu...` instead of a valid hash. No login would have succeeded against that value. I regenerated the hash and rewrote the row by piping the SQL over stdin, which removed the shell from the path entirely, and confirmed the stored value is a 60-character `$2a$10$` hash. Every later database write used the same stdin pattern.

BookLore was already failing its health check before I touched it. The container had been up eight hours, its health probe had been timing out with exit `-1`, and its last application log line was `2026-09-04T12:48:24` Eastern. Requests from outside the container and from inside it both timed out while Tomcat still held port 6060 open. The database write was unaffected by this, but it left me unable to verify the login. I restarted the container. It returned healthy in 45 seconds and the login then verified. The hang predates this work and its cause is not established.

qBittorrent rejected the stored credential. I stopped the container before editing `qBittorrent.conf`, because qBittorrent rewrites that file on exit and would have discarded a live edit.

`the password manager CLI's item-edit command` returned `invalid JSON provided` for all five updates when its standard input was not a terminal, because it tried to read stdin as an item template. Closing stdin resolved it.

## Verification

Every service was tested twice, once with the shared account password and once with a deliberately wrong one, so that a permissive endpoint could not read as a pass.

| Service | Correct password | Wrong password |
|---|---|---|
| Grafana | `GET /api/user` 200 | not run, admin API used |
| qBittorrent | login 204 with session cookie, `app/version` returned `v5.2.3` | 401 |
| Sonarr | 302 to `/` | 302 to `loginFailed=true` |
| Radarr | 302 to `/` | 302 to `loginFailed=true` |
| Prowlarr | 302 to `/` | 302 to `loginFailed=true` |
| Jellyfin | `AuthenticateByName` 200 | 401 |
| Forgejo | 303 to `/` | 200, login page redisplayed |
| Immich | 201 | 401 |
| Open WebUI | 200 | 400 |
| BookLore | 200 with access token | 400 `Invalid credentials` |
| PeaNUT | 302 with session cookie issued | 302, no session cookie |
| Nginx Proxy Manager | `POST /api/tokens` 200 | 400 |
| NetBird | stored hash verifies | control fails |
| Coolify | stored hash verifies | control fails |
| Pelican Panel | stored hash verifies | control fails |
| Splunk `dkadi` | `GET /services/server/info` 200 | 401 |
| Portainer | `POST /api/auth` 200 | 422 |
| Executor | sign-in 200 | 401 |
| Wazuh dashboard | `POST /auth/login` 200 | 401 |

NetBird, Coolify, and Pelican Panel were verified by reading the stored hash back and running the same bcrypt comparison the application performs, because each authenticates through a browser flow rather than a callable endpoint. The Wazuh API on port 55000 returns 401 for `dkadi` both before and after; that account is an indexer and dashboard user and was never a Wazuh API user.

Coolify still holds two rows after the change, `id = 0` and `id = 2`, and the `jkhamdaraphone` hash is untouched. Jellyfin still holds `dkadi` and `IK-user`, and `IK-user` was not modified.

A repeat of the stored-credential audit, run while the per-service items still existed, put twelve items on the shared account password. The items that differed were the host and sudo credentials, the `admin` accounts, the Portainer Edge Agent pairs, and the service accounts, which is the intended result.

## Open Items

I re-verified the first three on 2026-09-06 in the evening: a read-only query of Jellyfin's user table on `media-01` still shows a null password for `IK-user`, Portainer's user list on `docker-main`, read with the shared account, still shows `dashboard` at role 1 beside `dkadi`, and the indexer's `internal_users.yml` on `security-01`, unchanged since 2026-08-04, still defines the five demo users. All three remain decisions rather than fixes.

- Jellyfin `IK-user` has no password set at all. Its `Password` column is null, so the account authenticates with an empty credential from the user picker. It is not an administrator. Left alone by instruction; it needs a decision.
- Portainer `dashboard` holds `Role` 1, the same administrator authority as `dkadi`. It appears to exist for the Homelab Dashboard's API access and should hold a scoped role instead.
- The Wazuh indexer still defines the shipped demo accounts `logstash`, `snapshotrestore`, `kibanaro`, `readall`, and `anomalyadmin`, none of them reserved. Their default passwords are published upstream.
- BookLore's eight-hour hang has no root cause. A restart cleared it and the health probe has not failed since.
- Splunk now carries two administrators, `admin` and `dkadi`, because Splunk cannot rename a user. Whether `admin` stays is an open decision.
