# GTX 1080 Ti and Llama Deployment

**Created:** 2026-09-04  
**Last updated:** 2026-09-04

## Date

I completed this deployment on 2026-09-04.

## Scope

I attached the GTX 1080 Ti in `grey-server` to LXC 110 `docker-main`, repaired the existing patched NVIDIA driver for the running and next Proxmox kernels, installed the current NVIDIA container runtime, and deployed the current Ollama release with Llama 3.1 8B. I kept the existing Docker workloads in place and took no snapshot or backup.

The [research record](../../../../Infrastructure/Compute/Galaxy/Documentation/Ollama%20GPU%20Docker%20Deployment%20Research%20-%202026-09-04.md) found Ollama 0.33.3 and NVIDIA Container Toolkit 1.20.0-1 current on the deployment date. It also established that Pascal support ends with NVIDIA's proprietary R580 branch. I therefore did not replace the known-working 580.159.03 driver with an unrelated driver upgrade during this deployment.

## Starting State

`docker-main` already had the requested 16 GiB memory allocation, 13 running containers, 13 GiB memory available, and 66 GiB free on its root filesystem. Docker 29.8.0 and Compose 5.5.1 were running. All defined container health checks passed and every restart count was zero. Nothing listened on TCP 11434.

The host saw the GTX 1080 Ti on PCI address `0000:2b:00.0`, but `nvidia-smi` failed because no NVIDIA module was loaded. The patched 580.159.03 DKMS source remained at `/usr/src/nvidia-580.159.03`; it was installed only for kernel `7.0.14-6-pve`. Grey was running `7.0.14-8-pve`, already had `7.0.14-15-pve` installed for its next reboot, and lacked headers and driver builds for both. The existing `nvidia-lxc-devices.service` had failed at boot for the same reason.

## Host Driver Repair

I installed the exact official Proxmox header packages for `7.0.14-8-pve` and `7.0.14-15-pve`. The apt simulation showed two new packages and no removal or upgrade. I then built and installed the retained patched proprietary 580.159.03 DKMS source against both kernels. Both build logs exited successfully, and DKMS now lists installed modules for `7.0.14-6-pve`, `7.0.14-8-pve`, and `7.0.14-15-pve`.

Restarting `nvidia-lxc-devices.service` loaded `nvidia`, `nvidia_modeset`, and `nvidia_uvm`. The service is enabled and active. I added `Before=pve-guests.service` because LXC 110 starts automatically and the old unit could race Proxmox guest startup before its device nodes existed. This is an ordering edge only: GPU service failure does not make the other guests depend on it. Host `nvidia-smi` reports the GTX 1080 Ti, 11,264 MiB, compute capability 6.1, and driver 580.159.03. I did not reboot Grey; the running kernel works and the next installed kernel has a completed DKMS build.

## LXC and Runtime

I added seven native Proxmox device mappings to LXC 110: `/dev/nvidia0`, `/dev/nvidiactl`, `/dev/nvidia-modeset`, `/dev/nvidia-uvm`, `/dev/nvidia-uvm-tools`, and the two `/dev/nvidia-caps` capability nodes. I excluded the stale vGPU nodes. One controlled LXC shutdown and start made the devices visible inside `docker-main`. All 13 existing containers returned to their prior running and health state before I continued.

I downloaded NVIDIA's official 580.159.03 runfile inside the LXC. Its SHA-256 was `32c85d99b0f640c9501f61b39ddad208fd0288d015c4fbc5fd0435c07783fa77`, matching NVIDIA's published checksum. I installed only user-space files with `--no-kernel-modules`, `--no-kernel-module-source`, and `--no-dkms`. LXC `nvidia-smi` then matched the host's card and driver.

I added NVIDIA's official container repository after verifying signing-key fingerprint `C95B321B61E88C1809C4F759DDCAE044F796ECB0`. Apt installed exactly four new packages at 1.20.0-1 and removed nothing: `libnvidia-container1`, `libnvidia-container-tools`, `nvidia-container-toolkit-base`, and `nvidia-container-toolkit`. `nvidia-ctk` merged the `nvidia` runtime into the existing logging-only Docker configuration, `dockerd --validate` passed, and all 13 containers returned healthy after the planned daemon restart.

A disposable Ubuntu 24.04 container using the explicit NVIDIA runtime reported the GTX 1080 Ti, driver 580.159.03, all 11,264 MiB, and compute capability 6.1. I removed the disposable image after verification. I did not enable the toolkit's `no-cgroups` option.

## Ollama Deployment

I placed the versioned Compose file at `/opt/docker/ollama/docker-compose.yml`. It pins `ollama/ollama:0.33.3` to digest `sha256:32931b46719f673c05fdbaa81ccb26da18ea4a1c57590a754874ab28ba269eb2`, requests all GPUs, uses the named model volume, limits its JSON logs, and binds TCP 11434 only to `192.168.40.35`.

The first `docker compose up` pulled the correct image but left Ollama in `Created`. The exact error was:

```text
nvidia-container-cli: mount error: failed to add device rules: unable to find any existing device filters attached to the cgroup: bpf_prog_query(BPF_CGROUP_DEVICE) failed: operation not permitted
```

This was the nested-LXC path the preflight anticipated. The explicit NVIDIA runtime had already passed a real container test, so I added `runtime: nvidia` beside `gpus: all` and recreated only the new Ollama container. It became healthy without disabling cgroup enforcement or changing another service.

I pulled `llama3.1:8b`, model ID `46e0c10c039e`, into the named volume. A non-streaming API request returned `GPU OK`. During and after that request, `ollama ps` reported `100% GPU`; Ollama selected CUDA, projected 5,027 MiB, offloaded all 33 of 33 layers, and NVIDIA reported 5,187 MiB in use.

## Verification

- Ollama reports version 0.33.3, the Compose container is healthy, and the configured image digest matches the pulled digest.
- The listener is only `192.168.40.35:11434`. Nginx Proxy Manager has no matching proxy or stream route, and UniFi has zero WAN port forwards.
- All 14 containers on `docker-main` are running. Every defined health check passes and every restart count is zero.
- `docker-main` has 13 GiB memory available after deployment and 61 GiB free on its root filesystem.
- Galaxy remains quorate with five of five votes.
- Grey has no failed NVIDIA unit. Its pre-existing failed `nut-monitor.service` and `zfs-import@hddpool.service` remain unrelated and unchanged.
- The versioned Compose file matches the live file. The versioned device-node unit matches the live unit, systemd orders it before `pve-guests.service`, and another CUDA generation passed after the host daemon reload.

I added Ollama to the fleet-update inventory as the eighth managed Compose project on `docker-main` and the twenty-fifth project overall. The controller-side validator and Ansible syntax check passed. A `--check` run against `docker-main` found all eight projects, including Ollama, and ended with zero unreachable and zero failed hosts without changing the live services.

## Remaining Work

No work remains for the requested deployment. The host still runs `7.0.14-8-pve` until the separately planned Galaxy rolling reboot; 580.159.03 is already built for installed kernel `7.0.14-15-pve`.
