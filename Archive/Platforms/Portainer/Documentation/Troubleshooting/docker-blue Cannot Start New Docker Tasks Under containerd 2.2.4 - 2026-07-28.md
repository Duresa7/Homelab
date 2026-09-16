# docker-blue Cannot Start New Docker Tasks Under containerd 2.2.4

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Investigation date:** 2026-07-28  
**Affected system:** Galaxy CT 108 `docker-blue` on `blue-server`  
**Status:** Resolved on 2026-07-28

## Symptom

Docker creates a new container record on `docker-blue` but can't start its task. The Portainer Edge Agent remains in `created`, while `cadvisor`, RustDesk `hbbs`, & RustDesk `hbbr` continue running.

```text
failed to create task for container: failed to create shim task: ttrpc: closed
```

## Reproduction

The failure is deterministic. Starting `portainer_edge_agent` failed twice. A minimal container using the already-present cAdvisor v0.60.5 image returned exit 125 with the same error:

```sh
docker run --name codex-portainer-repro --rm \
  --entrypoint /bin/true ghcr.io/google/cadvisor:v0.60.5
```

The test created no persistent container. Repeating it with `--cgroupns=host` and with `--cgroup-parent=user.slice` changed nothing.

## Exact Runtime Error

The containerd journal records a Go panic in the shim:

```text
panic: runtime error: invalid memory address or nil pointer dereference
github.com/containerd/containerd/v2/cmd/containerd-shim-runc-v2/runc.(*Container).Cgroup
    /go/src/github.com/containerd/containerd/cmd/containerd-shim-runc-v2/runc/container.go:279
github.com/containerd/containerd/v2/cmd/containerd-shim-runc-v2/task.(*service).Create
    /go/src/github.com/containerd/containerd/cmd/containerd-shim-runc-v2/task/service.go:257
```

containerd then disconnects the shim, cleans it up, & returns `ttrpc: closed` to Docker.

## Hypotheses and Tests

| Rank | Hypothesis | Prediction | Result |
|---:|---|---|---|
| 1 | containerd 2.2.4 shim fault | Any fresh task fails; moving to 2.2.6 removes the panic | Confirmed. The exact minimal test returned 0 after the 2.2.6 update, then the Portainer task started |
| 2 | Missing LXC `keyctl=1` feature | Other Docker LXCs with the feature start new tasks; CT 108 needs a feature change and restart | Rejected as the required fix. CT 108 still has `nesting=1` only & starts new tasks under containerd 2.2.6 |
| 3 | Portainer image or mounts | Minimal cAdvisor container starts while Portainer fails | Rejected. The minimal container fails before its command runs |
| 4 | Cgroup namespace or parent | Host cgroup namespace or a different systemd slice starts the test | Rejected. Both variants return the same shim failure |
| 5 | Stale containerd state | A runtime restart clears the failure without package changes | Not isolated. The approved repair changed the package version and restarted the runtime together |

## Version Comparison

| Component | Failed `docker-blue` state | Resolved `docker-blue` state |
|---|---|---|
| Docker Engine | 29.5.3 | 29.6.2 |
| containerd | 2.2.4 | 2.2.6 |
| runc | 1.3.5 | 1.3.6 |
| LXC features | `nesting=1` | `nesting=1`; unchanged |

`media-01` already ran the resolved 29.6.2 / 2.2.6 / 1.3.6 set, which gave the repair an exact live comparison.

## Failed Attempts

- A second `docker start portainer_edge_agent`
- A minimal container from the cAdvisor image
- The same minimal container with `--cgroupns=host`
- The same minimal container under `user.slice`

I removed each transient test container and its temporary output immediately after the check.

## Current Impact

None. Portainer lists `cadvisor`, `hbbs`, `hbbr`, & `portainer_edge_agent` through environment 7.

This remained routine troubleshooting, not a service incident. The package update restarted the three existing containers; `cadvisor` returned healthy and both RustDesk containers returned running.

## Correction

The APT simulation proposed four upgrades, zero new packages, & zero removals. I installed exact versions for Docker Engine 29.6.2, Docker CLI 29.6.2, Docker rootless extras 29.6.2, & containerd 2.2.6. The containerd package supplies runc 1.3.6.

I did not add `keyctl=1` or restart CT 108. The runtime update removed the panic before either fallback was needed.

## Verification

- The original cAdvisor `/bin/true` reproduction returned exit 0.
- `portainer_edge_agent` reports `running`, restart policy `always`, & image 2.39.1.
- Portainer environment 7 reports status 1, a nonzero check-in, a reachable tunnel, & 4 containers.
- `hbbs` & `hbbr` report running. cAdvisor reports healthy.

[Fleet expansion change record](../Change%20Records/Portainer%20Edge%20Agent%20Fleet%20Expansion%20-%202026-07-28.md)  
[Retained failure evidence](../../Evidence/Portainer%20Edge%20Agent%20Fleet%20Expansion%20-%202026-07-28/Logs/S04-docker-blue-Containerd-Failure-2026-07-28.md)  
[Repair and verification evidence](../../Evidence/Portainer%20Edge%20Agent%20Fleet%20Expansion%20-%202026-07-28/Logs/S06-docker-blue-Runtime-Repair-and-Fleet-Verification-2026-07-28.md)
