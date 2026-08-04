# Coolify Access Hardening

**Created:** 2026-07-22  
**Last updated:** 2026-07-31

## Summary

I replaced the reusable `Webhook Bypass` policy that exposed the entire `coolify-a1.alphsec.com` application with a path-scoped GitHub webhook exception. I didn't change Cloudflare Tunnel ingress, DNS, the Coolify origin, or any deployed application route.

## Change

1. I saved the pre-change Access application and policy state to `access-coolify-20260722T215406Z.json`, retained on my workstation outside this repository.
2. I created `Coolify GitHub Webhook` for `coolify-a1.alphsec.com/webhooks/source/github/events` with a bypass policy.
3. I removed the reusable `Webhook Bypass` policy from the root Coolify application and deleted the unused reusable policy.
4. I created `Coolify GitHub Webhook Child Paths` for `coolify-a1.alphsec.com/webhooks/source/github/events/*` with the same allow policy as the root application. This protects every child route while leaving the exact GitHub endpoint reachable.

## Verification

- A request to `/login` redirected to `AlphaSec.cloudflareaccess.com`, so the dashboard is protected.
- A request to `/wp-content` redirected to `AlphaSec.cloudflareaccess.com`, so a common scanner path doesn't reach Coolify.
- A request to the exact `/webhooks/source/github/events` path reached Coolify and returned its own redirect to `/login`, so Cloudflare didn't challenge the webhook endpoint.
- Requests to `/webhooks/source/github/events/`, `/webhooks/source/github/events/manual`, and an unmatched child path redirected to `AlphaSec.cloudflareaccess.com`.
- The Cloudflare API showed one allow policy on the root application, one bypass policy on the exact webhook application, and one allow policy on the wildcard child-path application.

## Rollback

The pre-change JSON snapshot contains the original application and reusable policy bodies. I can recreate the former broad bypass from that snapshot, but doing so would expose every Coolify route to unauthenticated requests again.

## UniFi Edge Path Restriction

I changed policy `699d0001c9d00a2842ccf453` from the entire Servers-A network on any TCP port to app-01 at `192.168.80.10` through the `App Access` port group. That group contains TCP 80 and 8000. The source remains the edge-01 client, and the policy's protocol, index, logging, connection state, and automatic response setting are unchanged.

I saved the complete pre-change state to `firewall_20260722T220050Z.json`, retained on my workstation outside this repository. Its SHA-256 digest is `7456B8E21D16A9D3BC96C1038B9C4CDB2D981FF40310C4253892AEBFE8A03C44`.

### Verification

- From edge-01, new connections to app-01 TCP 80 and 8000 succeeded.
- From edge-01, new connections to app-01 TCP 22, 443, 6001, 6002, and 9100 failed.
- From my Internal workstation, SSH to app-01 and edge-01 remained reachable on TCP 22.
- Read-only SSH health checks authenticated successfully to both app-01 and edge-01, and both hosts reported healthy.
- Caddy and cloudflared remained active on edge-01.
- An HTTP request from edge-01 to app-01 TCP 80 returned an application-layer 404, and the Coolify login on TCP 8000 returned 200. Both results prove the two required backend paths crossed the firewall.
- The public Coolify login remained behind Cloudflare Access, while the exact GitHub webhook continued to reach Coolify.

I saved the post-change state to `firewall_20260722T221119Z.json`, retained the same way. Its SHA-256 digest is `920EA04A0E2A1775BCE7FFB91B60A1C3E19CCDBD094C7040D631F47508ED95D1`.

### Rollback

The pre-change snapshot contains the complete original destination object. Restoring it would reopen edge-01 to the full Servers-A network on any TCP port, so I will use it only if the restricted path prevents a required service from operating.
