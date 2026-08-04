# Step 5 Route and Restart Verification

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Capture date:** 2026-07-22 EDT; exact timestamp not retained  
**Mechanism:** Windows PowerShell Internal-zone client, SSH Manager target `docker_network`, Cloudflare DNS-over-HTTPS

## DNS

The exact timestamp, expanded domain-array source, and complete per-query `Resolve-DnsName` objects weren't retained outside the task transcript. For each of the 19 names I ran:

```powershell
Resolve-DnsName -Name $domain -Type A -Server 192.168.40.1 -DnsOnly
```

All 19 results returned only `192.168.85.2`. The loop completed in 0.7 seconds with exit code 0.

## HTTP and HTTPS

For each name I ran:

```powershell
curl.exe --connect-timeout 10 --max-time 20 -sS -o NUL -w '%{http_code}' "http://$domain/"
curl.exe --connect-timeout 10 --max-time 20 -sS -o NUL -w '%{http_code}' "https://$domain/"
```

```text
jellyfin     301 302    seerr       301 307
sonarr       301 302    radarr      301 302
prowlarr     301 302    qbittorrent 301 200
semaphore    301 200    immich      301 200
booklore     301 200    termix      301 200
dashboard    301 200    forgejo     301 200
portainer    301 200    peanut      301 307
syncthing    301 200    wazuh       301 302
grafana      301 302    prometheus  301 302
splunk       301 303
```

Exit code: 0. Standard certificate validation remained enabled.

The TLS loop connected with .NET `SslStream`. Every row returned subject `CN=*.alphasecunited.com`, expiry `2026-10-08`, & thumbprint prefix `93C7598A8F3F`. The exact script and full output weren't retained outside the task transcript.

## Public DNS

For each name I ran:

```powershell
Invoke-RestMethod -Uri "https://cloudflare-dns.com/dns-query?name=$domain&type=A" -Headers @{accept='application/dns-json'}
```

All 19 responses returned status/Rcode 3 with no A answer. Exit code: 0. The complete response objects weren't retained outside the task transcript.

## NPM restart

```sh
docker restart nginx-proxy-manager
for attempt in 1 2 3 4 5 6 7 8 9 10
do
  state=$(docker inspect nginx-proxy-manager --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}')
  printf '%s\n' "$state"
  if printf '%s' "$state" | grep -q '^running healthy$'; then break; fi
  sleep 3
done
docker exec nginx-proxy-manager nginx -t
```

```text
nginx-proxy-manager
running starting
running starting
running healthy
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

Exit code: 0. The 19-name HTTPS loop returned the same application status codes after restart.

## Proxy errors and final health

```sh
find /opt/docker/nginx-proxy-manager/data/logs -maxdepth 1 -type f -name 'proxy-host-*_access.log' -mmin -10 -print0 | xargs -0 -r grep -hE ' 50[24] ' | wc -l
docker inspect nginx-proxy-manager --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}} {{.RestartCount}}'
```

```text
0
running healthy 0
```

Exit code: 0.
