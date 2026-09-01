# Agent Client Cutover

**Created:** 2026-09-01  
**Last updated:** 2026-09-01

**Cutover:** 2026-08-31

## Outcome

I replaced the direct UniFi Network and SSH Manager MCP configuration on `ubuntu-dev` with one user-scoped Executor connection in Codex and Claude Code. Both clients now connect to `https://mcp.alphasecunited.com/mcp` over Streamable HTTP with OAuth. Executor remains the only client-side homelab MCP entry and exposes the existing Cloudflare, Supabase, UniFi MCP Gateway, and SSH Manager MCP Gateway integrations through that endpoint.

I kept the requested no-approval behavior. Codex sets the Executor server's default tool approval mode to `approve`, and Claude Code persistently allows `mcp__executor__*`. Executor has no approval policy override on the SSH Manager connection. SSH Manager therefore remains able to run unrestricted root-capable operations without a client or Executor approval prompt.

## Implementation

1. I captured the pre-cutover Codex configuration, Claude Code configuration, Claude plugin inventory, and Claude settings in a private rollback archive outside this repository.
2. I removed the `ssh-manager` and `unifi-network` direct MCP entries from Codex. I removed the direct `ssh-manager` entry from Claude Code.
3. I uninstalled the UniFi plugin and removed its marketplace registration from both clients. I removed the standalone global SSH Manager package and its executable link.
4. I moved the retired local SSH Manager package and environment files, UniFi plugin and marketplace copies, Claude plugin data, stale memory guidance, caches, logs, and configuration snapshots into the same archive rather than deleting them.
5. I added one user-scoped remote MCP server named `executor` to each client and completed its OAuth flow. The clients keep their OAuth credentials outside this repository.
6. I configured Codex to approve Executor tools without a prompt and added `mcp__executor__*` to Claude Code's persistent allow rules, matching the decision that SSH operations should not require approval.

The rollback archive is `/home/ai-agent/.local/share/mcp-retired/ubuntu-dev-direct-mcps-20260901T032615Z`. Its root is mode `0700`, which prevents any other local account from traversing its contents, and its `README.md` records the full-restore procedure. It contains credentials and must remain outside a repository.

## Verification

- `codex mcp list` and `codex mcp get executor` reported one enabled OAuth connection named `executor`. Neither command listed `ssh-manager` or `unifi-network`.
- `claude mcp list` and `claude mcp get executor` reported the user-scoped HTTP server `executor` connected. Neither command listed a direct SSH Manager or UniFi server.
- The active Claude plugin inventory contained seven unrelated enabled plugins and no UniFi plugin. The active Codex plugin inventory contained no UniFi plugin or marketplace. The global npm inventory contained no SSH Manager package.
- A fresh ephemeral Codex 0.152.0 session initialized Executor, loaded its `execute` guidance, and saw Cloudflare, Supabase, UniFi MCP Gateway, and SSH Manager MCP Gateway as available integrations.
- That Codex session resolved `ssh-manager-mcp-gateway.user.sshManagerMcpGateway.ssh_list_servers` and called it through Executor. The first generated call used invalid dot notation for the hyphenated integration name and returned `'manager' is not defined`; the retry used the exact path as a bracket key and succeeded. It returned all eighteen configured servers, with `docker_blue` first and `docker_main` last. No approval prompt occurred.
- A fresh Claude Code 2.1.252 session initialized the Executor server as connected and exposed its six tools. The first model request stopped before a tool call because the Claude organization had reached its spend limit. Two 2026-09-01 retries reached tool selection, but explicit `$0.50` and `$1.00` session caps stopped them before either returned a tool result because the loaded tool context consumed those budgets. These are account or self-imposed usage bounds, not MCP connection or OAuth failures.
- One final `claude mcp get executor` check timed out after 30 seconds. DNS still resolved the name to `192.168.85.2`, TCP 443 on Nginx Proxy Manager and TCP 4788 on `docker-blue` both connected, and a pinned HTTPS health request returned `{"status":"ok"}`. The immediate `claude mcp get executor` retry reported connected, so the timeout did not persist.
- The rollback archive exists at mode `0700` with pre-cutover agent configuration, the retired SSH package, UniFi plugin and marketplace sources, and residual client data. The active `~/.claude/ssh-manager.env` and `~/.ssh-manager` paths are absent. I did not read or publish any archived credential value.

No standalone transcript was retained. The results above are the live command and client-session results observed during the cutover and follow-up verification.

## Open State

One verification remains: start a fresh Claude Code session with a sufficient bounded budget and call `ssh_list_servers` through Executor. The configuration, MCP initialization, and model-side tool selection already pass, but only a successful tool result proves the Claude model path end to end.

The private archive is temporary rollback material, not a retained backup. Delete it immediately after the remaining Claude call passes. Until then, restoring it would reinstate direct MCP catalogs beside Executor, so rollback must follow the archive's full-restore procedure rather than copying back selected files.

## References

- [Executor MCP Proxy](https://executor.sh/docs/mcp-proxy)
- [Codex Model Context Protocol](https://developers.openai.com/codex/extend/mcp)
- [Claude Code MCP](https://code.claude.com/docs/en/mcp)
- [MCP integration separation](MCP%20Integration%20Separation%20-%202026-08-31.md)
- [SSH Manager fleet reach completion](../../../Docker%20MCP%20Gateway/Documentation/Change%20Records/SSH%20Manager%20Fleet%20Reach%20Completion%20-%202026-08-31.md)
