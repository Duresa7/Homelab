# MCP Integration Separation

**Created:** 2026-08-31  
**Last updated:** 2026-08-31

## Outcome

I replaced Executor's combined Docker MCP Gateway integration with two integrations: `UniFi MCP Gateway` and `SSH Manager MCP Gateway`. UniFi now carries 5 tools through `unifiMcpGateway`, and SSH Manager carries 37 tools through `sshManagerMcpGateway`.

The original layout showed both servers as one integration because Executor registers an upstream MCP endpoint as an integration, and that endpoint returned one flat 42-tool catalog. Naming the combined entry differently could not create a second integration boundary. I split the upstream gateway into two authenticated endpoints so Executor could register each one independently.

## Implementation

1. I restricted the existing `docker-mcp-gateway` container at `192.168.40.39:8811` to the UniFi catalog and server.
2. I added `ssh-manager-mcp-gateway` at `192.168.40.39:8812`, restricted to the SSH Manager catalog and server.
3. I separated the gateway bearer tokens and managed-server secrets. The live `.env` now supplies a distinct token to each service, UniFi reads `unifi-secrets.env`, and SSH Manager reads `ssh-manager-secrets.env`. All three files are root-owned with mode `0600`.
4. I kept the existing UniFi gateway credential and changed its label to match its narrower purpose. I created a separate SSH Manager gateway credential. No secret value entered the repository or command output.
5. I registered `unifi-mcp-gateway` as `UniFi MCP Gateway` with personal connection `unifiMcpGateway`, then registered `ssh-manager-mcp-gateway` as `SSH Manager MCP Gateway` with personal connection `sshManagerMcpGateway`. Both connections use Executor's encrypted credential provider and leave their integrations' static header maps empty.
6. I refreshed and health-checked both new connections before removing the combined `docker-mcp-gateway` integration and `dockerMcpGateway` connection.

I did not create a snapshot or backup. Executor's persistent state remained under `/opt/docker/executor/data`, and the gateway deployment remained reproducible from its versioned Compose definition and catalogs. I retained no standalone command or API capture; the verification bullets below record the live results I observed.

## Verification

- Live Compose validation passed. `docker-mcp-gateway` and `ssh-manager-mcp-gateway` both reached healthy state on the pinned Docker MCP Gateway 0.43.3 image.
- The UniFi endpoint returned HTTP 200 from `/health`, rejected an unauthenticated MCP request with HTTP 401, returned 5 `unifi_` tools to an authenticated client, and closed the test session with HTTP 204.
- The SSH Manager endpoint returned HTTP 200 from `/health`, rejected an unauthenticated MCP request with HTTP 401, returned 37 `ssh_` tools to an authenticated client, and closed the test session with HTTP 204.
- Executor reported both integrations and both personal connections healthy. The UniFi refresh returned 5 tools, and the SSH Manager refresh returned 37 tools.
- The saved credential provider for each connection is `encrypted`; neither integration carries a static request header.
- An Executor execution resolved `unifi-mcp-gateway.user.unifiMcpGateway.unifi_tool_index` and completed without a tool error.
- A second Executor execution resolved `ssh-manager-mcp-gateway.user.sshManagerMcpGateway.ssh_list_servers` and completed without a tool error.
- The combined `docker-mcp-gateway` integration and `dockerMcpGateway` connection are absent.
- After both replacements passed, I shredded the retired combined `mcp-secrets.env`. The two scoped secret files remained root-owned with mode `0600` and held the expected 3 UniFi entries and 11 SSH Manager entries.

## Open State

**The reach gap closed later on 2026-08-31.** The split itself did not widen SSH reach, but the follow-up did. All eighteen servers now answer through `sshManagerMcpGateway`; the implementation and privilege boundary are in [SSH Manager Fleet Reach Completion](../../../Docker%20MCP%20Gateway/Documentation/Change%20Records/SSH%20Manager%20Fleet%20Reach%20Completion%20-%202026-08-31.md).

At the separation step, the split did not widen SSH reach or change Executor approval policy. SSH Manager reached 12 of its 18 configured servers, and its 37 tools had no Executor approval override. The five Proxmox nodes and `ubuntu-dev` remained blocked for the reasons recorded in the SSH Manager integration record. UniFi create, update, and delete operations remained disabled in its catalog.

Both gateway endpoints remain internal HTTP protected by distinct bearer tokens. Executor is their intended client and reaches them directly over the internal network.
