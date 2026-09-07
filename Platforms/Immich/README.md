# Immich

**Created:** 2026-07-22  
**Last updated:** 2026-09-06

I run Immich 3.1.0 on `docker-main` with the application on TCP 2283 and its library under `/data/immich`. The internal browser path is `https://immich.alphasecunited.com` through Nginx Proxy Manager; direct fallback remains `http://192.168.40.35:2283`. Video transcoding runs on Grey's GTX 1080 Ti through NVENC since 2026-09-05 under the `optimal` policy with H.264 and HEVC accepted, so only sources above 1080p or in an unusual format get a transcoded copy; the server container uses the `nvidia` runtime and the `nvenc` service from Immich's `hwaccel.transcoding.yml`, and the transcoding setting is NVENC with hardware decoding on. The card is Pascal, so B-frames and Temporal AQ stay off in the video transcoding settings. Machine learning runs on the same card through the `release-cuda` image with the `cuda` service from `hwaccel.ml.yml`, using CLIP `ViT-SO400M-16-SigLIP2-384__webli`, the default face model `buffalo_l` at detection score 0.65, recognition distance 0.55, and minimum faces 5, and OCR `PP-OCRv5_server`.

**Owner:** Homelab photo and video library

NPM disables request buffering, permits request bodies up to 50,000 MiB, & uses 600-second proxy read, proxy send, and response-send timeouts. UniFi permits only NPM at `192.168.85.2` to the cross-zone TCP 2283 path. The database, Redis, machine-learning service, & storage paths aren't published through NPM.

The server and machine-learning images track Immich's `release` tag. Valkey uses the release-supported `docker.io/valkey/valkey:9` image, and PostgreSQL stays on Immich's exact PostgreSQL 14, VectorChord 0.4.3, and pgvectors 0.2.0 build. I refresh those two dependency pins from the Compose file attached to the current Immich release instead of changing either stateful service to an unconstrained `latest` tag.

## Layout

- `Configuration/` holds the live `docker-compose.yml` and the release `hwaccel.transcoding.yml` and `hwaccel.ml.yml` from `/opt/docker/immich-app`. The `.env` file with the database password stays on `docker-main` only.
- `Documentation/` holds the retained storage migration and the dated change records.

## Records

- [Internal HTTPS onboarding](../Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md)
- [Storage migration from WD Red Plus to Toshiba](Documentation/Immich-Storage-Migration-WD-to-Toshiba-2026-05-28.md)
- [GTX 1080 Ti NVENC transcoding](Documentation/Change%20Records/GTX%201080%20Ti%20NVENC%20Transcoding%20-%202026-09-05.md)
- [GTX 1080 Ti CUDA machine learning](Documentation/Change%20Records/GTX%201080%20Ti%20CUDA%20Machine%20Learning%20-%202026-09-05.md)
- [Facial recognition model research](Documentation/Facial%20Recognition%20Model%20Research%20-%202026-09-05.md)
- [Facial recognition threshold tuning](Documentation/Change%20Records/Facial%20Recognition%20Threshold%20Tuning%20-%202026-09-05.md)
- [Storage footprint review and transcode policy](Documentation/Change%20Records/Storage%20Footprint%20Review%20and%20Transcode%20Policy%20-%202026-09-05.md)
- [Compose configuration](Configuration/docker-compose.yml), [hardware transcoding overlay](Configuration/hwaccel.transcoding.yml), and [machine learning overlay](Configuration/hwaccel.ml.yml)
- [2026-09-03 container image updates](../../Operations/Maintenance/Container%20Image%20Updates%20-%202026-09-03.md)
