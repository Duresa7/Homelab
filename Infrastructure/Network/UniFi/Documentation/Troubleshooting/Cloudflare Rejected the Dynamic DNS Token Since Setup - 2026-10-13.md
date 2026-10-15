# Cloudflare rejected the dynamic DNS token since setup

**Created:** 2026-10-15  
**Last updated:** 2026-10-15

**Investigated:** 2026-10-13; re-checked 2026-10-15  
**Owner:** UniFi / Ahsoka Gateway dynamic DNS  
**Status:** Resolved; two follow-ups open

## Symptom

After a WAN outage from about 1:10 AM to 1:25 AM EDT on 2026-10-13, the ISP gave the gateway a new public address. `https://unifi.duresakadi.com` stopped reaching the gateway because `unifi-ddns.duresakadi.com`, the A record behind it, still held the old address. UniFi's dynamic DNS should have rewritten that record and had not. The [incident report](../../../../../Security/Incidents/UniFi/Dynamic%20DNS%20Never%20Updated%20the%20Console%20Name%20-%202026-10-13.md) holds the impact and the full timeline.

## Exact error

The gateway logged a forced update and an error response on every attempt, about every two minutes:

```text
Update forced for alias unifi-ddns.duresakadi.com
Error response from DDNS server, ignoring ...
```

These are the message texts as I counted them, not complete log lines. Cloudflare's answer was `Invalid API Token`. The UniFi interface showed no obvious error.

## What I checked

I turned on SSH on Ahsoka Gateway (`192.168.1.1`, UCG-Fiber, firmware 5.1.33.34087) for the investigation and used only read-only commands.

- **The service.** UniFi's dynamic DNS with the Cloudflare provider runs inadyn 2.13.0. Its generated configuration is `/run/ddns-eth0-inadyn.conf`, for interface `eth0`, with hostname `unifi-ddns.duresakadi.com`, the zone `duresakadi.com` as username and a Cloudflare API token as password. inadyn runs with `-C`, which keeps it running after an error, and retries about every two minutes.
- **The logs.** They reach back to 2026-08-26. They held 34,719 `Update forced` lines and 34,711 `Error response` lines for that alias, and no successful update.
- **The token.** The secret in the configuration was a 53-character `cfat_` account token with a valid built-in checksum. A copying error would break the checksum, so this was a complete secret that Cloudflare no longer accepted.
- **Cloudflare's audit log.** At 9:27:44 AM EDT on 2026-08-13 I created the A record by hand with the address of the time. At 9:38:51 AM I created the account API token `UniFi Dynamic DNS`, DNS Write only, and pasted it into UniFi. At 10:04:17 AM I rolled it. Rolling gives a token a new secret and invalidates the old one immediately, while the name and permissions stay. The new secret went to the ACME client that renews the Let's Encrypt certificate for `unifi.duresakadi.com`, which used it that day and again at 3:49:32 AM on 2026-10-13. At 10:11 AM I created the DNS-only CNAME `unifi.duresakadi.com` pointing at `unifi-ddns.duresakadi.com`.
- **The record.** The A record had never been modified since I created it.
- **The permissions inadyn needs.** inadyn's Cloudflare plugin first calls `GET /zones?name=<zone>`, then looks up the record, then sends a `PATCH`. The inadyn README requires Zone.Zone Read and Zone.DNS Edit. `UniFi Dynamic DNS` had no Zone Read.

## Root cause

The secret in UniFi was the one I invalidated by rolling the token at 10:04:17 AM on 2026-08-13, 25 minutes 26 seconds after I entered it. Cloudflare refused it from then on. The token also lacked Zone Read, so inadyn could not have found the zone even before the roll. Dynamic DNS therefore never updated the record. The hand-created record held the right address until the address changed on 2026-10-13, which hid the failure for two months.

## Fix

In the Cloudflare dashboard, under Manage account, Account API tokens, I created a new account API token `UniFi DDNS` at 6:27:47 PM EDT on 2026-10-13: Zone, Zone, Read and Zone, DNS, Edit, scoped to `duresakadi.com` only, with no client-IP filter and no expiry. I pasted it into the UniFi dynamic DNS entry in place of the dead secret. I renamed the old token to `UniFi Cert V2` because the certificate client uses it; a rename leaves the secret alone. The [change record](../../../Cloudflare/Documentation/Change%20Records/UniFi%20DDNS%20Token%20Separation%20-%202026-10-13.md) covers the token changes and the deletion of an unused token.

## Verification

- At 6:29:26 PM EDT on 2026-10-13, `UniFi DDNS` updated the A record to the current WAN address, the first automatic update the record had had.
- 1.1.1.1 returned the new address. The gateway's resolver caught up from its cache about 270 seconds later.
- `https://unifi.duresakadi.com` returned HTTP 200 with a valid certificate.
- At 8:19 AM EDT on 2026-10-15 the A record still matched the current WAN address.
- I turned gateway SSH off again. On 2026-10-15 port 22 on `192.168.1.1` refused connections. I changed no gateway setting over SSH.

I retained no transcript or export from the investigation. The figures above are from the gateway's logs and configuration and Cloudflare's audit log as I read them.

## Recognising it again

A refused dynamic DNS update does not show up until the WAN address changes. The [UniFi README](../../README.md#dynamic-dns-and-the-console-name) lists the checks: compare the record with the WAN address, look at the record's `modified_on` time, and look at the token's last-used time.

## Open

- I don't know which host or tool runs the ACME renewal for `unifi.duresakadi.com` with `UniFi Cert V2`. The certificate is valid until 2027-01-11; the next renewal is due around December 2026.
- The certificate client's `_acme-challenge.unifi.duresakadi.com` TXT record from 3:49:32 AM EDT on 2026-10-13 was still there at 8:19 AM EDT on 2026-10-15. It is harmless and can be deleted.

Both are tracked in the change record's [open items](../../../Cloudflare/Documentation/Change%20Records/UniFi%20DDNS%20Token%20Separation%20-%202026-10-13.md#open).
