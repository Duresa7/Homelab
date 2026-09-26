# Docker MCP Gateway Integration

**Created:** 2026-08-31  
**Last updated:** 2026-09-25

## Outcome

I connected Executor 1.6.7 to Docker MCP Gateway at `http://192.168.40.39:8811/mcp`. Executor now discovers the gateway's 42 tools, 37 from SSH Manager and 5 from UniFi Network, and can invoke them through its `execute` tool.

The integration is `docker-mcp-gateway`. Its personal connection is `dockerMcpGateway`, stored under the claimed administrator account. The gateway bearer token is in Executor's encrypted credential provider rather than the integration URL or its static header map.

## Implementation

1. I enabled `EXECUTOR_ALLOW_LOCAL_NETWORK` in the live and versioned Compose definitions. The exception is required because the gateway endpoint is the host's internal address, `192.168.40.39:8811`. Local STDIO MCP servers remain disabled.
2. I verified the saved Executor login through the application endpoint and used the claimed account for the integration.
3. I registered Docker MCP Gateway as a remote MCP server over Streamable HTTP with an `Authorization: Bearer` credential template. I left the static header map empty.
4. I created personal connection `dockerMcpGateway` and imported the existing gateway bearer token from my credential store into Executor's encrypted credential provider.
5. I refreshed the connection so Executor discovered the complete gateway tool surface.

I did not create a snapshot or backup. Executor's persistent state already lives under `/opt/docker/executor/data`, and this change did not alter the gateway credential or either managed server. I retained no standalone command or API capture; the verification bullets below record the live results I observed.

## Verification

- The live Executor container was running and healthy with `EXECUTOR_ALLOW_LOCAL_NETWORK=true`; the live Compose file matched the versioned setting.
- Login returned HTTP 200 and an authenticated user session.
- A gateway probe without credentials reported that authentication was required. The same probe with the stored bearer credential connected to `Docker AI MCP Gateway` and reported 42 tools.
- The saved connection reports provider `encrypted`, while the integration configuration has no static headers.
- A connection refresh returned 42 tools. Executor classified 37 names under `ssh_` and 5 under `unifi_`.
- The connection health check returned `healthy`.
- Executor's MCP endpoint initialized over HTTPS with protocol version `2025-06-18` and exposed its seven native tools.
- An end-to-end `execute` call resolved `docker-mcp-gateway.user.dockerMcpGateway.ssh_list_servers` and returned `callOk: true`.
- A second end-to-end call ran `ssh_execute` against `docker_blue`; it returned `executor-gateway-ok`, an empty standard error stream, and exit code 0.
- An unauthenticated request to Executor's MCP endpoint remains HTTP 401.
- I stopped the five on-demand SSH Manager containers left by interrupted or unsuccessful verification sessions. Docker removed them through their `--rm` setting, the `ssh-manager-state` volume remained, and the final gateway session closed cleanly without leaving another container.

## Open State

**The reach gap closed later on 2026-08-31.** The 12-of-18 state below is the boundary this initial combined integration inherited. After the gateway was split, I opened the two bounded firewall paths, authorized the key on `ubuntu-dev`, verified its host identity, and passed all six hosts through the dedicated SSH Manager integration. See [SSH Manager Fleet Reach Completion](../../../Docker%20MCP%20Gateway/Documentation/Change%20Records/SSH%20Manager%20Fleet%20Reach%20Completion%20-%202026-08-31.md).

At this initial integration step, SSH Manager reached 12 of 18 configured servers. The five Proxmox nodes were blocked by the Proxmox Datacenter and UniFi management-network controls, and `ubuntu-dev` did not authorize the key. I did not widen either path while connecting Executor.

No Executor policy override applied to the gateway, and none of the 42 imported tools was marked as requiring Executor approval. UniFi create, update, and delete operations remained disabled at the gateway catalog. SSH Manager was unrestricted on the twelve hosts it reached, so code running through this personal Executor connection could perform write-capable and sudo SSH operations there. The later [agent client cutover](Agent%20Client%20Cutover%20-%202026-08-31.md) deliberately retained that no-approval behavior in both clients.
