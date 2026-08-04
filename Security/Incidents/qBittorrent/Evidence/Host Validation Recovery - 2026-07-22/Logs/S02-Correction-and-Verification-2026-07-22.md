# Step 2 Correction and Verification

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Incident ID:** ASU-QBIT-20260722-001

**Correction saved:** 2026-07-22 20:49:22 EDT  
**Final verification:** 2026-07-22 20:53:48 EDT  
**Mechanism:** SSH Manager to `red_server`, then `pct exec 842` into `media-01`  
**Working directory:** SSH Manager configured default

## Correction

```text
Command:
pct exec 842 -- docker exec radarr curl -sS -o /dev/null -w 'set_preferences_status=%{http_code}\n' -H 'Host: qbittorrent.alphasecunited.com' --data 'json=%7B%22web_ui_domain_list%22%3A%22qbittorrent.alphasecunited.com%3Bgluetun%3B192.168.40.42%22%7D' http://gluetun:8080/api/v2/app/setPreferences

stdout:
set_preferences_status=200
stderr: empty
exit code: 0
```

No backup or temporary file was created.

The safe preferences readback confirmed the new list without weakening the controls around it:

```text
Command:
pct exec 842 -- sh -lc "docker exec radarr curl -sS -H 'Host: qbittorrent.alphasecunited.com' http://gluetun:8080/api/v2/app/preferences | jq '{web_ui_domain_list,web_ui_host_header_validation_enabled,bypass_auth_subnet_whitelist_enabled,bypass_auth_subnet_whitelist}'"

stdout:
{
  "web_ui_domain_list": "qbittorrent.alphasecunited.com;gluetun;192.168.40.42",
  "web_ui_host_header_validation_enabled": true,
  "bypass_auth_subnet_whitelist_enabled": true,
  "bypass_auth_subnet_whitelist": "127.0.0.1/32\n172.18.0.0/16"
}
stderr: empty
exit code: 0
```

## Regression Check

```text
Readback:
WebUI\ServerDomains="qbittorrent.alphasecunited.com;gluetun;192.168.40.42"

Radarr:
attempt=1 status=200 total=0.001944s
attempt=2 status=200 total=0.001934s
attempt=3 status=200 total=0.001806s

Sonarr:
attempt=1 status=200 total=0.002278s
attempt=2 status=200 total=0.001927s
attempt=3 status=200 total=0.001886s
```

The readback and all six checks returned exit code 0.

## Saved-Client and Route Checks

```text
radarr_testall_status=200
sonarr_testall_status=200
direct_ip_root_status=200
npm_https_root_status=200 verify=0
radarr_health=[]
sonarr_health=[]
```

The API keys were read inside their respective containers, passed only in request headers, & weren't printed or retained.

## VPN Topology

```text
gluetun status=running health=healthy id=40cd4e3e0e2624ca1816b5c825ce9182a1d63cf64d8fdf551ca703870ccd3ffb
qbittorrent status=running network_mode=container:40cd4e3e0e2624ca1816b5c825ce9182a1d63cf64d8fdf551ca703870ccd3ffb
listen_port=51342
upnp=false
forwarded_port=51342
```

## Post-Correction Logs

```text
Command boundary:
docker logs --since 2026-07-22T20:49:23-04:00

radarr_post_fix_connection_errors=0
sonarr_post_fix_connection_errors=0
```

## Final Audit

```text
Command:
date -Is; pct exec 842 -- docker exec qbittorrent sh -lc "grep -E '^WebUI\\\\ServerDomains=' /config/qBittorrent/qBittorrent.conf"; pct exec 842 -- docker exec radarr sh -lc 'for i in 1 2 3; do curl -sS -o /dev/null -w "radarr_api_$i=%{http_code}\n" http://gluetun:8080/api/v2/app/version; done; key=$(sed -n "s:.*<ApiKey>\(.*\)</ApiKey>.*:\1:p" /config/config.xml); curl -sS -o /dev/null -w "radarr_testall=%{http_code}\n" -X POST -H "X-Api-Key: $key" http://127.0.0.1:7878/api/v3/downloadclient/testall; printf "radarr_health="; curl -sS -H "X-Api-Key: $key" http://127.0.0.1:7878/api/v3/health; printf "\n"'; pct exec 842 -- docker exec sonarr sh -lc 'for i in 1 2 3; do curl -sS -o /dev/null -w "sonarr_api_$i=%{http_code}\n" http://gluetun:8080/api/v2/app/version; done; key=$(sed -n "s:.*<ApiKey>\(.*\)</ApiKey>.*:\1:p" /config/config.xml); curl -sS -o /dev/null -w "sonarr_testall=%{http_code}\n" -X POST -H "X-Api-Key: $key" http://127.0.0.1:8989/api/v3/downloadclient/testall; printf "sonarr_health="; curl -sS -H "X-Api-Key: $key" http://127.0.0.1:8989/api/v3/health; printf "\n"'; pct exec 842 -- sh -lc "curl -sS -o /dev/null -w 'direct_ip_root=%{http_code}\n' http://192.168.40.42:8080/; curl -sS --resolve qbittorrent.alphasecunited.com:443:192.168.85.2 -o /dev/null -w 'npm_https_root=%{http_code} tls_verify=%{ssl_verify_result}\n' https://qbittorrent.alphasecunited.com/; docker inspect gluetun --format 'gluetun={{.State.Status}} health={{.State.Health.Status}} id={{.Id}}'; docker inspect qbittorrent --format 'qbittorrent={{.State.Status}} network_mode={{.HostConfig.NetworkMode}}'; docker exec radarr curl -sS -H 'Host: qbittorrent.alphasecunited.com' http://gluetun:8080/api/v2/app/preferences | jq -r '\"listen_port=\(.listen_port) upnp=\(.upnp)\"'; printf 'forwarded_port='; cat /opt/media-stack/config/gluetun/forwarded_port; printf '\nradarr_post_fix_errors='; docker logs --since 2026-07-22T20:49:23-04:00 radarr 2>&1 | grep -Ec 'Failed to connect to qBittorrent|Unable to test qBittorrent' || true; printf 'sonarr_post_fix_errors='; docker logs --since 2026-07-22T20:49:23-04:00 sonarr 2>&1 | grep -Ec 'Failed to connect to qBittorrent|Unable to test qBittorrent' || true"

stdout:
2026-07-22T20:53:48-04:00
WebUI\ServerDomains="qbittorrent.alphasecunited.com;gluetun;192.168.40.42"
radarr_api_1=200
radarr_api_2=200
radarr_api_3=200
radarr_testall=200
radarr_health=[]
sonarr_api_1=200
sonarr_api_2=200
sonarr_api_3=200
sonarr_testall=200
sonarr_health=[]
direct_ip_root=200
npm_https_root=200 tls_verify=0
gluetun=running health=healthy id=40cd4e3e0e2624ca1816b5c825ce9182a1d63cf64d8fdf551ca703870ccd3ffb
qbittorrent=running network_mode=container:40cd4e3e0e2624ca1816b5c825ce9182a1d63cf64d8fdf551ca703870ccd3ffb
listen_port=51342 upnp=false
forwarded_port=51342
radarr_post_fix_errors=0
sonarr_post_fix_errors=0
stderr: empty
exit code: 0
```

One earlier combined read-only verification exited 1 because the Docker template assumed every container had a health object and the first forwarded-port path was wrong. The separate container templates and configured `/gluetun/forwarded_port` path produced the results above; no service or setting changed during that correction.
