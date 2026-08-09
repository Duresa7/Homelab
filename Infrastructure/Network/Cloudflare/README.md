# Cloudflare

**Created:** 2026-07-09  
**Last updated:** 2026-08-09

I manage four DNS zones, one Cloudflare Tunnel, and one DNS-only Minecraft alias to an independent Playit tunnel here. `edge-01` remains the inbound web/application path and is configured from the Cloudflare Zero Trust dashboard rather than a local file. Playit carries only Minecraft for `minecraft.alphasecunited.com`; Cloudflare supplies the CNAME and SRV records but does not proxy the game stream. I keep the live Access application inventory in this component because those policies control administrative entry to Coolify.

- [Domain and DNS inventory](Configuration/domains.md)
- [Cloudflare Tunnel edge-01](Configuration/edge-01.md)
- [Access application inventory](Configuration/applications.md)
- [Coolify Access hardening change record](Documentation/Change%20Records/Coolify%20Access%20Hardening%20-%202026-07-22.md)
- [External service ingress design](../../../Architecture/External-Service-Ingress.md)
