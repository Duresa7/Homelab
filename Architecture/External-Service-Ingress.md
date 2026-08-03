# External Service Ingress

**Created:** 2026-07-24  
**Last updated:** 2026-07-24

Every service I publish to the Internet reaches its container through the same chain: Cloudflare's edge, the `edge-01` Cloudflare Tunnel, Caddy on edge-01, & Traefik on app-01. No ports are forwarded on the router; the tunnel is the only inbound path. This design crosses four owners, so the full path lives here & each component keeps its own record, linked at the bottom.

## The path

A request to `foo.<YOUR_PUBLIC_DOMAIN>` travels:

`Cloudflare edge (TLS) -> Tunnel edge-01 -> cloudflared on edge-01 -> Caddy :80 -> VLAN 90-to-80 firewall -> Traefik on app-01 :80 -> app container`

1. DNS. `*.<YOUR_PUBLIC_DOMAIN>` is a proxied CNAME to `<YOUR_TUNNEL_ID>.cfargotunnel.com`. Cloudflare terminates TLS at its edge, so the certificate is Cloudflare's & nothing downstream serves HTTPS.
2. Tunnel. Cloudflare hands the request to the `edge-01` tunnel. The ingress rule `*.<YOUR_PUBLIC_DOMAIN>` sends it to `http://localhost:80` on edge-01.
3. Caddy. The `http://*.<YOUR_PUBLIC_DOMAIN>` site block reverse-proxies to `192.168.80.10:80` & keeps the original Host header. Caddy runs with `auto_https off` because TLS already happened at the edge.
4. Firewall. edge-01 sits on VLAN 90 (`192.168.90.10`) & app-01 on VLAN 80 (`192.168.80.10`). A UniFi policy lets edge-01 reach app-01 only on TCP 80 & 8000.
5. Traefik. `coolify-proxy` (Traefik v3.6) listens on app-01 port 80 & routes by Host header to the container Coolify labeled when I deployed it.

## Two branches at the tunnel

The tunnel splits traffic by hostname. The dashboard takes a shortcut; deployed apps take the wildcard.

- `coolify-a1.<YOUR_PUBLIC_DOMAIN>` goes to `http://192.168.80.10:8000`, straight to the Coolify control panel, skipping Caddy & Traefik. It crosses the firewall on TCP 8000 & sits behind Cloudflare Access.
- `*.<YOUR_PUBLIC_DOMAIN>` goes to `http://localhost:80` on edge-01, into Caddy. Every deployed application rides this branch.
- Anything unmatched returns HTTP 404 at the tunnel.

## Why Caddy sits between the tunnel & Traefik

The tunnel could point straight at app-01, but I route the wildcard through Caddy on edge-01 so the tunnel has one origin on the edge VLAN & the crossing into VLAN 80 happens at a single host on two ports. Caddy hands the whole `*.<YOUR_PUBLIC_DOMAIN>` wildcard to Traefik; Traefik still does the per-app Host routing. Caddy also gives me a place on the edge for any origin that isn't a Coolify app.

## Automatic domains for new services

Because the wildcard exists at every layer, publishing a new external service needs one action: set the resource's domain to `<name>.<YOUR_PUBLIC_DOMAIN>` in Coolify. Coolify writes the Traefik router for that Host, & the wildcard DNS record, the wildcard tunnel rule, & the wildcard Caddy block already carry the subdomain to Traefik. I add no DNS record, no tunnel ingress rule, & no Caddy edit.

One gap follows from this. Only `coolify-a1.<YOUR_PUBLIC_DOMAIN>` sits behind Cloudflare Access, so any other `*.<YOUR_PUBLIC_DOMAIN>` host is reachable by anyone the moment it's deployed. I add an Access application or app-level auth for anything that shouldn't be public.

## Components

- Cloudflare Tunnel `edge-01`: [tunnel inventory](../Infrastructure/Network/Cloudflare/Configuration/edge-01.md)
- Caddy edge proxy: [Platforms/Caddy](../Platforms/Caddy/README.md)
- Coolify & its Traefik proxy: [Platforms/Coolify](../Platforms/Coolify/README.md)
- Cloudflare Access policies: [applications](../Infrastructure/Network/Cloudflare/Configuration/applications.md) & the [Coolify Access Hardening record](../Infrastructure/Network/Cloudflare/Documentation/Change%20Records/Coolify%20Access%20Hardening%20-%202026-07-22.md)
- UniFi edge path restriction: [firewall](../Infrastructure/Network/UniFi/Configuration/firewall.md)
- Visual: [homelab-overview diagram](Diagrams/homelab-overview.svg)

## Verified 2026-07-24

- The `edge-01` tunnel reported healthy with 4 connections through the Cloudflare API.
- `caddy.service` & `cloudflared.service` were both active on edge-01 (Caddy 2.6.2, cloudflared 2026.6.1).
- From edge-01, `curl -H "Host: test.<YOUR_PUBLIC_DOMAIN>" http://192.168.80.10:80` returned 404 from Traefik, which proves the Caddy-to-Traefik hop works & that unknown hosts fall through.
- The six Coolify containers reported healthy on app-01.
