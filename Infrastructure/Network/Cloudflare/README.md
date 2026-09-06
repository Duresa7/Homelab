# Cloudflare

**Created:** 2026-07-09  
**Last updated:** 2026-09-06

I manage four DNS zones, one Cloudflare Tunnel, and one DNS-only Minecraft alias to an independent Playit tunnel here. `edge-01` remains the inbound web/application path and is configured from the Cloudflare Zero Trust dashboard rather than a local file. Playit carries only Minecraft for `minecraft.alphasecunited.com`; Cloudflare supplies the CNAME and SRV records but does not proxy the game stream. I keep the live Access application inventory in this component because those policies control administrative entry to Coolify.

## Verification on 2026-09-06

The Executor Cloudflare connection exposes one tool, documentation search, so I could not read the account through it. I verified what public DNS and the connector host can show instead, from `ubuntu-dev` and `edge-01`:

- All four zones delegate to the same two Cloudflare nameservers.
- `coolify-a1.alphsec.com` and an arbitrary name under `*.alphsec.com` both resolve to two Cloudflare proxied addresses, which is how a proxied CNAME into the tunnel appears from outside; the apex has no public A record.
- `minecraft.alphasecunited.com` is a CNAME with a `_minecraft._tcp` SRV at priority 1, weight 1, port 26328, and `ts02` and `ts03` are CNAMEs with `_ts3._udp` SRV records on ports 53810 and 49125, all matching the [domain inventory](Configuration/domains.md) and the [TeamSpeak deployment record](../../../Platforms/Teamspeak%20Hosting/Documentation/Teamspeak-deployment.md). Relay targets are withheld here as everywhere.
- Six internal `alphasecunited.com` names, including `mcp` and `openwebui`, return NXDOMAIN from both 1.1.1.1 and 8.8.8.8, so nothing on the UniFi resolver has leaked into the public zone.
- `cloudflared.service` on `edge-01` is active since 2026-08-10 at version 2026.8.3. Its journal is not readable by the unprivileged account and it exposes no local metrics port, so the connection count was not re-read.
- An HTTPS request to `coolify-a1.alphsec.com` from `curl` returns a Cloudflare challenge response rather than the Access login redirect, so the Access applications could not be observed from the command line. They stand as verified through the API on 2026-07-22.

What this does not cover is the account itself: zone settings, the tunnel's ingress rules, and the Access policies. Reading those needs an account-scoped connection, which is a decision recorded in the root [TODO](../../../TODO.md).

- [Domain and DNS inventory](Configuration/domains.md)
- [Cloudflare Tunnel edge-01](Configuration/edge-01.md)
- [Access application inventory](Configuration/applications.md)
- [Coolify Access hardening change record](Documentation/Change%20Records/Coolify%20Access%20Hardening%20-%202026-07-22.md)
- [External service ingress design](../../../Architecture/External-Service-Ingress.md)
