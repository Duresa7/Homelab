# Cloudflare Access Applications

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

I last verified these Access applications against the Cloudflare API on 2026-07-22.

| Application | Protected URL | Decision | Purpose |
|---|---|---|---|
| Coolify | `coolify-a1.alphsec.com` | Allow two approved email identities | Protect the dashboard and all routes without a more-specific application |
| Coolify GitHub Webhook | `coolify-a1.alphsec.com/webhooks/source/github/events` | Bypass | Let GitHub deliver signed Coolify webhooks to the exact configured endpoint |
| Coolify GitHub Webhook Child Paths | `coolify-a1.alphsec.com/webhooks/source/github/events/*` | Allow two approved email identities | Prevent the webhook bypass from being inherited by manual, unknown, or future child routes |

Cloudflare evaluates the more-specific child-path application before the exact webhook application's inherited policy. I don't publish the dashboard, child paths, or common scanner targets without Access authentication.
