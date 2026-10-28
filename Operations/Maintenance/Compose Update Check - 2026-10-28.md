# Compose Update Check

**Created:** 2026-10-28  
**Last updated:** 2026-10-28

## Observed state

I inspected 63 running containers in 38 Compose projects on docker-main, docker-blue, docker-network, media-01, monitor-01, alpha-prod-01, and security-01 through SSH Manager. None of the initial container statuses reported unhealthy or restarting. app-01 failed connection with `EHOSTUNREACH` at 192.168.80.10:22.

I pulled the exact image references recorded in the running containers and compared the resulting local image IDs with the running image IDs. Ten containers had newer images available at those references: Hawser on all six hosts other than docker-main, qBittorrent and Radarr on media-01, and Minecraft and Playit on alpha-prod-01. I downloaded those images but did not recreate those containers or edit Compose files.

Five private registry image pulls failed: mcp-ssh-manager, unifi-network-mcp, alert-bot, teamspeak-monitor, and wazuh-mcp-server under forgejo.alphasecunited.com/homelab-images. I did not retain the error details, so their cause remains undiagnosed. The other successful pulls matched the running image IDs. This checks only the configured reference; a fixed version or digest matching does not establish that the application is on its newest release.

I retained no standalone command transcript for these checks. I created no snapshot or backup.

## CLI Proxy API update

CLI Proxy API matched its configured image during the initial pass. A subsequent pull found a newer image, and I updated only that service on docker-main from v8.0.45 to v8.0.46. Compose validation passed, the running image matched the pulled image, and the container reported restart count 0. The local root, management page, and internal HTTPS route returned HTTP 200; unauthenticated `/v1/models` returned the expected HTTP 401. Authenticated provider requests remain untested. The [platform change record](../../Platforms/CLI%20Proxy%20API/Documentation/Change%20Records/Image%20Update%20-%202026-10-28.md) holds the image ID and implementation details.

## Minecraft and Playit excluded

I excluded Minecraft and Playit on alpha-prod-01 from this update pass. Neither service was restarted, recreated, or updated. Their newer images were already downloaded during the check, but their running containers retain their previous images. I left their Compose configuration and update automation unchanged; this exclusion applies to this maintenance pass.

## Open work

Hawser on six hosts, qBittorrent, and Radarr remain on their pre-check running images. I still need to review compatibility and deploy those eight updates with service-specific health checks. qBittorrent and Radarr recreation will briefly interrupt their services; Hawser recreation briefly interrupts Dockhand management of its host.

I still need to investigate the five private registry pull failures and check newer releases for version-pinned and digest-pinned applications. app-01 and any Compose deployments outside the seven inspected hosts remain unverified. I have not established that the whole Compose fleet is on its latest releases.
