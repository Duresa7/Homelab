# Portainer Edge Agent Walkthrough

**Created:** 2026-07-20  
**Last updated:** 2026-07-20

## What This Guide Covers

I connected a Docker host on VLAN 80 to the Portainer server on VLAN 40 with an Edge Agent. This guide covers both Compose projects, the cross-VLAN rule, environment registration, & the checks used after enrollment.

## Current Status and Verified Versions

The Portainer server runs on `docker-main` at `192.168.40.35` with HTTPS on 9443 and the Edge tunnel on 8000. The recorded Edge Agent is version 2.39.1 on `alpha-prod-01` at `192.168.80.118`. It uses `EDGE_INSECURE_POLL=1` because the agent polls the server across the approved internal path.

## What You Need

- One Docker host for the Portainer server.
- One Docker host for each Edge Agent.
- TCP reachability from the agent to server ports 8000 and 9443.
- An Edge environment created in Portainer for each target host.

## How the Pieces Fit Together

> Diagram placeholder

## Walkthrough

### Step 1: Start the Portainer Server

I created `/opt/docker/portainer/docker-compose.yml`, published 9443 and 8000, mounted the Docker socket, & kept application data in `portainer_data`.

```sh
docker compose config
docker compose up -d
docker compose ps
```

I opened `https://192.168.40.35:9443` and confirmed the server could manage its local Docker engine.

### Step 2: Permit the Edge Polling Path

I added a UniFi allow rule from the VLAN 80 server zone to `192.168.40.35` on TCP 8000 and 9443. I tested those two ports from `alpha-prod-01` and kept other cross-VLAN traffic under the existing policy.

### Step 3: Create the Edge Environment

I selected Add Environment in Portainer, chose Edge Agent, named the environment for the target host, & copied the generated `EDGE_ID` and `EDGE_KEY` values into that host's local environment file.

### Step 4: Start the Edge Agent

I created `/opt/docker/portainer-edge-agent/docker-compose.yml` on `alpha-prod-01`, pinned `portainer/agent:2.39.1`, mounted the Docker socket, Docker volumes, host filesystem, & agent data, then started the project.

```sh
docker compose config
docker compose up -d
docker compose logs --tail 100 portainer_edge_agent
```

### Step 5: Confirm the Environment

I waited for `alpha-prod-01` to report online in Portainer, opened its container list, & compared it with `docker ps` on the host.

### Step 6: Test Restart Recovery

I restarted the Edge Agent container and confirmed the same environment returned online without creating a second Portainer record.

## What I Checked After Each Step

- Portainer listened on TCP 9443 and 8000.
- The Edge host reached both approved ports across the VLAN boundary.
- Agent 2.39.1 started without an enrollment error.
- `alpha-prod-01` reported online in Portainer.
- The remote container list matched the host's Docker state.
- Restarting the agent preserved the environment registration.

## Troubleshooting and Recovery

If the agent stays offline, test TCP 8000 and 9443 from the agent, then compare its `EDGE_ID` and `EDGE_KEY` with the environment you created. If the ID was reused on another host, create a new Edge environment instead of copying the old local file.

## Known Limits

The source record covers one registered Edge Agent. It doesn't document certificate hardening for `EDGE_INSECURE_POLL=1` or a Portainer server version.

## Source Records

- [Portainer Edge Agent setup](../Platforms/Portainer/Documentation/portainer-edge-agent.md)
