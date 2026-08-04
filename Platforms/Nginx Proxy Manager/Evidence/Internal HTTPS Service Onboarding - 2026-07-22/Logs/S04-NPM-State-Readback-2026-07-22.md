# Step 4 NPM State Readback

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Capture date:** 2026-07-22 EDT; exact timestamp not retained  
**Mechanism:** Authenticated NPM 2.15.1 browser session and SSH Manager target `docker_network`

No pre-change browser screenshot or complete pre-change query transcript was retained. The observed SQLite baseline returned one active proxy host: ID 1, `netbird.alphasecunited.com`, upstream `http://netbird-dashboard:80`, certificate ID 1, Force SSL, HTTP/2, exploit blocking, WebSockets, & enabled.

The authenticated UI path was `Hosts > Proxy Hosts > Add Proxy Host`. I entered each documented domain, upstream scheme, host, and port; enabled Block Common Exploits and WebSockets; selected the existing wildcard certificate; enabled Force SSL and HTTP/2; and saved. I added Immich's recorded Advanced snippet under Settings. The three S04 screenshots show the resulting 20-row inventory with every row Online.

Fresh database readback used:

```sh
docker exec nginx-proxy-manager node -e "const Database=require('better-sqlite3');const db=new Database('/data/database.sqlite',{readonly:true});console.log(JSON.stringify(db.prepare('SELECT id, domain_names, forward_scheme, forward_host, forward_port, certificate_id, ssl_forced, http2_support, block_exploits, allow_websocket_upgrade, enabled FROM proxy_host WHERE is_deleted=0 ORDER BY id').all(),null,2))"
```

Exit code: 0. It returned 20 rows. IDs 2 through 20 match the 19 services in `Configuration/internal-proxy-hosts.md`; every row has certificate ID 1 and all five Boolean controls set to 1. The complete 20-row JSON output wasn't retained outside the task transcript.

Immich readback used:

```sh
docker exec nginx-proxy-manager node -e "const Database=require('better-sqlite3');const db=new Database('/data/database.sqlite',{readonly:true});console.log(db.prepare('SELECT advanced_config FROM proxy_host WHERE id=9').get().advanced_config)"
```

```text
client_max_body_size 50000M;
proxy_request_buffering off;
client_body_buffer_size 1024k;
proxy_read_timeout 600s;
proxy_send_timeout 600s;
send_timeout 600s;
```

Exit code: 0.
