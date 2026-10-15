# Coolify Webhook Bypass Limited to GitHub

**Created:** 2026-10-15  
**Last updated:** 2026-10-15

**Implementation date:** 2026-10-15  
**Status:** Complete; a GitHub redelivery succeeded after app-01 returned  
**Affected systems:** Access application `Coolify GitHub Webhook`, its policy `GitHub Webhook Bypass`, and the new Zero Trust IP list `GitHub Webhooks`  
**Earlier change:** [Coolify Access Hardening - 2026-07-22](Coolify%20Access%20Hardening%20-%202026-07-22.md)

Cloudflare Security Insights raised a Critical `Overprovisioned Access Policies` finding (`access_policy_insecure`, type `exposed_infrastructure`) on `coolify-a1.alphsec.com/webhooks/source/github/events`. It first saw the condition on 2026-08-11 and last evaluated it on 2026-10-13. The cause was the bypass I created on 2026-07-22: it included `Everyone`, so any address on the internet reached Coolify's GitHub App webhook handler without Access, and the only check left was Coolify's own signature verification.

I kept the bypass, because GitHub can't complete an Access login and can't send custom headers, which rules out a service token. I narrowed who it applies to instead. All times are EDT.

## What changed

1. At 8:31:58 AM I created the Zero Trust IP list `GitHub Webhooks` with the nine ranges in the `hooks` key of `https://api.github.com/meta`, read the same morning:

   | Family | Ranges |
   |---|---|
   | IPv4 | `9.234.106.48/28`, `9.234.98.160/28`, `9.234.98.176/28`, `192.30.252.0/22`, `185.199.108.0/22`, `140.82.112.0/20`, `143.55.64.0/20` |
   | IPv6 | `2a0a:a440::/29`, `2606:50c0::/32` |

2. At 8:32:05 AM I changed the include rule on `GitHub Webhook Bypass` from `Everyone` to that IP list. The decision stayed Bypass, precedence 1, with no exclude or require rules. The policy is still scoped to the one application, not reusable.

I didn't change the `Coolify` or `Coolify GitHub Webhook Child Paths` applications, Tunnel ingress, DNS, Bot Fight Mode, or anything on edge-01 or app-01.

Rollback is setting the include rule back to `Everyone`, which restores the finding.

## Verification

Before the change, from my workstation, which is outside GitHub's ranges, a request with a browser user agent to the exact webhook path passed Access and returned a Cloudflare `502`. `/login` and `/webhooks/source/github/events/manual` redirected to `alphsec.cloudflareaccess.com`.

The 502 is app-01 being off, not a fault: I stopped it on 2026-10-09 and disabled its automatic startup, as recorded in [VMs](../../../../../Operations/Inventory/Galaxy/VMs.md). From edge-01, `http://192.168.80.10:8000/api/health` timed out with no response, the SSH Manager reported `EHOSTUNREACH 192.168.80.10:22`, and Caddy on edge-01 answered the webhook path with `502`. `cloudflared` and `caddy` were both `active`.

After the change, from the same workstation:

| Request | Result |
|---|---|
| `GET /webhooks/source/github/events` | `403`, page title `Error ・ Cloudflare Access`, body `Forbidden`, with `cf-access-domain: coolify-a1.alphsec.com` |
| `POST /webhooks/source/github/events`, user agent `GitHub-Hookshot/abc123` | `403` |
| `GET /webhooks/source/github/events/manual` | `302` to `alphsec.cloudflareaccess.com` |
| `GET /login` | `302` to `alphsec.cloudflareaccess.com` |

The exact path now ends at Access for an address outside the list. It returns Forbidden rather than a login page because that application has no Allow policy, so no identity could pass it. The dashboard and child paths behave as before.

The Cloudflare API showed the list holding all nine ranges and the policy's include as the single `ip_list` rule.

### Delivery from GitHub

I started app-01 at 8:57 AM. All six containers reported healthy within a minute, `http://192.168.80.10:8000/api/health` answered `200` from this workstation, and from edge-01 a `POST` to the webhook path on app-01:8000 returned `200`. The same four requests from this workstation through Cloudflare gave the same results as before app-01 came up, so the origin being alive changes nothing for an address outside the list.

At 9:03:17 AM I redelivered the 2026-10-14 1:08 PM push event from the `duresa7-git-access` GitHub App's Recent Deliveries page. GitHub marked the redelivery successful. The five deliveries before it, from 2026-10-13 12:12 AM to 2026-10-14 1:08 PM, all show as failed; they were sent while app-01 was off.

That one redelivery is the end-to-end check: GitHub's source address matched the list, Bot Fight Mode did not challenge it, and the request crossed the tunnel to Coolify.

I started app-01 only for this test. It goes back off afterwards, so its [VMs](../../../../../Operations/Inventory/Galaxy/VMs.md) row stays at stopped with automatic startup disabled, and the Grafana silences that run to 2026-10-25 stay in place.

## What I saw along the way

A plain `curl` with its default user agent got a managed challenge (`cf-mitigated: challenge`, `Just a moment...`) on every path of the host, before Access ran. The zone has Bot Fight Mode on, with security level `medium`, and no custom WAF rules. On the Free plan, a WAF skip rule can't exempt a path from Bot Fight Mode. The successful redelivery shows GitHub's deliveries get through it; a scripted client with a bare user agent does not, which is fine for this host.

Coolify holds three GitHub App sources, `Public GitHub`, `duresa7-git-access` and `jen-access`. I tested only `duresa7-git-access`; `jen-access` delivers to the same path from the same GitHub ranges.

## Open

- [ ] Confirm the Security Insights finding clears on its next scan. If the scanner still flags an IP-scoped bypass, mark it Accept risk and link this record.
- [ ] Keep the list current. GitHub adds ranges to `hooks` without notice; the three `9.234.x` ranges are recent ones. A delivery from a missing range fails at Access and shows only as a failed row in GitHub's Recent Deliveries. Compare the list against `api.github.com/meta` when I next work on Coolify, or automate the sync.
