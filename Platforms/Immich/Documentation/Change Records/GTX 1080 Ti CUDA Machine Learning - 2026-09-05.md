# GTX 1080 Ti CUDA Machine Learning

**Created:** 2026-09-05  
**Last updated:** 2026-09-05

**Date:** 2026-09-05  
**Status:** Complete on the server side; two re-index jobs wait for me in the admin UI

## Change

Following the [NVENC transcoding change](GTX%201080%20Ti%20NVENC%20Transcoding%20-%202026-09-05.md) earlier the same day, I moved Immich's machine learning onto the GTX 1080 Ti and switched the three models to larger ones the GPU makes practical. The library is small, 529 images and 5,367 videos, so re-indexing on the GPU is a short job.

I took no snapshot and no new backup copy. The pre-edit Compose file is byte-for-byte the version I committed to `Configuration/` in the NVENC record, SHA-256 `f8275fd1f4793f06823c0af7896c89d2dfb566034f5d452965b0696f9960fb22`, so a second copy in `Backups/` would have duplicated a tracked file.

## Starting State

The machine-learning container ran `immich-machine-learning:release` on `runc` with `DEVICE=cpu`, and its log showed `CPUExecutionProvider` only. All four ML features were enabled at Immich's defaults: CLIP `ViT-B-32__openai`, facial recognition `buffalo_l`, OCR `PP-OCRv5_mobile`, and duplicate detection. My stored overrides were a face minimum score of 0.65 and a duplicate distance of 0.04. The model cache volume held 1.1 GB, including an `antelopev2` folder from earlier use. The root filesystem had 52 GiB free.

## Compose Change

I downloaded `hwaccel.ml.yml` from the Immich v3.1.0 release into `/opt/docker/immich-app/`; its SHA-256 is `05828be46118e9f79c019c0752489a47fb3381d67ed102212a4f9d9f2575bd3d`. On `immich-machine-learning` I changed the image tag to `${IMMICH_VERSION:-release}-cuda`, uncommented the `extends` block pointing at the `cuda` service, and added `runtime: nvidia` for the same nested-LXC reason as the server. `docker compose config` validated with the `nvidia` device reservation and the runtime on the service.

The CUDA image is 4.85 GB on disk against 1.29 GB for the CPU image; the pull left 47 GiB free. I recreated only the machine-learning container. It became healthy, at restart count zero, on runtime `nvidia`.

## GPU Verification

A CLIP text request from the server container to `http://immich-machine-learning:3003/predict` returned an embedding. The ML log for that request read `Setting execution providers to ['CUDAExecutionProvider', 'CPUExecutionProvider']`, and `nvidia-smi` showed the ML process holding 420 MiB with the small default model loaded.

The log also carries repeated `pthread_setaffinity_np failed` lines from onnxruntime. That is the known LXC CPU-affinity complaint; inference completes and the result is correct, so I left it alone rather than pin thread counts.

## Model Selection

I checked each name against the v3.1.0 model list in `machine-learning/immich_ml/models/constants.py` and confirmed the CLIP and face repositories exist under the `immich-app` organisation before writing them:

| Feature | Before | After | Why |
| --- | --- | --- | --- |
| Smart search (CLIP) | `ViT-B-32__openai`, 512 dimensions | `ViT-SO400M-16-SigLIP2-384__webli`, 1152 dimensions | Highest recall in Immich's English table at 85.99 %, Pareto optimal, and multilingual. About 3.9 GB in memory, which the card and the 16 GiB LXC hold. |
| Facial recognition | `buffalo_l` | `antelopev2`, reverted to `buffalo_l` the same evening | I first chose the larger InsightFace package because it was already in the cache. Immich's facial recognition documentation says the default is typically considered the best and offers the alternatives for constrained systems, so I put `buffalo_l` back before any face job ran on the other model. |
| OCR | `PP-OCRv5_mobile` | `PP-OCRv5_server` | The full-size detector and recogniser. |

The vault has no Immich admin credential, so as in the NVENC change I wrote the values into the `system-config` row in `system_metadata` with `jsonb_set`, then restarted `immich-server`. On start the microservices worker logged:

```text
Dimension size of model ViT-SO400M-16-SigLIP2-384__webli is 1152, but database expects 512.
Updating database CLIP dimension size to 1152.
Successfully updated database CLIP dimension size from 512 to 1152.
```

That code path (`SmartInfoService.init` in v3.1.0) resizes the vector column and discards the old embeddings. It deliberately does not queue a re-index; the source carries a comment saying user confirmation should come first. The same is true for an OCR model change, which Immich never re-queues on its own.

I pre-loaded the new CLIP text model through the same `/predict` path so the download happened now rather than on the first search. The ML log showed the download and load, and GPU memory rose to 3,265 MiB with it resident. Face and OCR warm-up requests followed; their result is in the verification list.

## Verification

- Machine-learning container healthy on `release-cuda`, runtime `nvidia`, restart count zero. Server healthy after its restart and `/api/server/ping` returns 200.
- CUDA execution provider selected for every model load in the ML log; no CPU-only provider line after the recreate.
- Stored `machineLearning` object after the model change: `{"ocr": {"modelName": "PP-OCRv5_server"}, "clip": {"modelName": "ViT-SO400M-16-SigLIP2-384__webli"}, "facialRecognition": {"minScore": 0.65, "modelName": "antelopev2"}, "duplicateDetection": {"maxDistance": 0.04}}`. After the face revert the `facialRecognition` object holds only `minScore`, so the model falls back to the default `buffalo_l`; the server was restarted again and came back healthy.
- The versioned Compose file matches the live file at SHA-256 `b912cc661052a43be2bf0e667e2405b903f3d38e9aa647ac16e7f60949a97d32`; the versioned `hwaccel.ml.yml` matches the live one.
- Face and OCR warm-up requests against a synthetic image both returned HTTP 200 with empty detections, and the ML log showed `antelopev2` and both `PP-OCRv5_server` models downloading and loading on the CUDA provider.
- With the new CLIP text model, `antelopev2`, and both OCR models resident at once, the GPU held 4,257 MiB, the ML container used 4.5 GiB of memory, and the LXC still had 11.6 GiB available. The model cache volume grew from 1.1 GB to 5.5 GB.
- Idle ML memory returns to baseline five minutes after the last request, since the container unloads models after 300 seconds by default.
- I removed the pull and warm-up logs from `/root` and the synthetic test image from the server container. The superseded CPU image `immich-machine-learning:release`, 1.29 GB, is still on disk and can go in the next image prune.

No separate evidence transcript was retained. The values above were captured during the live change.

## Remaining Work

Smart search is empty until the new embeddings exist, and text results stay on the old OCR model until its job runs. From **Administration, Jobs** I still need to run, in this order:

1. **Smart Search: All**. Rebuilds the 1152-dimension CLIP index for every asset.
2. **OCR: All**. Re-reads text with the server model.

Face detection stays on `buffalo_l`, the model every existing face embedding already came from, so no face job is needed.

Duplicate detection re-runs from the new CLIP embeddings as they land. Until step 1 completes, a search returns nothing, which is expected and not a fault.
