# Cloudflare

**Created:** 2026-07-09  
**Last updated:** 2026-07-24

I manage four DNS zones & one Cloudflare Tunnel here. The tunnel, `edge-01`, is the only inbound path from the Internet to my homelab, & I configure it from the Cloudflare Zero Trust dashboard rather than a local file. I keep the live Access application inventory in this component because those policies control administrative entry to Coolify.

- [Domain and DNS inventory](Configuration/domains.md)
- [Cloudflare Tunnel edge-01](Configuration/edge-01.md)
- [Access application inventory](Configuration/applications.md)
- [Coolify Access hardening change record](Documentation/Change%20Records/Coolify%20Access%20Hardening%20-%202026-07-22.md)
- [External service ingress design](../../../Architecture/External-Service-Ingress.md)
