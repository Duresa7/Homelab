# Step 1 Preflight and Backup Removal

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Capture time:** 2026-07-28 09:55 EDT  
**Targets:** `alpha-prod-01`, `docker-network`  
**Mechanism:** SSH Manager; Linux shell; NPM SQLite read-only query

## Preflight

Commands issued:

```sh
ss -lntH
docker ps --format '{{.Names}}\t{{.Ports}}'
curl -sS -o /dev/null -D - --max-time 5 http://127.0.0.1:9000/
```

Observed result:

```text
0.0.0.0:9000
ts3-manager  0.0.0.0:9000->8080/tcp
HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8
Content-Length: 9706
```

The read-only NPM query returned 19 enabled proxy hosts and no `ts3-manager.alphasecunited.com` row. UniFi returned no matching DNS record and no NPM policy to `192.168.80.118:9000`. A TCP probe from `docker-network` timed out.

## Backup removal

I created one transaction-consistent, mode-0600 NPM SQLite copy during the change. At the owner's request I deleted the exact 126,976-byte file and its empty directory:

```text
/opt/docker/nginx-proxy-manager/backups/ts3-manager-internal-https-2026-07-28-prechange/database.sqlite
/opt/docker/nginx-proxy-manager/backups/ts3-manager-internal-https-2026-07-28-prechange
```

The deletion command used exact paths with `os.unlink()` and `os.rmdir()`. It did not use a recursive target or wildcard. No NPM backup from this change remains.
