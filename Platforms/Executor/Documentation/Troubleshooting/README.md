# Executor Troubleshooting

**Created:** 2026-09-07  
**Last updated:** 2026-09-25

One problem per record.

- [Active Work Timeout in 1.6.10 - 2026-09-21](Active%20Work%20Timeout%20in%201.6.10%20-%202026-09-21.md). Current verification: Executor owns a hard-coded 60-second active-work timer; SSH Manager accepts up to five minutes.

- [Integration Tool Calls Time Out at 60 Seconds - 2026-09-07](Integration%20Tool%20Calls%20Time%20Out%20at%2060%20Seconds%20-%202026-09-07.md). The first investigation, on 1.6.8, traced the limit to the MCP SDK's 60-second default. Superseded for 1.6.10 by the 2026-09-21 record. The detach-and-poll workaround still applies.
