# Storage Footprint Review and Transcode Policy

**Created:** 2026-09-05  
**Last updated:** 2026-09-05

**Date:** 2026-09-05  
**Status:** Policy applied; one Transcode Videos job in All mode waits for me in the admin UI to reclaim the space

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

## Remaining Work

From Administration, Jobs, run **Transcode Videos, All**. Expected outcome: roughly 260 GB freed under `library/encoded-video`, 137 fresh 1080p HEVC transcodes for the 4K sources, and a `df` on `/data` moving from 83 % toward 69 %. I will confirm the number in this record once the job has finished.
