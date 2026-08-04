# S03 NPM Host and Route Verification

**Created:** 2026-07-28  
**Last updated:** 2026-08-04

**Captured:** 2026-07-28 23:44-23:45 EDT  
**Targets:** NPM 2.15.1 on `docker-network` and an Internal-zone Windows client  
**Mechanism:** NPM API, SSH Manager MCP, & PowerShell

I read the administrator email and password through `<REDACTED_PASSWORD_MANAGER>` references, posted them to `/api/tokens`, then posted the proxy-host request with the bearer token. Neither secret appeared in output or a file.

NPM returned proxy host ID `23`, domain `kasm.alphasecunited.com`, upstream `https://192.168.78.10:443`, certificate ID 1, Force SSL enabled, WebSocket support enabled, & host enabled.

Verification:

```text
Resolve-DnsName: 192.168.85.2
HTTP: 301 to the HTTPS name
HTTPS: 200
TLS verification: 0
Health endpoint: {"ok": true}
Generated file: data/nginx/proxy_host/23.conf
nginx -t: successful
Cloudflare public DNS: NXDOMAIN
UniFi port forwards: 0
```
