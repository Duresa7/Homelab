# Nginx Proxy Manager Operations Runbook

**Created:** 2026-07-11  
**Last updated:** 2026-07-18

## Scope

I operate Nginx Proxy Manager 2.15.1 on `docker-network`. I use SSH Manager MCP target `docker_network` for remote CLI work. The live Compose project is `/opt/docker/nginx-proxy-manager`.

## Routine Health Check

I run this on `docker_network`:

```sh
cd /opt/docker/nginx-proxy-manager
docker compose ps
docker inspect -f 'status={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} ip={{(index .NetworkSettings.Networks "proxy").IPAddress}} restart={{.HostConfig.RestartPolicy.Name}}' nginx-proxy-manager
curl -sS -o /dev/null -w 'admin_http=%{http_code}\n' http://127.0.0.1:81/
curl -sS -o /dev/null -w 'http_entry=%{http_code}\n' http://127.0.0.1/
curl -sS -o /dev/null -w 'netbird_https=%{http_code}\n' https://REDACTED_CUSTOM_DOMAIN_016/
```

Expected baseline:

- Container state is `running` and health is `healthy`.
- Address on `proxy` is `172.31.85.10`.
- Restart policy is `unless-stopped`.
- The administrator UI returns HTTP `200`.
- The NetBird HTTPS host returns a successful application response and presents the certificate expiring `2026-10-08 23:49:46 UTC`.

The UI is available internally at `http://192.168.85.2:81`. I use an approved credential from 1Password only after confirming it matches the current administrator account. The saved credential from an initial API-login attempt was stale and returned HTTP `400`; I do not rely on that record. Live administrator login works, and the stale password-manager record is outside this platform's scope. I never display or retain a password in evidence.

## Logs

```sh
cd /opt/docker/nginx-proxy-manager
docker compose logs --no-color --tail=200
docker compose logs --no-color --tail=200 nginx-proxy-manager
```

I retain the exact command, complete output, timestamp, target, and exit code when logs are evidence for a change or problem, and I redact credentials, API tokens, cookies, and private-key content.

The NPM container uses bounded Docker `json-file` logging with `max-size=10m` and `max-file=3`, verified on 2026-07-12.

## Start, Stop, and Restart

```sh
cd /opt/docker/nginx-proxy-manager
docker compose start
docker compose stop
docker compose restart
docker compose ps
```

After a restart I wait for `healthy`, test port 81, and test every configured proxy host. For NetBird I validate certificate presentation, Force SSL, the authenticated dashboard, and the generated OAuth2, WebSocket, management, signal, and gRPC routes. I validate peer-dependent traffic after a peer is enrolled.

## Recreate or Verify the NetBird Proxy Host

The current HTTPS proxy host is saved, Online, and validated. I use these settings to verify it or recreate it during recovery.

1. Confirm internal DNS resolves `REDACTED_CUSTOM_DOMAIN_016` to `192.168.85.2`.
2. Confirm the Cloudflare DNS-01 wildcard/apex certificate exists in NPM and has not expired.
3. Create a Proxy Host with:
   - domain `REDACTED_CUSTOM_DOMAIN_016`;
   - scheme `http`;
   - forward host `netbird-dashboard`;
   - forward port `80`;
   - Block Common Exploits enabled;
   - WebSockets Support enabled.
4. Save the basic host and verify its row exists before editing advanced settings.
5. Reopen the host and paste the contents of [netbird-advanced-config.conf](../Configuration/netbird-advanced-config.conf) into Advanced.
6. Assign the wildcard/apex certificate, enable Force SSL, and enable HTTP/2. Leave HSTS disabled unless a separate reviewed change enables it.
7. Save and verify HTTP-to-HTTPS redirection, certificate presentation, the authenticated dashboard, and the generated route configuration from an internal client.

The advanced configuration routes long-lived WebSocket, API/OAuth2, native signal, management, and gRPC requests to `netbird-server:80`. HTTP/2 is required for the gRPC route.

## Certificate Handling

I use the least-privilege, zone-scoped Cloudflare DNS Write token stored in 1Password as `REDACTED_1PASSWORD_ITEM_TITLE_002`. I never place the token in Git, visible shell arguments, screenshots, or retained command output.

I request one DNS-01 certificate covering:

```text
*.REDACTED_CUSTOM_DOMAIN_001
REDACTED_CUSTOM_DOMAIN_001
```

The active certificate covers both names and expires `2026-10-08 23:49:46 UTC`. It is assigned to `REDACTED_CUSTOM_DOMAIN_016` with Force SSL and HTTP/2 enabled. I verified the non-interactive `dns-cloudflare` renewal path with a successful Let's Encrypt staging dry-run on 2026-07-12. NPM's Node backend initializes an hourly timer and checks immediately at startup for certificates within 30 days of expiry.

After issuance or renewal I:

- inspect the names and expiry in NPM;
- assign it only to intended proxy hosts;
- validate the presented certificate from a client using UniFi DNS;
- verify a renewal test or observed automated renewal before considering certificate-lifecycle validation complete.

## Configuration Validation

```sh
cd /opt/docker/nginx-proxy-manager
docker compose config --quiet
docker network inspect proxy
docker exec nginx-proxy-manager nginx -t
```

I run `nginx -t` after changing an Advanced snippet and before treating the UI save as successful. Then I inspect the generated host state through the NPM UI and test the client path.

## Update Procedure

The Compose reference uses `latest`; pulling can change the deployed application. I treat every update as a bounded change:

1. Record the current NPM version and image digest.
2. Back up the live Compose file, `data/`, and `letsencrypt/` through protected storage.
3. Review NPM release notes and migration requirements.
4. Run `docker compose pull` and `docker compose up -d`.
5. Wait for `healthy`, run `nginx -t`, and validate the UI, certificates, renewal state, and every proxy host.
6. Record step evidence and update the deployment record.

Tracking `latest` is my intentional 2026-07-12 maintenance decision. I continue to record the before/after image identity and verification for every update.

## Backup and Restore

I back up these live items together:

- `/opt/docker/nginx-proxy-manager/docker-compose.yml`
- `/opt/docker/nginx-proxy-manager/data/`
- `/opt/docker/nginx-proxy-manager/letsencrypt/`

The data includes account information, host definitions, private keys, certificates, and ACME state. It is protected material and must not be committed or placed in unredacted evidence.

To restore I recover ownership and permissions, confirm `proxy` exists with subnet `172.31.85.0/24`, then run `docker compose up -d`. I validate health, `nginx -t`, administrator login, certificate inventory, renewal state, and each proxy host.

## Troubleshooting

See [Troubleshooting-Log.md](Troubleshooting-Log.md). I record all new failures chronologically, including exact errors, unsuccessful attempts, root cause or current hypothesis, correction, and observed verification.
