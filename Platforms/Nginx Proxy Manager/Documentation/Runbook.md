# Nginx Proxy Manager Operations Runbook

**Created:** 2026-07-11  
**Last updated:** 2026-09-25

## Scope

I operate Nginx Proxy Manager 2.15.1 on `docker-network` through SSH Manager target `docker_network`. The live Compose project is `/opt/docker/nginx-proxy-manager`.

## Routine Health Check

I run this on `docker_network`:

```sh
cd /opt/docker/nginx-proxy-manager
docker compose ps
docker inspect -f 'status={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} ip={{(index .NetworkSettings.Networks "proxy").IPAddress}} restart={{.HostConfig.RestartPolicy.Name}}' nginx-proxy-manager
curl -sS -o /dev/null -w 'admin_http=%{http_code}\n' http://127.0.0.1:81/
curl -sS -o /dev/null -w 'http_entry=%{http_code}\n' http://127.0.0.1/
curl -sS -o /dev/null -w 'netbird_https=%{http_code}\n' https://netbird.alphasecunited.com/
docker exec nginx-proxy-manager nginx -t
```

Expected baseline:

- Container state is `running` and health is `healthy`.
- Address on `proxy` is `172.31.85.10`.
- Restart policy is `unless-stopped`.
- Label `dockhand.update` is `false`, and the image is a pinned version tag rather than `latest`.
- The administrator UI returns HTTP `200`.
- The NetBird HTTPS host returns a successful application response and presents the wildcard certificate (on 2026-09-24 it expired 2026-12-08 at 3:03 AM UTC).
- Each host in the [internal proxy inventory](../Configuration/internal-proxy-hosts.md) returns 200 or an expected application redirect. None returns 502 or 504.

The UI is available internally at `http://192.168.85.2:81`. Live administrator login works. I retrieve the `email` and `password` fields from the standard application account item through the repository's credential workflow. NPM uses that email as its login identity. The [service-login standardization record](../../../Operations/Maintenance/Service%20Login%20Password%20Standardization%20-%202026-09-04.md) documents this shared source. I keep the email, password, and short-lived API token out of shell output and files. `POST /api/tokens` authenticated on 2026-09-05 and the API created Open WebUI proxy host 28. The API is a supported path for scripted host changes; the browser stays the path for certificate work.

## Logs

```sh
cd /opt/docker/nginx-proxy-manager
docker compose logs --no-color --tail=200
docker compose logs --no-color --tail=200 nginx-proxy-manager
```

I retain the exact command, complete output, timestamp, target, and exit code when logs support a change or problem.

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

For the internal application set I also verify that UniFi resolves every name to `192.168.85.2`, HTTP redirects to HTTPS, the wildcard certificate validates, and Cloudflare's public resolver returns NXDOMAIN. I keep the administrator UI at `http://192.168.85.2:81`.

## Internal Application Hosts

The [internal proxy-host inventory](../Configuration/internal-proxy-hosts.md) is the current mapping of names, schemes, upstreams, ports, and application-specific settings. When I add or change one host I update that inventory, the UniFi local-DNS record, and the narrow NPM-to-backend firewall policy together.

I don't add database, Redis, exporter, agent, SSH, HEC, syslog, or synchronization ports to NPM. Direct IP-and-port access remains the rollback path.

## Recreate or Verify the NetBird Proxy Host

The current HTTPS proxy host is saved, Online, and validated. I use these settings to verify it or recreate it during recovery.

1. Confirm internal DNS resolves `netbird.alphasecunited.com` to `192.168.85.2`.
2. Confirm the Cloudflare DNS-01 wildcard/apex certificate exists in NPM and has not expired.
3. Create a Proxy Host with:
   - domain `netbird.alphasecunited.com`;
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

I request one DNS-01 certificate covering:

```text
*.alphasecunited.com
alphasecunited.com
```

The active certificate is ID 1. It covers both names and renews automatically; on 2026-09-24 it expired 2026-12-08 at 3:03 AM UTC. Every live proxy host uses it with Force SSL and HTTP/2 enabled. I verified the non-interactive `dns-cloudflare` renewal path with a successful Let's Encrypt staging dry-run on 2026-07-12. NPM's Node backend initializes an hourly timer and checks immediately at startup for certificates within 30 days of expiry.

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

Since 2026-09-25 the Compose file pins `jc21/nginx-proxy-manager:2.15.1` and carries `dockhand.update: "false"`, so Dockhand never updates NPM. Dockhand's own connection runs through NPM, and a Dockhand-driven update stranded the proxy on 2026-09-25 ([incident](../../../Security/Incidents/Nginx%20Proxy%20Manager/Scheduled%20Update%20Stranded%20the%20Proxy%20-%202026-09-25.md)). I upgrade by hand from the host shell:

1. Record the current NPM version and image digest.
2. Copy the live Compose file, `data/`, and `letsencrypt/` aside on the host. Delete the copy once the upgrade is verified.
3. Review NPM release notes and migration requirements.
4. Change the pinned tag in the live Compose file and in Dockhand's imported definition on `docker-main`, then run `docker compose pull` and `docker compose up -d` from the host shell.
5. Wait for `healthy`, run `nginx -t`, and validate the UI, certificates, renewal state, and every proxy host.
6. Record step evidence and add a line to the README's Changes list.

From 2026-07-12 to 2026-09-25 NPM tracked `latest`. I record the before and after image identity and the verification for every update.

## State and Restore

I keep no standing backups; a rebuild from this runbook and the Compose reference is the recovery path. NPM's state is these three live items:

- `/opt/docker/nginx-proxy-manager/docker-compose.yml`
- `/opt/docker/nginx-proxy-manager/data/`
- `/opt/docker/nginx-proxy-manager/letsencrypt/`

When I restore from a pre-change copy, `data/` and `letsencrypt/` go back as a matched set because the database, certificates, and ACME state refer to one another.

To restore I recover ownership and permissions, confirm `proxy` exists with subnet `172.31.85.0/24`, then run `docker compose up -d`. I validate health, `nginx -t`, administrator login, certificate inventory, renewal state, and each proxy host.

## Troubleshooting

See the [troubleshooting index](Troubleshooting/README.md). I create one dated Markdown record per new failure, include the exact error, unsuccessful attempts, root cause or current hypothesis, correction, and observed verification, then add the file to the index.
