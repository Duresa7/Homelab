# Dynamic DNS Never Updated the Console Name - 2026-10-13

**Created:** 2026-10-15  
**Last updated:** 2026-10-15

## Incident Metadata

| Field | Value |
|-------|-------|
| Incident date | 2026-10-13 |
| Report timezone | America/New_York (EDT). Cloudflare's audit log records UTC; I converted its times here |
| Service | `https://unifi.duresakadi.com`, the public name for Ahsoka Gateway, and the UniFi dynamic DNS entry that keeps it current |
| Gateway | Ahsoka Gateway, UniFi Cloud Gateway Fiber (`UCG-Fiber`) at `192.168.1.1`, firmware 5.1.33.34087 |
| Trigger | The ISP assigned a new WAN address after a WAN outage from about 1:10 AM to 1:25 AM |
| Detected | 2026-10-13; exact time not retained |
| Duration | About 17 hours, from about 1:25 AM until dynamic DNS updated the record at 6:29:26 PM. The dynamic DNS failure itself ran from its setup at 9:38:51 AM on 2026-08-13 until that update |
| Recovery | A new Cloudflare account API token with the permissions inadyn needs, entered in the UniFi dynamic DNS entry |
| Status | Resolved, with one follow-up open |
| Severity | SEV-3 - Service Degradation |

## Summary

`unifi.duresakadi.com` is a DNS-only CNAME to `unifi-ddns.duresakadi.com`, an A record that UniFi's dynamic DNS is meant to keep pointed at my WAN address. Dynamic DNS had never updated that record. I created the record by hand on 2026-08-13 with the address of the time, then created a Cloudflare token for the gateway. That day I set up two UniFi features on Ahsoka Gateway with that one token: dynamic DNS, and UniFi's built-in certificate manager, which gets the Let's Encrypt certificate for `unifi.duresakadi.com`. Twenty-five minutes after pasting the secret into dynamic DNS I rolled the token, which gave it a new secret and invalidated the old one. Only the certificate manager got the new secret. From then on, every update the gateway sent was refused with `Invalid API Token`.

Nothing in the UniFi interface showed it. The hand-made record already held the right address, and the address did not change for two months. On 2026-10-13 a WAN outage ended with a new address, the record kept the old one, and the name stopped reaching the gateway.

At 6:27:47 PM I created a new account API token, `UniFi DDNS`, with Zone Read and DNS Write on `duresakadi.com`, and entered it in UniFi. At 6:29:26 PM the gateway updated the A record to the current WAN address, the first automatic update the record had ever had. I renamed the old token to `UniFi Cert V2`, since the certificate manager still uses it, and deleted an unused token.

## Impact

| Area | Impact |
|------|--------|
| Console name | From about 1:25 AM to 6:29:26 PM on 2026-10-13, public DNS answered `unifi.duresakadi.com` with the previous WAN address, so the name did not reach the gateway. The gateway's own resolver caught up from its cache about 270 seconds after the update |
| Dynamic DNS | Failed on every attempt from its setup on 2026-08-13 until the fix on 2026-10-13, unnoticed until the address changed |
| Certificate | None. The certificate manager held the token's current secret and renewed the certificate at about 3:51 AM on 2026-10-13. After the fix `https://unifi.duresakadi.com` returned HTTP 200 with a valid certificate |

## Affected Assets

| Asset | Role and configuration | Observed state |
|-------|------------------------|----------------|
| Ahsoka Gateway | UCG-Fiber at `192.168.1.1`, firmware 5.1.33.34087. UniFi's Cloudflare dynamic DNS provider runs inadyn 2.13.0 from the generated `/run/ddns-eth0-inadyn.conf` on `eth0` | Retried about every two minutes with `-C`, which keeps inadyn running after an error. Every attempt failed |
| UniFi dynamic DNS entry | Hostname `unifi-ddns.duresakadi.com`, username the zone `duresakadi.com`, password a Cloudflare API token | Held the secret that the 10:04:17 AM roll on 2026-08-13 invalidated |
| A `unifi-ddns.duresakadi.com` | The record dynamic DNS maintains | Created by hand at 9:27:44 AM on 2026-08-13; never modified until 6:29:26 PM on 2026-10-13 |
| CNAME `unifi.duresakadi.com` | DNS-only CNAME to `unifi-ddns.duresakadi.com` | Unchanged; followed the stale A record |
| Cloudflare token `UniFi Dynamic DNS`, now `UniFi Cert V2` | Account API token, DNS Write only | Rolled 2026-08-13; its current secret is held by UniFi's certificate manager |
| UniFi certificate manager | Built into the UniFi console on Ahsoka Gateway. Its entry, named "Unifi Certificate", gets the Let's Encrypt certificate for `unifi.duresakadi.com` through DNS-01 with `UniFi Cert V2` and renews it automatically | Active and valid on 2026-10-15; renewed at about 3:51 AM on 2026-10-13 |

## Symptoms

- `unifi.duresakadi.com` resolved to the previous WAN address after the 2026-10-13 outage.
- The UniFi interface showed no obvious dynamic DNS error.
- The gateway's logs, which reach back to 2026-08-26, held 34,719 `Update forced for alias unifi-ddns.duresakadi.com` lines and 34,711 `Error response from DDNS server, ignoring ...` lines, and no successful update.
- Cloudflare's answer to each update was `Invalid API Token`.

## Timeline (EDT)

| Date | Time | Event |
|------|------|-------|
| 2026-08-13 | 9:27:44 AM | I created the A record `unifi-ddns.duresakadi.com` by hand with the WAN address of the time |
| 2026-08-13 | 9:38:51 AM | I created the account API token `UniFi Dynamic DNS` with DNS Write only and pasted its secret into the UniFi dynamic DNS entry |
| 2026-08-13 | 10:04:17 AM | I rolled the token. Cloudflare issued a new secret and the one in the dynamic DNS entry stopped working at once. The new secret went only to UniFi's certificate manager, which used it the same day |
| 2026-08-13 | 10:11 AM | I created the DNS-only CNAME `unifi.duresakadi.com` pointing at `unifi-ddns.duresakadi.com` |
| 2026-08-26 | | The gateway's retained logs begin. Every update from here to the fix failed |
| 2026-10-13 | About 1:10 AM to 1:25 AM | WAN outage. The ISP assigned a new public address, and the A record kept the old one |
| 2026-10-13 | 3:49:32 AM | UniFi's certificate manager used the rolled token, now `UniFi Cert V2`, from inside my home network to write the `_acme-challenge.unifi.duresakadi.com` TXT record, its DNS-01 challenge for a renewal |
| 2026-10-13 | About 3:51 AM | Let's Encrypt issued the renewed certificate. UniFi shows it as valid from 2:51 AM because Let's Encrypt backdates a certificate's start by about an hour |
| 2026-10-13 | 6:27:47 PM | I created the account API token `UniFi DDNS`, Zone Read and DNS Write on `duresakadi.com` only, and entered it in the UniFi dynamic DNS entry. I renamed `UniFi Dynamic DNS` to `UniFi Cert V2` |
| 2026-10-13 | 6:29:26 PM | `UniFi DDNS` updated the A record to the current WAN address, the first automatic update the record had had |
| 2026-10-13 | After the update | 1.1.1.1 returned the new address; the gateway's resolver caught up about 270 seconds later. `https://unifi.duresakadi.com` returned HTTP 200 with a valid certificate |
| 2026-10-13 | 7:35:24 PM | I deleted the unused token `Unifi Certificate`, last used 2026-07-22 |
| 2026-10-15 | | Port 22 on `192.168.1.1` refused connections, so the gateway SSH I enabled for the investigation is off again |
| 2026-10-15 | 8:19 AM | The A record still matched the current WAN address. The 3:49:32 AM `_acme-challenge` TXT record was still present |
| 2026-10-15 | | I took screenshots of UniFi's Certificates list. Its one certificate matched the 3:49:32 AM challenge record, which identified the certificate manager as the user of `UniFi Cert V2` |

## Findings

### The secret in UniFi was dead from 10:04 AM on setup day

The token in the generated inadyn configuration was a 53-character `cfat_` account token with a valid built-in checksum. It was intact; Cloudflare refused it because the roll at 10:04:17 AM on 2026-08-13 had replaced it, not because of a copy error. That secret was valid for 25 minutes 26 seconds. The gateway's logs start on 2026-08-26, so I cannot see what it sent in that window, but the A record was never modified after I created it, so no update landed then either.

### One token served two jobs

I set up two UniFi features on Ahsoka Gateway with `UniFi Dynamic DNS`: dynamic DNS and the certificate manager. When I rolled the token 25 minutes later, only the certificate manager got the new secret. Rolling a token gives it a new secret and keeps its name and permissions, so the token still carried the name `UniFi Dynamic DNS` while only the certificate manager could use it. The certificate manager used the new secret on 2026-08-13 and again at 3:49:32 AM on 2026-10-13.

### The certificate comes from UniFi's own certificate manager

On 2026-10-15 I took screenshots of the Certificates list in the UniFi console, which has **Add New** and **Manage** links, and of its one certificate. I did not record the menu path to the list.

| Field | Value |
|---|---|
| Name | "Unifi Certificate" |
| Status | Active |
| Valid | Yes |
| Subject CN | `unifi.duresakadi.com` |
| Issuer | Let's Encrypt, CN `YR2` |
| Valid From | Oct 13 2026 2:51 AM |
| Valid To | Jan 11 2027 1:51 AM |

This lines up with Cloudflare's audit log. At 3:49:32 AM on 2026-10-13 the rolled token wrote the `_acme-challenge.unifi.duresakadi.com` TXT record from inside my home network. DNS-01 is the Let's Encrypt challenge that proves control of a name through a TXT record at `_acme-challenge` under it. Let's Encrypt backdates a certificate's start by about an hour, so a 2:51 AM start means it issued the certificate at about 3:51 AM, two minutes after the challenge record. The end reads 1:51 AM rather than 2:51 AM only because January is on standard time; the certificate runs 90 days.

### The original token could not have worked anyway

`UniFi Dynamic DNS` held DNS Write only. inadyn's Cloudflare plugin first calls `GET /zones?name=<zone>` to find the zone, then looks up the record, then sends a `PATCH` to change it. The inadyn README requires Zone.Zone Read and Zone.DNS Edit for that. Without Zone Read the first call fails, so even an unrolled token would have failed.

### The failure was silent

UniFi shows no obvious error when updates are refused, and `-C` keeps inadyn running after each error, so the service never stopped. The hand-made A record already held the right address, so DNS answered correctly until the address changed. The record's last-modified time stayed at its creation time for two months.

## Root Cause

The UniFi dynamic DNS entry held a Cloudflare token secret that I invalidated by rolling the token 25 minutes after entering it. Cloudflare refused every update from then on with `Invalid API Token`. The token also lacked the Zone Read permission inadyn's Cloudflare plugin needs, so it would have failed even unrolled. The hand-created A record hid the failure until the WAN address changed on 2026-10-13.

## Contributing Factors

1. **One token for two UniFi features.** Dynamic DNS and the certificate manager on the same gateway shared it. After the roll only the certificate manager got the new secret, and the token kept the dynamic DNS name.
2. **Missing permission.** DNS Write alone does not let inadyn find the zone.
3. **No check after setup.** I did not confirm that the gateway had written the record once. A record created by hand with the right address looks the same as a working one until the address changes.
4. **No monitoring.** Nothing watched the record's age or the token's last-used time.

## Corrective Action

### 1. A dedicated token for dynamic DNS

At 6:27:47 PM on 2026-10-13 I created the account API token `UniFi DDNS` under Manage account, Account API tokens in the Cloudflare dashboard. It holds Zone, Zone, Read and Zone, DNS, Edit, scoped to `duresakadi.com` only, with no client-IP filter and no expiry. I pasted it into the UniFi dynamic DNS entry in place of the dead secret. Details are in the [change record](../../../Infrastructure/Network/Cloudflare/Documentation/Change%20Records/UniFi%20DDNS%20Token%20Separation%20-%202026-10-13.md).

### 2. The old token renamed for its real job

I renamed `UniFi Dynamic DNS` to `UniFi Cert V2`, because UniFi's certificate manager is what uses it. A rename does not change the secret, so renewal keeps working.

### 3. An unused token deleted

At 7:35:24 PM I deleted `Unifi Certificate`, an older token last used on 2026-07-22. The certificate entry in UniFi has the same name, "Unifi Certificate", but the two are separate. Renewal uses `UniFi Cert V2`, so deleting the token did not affect the certificate.

### 4. Gateway SSH turned off again

I enabled SSH on the gateway for the investigation and ran only read-only commands; I changed no gateway setting through it. I have since turned it off. On 2026-10-15 port 22 on `192.168.1.1` refused connections.

## Validation

| Check | Observed result |
|-------|-----------------|
| A record | Updated by `UniFi DDNS` at 6:29:26 PM on 2026-10-13 to the current WAN address |
| Public resolution | 1.1.1.1 returned the new address |
| Gateway resolver | Caught up from its cache about 270 seconds after the update |
| Console | `https://unifi.duresakadi.com` returned HTTP 200 with a valid certificate |
| Re-check, 2026-10-15 8:19 AM | The A record still matched the current WAN address |
| Gateway SSH, 2026-10-15 | Port 22 on `192.168.1.1` refused connections |
| Certificate, 2026-10-15 | UniFi's Certificates list showed "Unifi Certificate" Active and valid until 1:51 AM on 2027-01-11 |

Apart from the 2026-10-15 screenshots of UniFi's Certificates list, I retained no transcript, log extract or export from this investigation. The other figures above are from the gateway's logs, the generated inadyn configuration and Cloudflare's audit log as I read them.

## Lessons

1. **One token per integration, named for its job.** A token shared by two clients cannot be rolled for one without breaking the other.
2. **Grant the permissions the client documents.** For inadyn's Cloudflare plugin that is Zone Read and DNS Write on the zone.
3. **Prove dynamic DNS once after setup.** Check that the record's `modified_on` time, the time Cloudflare last changed it, has moved past the time I created it. A token's last-used time is also a cheap signal, but only when the token serves one job. The [UniFi README](../../../Infrastructure/Network/UniFi/README.md#dynamic-dns-and-the-console-name) has the check.
4. **Account API tokens for long-running integrations, with no client-IP filter and no expiry for dynamic DNS.** An account token belongs to the account rather than to my user. An IP filter would lock the gateway out right after the address change it exists to report, and an expiry would break it again silently.

## Closure Status and Open Items

**Resolved:** dynamic DNS has updated the A record, `https://unifi.duresakadi.com` reaches the gateway with a valid certificate, and the record still matched on 2026-10-15.

One follow-up is open. UniFi's certificate manager did not remove the `_acme-challenge.unifi.duresakadi.com` TXT record it wrote at 3:49:32 AM on 2026-10-13 for that day's renewal, and the record was still there at 8:19 AM on 2026-10-15. It is harmless and can be deleted. After the next renewal, expected around mid-December 2026, I'll check whether the certificate manager leaves another one behind. The item is in the change record's [open items](../../../Infrastructure/Network/Cloudflare/Documentation/Change%20Records/UniFi%20DDNS%20Token%20Separation%20-%202026-10-13.md#open).

I have no separate record of the 1:10 AM to 1:25 AM WAN outage and do not know its cause.

## Related Records

- [Troubleshooting record](../../../Infrastructure/Network/UniFi/Documentation/Troubleshooting/Cloudflare%20Rejected%20the%20Dynamic%20DNS%20Token%20Since%20Setup%20-%202026-10-13.md)
- [UniFi DDNS Token Separation](../../../Infrastructure/Network/Cloudflare/Documentation/Change%20Records/UniFi%20DDNS%20Token%20Separation%20-%202026-10-13.md)
- [UniFi dynamic DNS and the console name](../../../Infrastructure/Network/UniFi/README.md#dynamic-dns-and-the-console-name)
- [Cloudflare API tokens](../../../Infrastructure/Network/Cloudflare/README.md#api-tokens)
- [Cloudflare domain and DNS inventory](../../../Infrastructure/Network/Cloudflare/Configuration/domains.md#unifi-console-names)
