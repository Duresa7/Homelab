# Homarr Placement Research

**Created:** 2026-09-27  
**Last updated:** 2026-09-27

I recommend deploying Homarr with Docker Compose on `docker-main`, CT 110 on `grey-server`, at `192.168.40.35`. This is a placement recommendation only. I have not deployed Homarr or changed a running service.

## Live comparison

On 2026-09-27 at approximately 8:17 AM Eastern, I checked the five Docker LXCs through SSH Manager. I used `ssh_monitor` for memory and `ssh_execute` for CPU count, root and Docker filesystem capacity, running container names and status, and listeners on TCP 7575. These were read-only checks. I have not retained a separate raw transcript; the observed results are recorded below.

| LXC | CPUs | Allocated RAM | Available RAM | Root disk available | Running containers | Workload fit |
|---|---:|---:|---:|---:|---:|---|
| docker-main | 4 | 16 GiB | 13 GiB | 39 GiB | 14 | General applications, including Immich, BookLore, Forgejo, Dockhand and App Portal |
| docker-blue | 2 | 2 GiB | 1.3 GiB | 5.1 GiB | 11 | Remote access and integrations, including Executor, MCP gateways, RustDesk and MeshCentral |
| docker-network | 2 | 2 GiB | 1.6 GiB | 22 GiB | 6 | Nginx Proxy Manager and NetBird |
| monitor-01 | 2 | 2 GiB | 1.2 GiB | 5.8 GiB | 10 | Prometheus, Grafana, exporters and alerting |
| media-01 | 2 | 4 GiB | 2.7 GiB | 80 GiB | 11 | Jellyfin, media automation and downloads |

All five answered the checks, and none had a TCP listener on 7575. The filesystem figures refer to the root filesystem containing `/var/lib/docker`, not additional data mounts. The memory readings are rounded point-in-time values, not peak measurements. The monitor helper reported that `swapon` was unavailable on the four Debian 13 guests; their `free` readings still included swap totals and usage.

I also read CT 110's status through Proxmox on `grey-server`: running, four CPUs, 16 GiB allocated memory and approximately 2.5 GiB reported memory use. Grey itself reported 11 GiB of available RAM. Existing swap occupancy was approximately 1.6 GiB in CT 110 and 7.5 GiB on Grey; this snapshot does not establish active swapping or peak-load headroom.

## Recommendation

I would use `docker-main` because Homarr fits its existing application role and its present capacity does not call for an LXC resize. Dockhand already manages the local Docker engine there. I would keep the network access, monitoring, remote access and media guests focused on their existing workloads.

Homarr lists minimum requirements of 500 MB RAM, 600 MB disk space for the Docker image, and a single or dual-core CPU. Docker is its recommended installation method, and its Compose example uses persistent `/appdata` storage and TCP 7575. [Prerequisites](https://homarr.dev/docs/getting-started/), [Docker installation](https://homarr.dev/docs/getting-started/installation/docker/).

Before a later deployment, I would recheck capacity and the port, then select the desired integrations and access hostname. I have not tested integration reachability or changed DNS, proxy configuration, firewall rules, accounts, or containers.
