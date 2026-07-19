# S03-S05 Media Stack Refresh Verification Transcript

**Created:** 2026-07-17  
**Last updated:** 2026-07-18

**Capture timestamp:** 2026-07-17T21:25:24-04:00  
**Target:** `red_server`, Proxmox CT 842 `media-01`  
**Mechanism:** SSH Manager command execution; host shell invoking `pct exec`; guest POSIX shell  
**Guest working directory:** `/opt/media-stack`

The live Compose environment and application configuration contain secrets, so I did not print them. The VPN exit check retained only pass/fail status; I did not capture the provider address.

## Verification Request

```sh
pct exec 842 -- sh -lc 'cd /opt/media-stack; echo "container-state"; docker compose --profile vpn ps --format json | jq -s "map({Service,State,Health})"; echo "versions"; for c in jellyfin jellyseerr sonarr radarr prowlarr flaresolverr gluetun qbittorrent; do docker inspect "$c" --format "{{.Name}}|{{index .Config.Labels \"org.opencontainers.image.version\"}}|{{index .Config.Labels \"build_version\"}}"; done; echo "seerr-status"; wget -qO- http://127.0.0.1:5055/api/v1/status | jq "{version,updateAvailable,commitsBehind,restartRequired}"; echo "service-http"; for endpoint in 8096/System/Info/Public 5055/api/v1/status 8989/ping 7878/ping 9696/ping; do if wget -qO- "http://127.0.0.1:$endpoint" >/dev/null; then echo "$endpoint=passed"; else echo "$endpoint=failed"; fi; done; echo "vpn"; if docker exec gluetun sh -c '"'"'test -n "$(wget -qO- https://ipinfo.io/ip)"'"'"'; then echo exit-check=passed; else echo exit-check=failed; fi; echo "qbit"; docker exec gluetun wget -qO- http://127.0.0.1:8080/api/v2/app/preferences | jq "{excluded_file_names_enabled,pattern_count:(.excluded_file_names|split(\"\\n\")|length),has_exe:(.excluded_file_names|split(\"\\n\")|index(\"*.exe\")!=null),listen_port,upnp,autorun_enabled}"; printf "forwarded_port="; cat /opt/media-stack/config/gluetun/forwarded_port; echo; echo "torrents"; docker exec gluetun wget -qO- http://127.0.0.1:8080/api/v2/torrents/info | jq "length"'
```

## Result

- Exit code: `0`
- Standard error: empty
- Container state: all eight services `running`; Gluetun and Jellyfin `healthy`.
- Versions: Jellyfin 10.11.11; Seerr 3.3.0; Sonarr 4.0.19.2979-ls320; Radarr 6.3.0.10514-ls311; Prowlarr 2.4.0.5397-ls154; FlareSolverr 3.5.0; qBittorrent 5.2.3/libtorrent 2.0.13-ls468; Gluetun rolling `latest`.
- Seerr status: `updateAvailable=false`, `commitsBehind=0`, `restartRequired=false`.
- Jellyfin, Seerr, Sonarr, Radarr, and Prowlarr HTTP checks: `passed`.
- VPN exit lookup from the Gluetun namespace: `passed`; I deliberately did not retain the address.
- qBittorrent at capture: filtering enabled; `*.exe` present; UPnP disabled; autorun disabled; listening port equal to the Proton forwarded-port file; torrent count `0`.

Complete standard output:

```text
container-state
[
  {"Service":"flaresolverr","State":"running","Health":""},
  {"Service":"gluetun","State":"running","Health":"healthy"},
  {"Service":"jellyfin","State":"running","Health":"healthy"},
  {"Service":"jellyseerr","State":"running","Health":""},
  {"Service":"prowlarr","State":"running","Health":""},
  {"Service":"qbittorrent","State":"running","Health":""},
  {"Service":"radarr","State":"running","Health":""},
  {"Service":"sonarr","State":"running","Health":""}
]
versions
/jellyfin|10.11.11|
/jellyseerr|v3.3.0|
/sonarr|4.0.19.2979-ls320|Linuxserver.io version:- 4.0.19.2979-ls320 Build-date:- 2026-07-18T00:16:13+00:00
/radarr|6.3.0.10514-ls311|Linuxserver.io version:- 6.3.0.10514-ls311 Build-date:- 2026-07-12T19:55:20+00:00
/prowlarr|2.4.0.5397-ls154|Linuxserver.io version:- 2.4.0.5397-ls154 Build-date:- 2026-07-15T05:59:18+00:00
/flaresolverr|v3.5.0|
/gluetun|latest|
/qbittorrent|5.2.3_v2.0.13-ls468|Linuxserver.io version:- 5.2.3_v2.0.13-ls468 Build-date:- 2026-07-12T08:56:33+00:00
seerr-status
{"version":"3.3.0","updateAvailable":false,"commitsBehind":0,"restartRequired":false}
service-http
8096/System/Info/Public=passed
5055/api/v1/status=passed
8989/ping=passed
7878/ping=passed
9696/ping=passed
vpn
exit-check=passed
qbit
{"excluded_file_names_enabled":true,"pattern_count":73,"has_exe":true,"listen_port":58104,"upnp":false,"autorun_enabled":false}
forwarded_port=58104
torrents
0
```

My initial capture occurred while the filter list contained 73 patterns. I then reconciled the final researched baseline to 100 patterns. A subsequent API read returned:

```json
{
  "excluded_file_names_enabled": true,
  "pattern_count": 100,
  "has_exe": true,
  "has_docm": true
}
```

That follow-up request exited `0` with empty standard error. The exact 100-pattern list is in the [research record](../../../Documentation/Download%20Payload%20Filtering%20Research%20-%202026-07-17.md).

## Persistence Verification

I restarted qBittorrent once more after the final 100-pattern reconciliation:

```sh
pct exec 842 -- sh -lc 'cd /opt/media-stack && docker compose --profile vpn restart qbittorrent >/dev/null; for i in 1 2 3 4 5 6; do prefs=$(docker exec gluetun wget -qO- http://127.0.0.1:8080/api/v2/app/preferences 2>/dev/null) && break; sleep 2; done; printf "%s" "$prefs" | jq "{excluded_file_names_enabled,pattern_count:(.excluded_file_names|split(\"\\n\")|length),has_exe:(.excluded_file_names|split(\"\\n\")|index(\"*.exe\")!=null),has_docm:(.excluded_file_names|split(\"\\n\")|index(\"*.docm\")!=null),listen_port,upnp,autorun_enabled}"; printf "forwarded_port="; cat /opt/media-stack/config/gluetun/forwarded_port; echo; docker ps --filter name=qbittorrent --format "state={{.State}} status={{.Status}}"'
```

Observed output after the restart:

```text
{
  "excluded_file_names_enabled": true,
  "pattern_count": 100,
  "has_exe": true,
  "has_docm": true,
  "listen_port": 58104,
  "upnp": false,
  "autorun_enabled": false
}
forwarded_port=58104
state=running status=Up 2 seconds
```

The command exited `0`. Complete standard error contained only Compose progress:

```text
Container qbittorrent Restarting
Container qbittorrent Started
```

## Arr-to-qBittorrent Connectivity

I checked the post-refresh containers from their own network namespaces without reading or printing stored API keys or passwords:

```sh
pct exec 842 -- sh -lc 'for c in sonarr radarr; do if docker exec "$c" curl -fsS http://gluetun:8080/api/v2/app/version >/dev/null; then echo "$c-to-qbittorrent=passed"; else echo "$c-to-qbittorrent=failed"; exit 1; fi; done'
```

Complete standard output:

```text
sonarr-to-qbittorrent=passed
radarr-to-qbittorrent=passed
```

Standard error: empty  
Exit code: `0`
