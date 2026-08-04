# Step 3 UniFi Readback

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Capture date:** 2026-07-22 EDT; exact timestamp not retained  
**Mechanism:** UniFi Network MCP against site `default`

The mutation calls used preview, user confirmation, and confirmed create operations. The exact mutation and readback timestamps plus complete structured responses weren't retained outside the task transcript. This record keeps the exact requests, returned counts, record IDs, and verified boundary without presenting the summary as a complete API transcript.

## DNS request

```json
{"tool":"unifi_list_dns_records","arguments":{}}
```

Structured result summary: `success=true`, `count=20`. The existing NetBird record and all 19 application records are enabled A records with TTL 300 and value `192.168.85.2`. New record IDs run from `6a60fd2a2d027bb05525a834` through `6a60fd2b2d027bb05525a864` and are listed in `Infrastructure/Network/UniFi/Configuration/DNS/local-dns.md`.

## Firewall request

```json
{"tool":"unifi_list_firewall_policies","arguments":{"limit":500,"include_predefined":false,"summary":true}}
```

Structured result summary: `success=true`, `total_count=39`, `returned_count=39`.

```text
6a60fd2c2d027bb05525a86d Allow NPM to media-01 web UIs        enabled ALLOW
6a60fd2c2d027bb05525a870 Allow NPM to ansible-01 Semaphore    enabled ALLOW
6a60fd2c2d027bb05525a873 Allow NPM to docker-main web UIs     enabled ALLOW
6a60fd2c2d027bb05525a876 Allow NPM to security-01 web UIs     enabled ALLOW
6a60fd2c2d027bb05525a879 Allow NPM to splunk-siem web UI      enabled ALLOW
```

Each policy uses exact source `192.168.85.2`, its documented destination IP, TCP, the documented destination ports, logging, & an enabled return companion.

## WAN publication request

```json
{"tool":"unifi_list_port_forwards","arguments":{}}
```

```json
{"success":true,"site":"default","count":0,"port_forwards":[]}
```

No UniFi port forward publishes NPM to the WAN.
