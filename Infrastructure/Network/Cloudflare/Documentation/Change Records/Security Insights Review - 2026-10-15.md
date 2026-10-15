# Security Insights Review

**Created:** 2026-10-15  
**Last updated:** 2026-10-15

**Implementation date:** 2026-10-15  
**Status:** HSTS applied; DMARC, security.txt and the Accept-risk classifications open  
**Affected systems:** Cloudflare zone `alphsec.com` (HSTS), the Cloudflare login (two-factor authentication), Security Insights classifications  
**Related:** [Coolify Webhook Bypass Limited to GitHub - 2026-10-15](Coolify%20Webhook%20Bypass%20Limited%20to%20GitHub%20-%202026-10-15.md)

I ran a full Security Insights scan at 9:19 AM after narrowing the Coolify webhook bypass that morning. The Critical `Overprovisioned Access Policies` finding was gone. The export held 22 findings, 12 Moderate and 10 Low, and this record is what I decided about each. All times are EDT.

## The findings

| Finding | Subject | Severity | Decision |
|---|---|---|---|
| Users without MFA | the Cloudflare login | Moderate | Fixed. I enabled two-factor authentication on the login the same morning |
| Domains without HSTS | `coolify-a1.alphsec.com` | Moderate | Fixed, below |
| Unproxied CNAME record, no Always Use HTTPS, no TLS | `enterpriseenrollment.alphasecunited.com` and `enterpriseregistration.alphasecunited.com`, three findings each | Moderate | Accept risk. These are the Intune and Entra device-registration CNAMEs to Microsoft. They must stay DNS-only, and the plain-HTTP answer the scanner saw is Microsoft's own 302 to `intune.microsoft.com` |
| DMARC record error | `alphasecunited.com`, `send.mail.alphasecunited.com` | Low | Open. Both carry SPF and MX and no `_dmarc` record. One record at `_dmarc.alphasecunited.com` with `p=none` and a report address covers the subdomain; I still need to decide the mailbox that receives the reports |
| Security.txt not configured | `alphsec.com`, `alphasecunited.com`, `duresakadi.com` | Low | Open. Cloudflare serves a managed `security.txt` per zone from the dashboard; it only answers on proxied hostnames |
| Review AI crawlers with AI Labyrinth | `alphasecunited.com` | Low | Dismiss. A feature suggestion, not a finding |
| Dangling A record (four), DMARC, Always Use HTTPS, Security.txt | `duresakadi.me` | Moderate and Low | Out of scope. I am leaving that zone as it is, and it stays undocumented here |

The zone readback behind the table: `alphsec.com` had Always Use HTTPS on and HSTS off; `alphasecunited.com` has no proxied record at all, with the apex and `www` on Vercel and every other name DNS-only; `duresakadi.com` had Always Use HTTPS on and only proxied placeholder records besides the UniFi names.

## What changed

At 10:28:46 AM I enabled HSTS on `alphsec.com` through the API: `strict_transport_security` enabled, `max_age` 15552000 (180 days), `include_subdomains` true, `preload` false, `nosniff` unchanged at false. Every name in that zone is a proxied CNAME to the tunnel and answers only over HTTPS, so there is nothing in the zone the header can break. Preload stays off because it cannot be undone inside the 180 days once a browser list has it.

## Verification

- A request to `https://coolify-a1.alphsec.com/login` returned `302` to Access with `strict-transport-security: max-age=15552000; includeSubDomains`.
- A request to `http://coolify-a1.alphsec.com/login` still returned `301` to the HTTPS URL, so Always Use HTTPS is unchanged.
- The API read the setting back with the values above, `modified_on` 2026-10-15T14:28:46Z.

## Rollback

Set `strict_transport_security.enabled` back to false. Browsers that have seen the header keep enforcing HTTPS for up to 180 days, which costs nothing here.

## Open

- [ ] Add `_dmarc.alphasecunited.com` once I have the report mailbox: `v=DMARC1; p=none; rua=mailto:<mailbox>`, then move to `p=quarantine` after a few weeks of clean reports.
- [ ] Decide whether to enable the managed `security.txt` on `alphsec.com`, `alphasecunited.com` and `duresakadi.com`.
- [ ] Mark the six Intune and Entra findings Accept risk in Security Insights, and dismiss the AI Labyrinth suggestion. The API I use has no call for classifications, so this is six clicks in the dashboard.
