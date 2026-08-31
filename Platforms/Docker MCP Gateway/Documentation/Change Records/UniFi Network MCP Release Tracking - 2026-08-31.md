# UniFi Network MCP Release Tracking

**Created:** 2026-08-31  
**Last updated:** 2026-08-31

## Outcome

I changed the Docker MCP Gateway catalog from a fixed UniFi Network MCP version and digest to `ghcr.io/sirkirby/unifi-network-mcp:latest`. This lets me upgrade it manually by pulling the tag and restarting the gateway.

## Verification

At the time of this change, `latest` resolved to `sha256:4ebc2582d7c85f08fc52dc8f988abd7cf1c0350837fe84ca35f4c7884eab2f0b`, the same manifest used by 0.29.3. I pulled the tag on `docker-blue`, recreated the gateway, and verified an authenticated UniFi system-information call through the gateway.

## Open State

UniFi MCP upgrades are manual. The `latest` tag is mutable, so a future pull may change the running version without a repository edit. The read-only UniFi policy and gateway authentication are unchanged.
