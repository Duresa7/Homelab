# ubuntu-dev Image Prune and npm Cache Clean

**Created:** 2026-11-09  
**Last updated:** 2026-11-09

On 2026-11-09, after the [storage expansion](../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/ubuntu-dev%20Storage%20Expansion%20-%202026-11-09.md), I freed space on VM 105 `ubuntu-dev`. I stopped no container or process and created no snapshot or backup.

## Before

`/` had 193,835,847,680 bytes used and 136,943,206,400 bytes available (59%). Docker held 20 images (11.63 GB, 10.26 GB reclaimable), two exited containers and 15.25 GB of build cache. No `docker build` or `npm install` was running.

## Work

- `docker image prune -a -f` removed every image no container references and reported 6.391 GB reclaimed. Two images remain, both used by the exited containers `app-portal-docs-review` and `app-portal-upgrade-old`, which I kept.
- `npm cache clean --force` emptied the npm content cache under `~/.npm/_cacache`.

I left the Docker build cache (15.25 GB, 14.8 GB reclaimable) and `~/.npm/_npx` (2.6 GB) in place. Packages started through `npx`, including running tool servers, load from `_npx`.

## After

`df -h /` reports 323G capacity, 171G used, 138G available and 56% usage. `docker system df` shows two images totalling 447.2 MB.
