# Integration Search Tools

**Created:** 2026-09-06  
**Last updated:** 2026-09-06

I enabled Executor's per-integration search tools in all five local client profiles by setting their endpoint to `https://mcp.alphasecunited.com/mcp?search_tools=true`.

| Profile | Configuration |
|---|---|
| Codex | `/home/ai-agent/.codex/config.toml` |
| Codex Alt | `/home/ai-agent/.codex_alt/config.toml` |
| Codex Personal | `/home/ai-agent/.codex_personal/config.toml` |
| Claude | `/home/ai-agent/.claude.json` |
| Claude Alt | `/home/ai-agent/.claude_alt/.claude.json` |

I parsed each configuration and checked that the edit changed only the Executor URL. I normalized repeated search parameters found during verification and confirmed that each Codex URL contains one `search_tools=true` parameter. I kept approval settings and model resume behavior as configured.

`codex mcp get executor` recognized the enabled Streamable HTTP connection. Both Claude profile checks read the new URL but returned `Needs authentication`. I retained no standalone command capture.

I then renewed OAuth for both Claude profiles with `claude mcp login executor --no-browser`, selecting `.claude_alt` through `CLAUDE_CONFIG_DIR` for the alternate profile. I completed each normal account sign-in, consent request, and localhost callback using the saved Executor account. Account sign-in, consent, and callback each returned HTTP 200. I did not inspect or copy Claude's credential files.

After both logins completed, I ran the connection checks again. Default Claude and Claude Alt each reported `Connected` at `https://mcp.alphasecunited.com/mcp?search_tools=true`. I parsed both saved configurations and confirmed the same endpoint. Reauthentication resolved the failures without a server or approval-policy change; the checks do not distinguish URL-based credential lookup from an expired prior token as the original cause.

I removed the temporary login output, credential-reference environment file, and authentication helper. I retained no standalone authentication capture.

I updated my local workspace notes to prefer the integration search tools first, inspect the returned tool path with `tools.describe.tool`, and invoke it through `execute`. The notes include code-side search and pagination as fallbacks and explain UniFi's separate underlying catalog. I checked the search names, query parameter, and dispatch behavior against Executor's MCP tool-server source.

The saved configuration change and both Claude authentications are complete. Fresh authenticated discovery in the three Codex profiles remains unverified. Existing sessions need to reconnect before they can load the new tool catalog.
