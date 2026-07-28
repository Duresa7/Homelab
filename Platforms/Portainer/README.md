# Portainer

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

I run Portainer CE 2.39.1 on `docker-main` at `192.168.40.35`. The server manages its local Docker socket & uses Edge Agents for Docker hosts that sit on other VLANs.

## Current State

| Environment | Portainer type | Agent state | Management state |
|---|---:|---|---|
| `docker-main` | Local Docker | Server container running | Operational |
| `alpha-prod-01` | Edge Agent | Running | Operational |
| `media-01` | Edge Agent | Running | Operational; Portainer listed 10 containers through the tunnel on 2026-07-28 |
| `docker-network` | Edge Agent | Running | Operational; Portainer listed 5 containers through the tunnel on 2026-07-28 |
| `docker-blue` | Edge Agent | Running | Operational; Portainer listed 4 containers through the tunnel on 2026-07-28 |

Each agent uses `portainer/agent:2.39.1`, restart policy `always`, the Docker socket, `/var/lib/docker/volumes`, `/`, & a named `portainer_agent_data` volume. The shared compose reference is [Configuration/portainer-edge-agent/docker-compose.yml](Configuration/portainer-edge-agent/docker-compose.yml). Generated Edge IDs & keys stay outside this repository; the workspace holds no copy.

`docker-network` reaches `docker-main` through one logged TCP policy from `192.168.85.2` to `192.168.40.35` using the existing `Portainer Edge Agents` port group for 8000 & 9443. `docker-blue` runs Docker 29.6.2, containerd 2.2.6, & runc 1.3.6 after the 2.2.4 shim crashed on every new task.

## Records

- [Edge Agent setup](Documentation/portainer-edge-agent.md)
- [Fleet expansion change record](Documentation/Change%20Records/Portainer%20Edge%20Agent%20Fleet%20Expansion%20-%202026-07-28.md)
- [Troubleshooting index](Documentation/Troubleshooting/README.md)
- [docker-blue containerd startup failure](Documentation/Troubleshooting/docker-blue%20Cannot%20Start%20New%20Docker%20Tasks%20Under%20containerd%202.2.4%20-%202026-07-28.md)

## Layout

- `Configuration/`: versioned compose references without credentials
- `Documentation/`: current setup, dated changes, & troubleshooting
- `Evidence/`: retained, secret-free verification from bounded work
