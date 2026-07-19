# Media Stack Operations Runbook

**Created:** 2026-07-17  
**Last updated:** 2026-07-18

## Scope and Access

I operate the LXC through the SSH Manager target `red_server`. The live Compose project is `/opt/media-stack` inside CT 842. I never print, copy, or commit the live `.env`, application XML files containing API keys, WireGuard configuration, or qBittorrent credentials.

Enter a guest shell when interactive work is necessary:

```sh
pct enter 842
```

I prefer bounded commands through `pct exec 842 -- ...` for repeatable checks.

## Routine Health Check

```sh
pct status 842
pct exec 842 -- sh -lc 'cd /opt/media-stack && docker compose --profile vpn ps'
pct exec 842 -- sh -lc 'df -h / /data'
pct exec 842 -- sh -lc 'test "$(docker inspect -f "{{.State.Health.Status}}" gluetun)" = healthy'
pct exec 842 -- sh -lc 'test "$(docker inspect -f "{{.State.Health.Status}}" jellyfin)" = healthy'
```

Expected baseline:

- CT 842 is running.
- Eight containers are running; Gluetun and Jellyfin report healthy.
- The root/data filesystem has sufficient free space.
- qBittorrent's Docker network mode is `container:<gluetun-container-id>`.

Service URLs use the guest address:

```text
Jellyfin     http://192.168.40.42:8096
Seerr        http://192.168.40.42:5055
Sonarr       http://192.168.40.42:8989
Radarr       http://192.168.40.42:7878
Prowlarr     http://192.168.40.42:9696
qBittorrent  http://192.168.40.42:8080
```

## Start, Stop, and Restart

Start or reconcile the complete stack:

```sh
pct exec 842 -- sh -lc 'cd /opt/media-stack && docker compose --profile vpn up -d'
```

Stop the complete stack:

```sh
pct exec 842 -- sh -lc 'cd /opt/media-stack && docker compose --profile vpn down'
```

Restart an ordinary application by name. For the download path, I restart Gluetun and qBittorrent together so dependency ordering and port synchronization are reapplied:

```sh
pct exec 842 -- sh -lc 'cd /opt/media-stack && docker compose --profile vpn up -d --force-recreate gluetun qbittorrent'
```

I never remove `network_mode: service:gluetun` from qBittorrent as a troubleshooting shortcut.

## VPN and Port-Forward Verification

Confirm the provider exit from the shared network namespace without retaining the live address in repository evidence:

```sh
pct exec 842 -- docker exec gluetun wget -qO- https://ipinfo.io/ip
```

Compare Gluetun's active port file with qBittorrent's `listen_port` API preference. Also confirm `random_port=false` and `upnp=false`. The assigned number is ephemeral and I do not document it.

If the port is stale after a reconnect, recreate Gluetun and qBittorrent together, then repeat the comparison. Do not add a UniFi gateway port forward.

## Updates

All images intentionally track `latest`. I treat every pull as a bounded change:

1. Record current image IDs and application versions without capturing secrets.
2. Confirm protected backups exist for `/opt/media-stack/config` and `/data`.
3. Pull and recreate the stack.
4. Verify container health, Jellyfin hardware acceleration, Proton exit, forwarded-port synchronization, management UIs, and Arr download-client tests.

```sh
pct exec 842 -- sh -lc 'cd /opt/media-stack && docker compose --profile vpn pull'
pct exec 842 -- sh -lc 'cd /opt/media-stack && docker compose --profile vpn up -d --force-recreate'
```

The Seerr container retains the Compose service and container name `jellyseerr` for migration compatibility, but its image is `ghcr.io/seerr-team/seerr:latest`. I do not switch it back to the retired `fallenbagel/jellyseerr` image.

## Download Payload Filter

qBittorrent's **Excluded file names** option is enabled with the 100-pattern baseline in my [payload-filtering research](Download%20Payload%20Filtering%20Research%20-%202026-07-17.md). The list rejects common executable, installer, script, shortcut, macro-enabled document, driver, and loadable-library suffixes while preserving media, subtitles, archives, and disc images.

Verify the setting through the local qBittorrent API from Gluetun's shared namespace:

```sh
pct exec 842 -- sh -lc 'docker exec gluetun wget -qO- http://127.0.0.1:8080/api/v2/app/preferences | jq "{excluded_file_names_enabled,pattern_count:(.excluded_file_names|split(\"\\n\")|length),autorun_enabled}"'
```

Expected values are `excluded_file_names_enabled=true`, `pattern_count=100`, and `autorun_enabled=false`. The filter applies to newly added torrents; changing it does not retroactively rewrite file priorities for an existing queue. I do not add archive or disc-image patterns without first deciding to reject those release formats.

## Backup and Restore

Back up these paths through the approved protected backup mechanism:

- `/opt/media-stack/compose.yml`
- `/opt/media-stack/.env`
- `/opt/media-stack/config`
- `/data`

The `.env` and application configuration contain secrets. They must not enter Git, screenshots, ordinary evidence transcripts, or unencrypted general-purpose storage.

Restore the files with their original ownership and modes, validate with `docker compose --profile vpn config --quiet`, and start the complete profile. Verify the kill switch and provider-side port before enabling acquisition.

## Credential Recovery

Retrieve the qBittorrent login from approved secret storage. I never reset the credential by placing plaintext in Compose, shell arguments, documentation, or evidence.

## Escalation

Record new operational faults chronologically in [Troubleshooting-Log.md](Troubleshooting-Log.md). Create a security incident under `Security/Incidents/` if VPN traffic leaks, credentials are exposed, or availability/security impact becomes material.
