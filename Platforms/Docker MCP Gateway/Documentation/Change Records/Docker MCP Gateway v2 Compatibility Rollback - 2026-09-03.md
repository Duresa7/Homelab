# Docker MCP Gateway v2 Compatibility Rollback

**Created:** 2026-09-03  
**Last updated:** 2026-09-04

**Superseded in part:** the same afternoon, 0.43.3 also started one SSH Manager container per client session under parallel load, so the behaviour this record attributes to the v2 image is not a v2 regression and the pin is not required by it. The rollback and its verification stand as performed. See the [troubleshooting record](../Troubleshooting/Managed%20SSH%20Manager%20Containers%20Accumulated%20Under%20long-lived%20-%202026-09-03.md).

## Outcome

I tested the official Docker MCP Gateway `latest` image on both gateway services and rolled both back to the exact 0.43.3 image and digest. The initial sequential verification appeared to show that 0.43.3 restored one shared managed SSH Manager container. Parallel testing later that afternoon disproved that conclusion: both gateway versions keep one managed container per client session. The later [shared server cutover](SSH%20Manager%20Shared%20Server%20Cutover%20-%202026-09-03.md) is the actual fix and leaves the gateway managing no SSH Manager container.

## Changes

I changed the two live Compose services on `docker-blue` from the digest-pinned 0.43.3 image to the official `latest` tag, validated the Compose model, pulled the image, and recreated both gateways. Their HTTP health endpoints answered, but each new Executor session started another `homelab/mcp-ssh-manager:latest` managed container. Management calls then began failing with `Internal tool error [24f44628]` and `Internal tool error [423f64f3]` while the gateway container itself still reported healthy.

I restored both services to `docker.io/docker/mcp-gateway:v0.43.3@sha256:e3ee13818cb067a506c5e9acdb2bb4fe0e601caef7d116fc329755782f1a3cfa` and recreated them. Five managed SSH Manager containers from the compatibility test were still present after the image rollback, so I restarted only `ssh-manager-gateway`. That self-restart caused the initiating SSH Manager call to return `Internal tool error [c7c222c5]`, as expected, while Docker removed the managed containers through their `--rm` lifecycle.

I changed no MCP catalog, secret, token, host entry, allowlist, or Executor connection. I retained no temporary backup or snapshot.

## Verification

- Both gateway Compose services returned to the exact 0.43.3 tag and pinned manifest digest and reported healthy.
- The UniFi and SSH Manager health endpoints returned HTTP 200.
- A real UniFi network-list call returned one page containing 22 networks.
- A fresh SSH Manager session returned the configured server catalog, and a separate session ran a command on `docker-network` successfully.
- After those sequential calls, Docker reported one managed SSH Manager container. Later parallel calls produced 22 containers on 0.43.3, proving that the sequential test had measured Executor reusing one client session rather than the gateway sharing one server.

## Open State

The gateway remains pinned to 0.43.3 for now, but this test no longer justifies the pin. SSH Manager runs as a separate persistent service, so a future gateway update does not depend on gateway-level `--long-lived`. Its acceptance test is both endpoint checks, real calls through each integration, parallel SSH calls with zero gateway-managed SSH containers, and a cross-call interactive-session test against the shared server.

## Related Records

- [Docker MCP Gateway platform record](../../README.md)
- [SSH Manager gateway process exhaustion](SSH%20Manager%20Gateway%20Process%20Exhaustion%20-%202026-09-02.md)
- [SSH Manager shared server cutover](SSH%20Manager%20Shared%20Server%20Cutover%20-%202026-09-03.md)
- [2026-09-03 container image updates](../../../../Operations/Maintenance/Container%20Image%20Updates%20-%202026-09-03.md)
