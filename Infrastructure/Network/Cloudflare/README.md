# Cloudflare

**Created:** 2026-07-09  
**Last updated:** 2026-09-06

I manage four DNS zones, one Cloudflare Tunnel, and one DNS-only Minecraft alias to an independent Playit tunnel here. `edge-01` remains the inbound web/application path and is configured from the Cloudflare Zero Trust dashboard rather than a local file. Playit carries only Minecraft for `minecraft.alphasecunited.com`; Cloudflare supplies the CNAME and SRV records but does not proxy the game stream. I keep the live Access application inventory in this component because those policies control administrative entry to Coolify.

## Verification on 2026-09-06

I verified the account twice on this date. In the morning the only Executor Cloudflare connection was the `Cloudflare MCP` integration, whose 23 tools cover Workers development and not one of which reads zones, DNS records, the tunnel, or Access, so I verified what public DNS and the connector host can show from `ubuntu-dev` and `edge-01`:

- All four zones delegate to the same two Cloudflare nameservers.
- `coolify-a1.alphsec.com` and an arbitrary name under `*.alphsec.com` both resolve to two Cloudflare proxied addresses, which is how a proxied CNAME into the tunnel appears from outside; the apex has no public A record.
- `minecraft.alphasecunited.com` is a CNAME with a `_minecraft._tcp` SRV at priority 1, weight 1, port 26328, and `ts02` and `ts03` are CNAMEs with `_ts3._udp` SRV records on ports 53810 and 49125, all matching the [domain inventory](Configuration/domains.md) and the [TeamSpeak deployment record](../../../Platforms/Teamspeak%20Hosting/Documentation/Teamspeak-deployment.md). Relay targets are withheld here as everywhere.
- Six internal `alphasecunited.com` names, including `mcp` and `openwebui`, return NXDOMAIN from both 1.1.1.1 and 8.8.8.8, so nothing on the UniFi resolver has leaked into the public zone.
- An HTTPS request to `coolify-a1.alphsec.com` from `curl` returns a Cloudflare challenge response rather than the Access login redirect, so the Access applications could not be observed from the command line.

In the evening I read the account itself through the new `Cloudflare Account MCP` Executor integration, which wraps the REST API, and everything above held. The [Executor change record](../../../Platforms/Executor/Documentation/Change%20Records/Cloudflare%20Account%20MCP%20Integration%20-%202026-09-06.md) covers how that connection came to exist.

- The account holds exactly the four zones, all active on the Free plan and all on the same two nameservers. Record counts: `alphasecunited.com` 21, `alphsec.com` 2, `duresakadi.com` 2, `duresakadi.me` 11. `duresakadi.me` is the one paused zone: Cloudflare still answers its DNS, but the proxy is bypassed, so its four apex addresses and `www` are served DNS-only regardless of the orange cloud on each record.
- `alphsec.com` holds only the two proxied CNAMEs into the tunnel, `coolify-a1.alphsec.com` and `*.alphsec.com`, matching [edge-01](Configuration/edge-01.md).
- The Minecraft and TeamSpeak CNAME and SRV records match the morning's public reading. The rest of `alphasecunited.com` is mail and domain-verification records: one unproxied apex A record, Microsoft 365 autodiscover and enrollment CNAMEs, `www`, two MX records, SPF for Outlook and for the `send.mail` Amazon SES subdomain, a Resend DKIM key, and verification TXT records for Apple, OpenAI, Anthropic, Microsoft, and a GitHub organization.
- `duresakadi.com` carries the UniFi dynamic DNS A record and a `unifi` CNAME to it. `duresakadi.me` carries four proxied apex A records, a `www` CNAME, five MX records, and an SPF record for its registrar's forwarding.
- The `edge-01` tunnel is healthy with four connections in the Ashburn region, configuration version 12, and the three ingress rules recorded in [edge-01](Configuration/edge-01.md) in the same order: `coolify-a1.alphsec.com` to `http://192.168.80.10:8000`, `*.alphsec.com` to `http://localhost:80`, then `http_status:404`.
- Cloudflare reported the connector's client version as 2026.7.3 on all four connections. The binary and package on `edge-01` were 2026.8.3, installed 2026-09-04, but the `cloudflared` process had run since the 2026-08-10 boot and never picked the new binary up. I restarted the service at 14:21 EDT through the SSH Manager. The old process logged its four connections closing, the new one logged version 2026.8.3, registered four QUIC connections within two seconds, and pulled ingress configuration version 12 from the dashboard. Cloudflare then reported the tunnel healthy with 2026.8.3 on all four connections, and both `coolify-a1.alphsec.com` and a wildcard name answered from the edge with the same challenge response as before. Caddy on `edge-01` was untouched and stayed active. Details are in [edge-01](Configuration/edge-01.md).
- The three Access applications match [applications](Configuration/applications.md) exactly: the root `Coolify` application and the child-path application each carry one allow policy for the same two email identities, and the exact webhook application carries one bypass policy for everyone. One reusable policy, `Allow dkadi`, backs the two allow applications.

- [Domain and DNS inventory](Configuration/domains.md)
- [Cloudflare Tunnel edge-01](Configuration/edge-01.md)
- [Access application inventory](Configuration/applications.md)
- [Coolify Access hardening change record](Documentation/Change%20Records/Coolify%20Access%20Hardening%20-%202026-07-22.md)
- [External service ingress design](../../../Architecture/External-Service-Ingress.md)
