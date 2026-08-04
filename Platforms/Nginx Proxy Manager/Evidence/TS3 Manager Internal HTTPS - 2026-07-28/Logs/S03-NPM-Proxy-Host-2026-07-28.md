# Step 3 NPM Proxy Host

**Created:** 2026-07-28  
**Last updated:** 2026-08-04

**Capture time:** 2026-07-28 09:55 EDT  
**Target:** Nginx Proxy Manager 2.15.1 on `docker-network`  
**Mechanism:** Local PowerShell to the NPM API; SSH Manager verification

## API request

I used `<REDACTED_PASSWORD_MANAGER>` references for the NPM email and password, posted them to `/api/tokens`, held the bearer token in a PowerShell variable, & cleared all three variables when the request finished. The password and token were not printed.

Sanitized request:

```text
POST /api/nginx/proxy-hosts
domain_names=["ts3-manager.alphasecunited.com"]
forward_scheme=http
forward_host=192.168.80.118
forward_port=9000
access_list_id=0
certificate_id=1
ssl_forced=true
http2_support=true
block_exploits=true
allow_websocket_upgrade=true
hsts_enabled=false
```

Response:

```text
id=22
enabled=true
```

## Route verification

```text
generated=present
nginx configuration syntax=successful
http=301 https://ts3-manager.alphasecunited.com/
https=200
certificate subject=CN=*.alphasecunited.com
certificate expiry=2026-10-08 23:49:46 UTC
```

## Restart verification

I restarted only `nginx-proxy-manager` and waited for its health check.

```text
health=healthy
status=running
restart=unless-stopped
admin=200
ts3_http=301
ts3_https=200
nginx configuration syntax=successful
```
