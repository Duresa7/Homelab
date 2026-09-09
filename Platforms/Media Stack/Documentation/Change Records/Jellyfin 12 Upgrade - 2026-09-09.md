# Jellyfin 12 Upgrade

**Created:** 2026-09-09  
**Last updated:** 2026-09-09

I updated Jellyfin on `media-01`, CT 842 on `red-server`, from 10.11.11 to 12.0.0 using its configured `jellyfin/jellyfin:latest` image.

## Change

I validated the live Compose configuration in `/opt/media-stack`, confirmed Jellyfin was healthy, and checked free space: 79 GiB on the root filesystem and 394 GiB on `/data`. I ran these commands through SSH Manager target `red_server`:

```sh
pct exec 842 -- sh -lc 'cd /opt/media-stack && docker compose pull jellyfin'
pct exec 842 -- sh -lc 'cd /opt/media-stack && docker compose up -d --no-deps jellyfin'
```

Both operations succeeded. The former image ID was `sha256:aefb67e6a7ff1debdd154a78a7bbb780fd0c873d8639210a7f6a2016ad2b35db`. The pulled and running image ID is `sha256:baba630419915985442f315f08b0cf46d9f4c8a0cc4bd38e94a6d35751dd5ef5`, also returned as the repository digest.

Initial startup reset the encoding configuration after rejecting the old empty encoder preset. I restored the documented QSV settings while Jellyfin was stopped, retained the valid `auto` preset, and started it again. The [encoding configuration repair](../Troubleshooting/Jellyfin%2012%20Encoding%20Configuration%20Reset%20-%202026-09-09.md) records the cause and checks.

I created no snapshot or backup, following the current workspace policy. I made no Compose definition change. Other containers retained their existing uptimes.

## Verification

After the repair, I observed:

- `/System/Info/Public` reported version `12.0.0`, server `Jelly-Media`, and completed setup.
- Docker reported Jellyfin healthy. Logs from the final start contained `Startup complete` and zero error or fatal entries.
- Both `https://jellyfin.alphasecunited.com/web/` and `https://jellyfin.alphasecunited.com/Moonfin/Web/` returned HTTP 200.
- A two-second 1280×720, 30 fps synthetic H.264 encode using `h264_qsv` and `/dev/dri/renderD128` exited 0. Intel iHD initialized successfully.
- Startup loaded AniList 13.0.0.0 and Moonbase 2.2.0.0.
- All eight media services remained running; Gluetun remained healthy.

I retained no separate terminal capture for the preflight, pull, recreation, repair, or verification; these results come from live SSH Manager responses. The pull progress response was truncated, but its exit code was 0 and the new image was verified in the running container.

Actual client playback, HDR tone mapping, and authenticated Seerr single sign-on were not exercised during this update.
