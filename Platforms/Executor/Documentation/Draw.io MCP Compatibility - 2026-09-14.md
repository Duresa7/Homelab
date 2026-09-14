# Draw.io MCP Compatibility

**Created:** 2026-09-14  
**Last updated:** 2026-09-14  
**Assessment date:** 2026-09-14

I assessed `jgraph/drawio-mcp` against my self-hosted Executor 1.6.8. The remote App Server fits Executor's MCP transport, but its inline diagram viewer does not pass through Executor's ordinary `execute` interface. I can use its shape search and XML text results; the interactive draw.io experience needs a direct connection from an MCP Apps-capable client or additional integration work. This is a source-based compatibility assessment, not a completed draw.io deployment.

## Verified local state

I checked the running container through SSH Manager on `docker_blue`. Its OCI version is `1.6.8`, its root filesystem is read-only, `EXECUTOR_ALLOW_LOCAL_NETWORK=true`, and `EXECUTOR_ALLOW_STDIO_MCP=false`. Executor's live connection inventory returned seven connections and no draw.io connection. I made no configuration changes and retained no standalone terminal transcript for these checks.

The first SSH request used `docker-blue`, which was not a configured SSH Manager alias. I retried with `docker_blue`. A `sudo` heredoc also failed because its input conflicted with password input; the subsequent `python -c` inspection succeeded.

I also tested the hosted draw.io endpoint from `docker_blue` with Python `urllib`. Initialization returned HTTP `200` without authentication when I used `User-Agent: node`; the default Python user agent had returned HTTP `403`. The server negotiated protocol `2025-03-26` and identified itself as `drawio-mcp-app` version `1.0.0`. An initial tool-list request without the session returned HTTP `400`. After retaining the `Mcp-Session-Id` and sending `notifications/initialized`, tool discovery succeeded and listed `create_diagram` and `search_shapes`.

I called `create_diagram` with synthetic XML labelled `Compatibility test`. It succeeded and returned text containing JSON with the XML and `_buildId: 42835e3@2026-08-02T20:17:10.515Z`. This establishes hosted endpoint reachability and basic tool operation from the Docker host. It does not establish an Executor connection or browser rendering. I retained no standalone terminal transcript for this probe, and the hosted build differs from the repository revision inspected below.

## Transport and output

| Approach | What I verified upstream | Fit with my deployment |
|---|---|---|
| Hosted App Server, `https://mcp.draw.io/mcp` | Remote Streamable HTTP; `create_diagram` and `search_shapes`; no local desktop installation required. | Compatible transport. Discovery and tool execution still require an end-to-end Executor integration test. |
| Self-hosted App Server | The Node entry point serves `/mcp` on port `3001`; its default listen address is `127.0.0.1`, configurable with `LISTEN`. | Possible separate HTTP service. Self-hosting changes where requests go, but does not supply the missing viewer forwarding. |
| Tool Server, `npx @drawio/mcp` | STDIO transport; XML, CSV, and Mermaid editor URLs; shape search and local `.drawio` page operations. | Cannot run directly in my current Executor configuration because STDIO is disabled. A separate HTTP bridge would be additional work. |

I checked the [App Server entry point](https://github.com/jgraph/drawio-mcp/blob/14b318b19cc37b159f841227b9d11fbd18ce18ea/mcp-app-server/src/index.js), [App Server documentation](https://github.com/jgraph/drawio-mcp/blob/14b318b19cc37b159f841227b9d11fbd18ce18ea/mcp-app-server/README.md), [Tool Server implementation](https://github.com/jgraph/drawio-mcp/blob/14b318b19cc37b159f841227b9d11fbd18ce18ea/mcp-tool-server/src/index.js), and [Executor 1.6.8 remote connector](https://github.com/UsefulSoftwareCo/executor/blob/2dc399e51094fccd2a45103a38d77179c6d648ff/packages/plugins/mcp/src/sdk/connection.ts).

The Tool Server launches the browser on the machine running that server. On Linux it spawns `xdg-open`, logs launch errors, and returns an editor URL regardless. Running it behind a headless gateway would therefore give me a clickable URL, not open a browser on my workstation. Its file tools would also read the server's filesystem. I verified these behaviors in the [Tool Server implementation](https://github.com/jgraph/drawio-mcp/blob/14b318b19cc37b159f841227b9d11fbd18ce18ea/mcp-tool-server/src/index.js#L217).

## Why the inline viewer does not follow the tool call

The draw.io App Server advertises `_meta.ui.resourceUri` pointing to `ui://drawio/mcp-app.html`. Its tool returns JSON inside text content; the host must fetch the HTML resource and render it to turn that data into an interactive diagram. I verified this in the [draw.io tool and resource registration](https://github.com/jgraph/drawio-mcp/blob/14b318b19cc37b159f841227b9d11fbd18ce18ea/mcp-app-server/src/shared.js#L6515) and the [MCP Apps protocol overview](https://modelcontextprotocol.io/extensions/apps/overview).

Executor 1.6.8 preserves downstream `_meta` in its internal [tool manifest](https://github.com/UsefulSoftwareCo/executor/blob/2dc399e51094fccd2a45103a38d77179c6d648ff/packages/plugins/mcp/src/sdk/manifest.ts). Its external `execute` tool, however, has no draw.io UI metadata and wraps execution output in its own response. The inspected host implementation registers Executor's own artifact shell resource; it does not register a downstream draw.io resource proxy. Executor's own MCP Apps artifact support therefore does not establish downstream MCP Apps compatibility. I checked the [execution output formatter](https://github.com/UsefulSoftwareCo/executor/blob/2dc399e51094fccd2a45103a38d77179c6d648ff/packages/hosts/mcp/src/tool-server.ts#L629), [`execute` registration](https://github.com/UsefulSoftwareCo/executor/blob/2dc399e51094fccd2a45103a38d77179c6d648ff/packages/hosts/mcp/src/tool-server.ts#L1551), and [shell resource registration](https://github.com/UsefulSoftwareCo/executor/blob/2dc399e51094fccd2a45103a38d77179c6d648ff/packages/hosts/mcp/src/tool-server.ts#L2065).

My conclusion is that normal tool calls can work through Executor while the draw.io viewer cannot appear through that route without an adapter. I did not test an inline viewer end to end.

## Useful fallback and remaining work

For an Executor-only workflow, I would request XML, use `search_shapes` when diagram symbols are needed, and save the returned `xml` value as a `.drawio` file. The App Server does not return an editor URL or PNG/SVG/PDF export. Its current implementation also accepts Mermaid, but Mermaid conversion, ELK layout, and libavoid routing happen in the viewer. A successful text response does not prove those browser operations ran. The root README's XML-only comparison table does not match the current [App Server implementation](https://github.com/jgraph/drawio-mcp/blob/14b318b19cc37b159f841227b9d11fbd18ce18ea/mcp-app-server/src/shared.js#L6638).

For the next integration trial, the hosted HTTP endpoint requires the least deployment work. Diagram input would be sent to the hosted draw.io service; a separate self-hosted App Server would keep that MCP request on my own server. I checked this distinction against the project's [data residency documentation](https://github.com/jgraph/drawio-mcp/blob/14b318b19cc37b159f841227b9d11fbd18ce18ea/README.md#data-residency--offline-use).

I have not added a connection, changed Executor policy, deployed a bridge, or validated a diagram through Executor. Those remain separate from this assessment.
