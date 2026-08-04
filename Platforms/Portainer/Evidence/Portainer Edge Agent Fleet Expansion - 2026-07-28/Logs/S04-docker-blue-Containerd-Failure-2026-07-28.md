# Step 4 docker-blue Containerd Failure

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Capture date:** 2026-07-28  
**Execution mechanism:** SSH Manager MCP through `blue_server`, `pct exec 108`  
**Target:** `docker-blue`

## Original Failure

```sh
cd /opt/docker/portainer-edge-agent
docker compose up -d
```

```text
Container portainer_edge_agent Starting
Error response from daemon: failed to create task for container: failed to create shim task: ttrpc: closed
```

`docker start portainer_edge_agent` returned the same error.

## Minimal Reproduction

```sh
docker run --name codex-portainer-repro --rm \
  --entrypoint /bin/true ghcr.io/google/cadvisor:v0.60.5
```

```text
minimal-container-exit=125
docker: Error response from daemon: failed to create task for container: failed to create shim task: ttrpc: closed
repro-container-present=0
```

The same result occurred with `--cgroupns=host` & with `--cgroup-parent=user.slice`. Each command removed its transient container & temporary output.

## containerd Journal

```sh
journalctl -u containerd --since "15 minutes ago" --no-pager
```

```text
panic: runtime error: invalid memory address or nil pointer dereference
github.com/containerd/containerd/v2/cmd/containerd-shim-runc-v2/runc.(*Container).Cgroup
    /go/src/github.com/containerd/containerd/cmd/containerd-shim-runc-v2/runc/container.go:279
github.com/containerd/containerd/v2/cmd/containerd-shim-runc-v2/task.(*service).Create
    /go/src/github.com/containerd/containerd/cmd/containerd-shim-runc-v2/task/service.go:257
shim disconnected
failed to delete task error="ttrpc: closed"
```

## Runtime Comparison

```sh
docker version --format 'server={{.Server.Version}}'
containerd --version
runc --version | head -n 1
```

```text
docker-blue:
server=29.5.3
containerd containerd.io v2.2.4
runc version 1.3.5

media-01:
server=29.6.2
containerd containerd v2.2.6
runc version 1.3.6
```

`apt-cache policy` on `docker-blue` offers Docker 29.6.2 & containerd 2.2.6. `pct config 108` reports `features: nesting=1`; working CT 842 reports `features: nesting=1,keyctl=1`.

## Preserved Service State

```text
cadvisor|Up 2 days (healthy)
hbbs|Up 5 days
hbbr|Up 5 days
```

I did not restart Docker, containerd, or CT 108.
