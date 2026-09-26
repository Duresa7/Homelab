# Access Paths

**Created:** 2026-09-25  
**Last updated:** 2026-09-25

This is how anything reaches the lab: the public, the LAN, me from outside, me at a console, and my MCP clients. Five paths, each with one owner. Figures are from the live readback on 2026-09-24 and 2026-09-25 unless a line says otherwise.

![Homelab overview, including the Cloudflare Tunnel to edge-01](../Assets/Diagrams/homelab-overview.svg)

## Summary

| Path | Who uses it | Entry point | Names | Owner |
|---|---|---|---|---|
| Public ingress | Anyone on the Internet | Cloudflare Tunnel to `edge-01` | `*.alphsec.com` | [External Service Ingress](External-Service-Ingress.md) |
| Internal HTTPS | LAN clients | Nginx Proxy Manager at `192.168.85.2` | `*.alphasecunited.com` | [Nginx Proxy Manager](../Platforms/Nginx%20Proxy%20Manager/README.md) |
| Remote access | Me, off the LAN | UniFi `Management Access` WireGuard server; NetBird mesh | addresses, not names | [UniFi VPN networks](../Infrastructure/Network/UniFi/Configuration/vpn-networks-port-profiles.md), [NetBird](../Platforms/Netbird/README.md) |
| Remote control | Me, at a device's console | MeshCentral and RustDesk on `docker-blue` | `mesh.alphasecunited.com` | [MeshCentral](../Platforms/MeshCentral/README.md), [RustDesk](../Platforms/RustDesk/README.md) |
| Agent access | My MCP clients on `ubuntu-dev` | Executor at `mcp.alphasecunited.com` | one MCP endpoint | [Executor](../Platforms/Executor/README.md) |

The router forwards no ports. Public traffic enters only through the Cloudflare Tunnel. The UniFi WireGuard server listens on the gateway itself.

## Public ingress

`Cloudflare edge (TLS) -> Tunnel edge-01 -> cloudflared on edge-01 -> Caddy :80 -> Traefik on app-01 :80 -> app container`

- `edge-01` is VM 121 on purple-server, `192.168.30.10`, DMZ VLAN 30. It runs `cloudflared` 2026.8.3 and Caddy 2.6.2, both as system units.
- Caddy forwards `*.alphsec.com` to Traefik (`traefik:v3.7`, label v3.7.12) on app-01, `192.168.80.10`, VLAN 80. Coolify 4.3.23 writes the Traefik routers.
- `coolify-a1.alphsec.com` skips Caddy and goes straight to the Coolify panel on TCP 8000. It is the only host behind Cloudflare Access.

The full chain, the firewall hop and the Access gap are in [External Service Ingress](External-Service-Ingress.md).

## Internal HTTPS

`LAN client -> UniFi local DNS -> NPM 192.168.85.2:443 -> backend web port`

- Nginx Proxy Manager 2.15.1 runs on CT 107 `docker-network`, VLAN 85. It holds 24 live proxy hosts: NetBird and 23 applications.
- UniFi holds 24 local A records pointing at `192.168.85.2`, one per live host. None of these names exists in public DNS.
- One Let's Encrypt certificate covers `*.alphasecunited.com` and `alphasecunited.com`. It renews through Cloudflare DNS-01, so no inbound port is needed; on 2026-09-24 it expired 2026-12-08.
- 13 UniFi policies name NPM. Ten let `192.168.85.2` reach one backend each on its listed web ports. Three admit clients to NPM on 443: the Hawser agents on alpha-prod-01 and security-01, and HQ-WS001.

The host list is the [proxy-host inventory](../Platforms/Nginx%20Proxy%20Manager/Configuration/internal-proxy-hosts.md).

## Remote access

Two VPNs exist, and they reach different things.

- **UniFi `Management Access`**: a WireGuard server on the gateway, `10.6.0.1/24`, UDP 51822, enabled. It sits in the `Vpn` zone. Policies admit it to the `Internal` zone, the DMZ, RDP on the identity hosts and PeaNUT; the [firewall inventory](../Infrastructure/Network/UniFi/Configuration/firewall.md) lists them. The three other remote-user VPN servers (FamilyVPN, Game-Access, Temp) are disabled.
- **NetBird**: a self-hosted WireGuard mesh on CT 107, management 0.79.0 and dashboard v2.93.0. `docker-network` is the only routing peer, and the only granted resource is `192.168.85.0/24`. Peers get no DNS from NetBird, so they reach NPM by address but cannot resolve the `alphasecunited.com` names. The detail is in [Access-Network.md](../Platforms/Netbird/Configuration/Access-Network.md).

## Remote control

Both servers run on CT 108 `docker-blue`, `192.168.40.39`, VLAN 40.

- **MeshCentral** 1.2.6 is a pilot. Browser and agents share TCP 443, published through NPM proxy host 29. Six devices were enrolled on 2026-09-18. `Allow Identity to MeshCentral` admits HQ-MGT01 and HQ-WS001 from VLAN 65; the domain controllers are deliberately left out.
- **RustDesk** `hbbs` and `hbbr` 1.1.16 are the incumbent. They stay until MeshCentral passes its four console tests.

## Agent access

`MCP client on ubuntu-dev -> https://mcp.alphasecunited.com (NPM host 27) -> Executor 192.168.40.39:4788 -> gateways and remote MCPs`

- Executor 1.6.10 on `docker-blue` is the one MCP endpoint. Every tool call is capped at 60 seconds.
- Docker MCP Gateway v0.43.3 runs two instances on `docker-blue`: UniFi Network MCP on `:8811` and SSH Manager MCP on `:8812`.
- SSH Manager lists 24 servers. On the 17 Linux nodes and guests its privilege paths reach root.
- UniFi runs in bypass mode: a create, update or delete reaches the controller with no preview step.
- The Cloudflare Account MCP is remote (`mcp.cloudflare.com`) and holds a full-access account token. The Wazuh MCP on security-01 holds a read-only credential.

Neither gateway holds a mutation back, so the read-only default is my rule, not a control. I keep diagnostics read-only unless a change is planned, and I approve anything disruptive before it runs. The trust detail is in the [Executor](../Platforms/Executor/README.md) and [Docker MCP Gateway](../Platforms/Docker%20MCP%20Gateway/README.md) records.

## Open

- NetBird peers cannot resolve internal names. A NetBird nameserver group for `alphasecunited.com` pointing at UniFi would close it.
- NPM proxy host 12 (`dashboard.alphasecunited.com`) points at a stopped container: the Homelab Dashboard on `docker-main` has been stopped since 2026-09-22, and so has the internal docs site.
- Only `coolify-a1.alphsec.com` sits behind Cloudflare Access. Any other `*.alphsec.com` app is public the moment Coolify deploys it.
