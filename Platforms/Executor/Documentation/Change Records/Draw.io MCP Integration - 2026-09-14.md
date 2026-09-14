# Draw.io MCP Integration

**Created:** 2026-09-14  
**Last updated:** 2026-09-14

I connected the official hosted draw.io MCP to Executor and verified both tools through `execute`. This completes the connection work left open in the [compatibility assessment](../Draw.io%20MCP%20Compatibility%20-%202026-09-14.md).

| Setting | Saved value |
|---|---|
| Display name | `Draw.io MCP` |
| Integration | `drawio` |
| Endpoint | `https://mcp.draw.io/mcp` |
| Transport | Remote, `streamable-http` |
| Authentication | `none` |
| Connection owner and name | `user`, `drawio` |
| Connection address | `tools.drawio.user.drawio` |
| Identity label | `Draw.io MCP` |
| Tools | `create_diagram`, `search_shapes` |
| Workspace policy | `drawio.*`, Always run (`approve`), added during the follow-up verification |

I registered the integration with `executor.mcp.addServer`, read it back with `executor.mcp.getServer`, and created the personal connection with `executor.coreTools.connections.create`. The saved configuration contains the expected endpoint, transport, and no-auth template. No custom request headers or credentials were needed.

I searched the `drawio` namespace and found exactly two tools. Through `drawio.user.drawio.search_shapes`, the query `router` with limit `2` returned the Cisco `10700` and `ATM Router` shapes with style strings and dimensions. Through `drawio.user.drawio.create_diagram`, a synthetic rectangle labelled `Executor connection verified` returned successful text content. Parsing that content confirmed the returned XML exactly matched the submitted XML. The response identified build `42835e3@2026-08-02T20:17:10.515Z`.

A connection refresh returned both tool addresses, and a saved-connection read confirmed the personal connection. Executor reported `lastHealth: null`, so the successful calls are the operational verification; I did not record a healthy badge that the API did not supply. Both initial calls completed without an approval pause; I added an explicit policy during the follow-up below. I retained no separate raw tool transcript for this change.

The hosted service receives diagram input. I can save the returned XML as a `.drawio` file and open it in the browser editor without draw.io Desktop. The inline viewer and its browser-side layout/conversion remain outside Executor's ordinary `execute` path, as described in the compatibility assessment. No container restart, desktop installation, or STDIO configuration change was required.

## Follow-up against the earlier gateway failures

I compared this connection with the [SSH managed-container accumulation](../../../Docker%20MCP%20Gateway/Documentation/Troubleshooting/Managed%20SSH%20Manager%20Containers%20Accumulated%20Under%20long-lived%20-%202026-09-03.md) and the [UniFi shared-server cutover](../../../Docker%20MCP%20Gateway/Documentation/Change%20Records/UniFi%20Shared%20Server%20Cutover%20-%202026-09-07.md). Those failures involved gateway-managed containers per MCP session, SSH process exhaustion, and repeated UniFi controller logins. The saved draw.io configuration points directly to the hosted HTTPS endpoint with no authentication. There is no draw.io Docker gateway, local child process, or controller login in that path.

I issued six concurrent, separate Executor executions: three `search_shapes` calls and three `create_diagram` calls. Every shape response contained the requested two results with titles and styles, and every diagram response exactly matched its unique submitted XML. Measured tool-call times were 106, 106, 110, 112, 259, and 676 milliseconds. None returned an approval pause or transport error.

Before and after the burst, Docker inspection on `docker_blue` showed the same five Executor/MCP containers, unchanged start times, and zero restart counts. No local draw.io container or additional managed MCP container appeared. This checks the relevant concurrent-call behavior, rather than relying only on repeated calls within one execution. It is a bounded test, not a long-duration session or memory-leak audit.

I found no draw.io policy in the live policy list and added workspace policy `drawio.*` with action `approve`, matching the explicit Always run policy used for UniFi and SSH. I read it back, refreshed the draw.io connection, confirmed both tool addresses remained present, and passed another shape-search call. The refresh still reported `lastHealth: null`; tool execution supplies the success evidence. I retained no separate raw transcript for this follow-up.

Executor's [60-second tool-call limit](../Troubleshooting/Integration%20Tool%20Calls%20Time%20Out%20at%2060%20Seconds%20-%202026-09-07.md) still applies. The tests completed well below it, but this setup cannot guarantee against a hosted-service outage, rate limit, or future timeout. I did not restart services or change global timeout settings.
