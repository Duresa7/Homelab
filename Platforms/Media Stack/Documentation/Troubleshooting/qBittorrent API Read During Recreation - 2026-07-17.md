# qBittorrent API Read During Recreation

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Investigated:** 2026-07-17

## Symptom

My first post-recreation verification reached qBittorrent immediately after Docker reported the container running and failed with:

```text
ConnectionResetError: [Errno 104] Connection reset by peer
```

## Readiness Check

I suspected an application-readiness race: the container process was running, but the Web UI socket had not completed initialization. Gluetun was already healthy and Docker had started qBittorrent successfully. No active torrents existed before the controlled restart.

## Corrective Action and Verification

I repeated the read-only verification with an HTTP-ready loop before parsing preferences. It then confirmed provider/qBittorrent port equality, `random_port=False`, `upnp=False`, local-auth bypass, enabled Docker-subnet bypass, Gluetun healthy, qBittorrent running, and qBittorrent attached to Gluetun's exact container namespace. The corrected command exited `0`. No service configuration change was required.
