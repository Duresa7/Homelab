# Media Stack Operations Runbook

**Created:** 2026-07-17  
**Last updated:** 2026-07-22

## Scope and Access

I operate the LXC through the SSH Manager target `red_server`. The live Compose project is `/opt/media-stack` inside CT 842, & Compose loads deployment-specific values from `/opt/media-stack/.env`.

Enter a guest shell when interactive work is necessary:

```sh
pct enter 842
```

I prefer bounded commands through `pct exec 842 -- ...` for repeatable checks.

## Routine Health Check

```sh
pct status 842
pct config 842 | grep '^mp0:'
findmnt -T /mnt/bindmounts/media-01-hdd/data
pct exec 842 -- sh -lc 'cd /opt/media-stack && docker compose --profile vpn ps'
pct exec 842 -- sh -lc 'findmnt -T /data && df -hT / /data'
pct exec 842 -- sh -lc 'test "$(docker inspect -f "{{.State.Health.Status}}" gluetun)" = healthy'
pct exec 842 -- sh -lc 'test "$(docker inspect -f "{{.State.Health.Status}}" jellyfin)" = healthy'
```

Expected baseline:

- CT 842 is running.
- Eight containers are running; Gluetun and Jellyfin report healthy.
- `/` is the 100 GiB NVMe-backed root; `/data` is the 916 GiB ext4 HDD filesystem.
- CT 842 `mp0` maps `/mnt/bindmounts/media-01-hdd/data` to `/data` with `backup=0`.
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

1. Record current image IDs and application versions.
2. Confirm a current backup exists for `/opt/media-stack/config`; `/data` is replaceable media & isn't backed up.
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

Back up these paths before changing the stack:

- `/opt/media-stack/compose.yml`
- `/opt/media-stack/.env`
- `/opt/media-stack/config`

`/data` is a host bind mount with `backup=0`, so Proxmox `vzdump` doesn't include movies, television, downloads, or transcodes. I rebuild that filesystem on replacement storage & acquire the media again after a disk loss.

Restore the files with their original ownership and modes, validate with `docker compose --profile vpn config --quiet`, and start the complete profile. Verify the kill switch and provider-side port before enabling acquisition.

## HDD Mount Failure

CT 842 refuses startup when `/mnt/bindmounts/media-01-hdd/data` is absent. Check the disk, UUID, ext4 state, mount units, & bind source before retrying:

```sh
MEDIA_DATA_DISK=/dev/disk/by-id/ata-ST1000LM035-1RK172_WCB0SRHK
MEDIA_DATA_MOUNT=/mnt/bindmounts/media-01-hdd
MEDIA_DATA_MOUNT_UNIT="$(systemd-escape --path --suffix=mount "$MEDIA_DATA_MOUNT")"
MEDIA_DATA_AUTOMOUNT_UNIT="$(systemd-escape --path --suffix=automount "$MEDIA_DATA_MOUNT")"
lsblk -f "$MEDIA_DATA_DISK"
smartctl -H -A "$MEDIA_DATA_DISK"
grep -F "$MEDIA_DATA_MOUNT" /etc/fstab
findmnt -T "$MEDIA_DATA_MOUNT/data"
systemctl status "$MEDIA_DATA_MOUNT_UNIT" "$MEDIA_DATA_AUTOMOUNT_UNIT"
```

Do not create `/mnt/bindmounts/media-01-hdd/data` on the NVMe-backed host directory. That child belongs on the mounted HDD; creating it underneath the absent mount defeats the startup guard.

## qBittorrent Login

Use `<YOUR_QBITTORRENT_USERNAME>` & `<YOUR_QBITTORRENT_PASSWORD>` when rebuilding the Web UI login, then rerun the Sonarr and Radarr download-client tests.

## Recording a Failure

Create one dated file per new operational fault under [Troubleshooting](Troubleshooting/README.md), then add it to the folder index. Create a security incident under `Security/Incidents/` if VPN traffic leaks, credentials are exposed, or availability/security impact becomes material.
