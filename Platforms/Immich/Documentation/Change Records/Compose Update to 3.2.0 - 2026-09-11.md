# Compose Update to 3.2.0

**Created:** 2026-09-11  
**Last updated:** 2026-09-11

I updated Immich on `docker-main` from 3.1.0 to 3.2.0 using its existing Compose project at `/opt/docker/immich-app`. I checked the [3.2.0 release notes](https://github.com/immich-app/immich/releases/tag/v3.2.0) and release Compose images before applying the update.

Before the pull, all four containers were healthy and `/api/server/version` reported 3.1.0. Root had 43 GiB free and the library filesystem had 556 GiB free. I ran `docker compose pull --quiet`, then `docker compose up -d --wait --wait-timeout 180`. Both commands exited 0. Compose recreated the server and CUDA machine-learning containers and left PostgreSQL and Valkey running. All four passed their health checks.

I retained the existing PostgreSQL and Valkey digest pins. The PostgreSQL digest matches the 3.2.0 release file; that file specifies a newer Valkey 9 digest, which this pull did not adopt. No Compose or environment file changed. The Compose SHA-256 remained `b912cc661052a43be2bf0e667e2405b903f3d38e9aa647ac16e7f60949a97d32`, matching the repository reference.

At 3:36 AM Eastern I verified:

- `/api/server/version` reported 3.2.0 and `/api/server/ping` returned `pong`.
- `https://immich.alphasecunited.com` returned HTTP 200 from docker-main.
- Both application image version labels read `v3.2.0`.
- All four containers were healthy with zero restarts.
- Both application containers retained the `nvidia` runtime; `nvidia-smi --query-gpu=name --format=csv,noheader` inside the machine-learning container returned `NVIDIA GeForce GTX 1080 Ti`.

These checks establish service health and GPU visibility; I did not run a new upload, transcode, or machine-learning job. I summarized the commands and results here without retaining a separate raw transcript. No snapshot or backup was created. The README and living service inventory now record 3.2.0.
