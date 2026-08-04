# Step 2 Backend Compatibility Verification

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Capture date:** 2026-07-22 EDT; exact timestamp not retained  
**Mechanism:** SSH Manager  
**Shell:** Remote POSIX shell from each configured target

The original file-edit commands remain in the task transcript. These fresh post-change commands verify the resulting state.

## Media Stack

**Target:** `red_server`; CT 842

```sh
pct exec 842 -- sh -lc "grep -E 'JELLYFIN_PublishedServerUrl|KnownProxies|ServerDomains' /opt/media-stack/compose.yml /opt/media-stack/config/jellyfin/config/network.xml /opt/media-stack/config/qbittorrent/qBittorrent/qBittorrent.conf"
pct exec 842 -- sh -lc "sed -n '/<KnownProxies>/,/<\/KnownProxies>/p' /opt/media-stack/config/jellyfin/config/network.xml"
```

```text
/opt/media-stack/compose.yml:      JELLYFIN_PublishedServerUrl: https://jellyfin.alphasecunited.com
/opt/media-stack/config/jellyfin/config/network.xml:  <KnownProxies>
/opt/media-stack/config/jellyfin/config/network.xml:  </KnownProxies>
/opt/media-stack/config/qbittorrent/qBittorrent/qBittorrent.conf:WebUI\ServerDomains=qbittorrent.alphasecunited.com
  <KnownProxies>
    <string>192.168.85.2</string>
  </KnownProxies>
```

Exit code: 0.

## Semaphore

**Target:** `grey_server`; CT 100

```sh
pct exec 100 -- sh -lc "grep -E 'web_host' /root/config.json && systemctl is-active semaphore && curl -fsS -o /dev/null -w 'local_http=%{http_code}\n' http://127.0.0.1:3000/"
```

```text
  "web_host": "https://semaphore.alphasecunited.com"
active
local_http=200
```

Exit code: 0.

## Docker Main

**Target:** `docker_main`

```sh
grep -E '^(DOMAIN|ROOT_URL|SSH_DOMAIN)[[:space:]]*=' /opt/docker/forgejo/data/gitea/conf/app.ini
grep -E 'STGUIADDRESS' /opt/docker/syncthing/docker-compose.yml
ss -lntp | grep ':8384 '
docker inspect syncthing --format '{{.State.Status}} {{.State.Health.Status}}'
```

```text
DOMAIN = forgejo.alphasecunited.com
SSH_DOMAIN = 192.168.40.35
ROOT_URL = https://forgejo.alphasecunited.com/
      STGUIADDRESS: "0.0.0.0:8384"
LISTEN 0 4096 *:8384 *:* users:(("syncthing",pid=1349453,fd=47))
running healthy
```

Exit code: 0.

## Security Monitoring

**Target:** `security_01`

```sh
grep -E 'GF_SERVER_(DOMAIN|ROOT_URL|PROTOCOL)|web.external-url|GF_SECURITY_ADMIN_PASSWORD' /home/dkadi/monitoring/docker-compose.yml
curl --max-time 5 -fsS http://127.0.0.1:3000/api/health
curl --max-time 5 -fsS http://127.0.0.1:9090/-/healthy
```

```text
      - --web.external-url=https://prometheus.alphasecunited.com
      - GF_SERVER_DOMAIN=grafana.alphasecunited.com
      - GF_SERVER_ROOT_URL=https://grafana.alphasecunited.com
      - GF_SERVER_PROTOCOL=http
{
  "database": "ok",
  "version": "12.4.1",
  "commit": "46a02dc12a085445ab105b72fa159248f7d1dc9d"
}Prometheus Server is Healthy.
```

Exit code: 0. The grep output contains no `GF_SECURITY_ADMIN_PASSWORD` entry. The rotated administrator login returned HTTP 200 in a separate authenticated check; no credential value or storage location was captured.
