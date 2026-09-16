# Dockhand

**Created:** 2026-09-15  
**Last updated:** 2026-09-16

I run Dockhand 1.0.48 on `docker-main` at [dockhand.alphasecunited.com](https://dockhand.alphasecunited.com). After retiring Portainer on 2026-09-16, I verified seven connected Docker hosts, 42 Compose projects, 64 running containers, and six stopped Hawser updater containers. Dockhand and six Hawser 0.2.48 agents manage the remaining applications.

| Host | Address | Connection | Projects before Dockhand deployment | Containers before Dockhand deployment |
|---|---|---|---:|---:|
| docker-main | 192.168.40.35 | Local Docker socket | 10 | 15 |
| docker-blue | 192.168.40.39 | Hawser Edge | 7 | 11 |
| docker-network | 192.168.85.2 | Hawser Edge | 5 | 6 |
| monitor-01 | 192.168.73.2 | Hawser Edge | 4 | 9 |
| media-01 | 192.168.40.42 | Hawser Edge | 4 | 11 |
| alpha-prod-01 | 192.168.80.118 | Hawser Edge | 8 | 8 |
| security-01 | 192.168.72.2 | Hawser Edge | 2 | 2 |

I excluded `app-01` and Coolify. The initial Dockge replacement preserved application container IDs and start timestamps. The later approved monitor-only repair recreated `teamspeak-monitor`.

## Access and configuration

On 2026-09-15 I changed the administrator username and password to match my approved shared login credential. The current values are also saved in my credential vault; the item is not named here. I verified a fresh HTTPS login, administrator access, and all seven environments. Authentication remains enabled. NPM proxy host 31 forwards to `http://192.168.40.35:3003` with certificate 1, Force SSL, HTTP/2, and WebSocket upgrades. Internal DNS points the service name to NPM at `192.168.85.2`.

The hub runs `/opt/docker/dockhand/compose.yaml`, stores state at `/opt/docker/dockhand/data`, and uses `/opt/docker/dockhand/stacks` for new stack definitions. It mounts the local Docker socket and `/opt/docker` at the same path. The six remote hosts run `/opt/docker/hawser/compose.yaml`. Each agent initiates an authenticated connection to `wss://dockhand.alphasecunited.com/api/hawser/connect` with a host-specific token. The `.env` beside that file still holds the token, but since the cutover the deployed `compose.yaml` carries the resolved value itself; both files are root-owned at mode 0600 on all six hosts. The agents map the service name directly to `192.168.85.2` and publish no listener port. The hub reference remains pinned by digest. Hawser uses `latest` with the companion updater; the deployed agent contents remain 0.2.48. I retain the [configuration references](Configuration).

## Existing stack files

I imported all 47 Compose projects on 2026-09-15; 42 remain after removing the five Portainer projects. Dockhand now reads their editable definitions from `/opt/docker/dockhand/stacks/imported/<host>/<project>/compose.yaml` on `docker-main`. I resolved environment files into protected mode-0600 definitions, merged BookLore's override, retained absolute bind and build paths, and enabled the already-running media VPN services in the imported definition. The host directory names use underscores, such as `docker_blue`.

I validated each normalized definition against its source with Docker Compose before adoption. Import did not deploy or restart any application. I then created, deployed, read, saved, and removed a disposable stack through Dockhand on every host. All seven tests passed. The 69 existing container IDs, start times, and running states remained unchanged during this preparation.

The imported files are the source for future Dockhand stack edits. Deploying a project through Dockhand also writes its normalized definition over the project's own Compose file. The [registry and agent cutover](Documentation/Change%20Records/Registry%20and%20Agent%20Cutover%20-%202026-09-15.md) did that to eleven of the 42 on 2026-09-15: five application projects and the six Hawser projects. Those eleven are now JSON with their environment files resolved inline, at mode 0600. The other 31 still hold their original YAML at their original modes, and a UI edit does not reach them, so I must reconcile one of those before using it for a later command-line deployment. The copies tracked in this repository stay in the authored YAML form, referencing secrets rather than resolving them, so they are the readable reference and never a byte match for a rewritten host file.

## Portainer retirement

I retired Portainer and its four Edge Agents on 2026-09-16. I removed their data, images, host files, imported definitions, credentials, NPM host, DNS record, dedicated firewall rules, and maintenance and monitoring entries. Dockhand still reaches every host; all remaining containers retained their IDs and start times. [Retirement record](../../Archive/Platforms/Portainer/Documentation/Change%20Records/Retirement%20-%202026-09-16.md).

## Updates

I verified Dockhand's authenticated image-pull and container-replacement path on all seven hosts on 2026-09-15 using disposable `busybox:stable` containers with no host mounts, published ports, or network access. Every replacement started; I removed the test containers and newly introduced image tags. Existing application container IDs and states remained unchanged. This verifies the management path, not compatibility of a future application release.

Registry-backed containers can use Dockhand's container update controls. This does not require adopting every existing Compose file. A pinned version or digest still controls which release can be selected. The check found nine available updates; I did not apply them.

I published the existing contents of six custom images to the private `homelab-images` organization in Forgejo: `docusaurus`, `mcp-ssh-manager`, `unifi-network-mcp`, `alert-bot`, `teamspeak-monitor`, and `wazuh-mcp-server`. Each uses `forgejo.alphasecunited.com/homelab-images/<image>:stable`. Dockhand's [registry entry](Configuration/forgejo-registry.json) uses a non-administrator service account with package read/write permission, so native pull and push controls both work. Anonymous manifest access returned HTTP 401.

Registry checks, pull/replacement, and native image push passed for all six images using disposable containers. I completed the [registry and agent cutover](Documentation/Change%20Records/Registry%20and%20Agent%20Cutover%20-%202026-09-15.md) on 2026-09-15. All six running custom applications now use the private registry names with update checks enabled. A fleet-wide Check for updates returned zero registry errors. The migration preserved all twelve targeted image IDs and every unrelated container ID and start time.

Custom source changes still require a build and publication before Check for updates can discover them. The deployed definitions retain the four existing build contexts and add the two MCP Dockerfiles. Dockhand's stack build controls can build them; Images > Push publishes the selected image to Forgejo. A registry check does not fetch or modify source code.

Dockhand's own update check passed with no error. Its self-update flow is in Settings > About. I applied the [Hawser update overlay](Configuration/hawser-update-overlay.yaml) and installed the [updater script](Scripts/update-hawser.sh) on all six agent hosts. To update an agent, I select its stopped `hawser-updater` container in Dockhand and press Start, following the [upstream workflow](https://dockhand.pro/manual/#updating-hawser-agent). The maintenance profile keeps this helper out of normal stack deployments. The Hawser container itself is excluded from direct image updates. Starting it briefly disconnects that host from Dockhand while its agent is replaced. Application containers stay running.

On 2026-09-16 I ran all six updater helpers through Dockhand. Each exited with code 0; every agent matched the pulled `latest` image at 0.2.48 and passed the connection test. Only security-01's agent was recreated, with unchanged image contents. All application containers remained unchanged. The helpers are stopped in `exited` state and can be started again. [Update verification](Documentation/Change%20Records/Hawser%20Update%20Verification%20-%202026-09-16.md).

## Records

- [Dockge replacement and verification](Documentation/Change%20Records/Dockge%20Replacement%20-%202026-09-15.md)
- [Fleet verification](Evidence/Dockge%20Replacement%20-%202026-09-15/Verification.json)
- [Local TeamSpeak monitor registry-check error](Documentation/Troubleshooting/Local%20TeamSpeak%20Monitor%20Registry%20Check%20-%202026-09-15.md)
- [Login alignment and update-path verification](Documentation/Change%20Records/Login%20Alignment%20and%20Update%20Verification%20-%202026-09-15.md)
- [Private registry and editable stack preparation](Documentation/Change%20Records/Registry%20and%20Stack%20Preparation%20-%202026-09-15.md)
- [Registry and agent cutover](Documentation/Change%20Records/Registry%20and%20Agent%20Cutover%20-%202026-09-15.md)
