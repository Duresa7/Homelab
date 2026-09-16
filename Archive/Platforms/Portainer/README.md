# Portainer

**Created:** 2026-07-28  
**Last updated:** 2026-09-16

**Status:** Retired on 2026-09-16. Dockhand replaced the server and four Edge Agents. I removed all live Portainer resources; [Retirement](Documentation/Change%20Records/Retirement%20-%202026-09-16.md) records verification. The deployment details below describe the former installation.

I ran Portainer CE 2.45.0 on `docker-main` at `192.168.40.35`. I verified the server version on 2026-09-01 when the unauthenticated `https://localhost:9443/api/status` endpoint returned `Version` `2.45.0`. The server manages its local Docker socket & four Edge Agent hosts on other VLANs. Both server and agents follow their `:latest` tags; those tags resolved to 2.45.0 on 2026-09-03.

I replaced Dockge with [Dockhand](../../../Platforms/Dockhand/README.md) on 2026-09-15 and connected seven Docker hosts, including all five environments below. Dockhand sees the 40 existing projects and 62 existing containers; Coolify is excluded. All projects were subsequently imported for editing, and I retired Portainer on 2026-09-16.

## Last recorded state before retirement

| Environment | Portainer type | Agent state | Management state |
|---|---:|---|---|
| `docker-main` | Local Docker | Server container running | Operational |
| `alpha-prod-01` | Edge Agent | Running | Operational; endpoint status 1 on 2026-09-03 |
| `media-01` | Edge Agent | Running | Operational; endpoint status 1 on 2026-09-03 |
| `docker-network` | Edge Agent | Running | Operational; endpoint status 1 on 2026-09-03 |
| `docker-blue` | Edge Agent | Running | Operational; endpoint status 1 on 2026-09-03 |

Each agent uses `portainer/agent:latest`, 2.45.0 at retirement, restart policy `always`, the Docker socket, `/var/lib/docker/volumes`, `/`, & a named `portainer_agent_data` volume. The shared compose reference is [Configuration/portainer-edge-agent/docker-compose.yml](Configuration/portainer-edge-agent/docker-compose.yml). Generated Edge IDs & keys stay outside this repository; the workspace holds no copy.

`docker-network` reaches `docker-main` through one logged TCP policy from `192.168.85.2` to `192.168.40.35` using the existing `Portainer Edge Agents` port group for 8000 & 9443. `docker-blue` runs Docker 29.6.2, containerd 2.2.6, & runc 1.3.6 after the 2.2.4 shim crashed on every new task.

## Records

- [Edge Agent setup](Documentation/portainer-edge-agent.md)
- [Fleet expansion change record](Documentation/Change%20Records/Portainer%20Edge%20Agent%20Fleet%20Expansion%20-%202026-07-28.md)
- [Portainer 2.45.0 upgrade](Documentation/Change%20Records/Portainer%202.45.0%20Upgrade%20-%202026-08-31.md)
- [Troubleshooting index](Documentation/Troubleshooting/README.md)
- [docker-blue containerd startup failure](Documentation/Troubleshooting/docker-blue%20Cannot%20Start%20New%20Docker%20Tasks%20Under%20containerd%202.2.4%20-%202026-07-28.md)

## Layout

- `Configuration/`: versioned compose references without credentials
- `Documentation/`: current setup, dated changes, & troubleshooting
- `Evidence/`: retained, secret-free verification from bounded work
