# Brandfetch MCP Integration

**Created:** 2026-09-14  
**Last updated:** 2026-09-14

I connected Brandfetch to Executor using the stored MCP token and verified a brand search through Executor. This completes the authentication and discovery work left open in the [compatibility assessment](../Brandfetch%20MCP%20Compatibility%20-%202026-09-14.md).

| Setting | Verified value |
|---|---|
| Display name | `Brandfetch MCP` |
| Integration namespace | `brandfetch` |
| Endpoint | `https://mcp.brandfetch.io/mcp` |
| Transport | Remote Streamable HTTP |
| Connection | Personal `brandfetch`, address `tools.brandfetch.user.brandfetch` |
| Authentication | Template `header`, API key applied to `Authorization` with prefix `Bearer ` |
| Credential provider | `encrypted` |
| Static integration headers | Empty |
| Discovered tools | 6 |

I retrieved the stored credential into process memory and passed it to Executor's HTTPS API. The token was not written to a script, command argument, or evidence file. I retained no standalone terminal transcript for these operations.

## Creation and verification

Executor's authenticated `/api/mcp/probe` returned HTTP `200`, `connected: true`, server name `brandfetch-mcp-server`, and six tools. The first integration creation attempt returned HTTP `400` with an empty body. Retrying the same payload, including with an Origin header, returned the same result. I had sent the stored authentication placement shape to an endpoint that accepts an authored authentication template or shorthand. Switching to the documented shorthand `auth: {kind: "header", headerName: "Authorization", prefix: "Bearer "}` resolved the request.

Creating the integration, creating its connection, and refreshing discovery each returned HTTP `200`. Readback confirmed the endpoint and bearer template, with no static header values. Executor's connection inventory confirmed provider `encrypted` and address `tools.brandfetch.user.brandfetch`.

The live catalog contains `brand_search`, `get_brand`, `enrich_transaction`, `get_brand_context`, `build_logo_urls`, and `send_feedback`. The hosted catalog does not expose the `get_asset_base64` tool listed in the repository documentation checked during the assessment.

I discovered and described `brandfetch.user.brandfetch.brand_search` through Executor, then called it with `query: "Nike"`. The call succeeded without an approval pause and returned five matches, with `Nike` at `nike.com` first. I returned only names and domains from the result. I retained no standalone transcript for this tool verification.

## Verification scope

Authentication, tool discovery, and brand search are verified. I did not call the tools that consume API credits, download assets, test the interactive brand card, or send feedback to Brandfetch. I made no policy changes. No additional container or client configuration was required.
