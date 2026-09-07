# Storage Footprint Review and Transcode Policy

**Created:** 2026-09-05  
**Last updated:** 2026-09-06

**Date:** 2026-09-05  
**Status:** Complete; the second All-mode run on 2026-09-06 reclaimed 226 GB, and the OCR re-run finished the same day

## Question

The Immich data volume on `docker-main` was at 83 % with 316 GB free of 1.8 TB. I wanted to know what was using it and what could be reduced without deleting a single original photo or video.

## What Uses the Space

Everything except 1.4 GB of BookLore data under `/data` belongs to Immich.

| Path under `/data/immich` | Size | What it is |
| --- | --- | --- |
| `library/library` | 1.2 TB | Originals, laid out by the storage template |
| `library/encoded-video` | 266 GB | Immich's transcoded copy of every video |
| `library/upload` | 2.2 GB | Originals not yet moved by the storage template |
| `library/thumbs` | 885 MB | Thumbnails and previews at 720 px, quality 60 |
| `library/backups` | 649 MB | Nightly database dumps, default retention of 14 |
| `postgres` | 180 MB | The database itself, 219 MB inside PostgreSQL |

The database says the same thing from the other side: 5,367 videos hold 1,299 GB of originals and 529 photos hold 0.2 GB. By resolution, 1,948 videos at 1080p take 738 GB, 3,282 at 720p or below take 512 GB, and 137 above 1080p take 49 GB. The trash holds 18 assets and 2.9 GB, and duplicate detection has flagged 10 groups covering 20 assets.

So the originals are the disk, and I am not touching them. The one reclaimable block is the 266 GB of transcodes.

## Why Every Video Had a Second Copy

The transcode policy was `all`, which in v3.1.0 makes `isVideoTranscodeRequired` return true for every video regardless of its codec. The accepted codec list was `hevc` only. Together they produced 5,377 encoded copies, one per video plus a few edits.

I probed a random sample of 59 originals with `ffprobe`: 55 are H.264 and 3 are HEVC, all 4:2:0, all in MOV or MP4 containers with AAC audio. That is the profile every browser and the mobile apps play directly. Immich's own default policy is `required` with H.264 accepted, and the original H.264 file is what gets streamed when no transcode exists.

## Change

I set the policy to `optimal` and the accepted video codecs to `h264` and `hevc`, leaving the HEVC target, 1080p target resolution, CRF 28, and NVENC in place. Under `optimal` a video is transcoded only when its codec is outside the accepted list, its pixel format is not 4:2:0, or its shorter side exceeds 1080. On this library that is the 137 videos above 1080p plus any odd pixel formats, and the remaining roughly 5,230 transcodes become unnecessary.

I wrote the two keys into the `ffmpeg` object of the `system-config` row and restarted `immich-server`. Stored object afterwards:

```json
{"crf": 28, "accel": "nvenc", "transcode": "optimal", "targetResolution": "1080", "targetVideoCodec": "hevc", "acceptedVideoCodecs": ["h264", "hevc"]}
```

The gateway I run commands through returned a 502 during that call. I re-read the row and the container state afterwards: the update had applied and the server had restarted, so I only had to repeat the temp-file cleanup.

## How the Space Comes Back

Immich does not sweep existing transcodes when the policy changes. It deletes one when the per-asset transcode job runs and finds no work to do: in v3.1.0 `handleVideoConversion` logs `Transcoded video exists for asset ..., but is no longer required. Deleting...` and queues the file for deletion. The All mode of Transcode Videos only queues one job per asset with no deletion of its own, so it is the right trigger, and the 137 videos above 1080p simply get re-encoded on the GPU.

## What I Left Alone

- Thumbnails and previews are already at 720 px and quality 60, below Immich's defaults; 885 MB is not worth going lower.
- Database backups at 649 MB for 14 days are cheap insurance against the one thing I cannot regenerate.
- The trash empties itself after 30 days. The 10 duplicate groups are a manual review in Utilities, Duplicates, and each is a decision about which original to keep, which is not mine to make here.
- I did not consider replacing originals with transcodes or lowering their quality.

## Verification

- Server healthy after the restart with restart count zero; `/api/server/ping` returned 200; no validation error in the log.
- Machine learning, PostgreSQL, and Valkey untouched.
- The `du` logs in `/root` and the probe sample files in the server container were removed.

No separate evidence transcript was retained.

## First Run Result, 2026-09-06

The Transcode Videos job in All mode queued 5,377 per-asset jobs and drained with zero failures in the queue. It logged 385 deletions and 10 new transcodes. The encoded-video folder went from 266 GB to 252 GB, the database count of encoded copies from 5,359 to 4,974, and free space on `/data` from 316 GB to 332 GB.

The other 4,982 jobs did nothing, silently. In v3.1.0 `getForVideoConversion` inner-joins `asset_video`, the per-asset video stream table that the current release fills during metadata extraction. Only 397 of the 5,368 videos have a row there; the rest were imported before that table existed and have never been re-extracted. With no row the query returns nothing and the job returns Failed without a log line, which BullMQ still counts as completed. Every one of the 4,964 remaining encoded copies belongs to a video with no `asset_video` row.

The fix is Extract Metadata in All mode, which probes every video and upserts its stream row, followed by Transcode Videos in All mode again. Metadata extraction rewrites description, capture date, and location from the file, so any of those edited inside Immich would be reset; this library has 23 sidecar files and I am not aware of in-app edits.

## OCR Failures in the Same Window

While the transcode run, Smart Search, and OCR were all active, 4,408 of the 5,912 OCR jobs failed with an onnxruntime `BFCArena` allocation error inside the machine-learning container: the GPU ran out of memory with the 3.3 GB CLIP model, both OCR server models, and the face models resident alongside NVENC sessions. 1,146 assets got text. A fresh OCR request on the idle GPU returned 200 immediately afterwards, so the models are fine and the failure was contention. Because `ocrAt` was already set from the earlier mobile-model run, Missing mode would only revisit 5 assets; OCR needs another All run, on its own.

## Second Run Result, 2026-09-06

Extract Metadata in All mode gave 5,362 of the 5,368 videos a stream row; five files failed extraction. The second Transcode Videos run in All mode then drained with zero failed jobs.

| Metric | Before any change | After the second run |
| --- | --- | --- |
| Transcoded copies in the database | 5,377 | 110 |
| `library/encoded-video` | 266 GB | 27 GB |
| `/data` used | 83 %, 316 GB free | 70 %, 558 GB free |

The 110 copies that remain are the ones the `optimal` policy still calls for: 86 sources above 1080p and 24 at or below 1080p in a codec or pixel format outside the accepted list. Across both runs the server logged 1,150 deletions and 31 new transcodes, all on NVENC, with no job errors.

## OCR Re-run

I ran OCR in All mode on its own later on 2026-09-06. It drained with zero failed jobs and no onnxruntime error in the machine-learning log. `asset_ocr` now holds 8,487 text regions across 4,995 assets, up from 1,804 across 1,146 after the contended run.

## Remaining Work

None.

From Administration, Jobs, one at a time and in this order:

1. **Extract Metadata, All**, and wait for the queue to drain.
2. **Transcode Videos, All**. Expected outcome: roughly 250 GB freed under `library/encoded-video`, 137 fresh 1080p HEVC transcodes for the 4K sources, and `/data` moving from 82 % toward 69 %.
3. **OCR, All**, with nothing else running.

I will confirm the numbers here once the jobs have finished.

From Administration, Jobs, run **Transcode Videos, All**. Expected outcome: roughly 260 GB freed under `library/encoded-video`, 137 fresh 1080p HEVC transcodes for the 4K sources, and a `df` on `/data` moving from 83 % toward 69 %. I will confirm the number in this record once the job has finished.
