# NetBird Operations Runbook

**Created:** 2026-07-11  
**Last updated:** 2026-07-20

## Scope

I operate the NetBird v0.74.4 control plane on `docker-network` through SSH Manager target `docker_network`. The live Compose project is `/opt/docker/netbird`.

The Nginx Proxy Manager host, advanced routes, Let's Encrypt wildcard/apex certificate, Force SSL, and HTTP/2 are active. My authoritative client entry point is `https://<YOUR_NETBIRD_DOMAIN>`; direct local checks stay useful for isolating a container or proxy failure.

## Routine Health Check

I run this on `docker_network`:

```sh
cd /opt/docker/netbird
docker compose ps
docker inspect -f 'name={{.Name}} status={{.State.Status}} restart={{.HostConfig.RestartPolicy.Name}}' netbird-dashboard netbird-server
curl -sS -o /dev/null -w 'dashboard_http=%{http_code}\n' http://127.0.0.1:8080/
curl -sS -o /dev/null -w 'idp_http=%{http_code}\n' http://127.0.0.1:8081/oauth2/.well-known/openid-configuration
getent ahostsv4 <YOUR_NETBIRD_DOMAIN>
curl -fsS -o /dev/null -w 'https=%{http_code} remote=%{remote_ip}\n' https://<YOUR_NETBIRD_DOMAIN>/
```

Expected baseline:

- Both containers are `Up` with restart policy `unless-stopped`.
- Dashboard and embedded identity-provider checks return HTTP `200`.
- Internal DNS returns `192.168.85.2`.
- The HTTPS entry point returns HTTP `200` with a valid certificate.
- The server publishes `3478/udp`; the HTTP bindings stay on loopback.

I verify the reverse-proxy network path from the Nginx Proxy Manager container:

```sh
docker exec nginx-proxy-manager getent hosts netbird-dashboard netbird-server
docker exec nginx-proxy-manager curl -sS -o /dev/null -w 'dashboard_http=%{http_code}\n' http://netbird-dashboard/
docker exec nginx-proxy-manager curl -sS -o /dev/null -w 'idp_http=%{http_code}\n' http://netbird-server/oauth2/.well-known/openid-configuration
```

## Logs

```sh
cd /opt/docker/netbird
docker compose logs --no-color --tail=200
docker compose logs --no-color --tail=200 dashboard
docker compose logs --no-color --tail=200 netbird-server
```

I increase the tail or add `--since` when I need a bounded time window. I retain the exact command, complete output, timestamp, target, & exit code in the applicable job log.

Both NetBird containers use bounded Docker `json-file` logging with `max-size=10m` and `max-file=3`, verified on 2026-07-12.

## Start, Stop, and Restart

```sh
cd /opt/docker/netbird
docker compose start
docker compose stop
docker compose restart
docker compose ps
```

I use `docker compose up -d` after a configuration change. I verify the direct HTTP checks, the Nginx Proxy Manager network path, `nginx -t`, and the public HTTPS name after every recreation.

## Configuration Validation

Before applying a checked-in Compose change I run:

```sh
cd /opt/docker/netbird
docker compose config --quiet
docker network inspect proxy
```

The live configuration must retain:

- loopback-only dashboard and server HTTP bindings;
- UDP 3478 on the guest;
- membership in both the private `netbird` and external `proxy` networks;
- `172.31.85.10/32` as the only `reverseProxy.trustedHTTPProxies` entry for Nginx Proxy Manager.

The repository Compose file is a reader-editable reference. I don't replace the live `config.yaml` or `dashboard.env` with the example file.

## HTTPS Validation

I validate the live entry point from an internal client using UniFi DNS:

```sh
curl -fsS -o /dev/null -w 'https=%{http_code} remote=%{remote_ip}\n' https://<YOUR_NETBIRD_DOMAIN>/
```

My established baseline is a valid certificate, HTTP `200`, and a successfully authenticated administrator dashboard without mixed-content errors. After a configuration change or upgrade I also exercise the management, signal, relay/WebSocket, and gRPC routes through the same name. I completed first-peer and routed VPN-path validation on 2026-07-12; it is recorded in the linked change record below.

The corresponding Nginx Proxy Manager settings and advanced routes live in its [runbook](../../Nginx%20Proxy%20Manager/Documentation/Runbook.md).

## Peers, Networks, and the VPN Path

CT 107 is both the control plane and a NetBird peer acting as the **routing peer** for the Access-A zone. The routed network is defined in the dashboard (Network Routing → Networks) and documented in [Access-Network.md](../Configuration/Access-Network.md); the first-peer/VPN-path validation is recorded in [NetBird First Peer and Routed VPN Path - 2026-07-12](Change%20Records/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12.md).

I confirm the routing peer on `docker_network`:

```sh
netbird status
# Expect: Management/Signal Connected; Relays Available;
#         NetBird IP 100.121.111.204/16; Networks: 192.168.85.0/24
cat /proc/sys/net/ipv4/ip_forward   # expect 1
```

`Networks: 192.168.85.0/24` confirms CT 107 is advertising the Access-A route. Because lazy connections are enabled, an idle peer reports "Connecting" / `0/N Connected` until traffic re-establishes its tunnel on demand; that is expected, not a fault.

I verify the VPN path from an enrolled peer that is on the overlay (run on the peer):

```sh
# 1. Tunnel data path: overlay IPs are only reachable through WireGuard:
ping -c3 100.121.111.204                       # CT 107 overlay IP

# 2. Route steering: Access-A should resolve over the NetBird interface:
ip route get 192.168.85.2                      # expect: dev wt0 table 7120

# 3. Application layer through the tunnel (force SNI + tunnel IP):
curl -k -m5 --resolve <YOUR_NETBIRD_DOMAIN>:443:192.168.85.2 \
    -o /dev/null -w '%{http_code}\n' https://<YOUR_NETBIRD_DOMAIN>   # expect 200
```

A raw-IP HTTPS request (`https://192.168.85.2`) returns a TLS `unrecognized_name` alert rather than a page; that is expected, because the front end has no server block for a bare-IP SNI, and it still confirms the connection reached the service through the tunnel.

## Update Procedure

The generated Compose reference currently uses `latest`, so `docker compose pull` can change the deployed version. I treat an update as a bounded change:

1. Record the current container image digests and NetBird application version.
2. Back up the live configuration and `netbird_data` volume.
3. Review upstream release notes and compatibility with the Nginx Proxy Manager routes.
4. Pull and recreate only the two application services, naming them explicitly (see below).
5. Repeat the direct, proxy-network, DNS, HTTPS, authentication, and restart checks.
6. Retain step evidence and update the deployment record.

My verified update commands, run on `docker_network` in `/opt/docker/netbird`, are:

```sh
cd /opt/docker/netbird
docker compose pull netbird-server dashboard
docker compose up -d --force-recreate netbird-server dashboard
```

I name the two services, `netbird-server` and `dashboard`, explicitly rather than acting on the whole project. Two points make this the reliable form:

- `proxy` is an external Docker network declared under `networks:`, not a service. Including it in a service list (for example `docker compose pull proxy`) fails with `no such service: proxy`. Nginx Proxy Manager is a separate Compose project and is updated from its own directory, not through this one.
- Because both images track the `latest` tag, `--force-recreate` replaces the running containers with the freshly pulled images even when the tag string is unchanged. Without it, Compose can leave the existing containers in place when it considers their definition unchanged, so the pulled update wouldn't take effect.

Tracking `latest` is my intentional 2026-07-12 maintenance decision. I continue to record the before/after image identity and verification for every update.

## Backup and Restore

I back up these items together before an update or migration:

- `/opt/docker/netbird/docker-compose.yml`
- `/opt/docker/netbird/config.yaml`
- `/opt/docker/netbird/dashboard.env`
- Docker volume `netbird_data`

To restore, I recover the files with their original ownership and permissions, restore the volume, confirm the external `proxy` network exists, then run `docker compose up -d` and perform the full health check. I restore Nginx Proxy Manager independently if its proxy host or certificate state was also lost.

## Recording a Failure

I use [Troubleshooting-Log.md](Troubleshooting-Log.md) for known deployment issues. For a new problem I capture the exact symptom and error first, then document failed attempts, hypotheses, tests, corrective action, and verification chronologically. I create a separate security incident record if availability or security impact becomes material.
