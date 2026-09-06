# Ollama

**Created:** 2026-09-04  
**Last updated:** 2026-09-05

I run Ollama on `docker-main` with Grey's GTX 1080 Ti. The API is available directly on the internal Docker host at `http://192.168.40.35:11434`; I did not put it behind Nginx Proxy Manager or a WAN port forward because the API has no built-in authentication. The same Compose project runs an authenticated Open WebUI frontend at `https://openwebui.alphasecunited.com`, with direct recovery access on `http://192.168.40.35:3002`.

## Current State

| Item | Current value |
| --- | --- |
| Status | Ollama and Open WebUI healthy; real Qwen generation and Handy-compatible transcript cleanup verified on CUDA; WebUI-to-Ollama model discovery and internal HTTPS verified |
| Host | Galaxy LXC 110 `docker-main`, 4 vCPU, 16 GiB memory, 4 GiB swap |
| Live project | `/opt/docker/ollama` |
| Containers | `ollama` and `open-webui`, restart policy `unless-stopped` |
| Image | `ollama/ollama:0.33.3` pinned to digest `sha256:32931b46719f673c05fdbaa81ccb26da18ea4a1c57590a754874ab28ba269eb2` |
| Model | `qwen3.5:2b`, model ID `324d162be6ca`, 2.7 GB on disk; Qwen 3.5 family, 2.3B parameters, Q8_0 |
| GPU | NVIDIA GeForce GTX 1080 Ti, 11,264 MiB, compute capability 6.1 |
| Driver | Proprietary NVIDIA 580.159.03 on `grey-server`; matching user space inside `docker-main` |
| Container runtime | NVIDIA Container Toolkit 1.20.0-1; Compose selects runtime `nvidia` and requests all GPUs |
| Persistent state | Named volume `ollama_ollama-data` mounted at `/root/.ollama` |
| Web interface | `https://openwebui.alphasecunited.com`; Open WebUI rolling `main`, currently 0.11.3, authenticated, with named volume `ollama_open-webui-data` |
| Handy post-processing | Custom provider at `http://192.168.40.35:11434/v1` using `qwen3.5:2b` |
| Listeners | Ollama API at `192.168.40.35:11434`; Open WebUI at `192.168.40.35:3002` |
| Boot ordering | `nvidia-lxc-devices.service` runs before `pve-guests.service` on `grey-server` |

## Runtime Boundary

`grey-server` owns the NVIDIA kernel modules. The unprivileged LXC receives only the seven real NVIDIA character devices, and it carries matching driver user-space files without DKMS or a second kernel module. The Compose service needs both `runtime: nvidia` and `gpus: all` in this nested-LXC deployment. Since 2026-09-05 the [Immich](../Immich/README.md) server and machine-learning containers share the same card for NVENC transcoding and CUDA inference, so a loaded Ollama model, a running transcode, and Immich's CLIP model share the 11,264 MiB. The ordinary device-request path cannot inspect the outer LXC's BPF device filter, while the explicitly registered NVIDIA runtime passes the same workload without turning off cgroup enforcement.

The GTX 1080 Ti is Pascal hardware. It stays on the proprietary R580 driver branch; open NVIDIA kernel modules and the R590 or newer branches do not support this card. I retained the working 580.159.03 patched source already registered with DKMS rather than combining a driver replacement with the service deployment.

## Records

- [Compose configuration](Configuration/docker-compose.yml)
- [Host device-node service](Configuration/nvidia-lxc-devices.service)
- [Operations runbook](Documentation/Runbook.md)
- [Deployment record](Documentation/Change%20Records/GTX%201080%20Ti%20and%20Llama%20Deployment%20-%202026-09-04.md)
- [Qwen model replacement](Documentation/Change%20Records/Qwen%203.5%202B%20Model%20Replacement%20-%202026-09-04.md)
- [Open WebUI platform](../Open%20WebUI/README.md)
- [Deployment research](../../Infrastructure/Compute/Galaxy/Documentation/Ollama%20GPU%20Docker%20Deployment%20Research%20-%202026-09-04.md)
