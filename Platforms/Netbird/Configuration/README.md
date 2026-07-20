# NetBird Configuration

**Created:** 2026-07-10  
**Last updated:** 2026-07-20

The live deployment sits under `/opt/docker/netbird` on `docker-network`. The checked-in `docker-compose.yml` is a reader-editable reference based on the v0.74.3 installer output.

The live `config.yaml`, `dashboard.env`, datastore, & `netbird_data` volume are generated runtime state and aren't part of this reference. The deployed `reverseProxy.trustedHTTPProxies` value is `172.31.85.10/32`, matching Nginx Proxy Manager's fixed address on the external `proxy` network.

## Reference Contents

- `docker-compose.yml` defines the `netbird-dashboard` and combined `netbird-server` services.
- The dashboard and server HTTP ports bind only to loopback at `127.0.0.1:8080` and `127.0.0.1:8081`.
- UDP 3478 is published for STUN.
- Both services join the private `netbird` network and the external `proxy` network shared with Nginx Proxy Manager.

The Compose reference currently uses `latest` image tags. The verified deployment was created from the official v0.74.3 installer; a later pull can change the version, so I handle any pull as a controlled update.

Read the [deployment record](../Documentation/Deployment.md) for the resulting configuration and the [operations runbook](../Documentation/Runbook.md) before applying this reference to the live host.
