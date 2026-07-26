# cAdvisor Registers No Containers Under the Docker 29 overlayfs Driver

**Created:** 2026-07-25  
**Last updated:** 2026-07-26

**Issue date:** 2026-07-25  
**Resolved:** 2026-07-26, by upgrading cAdvisor to v0.60.5  
**Status:** Resolved  
**Affected systems:** `docker-network`, `docker-blue`, `media-01`, `alpha-prod-01`, `app-01`, `security-01`

## Symptom

I deployed cAdvisor v0.52.1 to seven Docker hosts and six of them reported no containers at all. Each one answered on TCP 9101 with HTTP 200 and emitted roughly 600 series, so the container looked healthy from the outside. Every one of those series belonged to the root cgroup `id="/"`, with an empty `name` label.

`docker-main` worked correctly and reported all 14 of its containers by name. The Prometheus query `count by (host)(container_last_seen{name!=""})` returned exactly one result: `docker-main=14`. Fleet-wide there are about 46 containers, so 32 were invisible.

## Root Cause

The six failing hosts use Docker 29's `overlayfs` storage driver. `docker-main` still uses the legacy `overlay2` driver. That single difference decides whether cAdvisor works.

`docker info` confirms the split:

```
DRIVER overlay2   docker-main
DRIVER overlayfs  alpha-prod-01
DRIVER overlayfs  media-01
DRIVER overlayfs  docker-network
DRIVER overlayfs  docker-blue
DRIVER overlayfs  app-01
DRIVER overlayfs  wazuh-01
```

cAdvisor's Docker factory registers successfully, then fails on every individual container while trying to resolve its read-write layer:

```
E0726 00:31:06.483014 1 manager.go:1116] Failed to create existing container:
/system.slice/docker-53401a1ac80e...scope: failed to identify the read-write
layer ID for container "53401a1ac80e..." - open /rootfs/var/lib/docker/image/
overlayfs/layerdb/mounts/53401a1ac80e.../mount-id: no such file or directory
```

That `layerdb/mounts` path is the old graph-driver layout. Docker 29's `overlayfs` driver is the containerd snapshotter, which stores layer metadata in containerd instead, so the file cAdvisor opens doesn't exist. The lookup happens during container creation rather than during metric collection, so the failure kills registration outright instead of just dropping filesystem metrics.

Docker version is not the variable. All seven hosts run Docker 29.5.3 or newer, and `docker-main` on 29.6.1 works fine. The storage driver is what differs, and `docker-main` kept `overlay2` because it predates the upgrade that made `overlayfs` the default.

## What I Tried On 2026-07-25

Three fixes, none of which recovered it. I also concluded v0.52.1 was the newest cAdvisor release, because `v0.53.0`, `v0.54.0`, and `v0.55.0` all return no manifest from `gcr.io/cadvisor/cadvisor`. That conclusion was wrong and cost a day; see the resolution below.

Adding `disk` to `--disable_metrics` didn't help. I expected it to skip the layer lookup, since that lookup exists to support `container_fs_*` metrics. It made no difference because the failure happens in `manager.go` during container creation, before metric selection is consulted.

Dropping `--docker_only=true` changed the shape of the output without fixing it. cAdvisor then reported 45 cgroups including `/system.slice` and `/init.scope`, but still no `docker-*.scope` entries and still no `name` labels. The Docker factory claims those cgroups and fails; nothing else picks them up.

Pointing the containerd factory at the socket directly, with `--containerd=/run/containerd/containerd.sock --containerd-namespace=moby`, also produced zero named containers. The log confirms `Registering containerd factory` and `Registration of the containerd container factory successfully`, so the factory loads. It just never gets the containers, because the Docker factory has already claimed and failed them.

## Resolution: cAdvisor v0.60.5, 2026-07-26

There was a newer cAdvisor all along. My version check asked for three tags that were never published and read the absence as "nothing newer exists":

```
gcr.io/cadvisor/cadvisor:v0.53.0   no manifest
gcr.io/cadvisor/cadvisor:v0.54.0   no manifest
gcr.io/cadvisor/cadvisor:v0.55.0   no manifest
gcr.io/cadvisor/cadvisor:latest    v0.55.1     <- three releases past mine
ghcr.io/google/cadvisor:latest     v0.60.5     <- eight
```

`gcr.io` stops at v0.55.1. The current publishing location is `ghcr.io/google/cadvisor`, which carries v0.60.5. The lesson is the method, not the number: resolve `latest` and read the version it reports, rather than probing tags you guessed at and treating a 404 as proof.

v0.60.5 handles the containerd snapshotter. I tested it on `security-01`, which runs Docker 29.6.1 on `overlayfs`, before touching anything else:

```
named containers: 6 of 6 running
read-write layer errors: 0
total series: 959
```

Six of six, against zero under v0.52.1 on the same host with the same flags. Rolling it to all seven hosts through the playbook:

| Host | Docker | Driver | Containers registered |
|---|---|---|---|
| docker-main | 29.6.1 | overlay2 | 14 of 14 |
| media-01 | 29.6.2 | overlayfs | 9 of 9 |
| alpha-prod-01 | 29.6.1 | overlayfs | 7 of 7 |
| app-01 | 29.6.1 | overlayfs | 7 of 7 |
| security-01 | 29.6.1 | overlayfs | 6 of 6 |
| docker-network | 29.6.1 | overlayfs | 4 of 4 |
| docker-blue | 29.5.3 | overlayfs | 3 of 3 |

50 containers, seven of which are the cAdvisor containers themselves. `ok=14 changed=3` per host, nothing failed, nothing unreachable. All seven answered 200 on 9101 from `security-01` with no firewall work needed, because the 2026-07-25 policies already covered 9101 to each zone.

Prometheus went from 38 targets to 44 and the container panels went fleet-wide. Their expressions now group by `host` as well as `name`, since a container name is only unique within a host and aggregating on name alone would silently merge two hosts running the same image.

I also changed what the playbook guards on. The old pre-flight assert refused to install unless the driver was `overlay2`, which encoded this specific cause and would have blocked the fix. It now counts the containers cAdvisor registered after installing and fails when a host with running containers reports none. That catches this failure and any future one with a different cause, and it cannot be wrong about which driver is acceptable.

## Original Workaround, 2026-07-25 to 2026-07-26

I removed cAdvisor from the six `overlayfs` hosts and kept it on `docker-main`. Six hosts each emitting 600 series of root-cgroup data is 3,600 series of storage plus a log line every minute, and none of it answers a question I couldn't already answer from `node_exporter`.

The removal runs through the same playbook that installed it:

```bash
cd /home/ansible/monitoring-exporters
ansible-playbook playbooks/cadvisor.yml -e target=cadvisor_incompatible -e cadvisor_state=absent
```

All six reported `port 9101 now returns 000` afterward. The `cadvisor` scrape job in `prometheus.yml` now lists `docker-main` alone.

I also put the finding into the tooling rather than only into this record. The playbook reads `docker info --format {{.Driver}}` and refuses to install unless the driver is `overlay2`, overridable with `-e allow_incompatible_driver=true`. The inventory keeps the six hosts in a `cadvisor_incompatible` group with the reason written next to them, and `tests/validate_project.py` fails if any of them reappears as a cAdvisor target. Re-adding a host by accident now breaks loudly instead of silently collecting nothing.

While the workaround stood, the container row on the Homelab Overview dashboard covered `docker-main` only, 14 containers of roughly 46, and the panel descriptions said so. A container panel that silently covers a seventh of the fleet is worse than one that admits its scope.

## Paths I Did Not Need

A Docker-API exporter reading `/containers/<id>/stats` would have sidestepped layer metadata entirely, at the cost of a third-party image with the Docker socket mounted on six hosts carrying live workloads, plus new metric names and therefore new dashboard expressions. Worth it if v0.60.5 had failed; wasted work now.

Switching the six hosts back to `overlay2` would also have worked and was always the wrong trade: re-pulling every image and discarding container filesystems on hosts running Immich, NPM, NetBird and the media stack, to fix a metrics gap.

## What I'd Do Differently

The problem was diagnosed correctly on 2026-07-25 and the wrong conclusion was drawn from it anyway, because I never checked whether a newer build existed. Three guessed tags returning 404 is not a version check. Pull `latest` and ask the binary what it is.

The second lesson is where a constraint gets encoded. I wrote "driver must be `overlay2`" into the playbook as a pre-flight assert, and that assert would have refused to install the version that fixes it. Guards belong on the symptom you care about, which here is "did it register any containers", not on the cause you happened to find first.
