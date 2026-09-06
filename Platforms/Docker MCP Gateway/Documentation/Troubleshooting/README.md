# Docker MCP Gateway Troubleshooting

**Created:** 2026-09-03  
**Last updated:** 2026-09-04

I keep one dated Markdown record per problem in this folder. The index links to the complete symptom, cause, correction and verification for each issue.

## Issue Index

| # | Date | Symptom | Resolution | Status |
|---:|---|---|---|---|
| <a id="1-managed-ssh-manager-containers-accumulated-under-long-lived"></a>[1](Managed%20SSH%20Manager%20Containers%20Accumulated%20Under%20long-lived%20-%202026-09-03.md) | 2026-09-03 | 22 managed SSH Manager containers and 192 of 256 gateway processes 36 minutes after a restart, on 0.43.3 with `--long-lived` | The gateway keeps one container per client session and only releases it when the client closes the session, which Executor never does. Restarted the gateway to clear it, then moved the server to its own persistent service | Resolved |
| [2](Gateway%20Started%20Before%20SSH%20Manager%20-%202026-09-04.md) | 2026-09-04 | Executor's SSH Manager connection was healthy but exposed no callable tools after a `docker-blue` restart | The gateway's one startup attempt reached SSH Manager before it listened, then cached an empty catalog. Restarting only the gateway after SSH Manager was healthy restored all 37 tools | Recovered; startup prevention open |
