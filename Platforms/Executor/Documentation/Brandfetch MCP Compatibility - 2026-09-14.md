# Brandfetch MCP Compatibility

**Created:** 2026-09-14  
**Last updated:** 2026-09-25  
**Assessment date:** 2026-09-14

**Follow-up:** I completed the [Brandfetch integration](Change%20Records/Brandfetch%20MCP%20Integration%20-%202026-09-14.md) later on 2026-09-14 using a bearer token. The assessment below records the earlier checks.

I checked whether I can connect `https://mcp.brandfetch.io/mcp` to my self-hosted Executor. The hosted Streamable HTTP server fits the remote MCP integration type already in use. Authentication and an end-to-end tool call remain untested; I have not added a Brandfetch integration or connection.

## Live checks

I read Executor's live connection inventory. It returned seven connections, with no Brandfetch connection. My first inventory formatter treated `data` as an array and failed with `not a function`; reading `data.connections` succeeded. I retained no standalone transcript for this check.

I sent an unauthenticated MCP `initialize` request from `docker_blue` through SSH Manager, using protocol `2025-03-26` and `User-Agent: node`. The endpoint returned HTTP `401` with `Missing API credentials`, confirming host reachability but not successful MCP initialization. The response had no `WWW-Authenticate` header. Both OAuth metadata requests below returned HTTP `200`. The probe exited with code `0` and empty stderr. I retained no standalone terminal transcript for this probe.

| Metadata | Observed result |
|---|---|
| `https://mcp.brandfetch.io/.well-known/oauth-protected-resource` | Authorization server `https://developers.brandfetch.com`; bearer credentials supported in a header |
| `https://developers.brandfetch.com/.well-known/oauth-authorization-server` | Authorization code flow, PKCE `S256`, scope `read`, dynamic registration at `/api/oauth/register`; no client metadata document support advertised |

I also ran the same unauthenticated checks from `ubuntu-dev` and observed the same results. Looking for authorization-server metadata on the MCP hostname returned HTTP `404`; the protected-resource document correctly directs that request to `developers.brandfetch.com`.

## Connection approach

I would use an MCP integration named `Brandfetch MCP`, namespace `brandfetch`, with endpoint `https://mcp.brandfetch.io/mcp`. Brandfetch's [current authentication documentation](https://docs.brandfetch.com/mcp/overview) supports browser OAuth or an MCP token generated in the Developer Dashboard's Keys and MCP section, supplied as an `Authorization` bearer header.

The live metadata suggests OAuth can use dynamic client registration, avoiding the specific client metadata document fetch that failed for [Cloudflare Account MCP](Change%20Records/Cloudflare%20Account%20MCP%20Integration%20-%202026-09-06.md). I have not tested registration, callback acceptance, or Executor's automatic discovery against the headerless `401`, so this is a compatibility inference. A dedicated MCP token in Executor's encrypted connection credential store provides another supported authentication path.

The initial search-engine copy of Brandfetch's documentation showed an older URL containing `apiKey` and `clientId` query parameters. Opening the current page showed OAuth and bearer-token instructions instead. I used the current page for this assessment.

## Tools and remaining verification

I checked the [official server repository](https://github.com/Brandfetch/brandfetch-mcp-server), which documents `brand_search`, `get_brand`, `get_brand_context`, `enrich_transaction`, `build_logo_urls`, `get_asset_base64`, and `send_feedback`. This is the documented catalog, not an authenticated live tool count. The repository says brand retrieval, context, and transaction enrichment consume API credits; brand search and logo URL construction do not consume those credits.

Brandfetch's documentation also describes an interactive brand card on MCP Apps hosts. I would expect normal data calls to be the useful Executor path; I have not verified forwarding that card through Executor.

To complete the integration, I still need to authenticate a Brandfetch connection, discover its actual tools through Executor, and run a brand search. No credentials were used, API-credit-consuming tools called, or Executor configuration changed during this assessment.
