# Portainer Edge Agent Setup

**Created:** 2026-04-14  
**Last updated:** 2026-07-28

**Implementation date:** 2026-04-14; fleet expanded 2026-07-28  
**Status:** Operational; all four Edge Agent environments are manageable through `docker-main`  
**System:** `docker-main` on grey-server  
**Purpose:** Manage remote Docker hosts through Portainer Edge Agents across VLANs

## Infrastructure

| Host | IP | VLAN | Role |
|------|----|------|------|
| docker-main | 192.168.40.35 | VLAN 40 (Personal-A) | Portainer Server |
| alpha-prod-01 | 192.168.80.118 | VLAN 80 (`AlphaSec-Servers`) | Edge Agent |
| docker-blue | 192.168.40.39 | VLAN 40 (Personal-A) | Edge Agent |
| media-01 | 192.168.40.42 | VLAN 40 (Personal-A) | Edge Agent |
| docker-network | 192.168.85.2 | VLAN 85 (`AlphaSec-Access`) | Edge Agent |

## Network Diagram

```
VLAN 40 (Personal-A)          VLAN 80 (AlphaSec-Servers)
┌─────────────────────┐        ┌──────────────────────┐
│     docker-main     │        │    alpha-prod-01      │
│   192.168.40.35     │        │   192.168.80.118      │
│                     │        │                       │
│  Portainer Server   │◄───────│  Portainer Edge Agent │
│  :9443 (UI/API)     │  polls │  EDGE_INSECURE_POLL=1 │
│  :8000 (tunnel)     │        │                       │
└─────────────────────┘        └──────────────────────┘
         ▲
         │
    Browser access
    https://portainer.alphasecunited.com
```

## Portainer Server (docker-main)

The browser UI uses `https://portainer.alphasecunited.com` through internal NPM. NPM connects to the existing HTTPS listener on `192.168.40.35:9443`; direct access remains the rollback path. This doesn't change the Edge Agent tunnel on TCP 8000. See [Internal HTTPS Service Onboarding - 2026-07-22](../../Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md).

**Path:** `/opt/docker/portainer/docker-compose.yml`

```yaml
name: portainer
services:
  portainer:
    container_name: portainer_ce
    image: portainer/portainer-ce:latest
    ports:
      - "9443:9443"
      - "8000:8000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - portainer_data:/data
    restart: always
volumes:
  portainer_data:
```

## Edge Agent Pattern

**Path:** `/opt/docker/portainer-edge-agent/`

**docker-compose.yml**
```yaml
name: portainer-edge-agent
services:
  portainer_edge_agent:
    image: portainer/agent:2.39.1
    container_name: portainer_edge_agent
    restart: always
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /var/lib/docker/volumes:/var/lib/docker/volumes
      - /:/host
      - portainer_agent_data:/data
    environment:
      - EDGE=1
      - EDGE_ID=${EDGE_ID}
      - EDGE_KEY=${EDGE_KEY}
      - EDGE_INSECURE_POLL=1
volumes:
  portainer_agent_data:
```

**.env** requires the generated Edge ID and key:
```env
EDGE_ID=<YOUR_PORTAINER_EDGE_ID>
EDGE_KEY=<YOUR_PORTAINER_EDGE_KEY>
```

I store one Edge ID & key per environment outside this repository. Live `.env` files are `root:root` mode 0600; the workspace holds no generated value.

## UniFi Firewall Rule

| Field | Value |
|-------|-------|
| Name | Allow `AlphaSec-Servers` to Portainer Edge |
| Description | Allow `AlphaSec-Servers` VMs to reach Portainer Edge tunnel and API on docker-main |
| Source Zone | `AlphaSec-Servers` |
| Source | Any |
| Destination Zone | Internal |
| Destination IP | 192.168.40.35 (docker-main) |
| Ports | 8000, 9443 |
| Action | Allow |
| Auto Allow Return Traffic | Enabled |

`docker-network` uses a second, narrower rule because it sits in the Access zone:

| Field | Value |
|---|---|
| Name | Allow docker-network to Portainer Edge |
| Source | `192.168.85.2` |
| Destination | `192.168.40.35` |
| Destination ports | Existing `Portainer Edge Agents` group, TCP 8000 & 9443 |
| Logging | Enabled |
| Policy ID | `6a68eb3f052792cd2140c9ad` |
| Status | Enabled; TCP 8000 & 9443 were reachable from `docker-network` after creation |

## Registered Edge Agents

| VM | IP | VLAN | Date Added |
|----|----|------|------------|
| alpha-prod-01 | 192.168.80.118 | VLAN 80 | 2026-04-14 |
| media-01 | 192.168.40.42 | VLAN 40 | 2026-07-28; running & manageable |
| docker-network | 192.168.85.2 | VLAN 85 | 2026-07-28; running & manageable |
| docker-blue | 192.168.40.39 | VLAN 40 | 2026-07-28; running & manageable |

Portainer environment 7 lists 4 `docker-blue` containers, environment 8 lists 10 `media-01` containers, & environment 9 lists 5 `docker-network` containers. The dated [fleet expansion change record](Change%20Records/Portainer%20Edge%20Agent%20Fleet%20Expansion%20-%202026-07-28.md) holds the API registration, deployment checks, firewall policy, `docker-blue` repair, rollback points, & final verification.
