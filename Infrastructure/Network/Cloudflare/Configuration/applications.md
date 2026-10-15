# Cloudflare Access Applications

**Created:** 2026-07-22  
**Last updated:** 2026-10-15

I last verified these Access applications against the Cloudflare API on 2026-09-06, through the Executor Cloudflare Account MCP connection. All three were unchanged since 2026-07-22, and the two allow applications share one reusable policy, `Allow dkadi`, with the same two email identities. On 2026-10-15 I limited the webhook bypass to GitHub's webhook ranges, held in the Zero Trust IP list `GitHub Webhooks`; [change record](../Documentation/Change%20Records/Coolify%20Webhook%20Bypass%20Limited%20to%20GitHub%20-%202026-10-15.md).

| Application | Protected URL | Decision | Purpose |
|---|---|---|---|
| Coolify | `coolify-a1.alphsec.com` | Allow two approved email identities | Protect the dashboard and all routes without a more-specific application |
| Coolify GitHub Webhook | `coolify-a1.alphsec.com/webhooks/source/github/events` | Bypass for the `GitHub Webhooks` IP list only | Let GitHub deliver signed Coolify webhooks to the exact configured endpoint; any other address gets Access `Forbidden` |
| Coolify GitHub Webhook Child Paths | `coolify-a1.alphsec.com/webhooks/source/github/events/*` | Allow two approved email identities | Prevent the webhook bypass from being inherited by manual, unknown, or future child routes |

Cloudflare evaluates the more-specific child-path application before the exact webhook application's inherited policy. I don't publish the dashboard, child paths, or common scanner targets without Access authentication.
