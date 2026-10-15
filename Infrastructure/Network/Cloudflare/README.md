# Cloudflare

**Created:** 2026-07-09  
**Last updated:** 2026-10-15

Cloudflare holds four DNS zones and one Cloudflare Tunnel. The tunnel connector runs on `edge-01` in the DMZ and carries web ingress; the gateway forwards no ports. Minecraft and TeamSpeak use Playit for their public connections. The Cloudflare Tunnel ingress is configured from the Zero Trust dashboard, not a local file. Three Access applications control administrative entry to Coolify.

| Fact | Value |
| --- | --- |
| Zones | `alphasecunited.com`, `alphsec.com`, `duresakadi.com`, `duresakadi.me` (paused), all on the Free plan |
| Tunnel | `edge-01`, four connections, ingress configuration version 12 on 2026-09-06 |
| Connector | `cloudflared` 2026.9.3 installed on `edge-01` on 2026-10-02; active process still on 2026.8.3 with four connections until restart ([package updates](../../../Operations/Maintenance/Guest%20Package%20Updates%20-%202026-10-02.md)) |
| Public services | `coolify-a1.alphsec.com` straight to Coolify on `app-01`; `*.alphsec.com` through Caddy on `edge-01` to the deployed apps |
| Access | Three applications for Coolify; two allow policies for the same two email identities and one webhook bypass |
| Dynamic DNS | `unifi-ddns.duresakadi.com`, kept at the WAN address by Ahsoka Gateway, behind the console name `unifi.duresakadi.com` ([UniFi](../UniFi/README.md#dynamic-dns-and-the-console-name)) |

**Last full verification against the account:** 2026-09-06, through the Cloudflare Account MCP ([Account Verification](Documentation/Change%20Records/Account%20Verification%20-%202026-09-06.md)). On 2026-10-09 I restored the DNS-only CNAME and SRV for `minecraft.alphasecunited.com`, reusing the Playit allocation retained when I retired Game 01 on 2026-09-12. API readback and public DNS checks passed. The [publication record](../../../Platforms/Minecraft/Documentation/Change%20Records/DNS%20Publication%20-%202026-10-09.md) records the SRV login transport verification and server-list ping limitation.

## API tokens

Each token serves one integration and is named for it. Rolling a token gives it a new secret and invalidates the old one at once, so a token shared by two clients cannot be rolled for one without breaking the other. That is how UniFi dynamic DNS failed from 2026-08-13 to 2026-10-13 ([incident](../../../Security/Incidents/UniFi/Dynamic%20DNS%20Never%20Updated%20the%20Console%20Name%20-%202026-10-13.md)). For an integration that runs unattended I create an account API token, under Manage account, Account API tokens, because it belongs to the account rather than to my user. A dynamic DNS token gets no client-IP filter and no expiry.

These are the tokens my records document, as of 2026-10-15. Other tokens in the account serve integrations outside these records.

| Token | Permissions | Used by |
| --- | --- | --- |
| `UniFi DDNS` | Zone Read and DNS Write on `duresakadi.com`; no client-IP filter, no expiry | Dynamic DNS on Ahsoka Gateway, since 2026-10-13 ([token change](Documentation/Change%20Records/UniFi%20DDNS%20Token%20Separation%20-%202026-10-13.md)) |
| `UniFi Cert V2` | DNS Write | UniFi's built-in certificate manager on Ahsoka Gateway, which renews the `unifi.duresakadi.com` certificate through DNS-01 ([UniFi](../UniFi/README.md#dynamic-dns-and-the-console-name)). Last used 2026-10-13 |
| `executor-mcp` | Every account and zone permission group | Executor's Cloudflare Account MCP ([record](../../../Platforms/Executor/Documentation/Change%20Records/Cloudflare%20Account%20MCP%20Integration%20-%202026-09-06.md)) |

> **Before rolling or deleting `UniFi Cert V2`:** create a replacement token first and enter it in the UniFi certificate entry through the **Manage** link on UniFi's Certificates list. Renewal is automatic, and the next one is expected around mid-December 2026. If the token stops working before the certificate entry has the replacement, renewal fails silently and the certificate expires at 1:51 AM on 2027-01-11.

## Records

- [Domain and DNS inventory](Configuration/domains.md)
- [Cloudflare Tunnel edge-01](Configuration/edge-01.md)
- [Access application inventory](Configuration/applications.md)
- [UniFi DDNS Token Separation - 2026-10-13](Documentation/Change%20Records/UniFi%20DDNS%20Token%20Separation%20-%202026-10-13.md)
- [Account Verification - 2026-09-06](Documentation/Change%20Records/Account%20Verification%20-%202026-09-06.md)
- [Coolify Access Hardening - 2026-07-22](Documentation/Change%20Records/Coolify%20Access%20Hardening%20-%202026-07-22.md)
- [External service ingress design](../../../Architecture/External-Service-Ingress.md)
