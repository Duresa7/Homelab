# Immich

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

I run Immich on `docker-main` with the application on TCP 2283 and its library under `/data/immich`. The internal browser path is `https://immich.<YOUR_BASE_DOMAIN>` through Nginx Proxy Manager; direct fallback remains `http://192.168.40.35:2283`.

**Owner:** Homelab photo and video library

NPM disables request buffering, permits request bodies up to 50,000 MiB, & uses 600-second proxy read, proxy send, and response-send timeouts. UniFi permits only NPM at `192.168.85.2` to the cross-zone TCP 2283 path. The database, Redis, machine-learning service, & storage paths aren't published through NPM.

## Layout

- `Documentation/` holds the retained storage migration and future operating records.
- The active Docker Compose project and credentials remain on `docker-main`; this public workspace doesn't duplicate credential-bearing runtime configuration.

## Records

- [Internal HTTPS onboarding](../Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md)
- [Storage migration from WD Red Plus to Toshiba](Documentation/Immich-Storage-Migration-WD-to-Toshiba-2026-05-28.md)
