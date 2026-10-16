# Security Insights Review

**Created:** 2026-10-15  
**Last updated:** 2026-10-16

**Implementation date:** 2026-10-15  
**Status:** HSTS, DMARC and Microsoft 365 DKIM applied; security.txt and the Accept-risk classifications open  
**Affected systems:** Cloudflare zone `alphsec.com` (HSTS, mail lockdown), `duresakadi.com` (mail lockdown), `alphasecunited.com` (DMARC Management), the Cloudflare login (two-factor authentication), Security Insights classifications  
**Related:** [Coolify Webhook Bypass Limited to GitHub - 2026-10-15](Coolify%20Webhook%20Bypass%20Limited%20to%20GitHub%20-%202026-10-15.md)

I ran a full Security Insights scan at 9:19 AM after narrowing the Coolify webhook bypass that morning. The Critical `Overprovisioned Access Policies` finding was gone. The export held 22 findings, 12 Moderate and 10 Low, and this record is what I decided about each. All times are EDT.

## The findings

| Finding | Subject | Severity | Decision |
|---|---|---|---|
| Users without MFA | the Cloudflare login | Moderate | Fixed. I enabled two-factor authentication on the login the same morning |
| Domains without HSTS | `coolify-a1.alphsec.com` | Moderate | Fixed, below |
| Unproxied CNAME record, no Always Use HTTPS, no TLS | `enterpriseenrollment.alphasecunited.com` and `enterpriseregistration.alphasecunited.com`, three findings each | Moderate | Accept risk. These are the Intune and Entra device-registration CNAMEs to Microsoft. They must stay DNS-only, and the plain-HTTP answer the scanner saw is Microsoft's own 302 to `intune.microsoft.com` |
| DMARC record error | `alphasecunited.com`, `send.mail.alphasecunited.com` | Low | Fixed, below. Both carry SPF and MX and had no `_dmarc` record. One record at `_dmarc.alphasecunited.com` with `p=none` covers the subdomain, and Cloudflare's DMARC Management receives the reports |
| Security.txt not configured | `alphsec.com`, `alphasecunited.com`, `duresakadi.com` | Low | Open. Cloudflare serves a managed `security.txt` per zone from the dashboard; it only answers on proxied hostnames |
| Review AI crawlers with AI Labyrinth | `alphasecunited.com` | Low | Dismiss. A feature suggestion, not a finding |
| Dangling A record (four), DMARC, Always Use HTTPS, Security.txt | `duresakadi.me` | Moderate and Low | Out of scope. I am leaving that zone as it is, and it stays undocumented here |

The zone readback behind the table: `alphsec.com` had Always Use HTTPS on and HSTS off; `alphasecunited.com` has no proxied record at all, with the apex and `www` on Vercel and every other name DNS-only; `duresakadi.com` had Always Use HTTPS on and only proxied placeholder records besides the UniFi names.

## What changed

At 10:28:46 AM I enabled HSTS on `alphsec.com` through the API: `strict_transport_security` enabled, `max_age` 15552000 (180 days), `include_subdomains` true, `preload` false, `nosniff` unchanged at false. Every name in that zone is a proxied CNAME to the tunnel and answers only over HTTPS, so there is nothing in the zone the header can break. Preload stays off because it cannot be undone inside the 180 days once a browser list has it.

### DMARC on the three zones

The report mailbox question settled itself once I looked at what the zones actually do with mail. `alphsec.com` and `duresakadi.com` send none: no MX, no sender. `alphasecunited.com` sends from two places: Microsoft 365 at the apex, with the Outlook MX and SPF `include:spf.protection.outlook.com`, and Resend, which signs under `mail.alphasecunited.com` and uses `send.mail.alphasecunited.com` as its envelope domain with SPF `include:amazonses.com`. The two kinds of zone want opposite records.

For the two zones that send nothing I used Cloudflare's lockdown for a domain that sends no email, in the dashboard, at 7:53:02 PM for `duresakadi.com` and 7:53:59 PM for `alphsec.com`. It wrote three records on each: SPF `v=spf1 -all`, an empty DKIM key, and `_dmarc` with `v=DMARC1; p=reject; sp=reject; adkim=s; aspf=s` and my personal mailbox as the report address. Nothing legitimate sends as those domains, so rejecting everything is the right policy, and the strictness costs nothing.

For `alphasecunited.com` that same record would have bounced my own mail. Resend's signing domain is `mail.alphasecunited.com` and its envelope is `send.mail.alphasecunited.com`, which pass relaxed alignment against the apex and fail strict. Microsoft 365 is not yet signing as the domain at all, so its mail passes DMARC through SPF alone, which breaks on forwarding. So at 7:59:16 PM I enabled Cloudflare's DMARC Management on the zone in the dashboard; there is no API for it. It wrote `_dmarc.alphasecunited.com` as `v=DMARC1; p=none; rua=mailto:c69f31f4b9c14cc09b80ad512503cb03@dmarc-reports.cloudflare.net`, relaxed alignment by default, and it reads the reports into a per-sender chart under the zone. `p=none` tells receivers to deliver as before and only report, so it cannot change delivery for Resend or Microsoft 365. Cloudflare publishes the external-destination authorization record at `alphasecunited.com._report._dmarc.dmarc-reports.cloudflare.net`, so Microsoft and Yahoo send their reports as well as Google; a personal mailbox on another domain cannot publish that record and would have received Google's only.

### Microsoft 365 DKIM for alphasecunited.com

Turning on DKIM signing for the domain in the Defender portal (Email authentication settings, DKIM tab) fails until the two DNS records Microsoft issues exist. At 8:09:19 PM on 2026-10-15 I added both to the zone through the API, DNS-only, with the comment `Microsoft 365 DKIM`. Within a minute both answered from the zone's authoritative server, 1.1.1.1 and 8.8.8.8, and each chains to a live key at Microsoft's end. DKIM record names, targets and keys are withheld from this repository. The signing toggle itself is flipped in the Defender portal after the records exist. The first attempts failed because Microsoft's resolvers had cached the records' absence from the attempt that produced the error; Cloudflare's negative TTL on the zone is 30 minutes, and the toggle accepted once that had passed.

At 8:39:17 PM I sent a message from my Microsoft 365 mailbox to my personal mailbox. The receiving side's `Authentication-Results` reported `dkim=pass` with `header.d=alphasecunited.com`, `spf=pass`, and `dmarc=pass`, and the message carried a `DKIM-Signature` with `d=alphasecunited.com`. Microsoft's own `ARC-Authentication-Results` on the way out said the same. Microsoft 365 mail from the domain is now DKIM-signed and aligned, so it passes DMARC on both SPF and DKIM.

## Verification

- `_dmarc.alphasecunited.com` resolves through both 1.1.1.1 and 8.8.8.8 with the record above, and `alphasecunited.com._report._dmarc.dmarc-reports.cloudflare.net` answers `v=DMARC1;`. There is no `_dmarc` under `mail` or `send.mail`, so both inherit the apex `p=none`.
- The zone's MX, SPF and Resend records kept their 2026-07 modification dates; DMARC Management wrote the one `_dmarc` record and nothing else. Both SPF records resolve.
- `_dmarc.alphsec.com` and `_dmarc.duresakadi.com` resolve with the reject record, and the API shows `v=spf1 -all` and the empty DKIM key beside each.
- A request to `https://coolify-a1.alphsec.com/login` returned `302` to Access with `strict-transport-security: max-age=15552000; includeSubDomains`.
- A request to `http://coolify-a1.alphsec.com/login` still returned `301` to the HTTPS URL, so Always Use HTTPS is unchanged.
- The API read the setting back with the values above, `modified_on` 2026-10-15T14:28:46Z.

## Rollback

Set `strict_transport_security.enabled` back to false. Browsers that have seen the header keep enforcing HTTPS for up to 180 days, which costs nothing here.

For DMARC, deleting a `_dmarc` record returns the zone to no policy, and Cloudflare stops receiving reports for `alphasecunited.com` when DMARC Management is disabled under the zone.

## Open

- [x] Add `_dmarc.alphasecunited.com`. Done 2026-10-15 through DMARC Management, above.
- [x] Flip the DKIM signing toggle for `alphasecunited.com` in the Defender portal and confirm a sent message carries a `DKIM-Signature` with `d=alphasecunited.com`. Done 2026-10-15 at 8:39 PM, above.
- [ ] After a few weeks of DMARC Management showing only Microsoft 365 and Resend as passing senders, move `alphasecunited.com` to `p=quarantine`, then `p=reject`.
- [ ] Decide whether to enable the managed `security.txt` on `alphsec.com`, `alphasecunited.com` and `duresakadi.com`.
- [ ] Mark the six Intune and Entra findings Accept risk in Security Insights, and dismiss the AI Labyrinth suggestion. The API I use has no call for classifications, so this is six clicks in the dashboard.
