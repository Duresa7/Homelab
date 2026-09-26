# Cloudflare

**Created:** 2026-07-09  
**Last updated:** 2026-09-25

Cloudflare holds four DNS zones and one Cloudflare Tunnel. The tunnel connector runs on `edge-01` in the DMZ and is the only inbound path from the Internet; the gateway forwards no ports. Its ingress is configured from the Cloudflare Zero Trust dashboard, not a local file. Three Access applications control administrative entry to Coolify.

| Fact | Value |
| --- | --- |
| Zones | `alphasecunited.com`, `alphsec.com`, `duresakadi.com`, `duresakadi.me` (paused), all on the Free plan |
| Tunnel | `edge-01`, four connections, ingress configuration version 12 on 2026-09-06 |
| Connector | `cloudflared` 2026.8.3 on `edge-01`, unit active on 2026-09-25 |
| Public services | `coolify-a1.alphsec.com` straight to Coolify on `app-01`; `*.alphsec.com` through Caddy on `edge-01` to the deployed apps |
| Access | Three applications for Coolify; two allow policies for the same two email identities and one webhook bypass |

**Last verified against the account:** 2026-09-06, through the Cloudflare Account MCP ([Account Verification](Documentation/Change%20Records/Account%20Verification%20-%202026-09-06.md)). On 2026-09-12 I deleted the Minecraft CNAME and SRV records when I retired Game 01 ([domains](Configuration/domains.md)).

## Records

- [Domain and DNS inventory](Configuration/domains.md)
- [Cloudflare Tunnel edge-01](Configuration/edge-01.md)
- [Access application inventory](Configuration/applications.md)
- [Account Verification - 2026-09-06](Documentation/Change%20Records/Account%20Verification%20-%202026-09-06.md)
- [Coolify Access Hardening - 2026-07-22](Documentation/Change%20Records/Coolify%20Access%20Hardening%20-%202026-07-22.md)
- [External service ingress design](../../../Architecture/External-Service-Ingress.md)
