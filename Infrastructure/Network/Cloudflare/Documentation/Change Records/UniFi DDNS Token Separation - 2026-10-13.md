# UniFi DDNS Token Separation

**Created:** 2026-10-15  
**Last updated:** 2026-10-15

**Implementation date:** 2026-10-13  
**Status:** Complete; one follow-up open  
**Affected systems:** Cloudflare account API tokens `UniFi DDNS` (new), `UniFi Cert V2` (renamed from `UniFi Dynamic DNS`) and `Unifi Certificate` (deleted); the Cloudflare dynamic DNS entry on Ahsoka Gateway  
**Incident:** [Dynamic DNS Never Updated the Console Name - 2026-10-13](../../../../../Security/Incidents/UniFi/Dynamic%20DNS%20Never%20Updated%20the%20Console%20Name%20-%202026-10-13.md)

On 2026-10-13 I gave the gateway's dynamic DNS its own Cloudflare token, named the old token for UniFi's certificate manager, which actually uses it, and deleted a token nothing had used since 2026-07-22. Before the change, one token served both UniFi features, and the secret UniFi held had been dead since I rolled the token on 2026-08-13. The [troubleshooting record](../../../UniFi/Documentation/Troubleshooting/Cloudflare%20Rejected%20the%20Dynamic%20DNS%20Token%20Since%20Setup%20-%202026-10-13.md) has the investigation.

All times are EDT. Cloudflare's audit log records them in UTC.

## What changed

### A new token for dynamic DNS

At 6:27:47 PM I created the account API token `UniFi DDNS` in the Cloudflare dashboard under Manage account, Account API tokens. An account API token belongs to the account rather than to my user, which suits an integration that runs unattended.

| Setting | Value |
|---|---|
| Permissions | Zone, Zone, Read and Zone, DNS, Edit |
| Zone resources | `duresakadi.com` only |
| Client IP filter | None |
| Expiry | None |

The dashboard labels the DNS permission Edit; Cloudflare's API calls the same permission DNS Write, which is the name the tables below use.

Zone Read is there because inadyn's Cloudflare plugin looks the zone up by name before it touches the record, and the inadyn README requires Zone.Zone Read with Zone.DNS Edit. The old token lacked it. The token has no IP filter because the gateway's address is exactly what changes; a filter on the old address would lock the gateway out at the moment it needs to report the new one. It has no expiry because an expired token would fail as silently as the old one did.

I pasted the token into the gateway's Cloudflare dynamic DNS entry in UniFi in place of the dead secret. The hostname `unifi-ddns.duresakadi.com` and the username `duresakadi.com` stayed the same.

### The old token renamed

I renamed `UniFi Dynamic DNS` to `UniFi Cert V2`. Since the roll on 2026-08-13 its secret has been held only by UniFi's built-in certificate manager on Ahsoka Gateway, which renews the Let's Encrypt certificate for `unifi.duresakadi.com` through DNS-01. DNS-01 means it proves it controls the name by writing a TXT record at `_acme-challenge.unifi.duresakadi.com`, which is why the token needs DNS Write. A rename does not change the secret, so renewal keeps working. The token holds DNS Write only. I left its permissions alone.

### An unused token deleted

At 7:35:24 PM I deleted `Unifi Certificate`, an older token last used on 2026-07-22. The certificate entry in UniFi has the same name, "Unifi Certificate", but the two are separate. Renewal uses `UniFi Cert V2`, so deleting the token did not affect the certificate.

## Verification

- At 6:29:26 PM `UniFi DDNS` updated the A record `unifi-ddns.duresakadi.com` to the current WAN address. It was the first change to the record since I created it by hand on 2026-08-13.
- 1.1.1.1 returned the new address, and the gateway's resolver caught up from its cache about 270 seconds later.
- `https://unifi.duresakadi.com` returned HTTP 200 with a valid certificate.
- At 8:19 AM on 2026-10-15 the A record still matched the current WAN address.

## Tokens after the change

| Token | Permissions | Used by |
|---|---|---|
| `UniFi DDNS` | Zone Read and DNS Write on `duresakadi.com`; no IP filter, no expiry | Dynamic DNS on Ahsoka Gateway |
| `UniFi Cert V2` | DNS Write | UniFi's certificate manager on Ahsoka Gateway, for `unifi.duresakadi.com`; last used 3:49:32 AM on 2026-10-13 |

The current list, with the other documented token, is in the [Cloudflare README](../../README.md#api-tokens).

## Open

- **Delete the stale challenge record.** UniFi's certificate manager did not remove the `_acme-challenge.unifi.duresakadi.com` TXT record it wrote at 3:49:32 AM on 2026-10-13 for that day's renewal. It was still there at 8:19 AM on 2026-10-15. It is harmless and can be deleted. After the next renewal, expected around mid-December 2026, check whether it leaves another one behind.

## Rollback

None planned: the state before the change was broken. `Unifi Certificate` stays deleted; nothing had used it since 2026-07-22. Renaming `UniFi Cert V2` back would not affect the certificate manager that uses it.
