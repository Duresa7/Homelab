# cAdvisor Registers No Containers Under the Docker 29 overlayfs Driver

**Created:** 2026-07-25  
**Last updated:** 2026-07-25

**Issue date:** 2026-07-25  
**Status:** Open upstream, worked around  
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

## What I Tried

Three fixes, none of which recovered it. v0.52.1 is the newest cAdvisor release; `v0.53.0`, `v0.54.0`, and `v0.55.0` all return no manifest from `gcr.io/cadvisor/cadvisor`, so there is no newer build to move to.

Adding `disk` to `--disable_metrics` didn't help. I expected it to skip the layer lookup, since that lookup exists to support `container_fs_*` metrics. It made no difference because the failure happens in `manager.go` during container creation, before metric selection is consulted.

Dropping `--docker_only=true` changed the shape of the output without fixing it. cAdvisor then reported 45 cgroups including `/system.slice` and `/init.scope`, but still no `docker-*.scope` entries and still no `name` labels. The Docker factory claims those cgroups and fails; nothing else picks them up.

Pointing the containerd factory at the socket directly, with `--containerd=/run/containerd/containerd.sock --containerd-namespace=moby`, also produced zero named containers. The log confirms `Registering containerd factory` and `Registration of the containerd container factory successfully`, so the factory loads. It just never gets the containers, because the Docker factory has already claimed and failed them.

## Resolution

I removed cAdvisor from the six `overlayfs` hosts and kept it on `docker-main`. Six hosts each emitting 600 series of root-cgroup data is 3,600 series of storage plus a log line every minute, and none of it answers a question I couldn't already answer from `node_exporter`.

The removal runs through the same playbook that installed it:

```bash
cd /home/ansible/monitoring-exporters
ansible-playbook playbooks/cadvisor.yml -e target=cadvisor_incompatible -e cadvisor_state=absent
```

All six reported `port 9101 now returns 000` afterward. The `cadvisor` scrape job in `prometheus.yml` now lists `docker-main` alone.

I also put the finding into the tooling rather than only into this record. The playbook reads `docker info --format {{.Driver}}` and refuses to install unless the driver is `overlay2`, overridable with `-e allow_incompatible_driver=true`. The inventory keeps the six hosts in a `cadvisor_incompatible` group with the reason written next to them, and `tests/validate_project.py` fails if any of them reappears as a cAdvisor target. Re-adding a host by accident now breaks loudly instead of silently collecting nothing.

## Consequence for the Dashboard

The container row on the Homelab Overview dashboard covers `docker-main` only, which is 14 containers of roughly 46. The panel titles and descriptions say so, because a container panel that silently covers a seventh of the fleet is worse than one that admits its scope.

Per-host CPU and memory still cover all 14 scraped hosts through `node_exporter`, and service reachability covers all 19 proxied names through `blackbox_exporter`. What's missing is per-container attribution on six hosts: which container on `media-01` is eating RAM, rather than whether `media-01` is under pressure at all.

## Follow-Up

Two paths out, tracked in the [platform TODO](../TODO.md).

Wait for cAdvisor to support the containerd snapshotter layout, then add the six hosts back to `cadvisor_targets` and re-run the playbook. Nothing else would need to change; the scrape job and the dashboard queries already aggregate by `name` and would pick up the extra hosts on their own.

The alternative is a Docker-API-based exporter that reads `/containers/<id>/stats` instead of walking cgroup layer metadata, which sidesteps the storage driver entirely. I didn't install one here because it would mean putting a third-party image on six hosts carrying live workloads, and that deserves its own vetting rather than being folded into this change.

Switching the six hosts back to `overlay2` would also work and is the wrong trade. It means re-pulling every image and discarding container filesystems on hosts running Immich, NPM, NetBird, and the media stack, to fix a metrics gap.
