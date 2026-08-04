# S01 UniFi Path and Packet Trace

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Captured:** 2026-07-28 23:42-23:43 EDT  
**Targets:** UniFi controller, `docker-network`, & `kasm-01`  
**Mechanism:** UniFi Network MCP and SSH Manager MCP

I previewed and created DNS record `6a69768d052792cd2140e39f` for `kasm.alphasecunited.com`, value `192.168.85.2`, type A, TTL 300. I previewed and created policy `6a69768a052792cd2140e39c` with source `192.168.85.2`, destination `192.168.78.10`, protocol TCP, destination port 443, & logging enabled. Both API results returned `success: true`.

The verification request was:

```sh
curl -kfsS -o /dev/null -w 'kasm_backend_http=%{http_code}\n' --connect-timeout 8 https://192.168.78.10/
```

It timed out with HTTP `000`. I ran a 12-second `tcpdump` on `kasm-01` while repeating the request. The capture saw `192.168.78.10.443 > 192.168.85.2.<REDACTED_EPHEMERAL_PORT>: Flags [S.]`, proving Kasm received the SYN and sent its SYN-ACK. The return direction was the failed leg.
