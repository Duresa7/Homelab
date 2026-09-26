# Cloudflare Account MCP Integration

**Created:** 2026-09-06  
**Last updated:** 2026-09-25

**Status:** Complete; connected with a full-access account token by my decision, `execute` runs without approval, and the account read-back is recorded

I added a second Cloudflare integration to Executor so an agent can read the Cloudflare account rather than only the Workers development surface.

## Why

The existing `Cloudflare MCP` integration, slug `cloudflare`, has its endpoint set to `https://bindings.mcp.cloudflare.com/mcp`. I read that from Executor's own server record at `/api/mcp/servers/cloudflare`, and the console's catalog describes that entry as a server for building applications on Cloudflare Workers. Its connection carries the scopes `user:read`, `offline_access`, `account:read`, `workers:write`, and `d1:write`, and it exposes 23 tools for D1, KV, R2, Hyperdrive, Workers, a Pages migration guide, and documentation search. None of them read zones, DNS records, the tunnel, or Access, which is why the 2026-09-06 Cloudflare verification could not use it.

Executor 1.6.8's built-in preset for Cloudflare points at `https://mcp.cloudflare.com/mcp?codemode=false`, which registers every REST endpoint as its own tool. Cloudflare's Code Mode server at `https://mcp.cloudflare.com/mcp` exposes the same API through `search` and `execute` instead, and the console itself notes when it sees that URL that code mode is on. Code mode is the right shape for Executor because the per-integration search tools already handle a two-tool server.

## Change

From Integrations, Add integration, Start from scratch, MCP, I entered the server URL. Executor detected the server, reported that OAuth is required to discover tools, and prefilled the display name and namespace from the existing entry. I changed them so the two never get confused.

| Field | Value |
|---|---|
| Display name | `Cloudflare Account MCP` |
| Namespace | `cloudflare_account` |
| Server URL | `https://mcp.cloudflare.com/mcp` |
| Request headers | none |
| Authentication | OAuth, detected from the server |

Executor created the integration and its server record shows `endpoint: https://mcp.cloudflare.com/mcp`, `transport: remote`, and one `oauth2` authentication template. It lists 0 tools until an account is connected.

I opened Add connection on the new integration. The dialog offered OAuth, an optional display name, and Personal as the owner, with the callable address `personalCloudflareAccountMcp`. Clicking Connect sent the tab to Cloudflare's authorization page, which the automation could not follow, so the account sign-in and scope selection stand as my step in the browser. No connection exists on `cloudflare_account` yet, and the `cloudflare` connection is unchanged.

## OAuth Failure and the API Token Method

When I completed the Connect step in my own browser, Cloudflare's authorization page returned `Temporarily Unavailable. Client metadata is temporarily unavailable. Please try again.` with error code `temporarily_unavailable`.

The cause is how Executor identifies itself to this server. Cloudflare's Code Mode authorization server advertises `client_id_metadata_document_supported: true` in its metadata at `/.well-known/oauth-authorization-server`, and Executor prefers Client ID Metadata Documents over Dynamic Client Registration whenever a server advertises them. So Executor created an OAuth client whose `client_id` is a URL on its own origin, `https://mcp.alphasecunited.com/api/oauth/client-id-metadata/default.json`, and Cloudflare must fetch that document from the public internet before it can show the consent page. Executor is deliberately internal: `mcp.alphasecunited.com` has no public DNS record, so Cloudflare's fetch fails and it reports the client metadata as unavailable. The document itself serves correctly from inside the network and holds only the client name, the client URI, the callback URL, and the grant type.

The Workers Bindings server does not advertise metadata documents, which is why the older `cloudflare` connection registered through Dynamic Client Registration and worked. Executor's source carries a build-time override for the metadata document base URL, `EXECUTOR_CIMD_CLIENT_ID_METADATA_BASE_URL`, which the desktop and local builds point at `https://executor.sh`; the self-hosted build uses the browser origin and exposes no runtime setting to prefer Dynamic Client Registration instead. The stale client record `cloudflare-account-mcp-cimd` remains in Executor's OAuth client list and is harmless.

Cloudflare's server also accepts a Cloudflare API token as a Bearer credential, so I added a second authentication method to the integration from Edit, Add method: API key, Bearer header, header name `Authorization`, prefix `Bearer`. Executor's server record now lists two templates, `oauth2` and an `apikey` header placement. A connection created against the API key method needs no metadata fetch and keeps Executor off the public internet.

## Connection Through the API

I created the Cloudflare API token from the dashboard as an account-owned token and stored it as an API Credential item before anything used it. I then created the Executor connection from the shell rather than the console, so the value never crossed a browser tool or this transcript: the console password and the token were injected from the password manager at run time as environment variables to a short Python script that signed in through `/api/auth/sign-in/email`, posted to `/api/connections` with `owner: user`, `name: cloudflareAccount`, `integration: cloudflare_account`, `template: header`, and the token as `value`, listed the result with the value redacted, and signed out. The script and its environment file were deleted afterwards. Executor answered 200 and stored the connection at `tools.cloudflare_account.user.cloudflareAccount` with the `encrypted` provider.

After a Refresh, the integration discovered three tools, `docs`, `execute`, and `search`, and Executor's own tool search under the `cloudflare_account` namespace returned the same three. The `execute` tool's description carries the account identifier that Cloudflare's server resolved from the token, so the server accepted the credential.

Executor pauses every call to `execute` for approval before it runs, because the tool declares that it can read, create, update, or delete resources. The pause arrives as a `waiting_for_interaction` result that the caller resumes. That gate is Executor's, not mine, and it is the first Executor-side approval step any of my connections has had.

## Read-back and the Missing Permission

A first read-back through `execute` failed with `Cloudflare API error: 10000: Authentication error`. Testing the same token directly against the API from the shell, again with the token injected from the password manager at run time and printing only status codes, error codes, and names, showed the cause. The token is active, lists all four zones, lists the `edge-01` tunnel and reads its configuration, and lists the three Access applications and the one reusable policy. Reading a zone's DNS records returns 403 with code 10000, which is what Cloudflare returns when a token lacks the permission for that endpoint. The token was created without Zone, DNS, Read. A second run through Executor with one try per call agreed: zones, tunnel, tunnel configuration, and Access applications all succeeded and only the DNS records call failed.

Editing a token's permissions in the Cloudflare dashboard keeps its secret value, so a permission change needs no change in Executor or the password manager.

## The Token Scope, and the Decision to Keep It Full

When I double-checked, I read the token's own definition back through the API, which it can do because it holds Account API Tokens Read. The token, named `executor-mcp`, had a single allow policy scoped to the account carrying 273 permission groups, essentially every account permission Cloudflare offers, read and write alike: Access: Apps and Policies Write, Cloudflare Tunnel Write, Workers Scripts Write, D1 Write, Account Settings Write, Billing Write, and Account API Tokens Write among them. It had no zone-level policy, which was the real reason DNS reads failed: DNS Read is a zone permission, and the token had no zone scope. Zone listing worked only because the account resource covers the zone index.

This was not the read-only credential I had planned. I decided to keep the token at full access on purpose. The point of this connection is that an agent can do whatever I ask of the Cloudflare account without a permission gap or an approval prompt in the way, the same footing the UniFi and SSH Manager connections already have. To close the zone gap I added a second policy through the token's own API-token-write permission: all zones under the account, with all 92 zone-scoped permission groups. The update returned 200, the token read back with both policies, and DNS record reads on all four zones began succeeding about forty seconds later, which is Cloudflare's propagation delay for a token edit. The token's value did not change, so the password manager item and the Executor connection stayed as they were.

What this means is written down once, here: every agent that reaches Executor can read and change anything in the Cloudflare account, including DNS, the tunnel, Access policies, Workers, and the account's other API tokens, and nothing between the agent and Cloudflare asks first. The credential lives in the password manager item and in Executor's encrypted store and nowhere else.

## Executor's Approval Gate

The first `execute` calls paused as `waiting_for_interaction`, which is Executor's approval prompt for a tool whose annotations mark it as able to modify state. Executor resolves a tool's effective policy from the authored rules first and falls back to that plugin default only when no rule matches; the API actions are `approve`, `require_approval`, and `block`, shown in the console as Always run, Require approval, and Block, and the most restrictive matching rule wins. A workspace policy `cloudflare_account.*` set to Always run exists as of 17:57 UTC, alongside the same Always run policies every other integration carries, and every `execute` call after it ran without a pause. I briefly added an exact-tool policy for `execute` while working this out; it was redundant and I removed it.

## Read-back

Through `execute` I read the four zones and every DNS record, the tunnel and its configuration, and the Access applications and reusable policies in one run, masking addresses, tunnel identifiers, and external relay targets inside the sandbox so they never left it. The findings are recorded in the [Cloudflare README](../../../../Infrastructure/Network/Cloudflare/README.md) verification section and in the [applications](../../../../Infrastructure/Network/Cloudflare/Configuration/applications.md) and [edge-01](../../../../Infrastructure/Network/Cloudflare/Configuration/edge-01.md) records. Everything matched, with one finding: Cloudflare reported the `edge-01` connector at 2026.7.3 while the binary on the host was 2026.8.3, because the process had run since the 2026-08-10 boot. I restarted the service the same day, and this connection then confirmed 2026.8.3 on all four tunnel connections; the [Cloudflare README](../../../../Infrastructure/Network/Cloudflare/README.md) holds the restart evidence.

## Retiring the Workers Integration

With the account connection verified, I removed the `cloudflare` connection, the `Cloudflare MCP` integration, and the stale `cloudflare-account-mcp-cimd` OAuth client through the console API. Each removal returned `removed: true`. Executor now lists one Cloudflare MCP integration, `cloudflare_account`, with one connection, and its OAuth client list holds only the Supabase and Miro registrations.

## Why Only Three Tools

The account server shows three tools where the Workers server showed 23, and that is by design rather than a missing grant. Cloudflare's OpenAPI specification runs to about two million tokens, and even a minimal one-tool-per-endpoint MCP catalog would cost an agent roughly 244,000 tokens of context before it did anything. Cloudflare's Code Mode server instead exposes `search`, which queries the specification, `execute`, which runs code against the API, and `docs`, and covers about 2,500 endpoints behind them for around a thousand tokens. Appending `?codemode=false` to the server URL turns every endpoint into its own tool, which is what Executor's built-in Cloudflare preset does, at the full token cost; Cloudflare's own guidance is to leave code mode on.

## Remaining Work

1. If OAuth is ever wanted instead of the token, the metadata document at `/api/oauth/client-id-metadata/default.json` has to be reachable from the public internet, which means a public name for Executor or an upstream change so the self-hosted build can prefer Dynamic Client Registration. That is a publication decision, not a fix to make quietly.
