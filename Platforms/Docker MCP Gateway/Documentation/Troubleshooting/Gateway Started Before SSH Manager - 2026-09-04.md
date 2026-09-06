# Gateway Started Before SSH Manager

**Created:** 2026-09-04  
**Last updated:** 2026-09-04

## Symptom

Executor showed its SSH Manager connection as healthy, but every attempted SSH tool call failed because the connection exposed no callable SSH tools. The SSH Manager service and the gateway container on `docker-blue` were both running and healthy.

## Error

The gateway startup log showed its one catalog request arrived before the upstream service accepted connections:

```text
Post http://ssh-manager:8080/mcp: connect 172.21.0.4:8080: connection refused
0 tools listed
```

The gateway health check did not treat the empty tool catalog as a failure.

## What I Tried

The normal connection refresh could not add tools that the gateway had never registered. The internal Proxmox browser route was unavailable from the current browser environment, and Portainer's web session was signed out. I used the authenticated Portainer API with a stored credential, confirmed every `docker-blue` container was up, and inspected only the affected gateway logs before changing anything.

## Root Cause

Docker started `ssh-manager-mcp-gateway` before the separate `mcp-ssh-manager` service was ready. The gateway tried its upstream once, received connection refused, and retained a zero-tool catalog while its own health endpoint continued to pass. Compose dependency ordering did not protect this Docker-daemon restart path because the two services live in separate projects.

## Recovery

I restarted only `ssh-manager-mcp-gateway` after `mcp-ssh-manager` was healthy. The new gateway process connected immediately and listed 37 tools. I refreshed the Executor connection and resumed the `grey-server` and `docker-main` work through the restored SSH path.

## Verification

The gateway log reported `37 tools listed`, Executor exposed the full SSH catalog, and live read-only calls to both `grey-server` and `docker-main` succeeded. Every other `docker-blue` container remained running and healthy.

## Remaining Work

The immediate fault is recovered. Startup ordering across the two Compose projects is still not durable, so another `docker-blue` Docker restart can require the same gateway-only restart. A later change should make the gateway health check fail on an empty catalog or give it an upstream retry loop; I did not mix that unrelated configuration change into the Ollama deployment.

