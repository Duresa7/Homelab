# Step 1 Preflight and Pattern

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Capture date:** 2026-07-28  
**Execution mechanism:** SSH Manager MCP, remote POSIX shell  
**Targets:** `docker_main`, `alpha_prod_01`, `docker_network`, `blue_server` CT 108, `red_server` CT 842

## Commands

```sh
docker ps --filter name=portainer --format '{{.Names}}|{{.Image}}|{{.Status}}'
docker inspect --format 'image={{.Config.Image}} restart={{.HostConfig.RestartPolicy.Name}}' portainer_edge_agent
docker inspect --format '{{range .Mounts}}{{.Source}}->{{.Destination}}{{println}}{{end}}' portainer_edge_agent
docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' portainer_edge_agent | sed 's/=.*//' | sort
docker version --format '{{.Server.Version}}'
test -d /opt/docker/portainer-edge-agent
```

I used `pct exec 108 --` and `pct exec 842 --` around the guest commands for `docker-blue` & `media-01`.

## Observed Result

| Target | Docker | Agent before change | Existing containers |
|---|---|---|---:|
| `docker-main` | Portainer server host | `portainer_ce` running; TCP 8000 & 9443 published | 14 |
| `alpha-prod-01` | Docker | Agent 2.39.1 running; restart `always`; expected mounts & variable names | 7 |
| `docker-network` | 29.6.1 | Absent | 4 |
| `docker-blue` | 29.5.3 | Absent | 3 |
| `media-01` | 29.6.2 | Absent | 9 |

No target held `/opt/docker/portainer-edge-agent`.

## Network Checks

The read-only TCP checks used:

```sh
timeout 3 sh -c '</dev/tcp/192.168.40.35/8000'
timeout 3 sh -c '</dev/tcp/192.168.40.35/9443'
```

`docker-blue` & `media-01` reached both ports. `docker-network` reached 9443 & failed on 8000. No retained output contained a credential.
