# Portainer Edge Agent Setup

**Created:** 2026-04-14  
**Last updated:** 2026-07-18

---

| Field | Details |
|-------|---------|
| **Author** | REDACTED_NAME_001 (REDACTED_USER_001) REDACTED_NAME_003 |
| **Organization** | REDACTED_PRIVATE_ORG_LABEL United |
| **Date** | 2026-04-14 |
| **Version** | 1.0 |
| **Status** | Completed |
| **System** | docker-main (Proxmox VE, Grey Server) |
| **Purpose** | Centralized Docker management via Portainer Edge Agent across VLANs |

---

## Infrastructure

| Host | IP | VLAN | Role |
|------|----|------|------|
| docker-main | 192.168.40.35 | VLAN 40 (Personal-A) | Portainer Server |
| alpha-prod-01 | 192.168.80.118 | VLAN 80 (REDACTED_PRIVATE_ORG_LABEL-Servers) | Edge Agent |

---

## Network Diagram

```
VLAN 40 (Personal-A)          VLAN 80 (REDACTED_PRIVATE_ORG_LABEL-Servers)
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
    https://192.168.40.35:9443
```

---

## Portainer Server (docker-main)

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

---

## Edge Agent (per VM)

**Path:** `/opt/docker/portainer-edge-agent/`

**docker-compose.yml** (same on every VM):
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

**.env**, unique per VM (get values from the Portainer Add Environment wizard):
```env
EDGE_ID=<generated-per-vm>
EDGE_KEY=<generated-per-vm>
```

---

## UniFi Firewall Rule

| Field | Value |
|-------|-------|
| Name | Allow REDACTED_PRIVATE_ORG_LABEL-Servers to Portainer Edge |
| Description | Allow REDACTED_PRIVATE_ORG_LABEL-Servers VMs to reach Portainer Edge tunnel and API on docker-main |
| Source Zone | REDACTED_PRIVATE_ORG_LABEL-Servers |
| Source | Any |
| Destination Zone | Internal |
| Destination IP | 192.168.40.35 (docker-main) |
| Ports | 8000, 9443 |
| Action | Allow |
| Auto Allow Return Traffic | Enabled |

---

## Registered Edge Agents

| VM | IP | VLAN | Date Added |
|----|----|------|------------|
| alpha-prod-01 | 192.168.80.118 | VLAN 80 | 2026-04-14 |
