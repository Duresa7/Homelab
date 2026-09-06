# GTX 1080 Ti NVENC Transcoding

**Created:** 2026-09-05  
**Last updated:** 2026-09-05

**Date:** 2026-09-05  
**Status:** Complete

## Change

I moved Immich video transcoding on `docker-main` from CPU to the GTX 1080 Ti in `grey-server`. The GPU path already existed for Ollama: the [Ollama deployment record](../../../Ollama/Documentation/Change%20Records/GTX%201080%20Ti%20and%20Llama%20Deployment%20-%202026-09-04.md) covers the host driver, the seven device nodes passed into LXC 110, the matching user-space driver inside the LXC, and NVIDIA Container Toolkit 1.20.0-1. This change reused all of that and touched only the Immich Compose project and one Immich system setting.

I took no snapshot. I copied the Compose file before editing it; the copy is at [Backups/docker-main-immich-docker-compose-2026-09-05.yml](../../../../Backups/docker-main-immich-docker-compose-2026-09-05.yml) and I removed it from the host once the change was verified.

## Starting State

Immich 3.1.0 was healthy with all four containers at restart count zero. The server container ran on `runc` with no device request and no `extends` block. The stored system configuration already asked for `hevc` output at 1080p with CRF 28 and the `all` transcode policy, so every video already went through ffmpeg on the four LXC vCPUs. The library held 5,367 videos. The GTX 1080 Ti was idle at 0 MiB used, and the bundled ffmpeg in the server image listed `h264_nvenc`, `hevc_nvenc`, and `cuda` support.

## Compose Change

I downloaded `hwaccel.transcoding.yml` from the Immich v3.1.0 release into `/opt/docker/immich-app/`; its SHA-256 is `a50d01758fdbd468270ef7104dce6f282e217ef916238098ac94a70ca8e4c326`. In `docker-compose.yml` I uncommented the `extends` block on `immich-server`, pointed it at the `nvenc` service, and added `runtime: nvidia`. The runtime line is the same nested-LXC requirement Ollama hit: the plain device reservation fails at `bpf_prog_query(BPF_CGROUP_DEVICE)` inside an unprivileged LXC, while the registered NVIDIA runtime passes.

`docker compose config` validated, and the rendered service carried the `nvidia` device reservation with `gpu`, `compute`, and `video` capabilities plus `runtime: nvidia`. I recreated only `immich-server` with `--no-deps`. It was healthy after 46 seconds. `nvidia-smi` inside the container reported the GTX 1080 Ti on driver 580.159.03, and a synthetic `h264_nvenc` encode succeeded.

## Pascal Encoder Limits

Before turning the setting on, I checked what Immich actually passes to ffmpeg in v3.1.0 (`server/src/utils/media.ts`, class `NvencSwDecodeConfig`). It adds `-b_ref_mode middle` only when B-frames are configured and `-temporal-aq 1` only when temporal AQ is enabled. Both are off in the stored configuration. That matters because a test `hevc_nvenc` encode with `-temporal-aq 1` failed on this card:

```text
[hevc_nvenc @ 0x57ead2d379c0] Provided device doesn't support required NVENC features
```

Pascal's HEVC encoder has no B-frame or temporal AQ support. Leave the B-frames and Temporal AQ settings at their defaults in the Immich video transcoding page; turning either on will fail every HEVC transcode on this GPU.

I then ran the exact option set Immich builds from the stored config. Software-decode input with `hwupload_cuda` and `scale_cuda`, and CUDA-decode input with `-hwaccel cuda -hwaccel_output_format cuda`, both encoded a 1080p test file with `hevc_nvenc -tune hq -qmin 0 -rc-lookahead 20 -i_qfactor 0.75 -preset p1 -cq:v 28`. A 10-bit `p010le` HEVC encode also succeeded.

## Immich Setting

The automation vault holds no Immich admin credential, so I could not use the admin UI or the authenticated `PUT /api/system-config` route. Immich keeps that setting in the `system_metadata` row keyed `system-config`, which is the same row the UI writes. I set `ffmpeg.accel` to `nvenc` there with `jsonb_set`, leaving every other key as it was, and restarted `immich-server` so both the API and microservices workers reloaded the configuration. Hardware decoding stays at Immich's default of enabled.

The stored `ffmpeg` object after the change:

```json
{"crf": 28, "accel": "nvenc", "transcode": "all", "targetResolution": "1080", "targetVideoCodec": "hevc", "acceptedVideoCodecs": ["hevc"]}
```

## Verification

- `immich-server` is healthy at restart count zero on runtime `nvidia`, and `/api/server/ping` returns 200. The server still reports version 3.1.0.
- Within the first minute after the restart the microservices worker logged two videos as `Transcoding video ... with NVENC-accelerated encoding and decoding`. No retry, fallback, or ffmpeg error appeared in the same window.
- During a live transcode `nvidia-smi` showed encoder 55 %, decoder 51 %, GPU 3 %, and 329 MiB used by one process from the server container.
- The other three Immich containers were untouched and stayed healthy. All 15 containers on `docker-main` are running; the three without a health result (`cli-proxy-api`, `forgejo`, `portainer_ce`) define no health check.
- The versioned Compose file matches the live file at SHA-256 `f8275fd1f4793f06823c0af7896c89d2dfb566034f5d452965b0696f9960fb22`, and the versioned `hwaccel.transcoding.yml` matches the live one.
- The host pre-edit copy is gone; the redacted copy is in `Backups/`. The file carried no secret, since the Compose file reads the database password from `.env`.

No separate evidence transcript was retained. The values above were captured during the live change.

## Remaining Work

Nothing remains for the requested change. Existing videos were already transcoded on CPU and Immich does not redo them on its own; a **Transcode Videos, All** run from Administration, Jobs would re-encode all 5,367 on the GPU, which is optional and would take hours. Sources with pixel formats NVDEC rejects, such as 4:4:4, fall back to Immich's built-in software decode and need no configuration.
