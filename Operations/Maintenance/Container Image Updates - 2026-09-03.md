# Container Image Updates

**Created:** 2026-09-03  
**Last updated:** 2026-09-04

**Implementation date:** 2026-09-03  
**Status:** Complete  
**Affected systems:** `docker-main`, `docker-blue`, `docker-network`, `media-01`, `alpha-prod-01`, `monitor-01`, `app-01`, `security-01`, `game-01`, `ansible-01`, `grey-server`

## Outcome

I completed the three reported image updates, inventoried every live Compose image across the nine Docker hosts, and moved eligible services to their upstream floating tag so future reconciliation can keep taking new releases. I excluded the Coolify-managed stack and generated applications. I also refreshed the stateful BookLore and Immich dependencies to the exact images their current release Compose files support instead of putting databases on an unconstrained tag.

The Docker MCP Gateway `latest` trial was rolled back to the exact 0.43.3 image and digest. What first looked like a v2-only long-lived regression was reproduced on 0.43.3 under parallel load later that afternoon. A separate shared-server cutover removed SSH Manager from the gateway's per-session container lifecycle; the gateways and all updated applications are healthy.

## Resulting Image Policy

| Workload | Scope | Resulting image reference or policy |
| --- | ---: | --- |
| Forgejo | 1 | `codeberg.org/forgejo/forgejo:16`; current major tag, not cross-major `latest` |
| What's Up Docker | 6 | `getwud/wud:latest` |
| cAdvisor | 9 | `ghcr.io/google/cadvisor:latest` |
| TeamSpeak Playit agent | 1 | `ghcr.io/playit-cloud/playit-agent:latest` |
| Portainer Edge Agent | 4 | `portainer/agent:latest` |
| CLI Proxy API | 1 | `eceasy/cli-proxy-api:latest` |
| blackbox exporter | 1 | `prom/blackbox-exporter:latest` |
| NUT exporter | 1 | `hon95/prometheus-nut-exporter:latest` |
| PeaNUT | 1 | `brandawg93/peanut:latest` |
| Executor | 1 | `ghcr.io/usefulsoftwareco/executor-selfhost:latest` |
| BookLore MariaDB | 1 | `lscr.io/linuxserver/mariadb:11.4.8`; exact dependency from BookLore v2.3.1 |
| Immich Valkey | 1 | `docker.io/valkey/valkey:9` at the Immich v3.1.0 release digest |
| Immich PostgreSQL | 1 | PostgreSQL 14, VectorChord 0.4.3, and pgvectors 0.2.0 at the Immich v3.1.0 release digest |
| Docker MCP Gateway | 2 | Exact `v0.43.3` digest retained after the update trial; SSH Manager now runs as a separate persistent service |

Existing `latest` and application-defined moving channels stayed in place. Local images stayed local, and the Coolify-owned services on `app-01` were not changed. The separate cAdvisor project on `app-01` is Ansible-managed monitoring rather than a Coolify workload and was included.

## Release Review

Forgejo 16.0.3 was the current stable release. The [Forgejo 16 announcement](https://forgejo.org/2026-07-release-v16-0/) calls out stricter mirror redirect handling, removal of avatar EXIF stripping, a container trusted-proxy default change, and centralized Git hooks. The instance uses SQLite, carries no custom templates, and does not enable reverse-proxy authentication. Its explicit `REVERSE_PROXY_TRUSTED_PROXIES = *` and `ALLOW_LOCALNETWORKS = true` settings remained unchanged. Forgejo 16 is not an LTS branch and is supported through 2026-10-29; the prior 15 branch is LTS through 2027-07-15.

What's Up Docker 8.4.0 is a same-major update. Its [release notes](https://github.com/getwud/wud/releases/tag/8.4.0) add registry providers and triggers, bound concurrent registry requests with retry handling for HTTP 429, preserve update results across registry errors, and redesign the UI. The release marks no breaking configuration change relevant to this deployment.

Playit 1.0 moves the CLI behind a background daemon and IPC interface, improves task lifecycle handling, and repairs UDP recovery according to the [1.0.0 release notes](https://github.com/playit-cloud/playit-agent/releases/tag/v1.0.0). The official Docker instructions still use the existing `SECRET_KEY` environment interface. Tag 1.0 resolved to the 1.0.10 image revision, whose [release notes](https://github.com/playit-cloud/playit-agent/releases/tag/v1.0.10) include pre-1.0 permission-upgrade fixes.

BookLore v2.3.1's [release Compose example](https://github.com/booklore-app/booklore/blob/v2.3.1/example-docker/docker-compose.yml) pins MariaDB 11.4.8. Immich v3.1.0's [release Compose file](https://github.com/immich-app/immich/releases/download/v3.1.0/docker-compose.yml) pins Valkey 9 and the PostgreSQL 14 VectorChord build. I used those application-owned references. I did not use LinuxServer MariaDB `latest`, which had already advanced to a newer database branch, or replace Immich's PostgreSQL image with a generic tag.

## Changes

I created the temporary Proxmox snapshot `pre-forgejo-v16-20260903` for LXC 110 before the Forgejo database migration. It covered the LVM root disk and the ZFS `/data` mount. I ran the Forgejo doctor check with no errors or warnings, flushed its queues, changed the Compose image to `codeberg.org/forgejo/forgejo:16`, and recreated the service. The container started as Forgejo 16.0.3.

I first deployed WUD 8.4.0 to the six Compose hosts and Playit 1.0 to the shared TeamSpeak tunnel project. I then changed the eligible tracked and live references in the table above to `latest`. The monitoring-exporters playbooks reconciled cAdvisor on nine hosts and WUD on six; the fleet-update projects covered the application services. The WUD idempotency run returned no change, failure, or unreachable host.

The live audit covered 42 active Compose projects represented by 43 Compose files across nine Docker hosts. It caught two valid floating aliases that the first pass missed, PeaNUT and Executor, and later caught BookLore's pinned MariaDB dependency. I reviewed the Immich dependency pins in the same pass.

Before changing the stateful dependencies, I created temporary LXC 110 snapshot `pre-stateful-images-20260903`. I stopped BookLore while MariaDB moved from 11.4.5 to the v2.3.1-supported 11.4.8 image. I refreshed Immich from Valkey 8 to its v3.1.0 Valkey 9 image and updated the digest of the existing PostgreSQL 14 VectorChord image. I stopped Immich server while its database container was recreated, then started the application after both dependencies became healthy.

I tested Docker MCP Gateway `latest` on both gateway services. The v2 image started one managed SSH Manager container per independent client session despite `--long-lived`, and calls eventually returned internal tool errors. I restored both services to the exact 0.43.3 tag and digest, then restarted only the SSH Manager gateway to clear five managed containers left by the test. A later parallel test produced the same accumulation on 0.43.3, so the [compatibility rollback record](../../Platforms/Docker%20MCP%20Gateway/Documentation/Change%20Records/v2%20Compatibility%20Rollback%20-%202026-09-03.md) is superseded on cause. The [shared server cutover](../../Platforms/Docker%20MCP%20Gateway/Documentation/Change%20Records/SSH%20Manager%20Shared%20Server%20Cutover%20-%202026-09-03.md) resolved the underlying per-session lifecycle by running SSH Manager as one persistent Compose service.

The remote execution channel returned an internal error while the Playit update waited for a new monitoring cycle and again while the stateful dependencies settled. I did not replay either mutation. Separate read-only checks found the requested images already running and healthy.

## Verification

- Forgejo reports 16.0.3. The post-upgrade doctor check returned no errors or warnings, local HTTP and `https://forgejo.alphasecunited.com/` returned 200, the SSH listener answered on TCP 222, and the container log contained no error-class line after migration.
- The monitoring-exporters validator, Ansible syntax check, deployment, and idempotency run passed. cAdvisor registered all 69 running containers across the nine hosts. Every WUD endpoint answered and exported container metrics.
- Prometheus reported all 56 active targets up. WUD reported `update_available="false"` for the services moved to floating tags that it can query.
- Playit loaded both TeamSpeak tunnels with restart count 0. Both DNS SRV checks, local UDP voice probes, public UDP voice probes, and query checks returned 1; both fault metrics returned 0.
- CLI Proxy API, Executor, PeaNUT, Portainer, blackbox exporter, NUT exporter, and the gateway health endpoints answered their service checks. The HTTPS checks for CLI Proxy API, BookLore, and Immich returned 200.
- MariaDB reports 11.4.8-r0-ls206 and healthy. `mariadb-check -c -A` returned `OK` for every BookLore, system, and metadata table, and BookLore v2.3.1 returned its application health response.
- Valkey reports 9.1.0 and returned `PONG`. Immich PostgreSQL reports 14.19, accepted an application-role readiness probe, and logged no error after that probe. All four Immich containers report healthy with restart count 0, and the server reports v3.1.0.
- Real UniFi and SSH Manager gateway calls passed after rollback and after the shared-server cutover. Four parallel SSH calls left zero gateway-managed SSH containers, and a fresh post-settle check on 2026-09-04 found both 0.43.3 gateways and the persistent SSH Manager service healthy with restart count 0.
- Final host checks found no new critical issue. `docker-main` retained its existing 83 percent `/data` utilization warning.

I removed both temporary Proxmox snapshots after their validation gates passed. I retained no backup or standalone evidence folder.

## Open State

No deployment step remains. Docker MCP Gateway stays pinned to 0.43.3 pending a separate deliberate update, but the pin is no longer tied to long-lived SSH behavior because SSH Manager now runs outside the gateway's managed-container lifecycle. Forgejo stays on its current-major tag, and the BookLore and Immich databases stay on application-supported pins. Every floating tag can move to a new release or major version on a future reconciliation, which is intentional for the services listed above. Coolify remains outside this policy.
