# Ollama GPU Docker Deployment Research

**Created:** 2026-09-04  
**Last updated:** 2026-09-04

I researched the least disruptive way to give Ollama in `docker-main` access to the GTX 1080 Ti installed in `grey-server`. This is a research snapshot, not a record of a live change. I did not inspect or modify the running Proxmox host or LXC while preparing it.

## Decision

I would keep Ollama in the existing `docker-main` LXC and pass the NVIDIA character devices through from `grey-server`. The host owns the kernel, so the proprietary NVIDIA kernel modules remain on `grey-server`; `docker-main` gets matching NVIDIA user-space libraries, NVIDIA Container Toolkit, and the device nodes used by CUDA. I would not configure PCI passthrough or build an NVIDIA kernel module inside the LXC.

The target versions on 2026-09-04 are:

| Component | Target | Reason |
| --- | --- | --- |
| Ollama | `0.33.3` | Current upstream release, published 2026-09-02 |
| Container image | `ollama/ollama:0.33.3@sha256:32931b46719f673c05fdbaa81ccb26da18ea4a1c57590a754874ab28ba269eb2` | Current stable tag pinned to the OCI index inspected on 2026-09-04 |
| NVIDIA Container Toolkit | `1.20.0-1` for all four toolkit packages | Current stable toolkit release |
| NVIDIA host driver | Proprietary R580 only; target `580.178.04` if its stock module passes a build test | Latest Pascal-compatible release as of 2026-09-04 |
| Initial model | `llama3.1:8b` | Its 4.9 GB Q4_K_M artifact fits the card's 11 GB VRAM |

[Ollama v0.33.3](https://github.com/ollama/ollama/releases/tag/v0.33.3) is the current release. The [official Docker instructions](https://docs.ollama.com/docker) use `ollama/ollama`, persist `/root/.ollama`, publish port 11434, and request NVIDIA acceleration with `--gpus=all`. I would pin the current numbered release and digest instead of deploying the floating `latest` tag. The [official tag registry](https://hub.docker.com/r/ollama/ollama/tags) is the place to resolve a new release and digest during a later controlled upgrade.

## Candidate Compose

This is the Compose file I would validate and deploy under `/opt/docker/ollama/docker-compose.yml` after the GPU preflight passes:

```yaml
name: ollama

services:
  ollama:
    image: ollama/ollama:0.33.3@sha256:32931b46719f673c05fdbaa81ccb26da18ea4a1c57590a754874ab28ba269eb2
    container_name: ollama
    restart: unless-stopped
    gpus: all
    ports:
      - "192.168.40.35:11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    healthcheck:
      test: ["CMD", "ollama", "list"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    stop_grace_period: 30s
    logging:
      driver: json-file
      options:
        max-size: 10m
        max-file: "3"

volumes:
  ollama-data:
```

The current Compose short form, [`gpus: all`](https://docs.docker.com/reference/compose-file/services/#gpus), requires Docker Compose 2.30.0 or newer. If `docker-main` does not meet that version, I would use Docker's documented [GPU device reservation](https://docs.docker.com/compose/how-tos/gpu-support/) instead:

```yaml
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

I would use one syntax, not both. The long form requires `capabilities: [gpu]`, and `count` cannot be combined with `device_ids`. This host has one GPU, so no `CUDA_VISIBLE_DEVICES` setting is needed.

The bind address deliberately exposes the port only on `docker-main`'s LAN address. The [local Ollama API has no authentication](https://docs.ollama.com/api/authentication), so I would not publish 11434 to every interface or forward it from the Internet. Any access across VLANs should be an explicit firewall or authenticated reverse-proxy decision.

## Pascal and CUDA compatibility

The [Ollama GPU matrix](https://docs.ollama.com/gpu) supports NVIDIA GPUs with compute capability 5.0 or newer and driver 531 or newer, and lists the GTX 1080 Ti at compute capability 6.1. The R580 driver already recorded in this repository clears that requirement. Ollama's source also builds its [CUDA 12 backend for architecture 61](https://github.com/ollama/ollama/blob/main/llama/server/CMakePresets.json).

Pascal must use the CUDA 12 backend. [CUDA 13 removed offline compilation and library support for Maxwell, Pascal, and Volta](https://docs.nvidia.com/cuda/archive/13.0.0/cuda-toolkit-release-notes/index.html). The official Ollama image currently carries CUDA 12 and CUDA 13 runners, so I would let Ollama auto-detect the correct runner first and confirm that its logs select `cuda_v12`. Ollama documents `OLLAMA_LLM_LIBRARY` as an experimental troubleshooting override, so I would add `OLLAMA_LLM_LIBRARY=cuda_v12` only if detection selects the wrong runner.

The current `llama4` artifacts do not fit this card: the [Scout Q4 artifact is 67 GB and Maverick is 245 GB](https://ollama.com/library/llama4). A practical first validation model is [`llama3.1:8b`](https://ollama.com/library/llama3.1:8b) at 4.9 GB, or [`llama3.2`](https://ollama.com/library/llama3.2) at 2.0 GB for the quickest smoke test. Ollama's [`ollama ps` output](https://docs.ollama.com/faq) is the authoritative application-level check for whether a loaded model is 100 percent GPU-resident or split between CPU and GPU.

## NVIDIA driver and the old kernel patch

The GPU must stay on NVIDIA's proprietary R580 branch. NVIDIA identifies R580 as the [last Linux driver branch for Maxwell, Pascal, and Volta](https://nvidia.custhelp.com/app/answers/detail/a_id/3142/). The newer 590, 595, and 610 branches are not an upgrade path for this card. NVIDIA also states that its [open kernel modules support Turing and newer GPUs](https://docs.nvidia.com/datacenter/tesla/driver-installation-guide/latest/kernel-modules.html); Maxwell, Pascal, and Volta require the proprietary flavor. The latest compatible release I found is [580.178.04](https://download.nvidia.com/XFree86/Linux-x86_64/580.178.04/README/supportedchips.html), whose supported-chip table explicitly includes the GTX 1080 Ti.

This repository preserves evidence of the previous workaround, but not the patch itself. The 2026-07-29 artifact sweep found extracted `nvidia-580.126.18-patched` and `nvidia-580.159.03-patched` trees, then removed them. Its execution record says 580.159.03 remained loaded and DKMS-installed against `7.0.2-6-pve` and `7.0.14-6-pve`. No patch file, patch contents, or build procedure remains in the working tree or Git history.

There is primary-source evidence for the class of problem: Canonical's [580.126.20 package record](https://lists.ubuntu.com/archives/noble-changes/2026-April/055299.html) includes a `buildfix_kernel_7.0.patch`. That does not prove that the deleted local patch is the same patch, and it does not justify applying an old diff to 580.178.04.

I would therefore leave the known-working 580.159.03 installation alone for the first Ollama deployment. If the driver itself is upgraded, I would treat that as separate host maintenance and first extract and build-test unmodified 580.178.04 against every installed PVE kernel and header set. I would patch only after a stock build produces a specific, reproducible compiler failure. The exact driver source checksum, patch, patch checksum, kernels, compiler output, and DKMS result should then be retained in the repository. A display-only problem is not a reason to change a headless CUDA stack when `nvidia`, `nvidia_uvm`, and an actual CUDA workload pass.

## LXC boundary

`docker-main` is LXC 110 on `grey-server`. Proxmox documents native [`dev[n]` passthrough](https://pve.proxmox.com/pve-docs/pct.1.html), including a device path and optional ownership and mode. I would enumerate the real devices after loading `nvidia_uvm`, then add only the NVIDIA character devices that exist. The likely set is `/dev/nvidia0`, `/dev/nvidiactl`, `/dev/nvidia-uvm`, and `/dev/nvidia-uvm-tools`; I would not hard-code that list before inspection. Pascal does not need MIG device nodes. Docker in an unprivileged LXC also requires the existing `keyctl=1` feature, which I would preserve rather than replacing the LXC feature line.

Because an LXC shares the host kernel, `grey-server` owns the NVIDIA module. Inside `docker-main`, `nvidia-smi` must see the passed device and matching R580 user-space libraries before Docker is configured. If those libraries are absent, I would install only the exact host-matching R580 user-space portion and would not install a second DKMS/kernel module in the LXC. I would not mix Debian-packaged and `.run`-installed driver components without first identifying how the existing installation is managed.

Proxmox recommends a QEMU VM for application-container workloads in the same `pct` documentation. Keeping the established Docker-in-LXC topology avoids migrating the twelve current workloads, but it makes the LXC and cgroup preflight mandatory.

## Container Toolkit

NVIDIA's current [Debian installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) installs four version-matched packages and runs `nvidia-ctk runtime configure --runtime=docker` before restarting Docker. I would pin all four to `1.20.0-1`:

```text
nvidia-container-toolkit
nvidia-container-toolkit-base
libnvidia-container-tools
libnvidia-container1
```

I would first run `nvidia-ctk runtime configure --runtime=docker --dry-run`, preserve the existing `/etc/docker/daemon.json`, inspect the merged result, and validate it with `dockerd --validate --config-file=/etc/docker/daemon.json`. The configuration command modifies Docker's daemon file. Its required Docker restart affects every service on `docker-main`, so I would inventory the existing containers and health state before the restart and compare them afterward.

NVIDIA's [toolkit troubleshooting guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/troubleshooting.html) records a systemd cgroup problem in which `systemctl daemon-reload` can make a running container lose GPU access. Current toolkit CDI support is preferable to weakening cgroup enforcement. I would verify `nvidia-ctk cdi list` and use the toolkit's default CDI behavior first. I would set `no-cgroups=true` only if the nested LXC reproduces the exact BPF/cgroup-device permission error and the outer LXC device allowlist is confirmed, because that setting removes an inner enforcement layer.

## Deployment gates

I would stop at the first failed gate rather than changing the next layer.

### 1. Host driver

On `grey-server`:

```bash
uname -r
nvidia-smi -L
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
modinfo -F version nvidia
modinfo -F license nvidia
dkms status
modprobe nvidia_uvm
ls -l /dev/nvidia*
```

Expected result: one GTX 1080 Ti, an R580 driver, proprietary/NVIDIA module licensing, DKMS installed for the running and fallback PVE kernels, and stable NVIDIA device nodes including UVM. A failure here belongs to the host-driver maintenance path, not the Ollama deployment.

### 2. LXC device and user space

Before editing, capture `pct config 110`, the LXC status, and the exact `/dev/nvidia*` inventory. Add device entries without replacing unrelated configuration, then perform one controlled LXC stop/start. Inside `docker-main`:

```bash
ls -l /dev/nvidia*
nvidia-smi -L
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
```

Expected result: the same GPU and driver version as the host. I would also verify all pre-existing Docker containers returned to their original running and health state after the LXC restart.

### 3. Docker runtime

Inside `docker-main`:

```bash
docker version
docker compose version
nvidia-ctk --version
nvidia-ctk runtime configure --runtime=docker --dry-run
dockerd --validate --config-file=/etc/docker/daemon.json
nvidia-ctk cdi list
docker run --rm --runtime=nvidia --gpus all ubuntu nvidia-smi
```

The final command is NVIDIA's [documented sample workload](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/sample-workload.html). It must succeed before an Ollama container is created. After the one necessary Docker restart, I would compare the full container list, restart counts, and health states with the captured baseline.

### 4. Ollama and model

From `/opt/docker/ollama`:

```bash
docker compose config --quiet
docker compose pull
docker compose up -d --wait
curl -fsS http://192.168.40.35:11434/api/version
docker compose exec ollama ollama pull llama3.1:8b
docker compose exec ollama ollama run llama3.1:8b 'Reply with exactly: GPU OK'
docker compose exec ollama ollama ps
docker compose logs --no-color --tail=200 ollama
nvidia-smi
```

Expected result: the API reports 0.33.3, generation succeeds, `ollama ps` reports 100 percent GPU for the initial model, the logs show the CUDA 12 runner, and `nvidia-smi` shows the Ollama process consuming GPU memory. A CPU/GPU split can be valid for a larger model, but it is a failed initial 8B acceptance test until explained.

## Rollback

I would keep each rollback scoped to the layer changed:

- Ollama: `docker compose down` removes the container and network while retaining the `ollama-data` volume. I would not use `down -v` or prune images or volumes. To revert an image, I would restore the previous tag and digest, pull it, and recreate only this Compose project.
- Docker runtime: restore the exact pre-change `/etc/docker/daemon.json`, validate it, restart Docker once, and verify every pre-existing container against the baseline. Any temporary host-side copy should be removed after the rollback evidence is retained according to the repository backup rules.
- LXC: remove only the newly added `dev[n]` entries, restore their captured predecessor if necessary, stop/start LXC 110, and verify its existing workload set.
- Host driver: avoid combining this with the Ollama deployment. For separate driver maintenance, retain a known-good PVE kernel and known-good R580 installer/package set, verify DKMS for both current and fallback kernels before reboot, and keep console access for selecting the fallback kernel. Do not remove 580.159.03 until 580.178.04 has passed `nvidia-smi`, UVM, the NVIDIA container sample, and Ollama generation.

This sequence contains the blast radius: the LXC restart and Docker restart are the only planned interruptions to `docker-main`, and the existing twelve containers get an explicit before-and-after health comparison. No kernel patch is part of the baseline deployment.
