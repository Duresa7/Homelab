# Unused Docker Image Prune

**Created:** 2026-10-31  
**Last updated:** 2026-10-31

## Scope

On 2026-10-31 I removed the Docker images that no container, running or stopped, references, on every reachable Docker host in the lab. I did not stop, restart, recreate, or update any container, and I did not prune volumes, networks, stopped containers, or build cache. I created no snapshot or backup.

I checked all 26 servers in SSH Manager for a working Docker CLI and daemon. Eight Linux hosts run Docker: docker-main (CT 110), docker-blue (CT 108), docker-network (CT 107), monitor-01 (CT 104), media-01 (CT 842), alpha-prod-01 (VM 401), security-01 (VM 200), and ubuntu-dev (VM 105). `dkadi` (and `root` on docker-main) reached the Docker socket directly on all eight, so no host needed sudo. The five Proxmox nodes, ci-k3s-01, splunk-siem, ansible-01, edge-01, HQ-DC01, HQ-DC02, and win11-dev have no Docker installed.

## Method

On each host I recorded `df -h /`, `docker system df`, and the running container list (ID, name, image), then listed the images that no container referenced, so I knew what the prune would remove. I ran `docker image prune -a -f` detached, read its `Total reclaimed space` line from the log, then recorded `df -h /`, `docker system df`, and the running container list again and diffed it against the first one. Afterwards I checked that no container on any host reported `unhealthy` or `restarting` and deleted the temporary log and list files from `/tmp`.

## Results

| Host | Before: used / free (use%) | Reclaimed | After: used / free (use%) | Images before / after | Containers unchanged |
| --- | --- | --- | --- | --- | --- |
| docker-main | 64G / 30G of 99G (68%) | 21.06 GB | 43G / 51G (46%) | 47 / 18 | Yes, 18 running |
| media-01 | 16G / 78G of 98G (17%) | 6.092 GB | 9.4G / 84G (11%) | 21 / 12 | Yes, 10 running |
| docker-network | 7.8G / 22G of 32G (27%) | 3.078 GB | 5.0G / 25G (17%) | 14 / 7 | Yes, 5 running |
| monitor-01 | 14G / 4.8G of 20G (75%) | 3.024 GB | 12G / 7.6G (60%) | 19 / 11 | Yes, 9 running |
| alpha-prod-01 | 15G / 38G of 55G (28%) | 2.3 GB | 12G / 40G (24%) | 21 / 11 | Yes, 8 running |
| docker-blue | 7.9G / 6.1G of 15G (57%) | 1.019 GB | 7.0G / 7.0G (50%) | 18 / 10 | Yes, 10 running |
| security-01 | 30G / 63G of 97G (33%) | 430.7 MB | 30G / 63G (33%) | 9 / 5 | Yes, 3 running |

The prunes reclaimed 37.0 GB in total. On every host the after list of running containers matched the before list exactly by container ID, name, and image, and no container reported `unhealthy` or `restarting`.

monitor-01 was the host under pressure, at 75% of its 20 GiB rootfs. It is now at 60% with 7.6G free. What it removed were the older Hawser 0.2.48, cAdvisor v0.60.5, `python:3-alpine`, `alpine:latest`, an untagged PeaNUT image, `prom/blackbox-exporter:v0.28.0`, an untagged 272 MB image, and an untagged 1.94 GB image (`dbbc38ea2110`). Earlier the same day `docker system df -v` listed that last one with no container. Its size, close to the 2.01 GB of the current `grafana/grafana:latest`, makes it most likely the Grafana image superseded by the last Grafana update. It accounts for most of the 3.0 GB reclaimed, because the named images add up to about 1 GB.

On docker-main the biggest single item was three unused Open WebUI images (`latest`, `v0.11.3`, `v0.11.1`) at 5.09 GB each, plus an old `immich-machine-learning:release` image, two LinuxServer MariaDB images, Nginx Proxy Manager, Watchtower, and the earlier App Portal 0.3.0 and `app-portal-server:local` builds. The running App Portal 0.6.0, Homarr v1.77.2, and Dockhand v1.0.51 containers were not touched.

On docker-blue the prune removed the old locally built `homelab/unifi-network-mcp:0.29.3-full-access` image, which the Forgejo-registry `unifi-network-mcp:stable` image superseded, and the `docker/mcp-l4proxy` and `docker/mcp-l7proxy` images. Those two are on Docker Hub and the MCP gateway pulls them again if it needs them. On security-01 it removed the superseded local `wazuh-mcp-server-local:4.3.0-x509-compat` build.

## Images the prune kept

`docker image prune -a` keeps an image whose tag a container still names, even when the container runs an older image ID. That kept the newer images I downloaded during the [Compose Update Check - 2026-10-28](Compose%20Update%20Check%20-%202026-10-28.md) and have not deployed yet: `ghcr.io/finsys/hawser:latest` (311 MB) on the six hosts other than docker-main, and `itzg/minecraft-server:stable-java25` (1.3 GB) and `ghcr.io/playit-cloud/playit-agent:latest` (23.4 MB) on alpha-prod-01. They are the 311 MB, and on alpha-prod-01 the 1.636 GB, that `docker system df` still lists as reclaimable. Those updates remain open in that record.

## Hosts not pruned

- **ubuntu-dev (VM 105).** I left this one alone on purpose. Docker on my development workstation is a local build sandbox with no running containers. Its 17 unused images, about 10 GB, are mostly local builds (the t1bridge and Deskflow build environments, `u8-soffice`, and several App Portal test tags) that cannot be pulled back and would have to be rebuilt. The disk is at 68% with 69G free, so nothing forces it. Clearing these should be my decision for each build, not part of a fleet sweep.
- **ci-k3s-01 (VM 820).** Out of scope. It runs k3s on containerd, not Docker.
- **app-01 (VM 116).** Stopped on purpose since 2026-10-09, `EHOSTUNREACH` on 192.168.80.10:22. I did not start it for this job, so its Coolify images are untouched.
- **HQ-MGT01 (VM 303).** Stopped, `EHOSTUNREACH` on 192.168.65.12:22, so I could not check it. HQ-DC01, HQ-DC02, and win11-dev, the Windows guests that answered, have no Docker CLI.
- **ObiPC, parrot-os-mac, Andor-ParrotOS-PC, and surface-pro.** Not reachable over SSH (`EHOSTUNREACH`), so I could not check them for Docker.

## Open work

I still need to deploy the staged Hawser, Minecraft, and Playit updates from the 2026-10-28 check. Once those containers are on the new images, the older images they run become unused and a later prune will remove them. app-01 has not been pruned and needs its own pass when it is back in service.
