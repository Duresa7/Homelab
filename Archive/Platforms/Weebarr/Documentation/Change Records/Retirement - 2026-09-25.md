# Retirement

**Created:** 2026-09-25  
**Last updated:** 2026-09-25

**Status:** Retired. Weebarr is absent from `media-01` and from every layer that fronted it.

I deployed Weebarr 0.2.0 on `media-01` (CT 842, `192.168.40.42`) on 2026-09-21; the [deployment record](Deployment%20-%202026-09-21.md) has the build and its checks. It was removed from the host between 2026-09-21 and 2026-09-24; the removal date and commands are not recorded. This record holds the state I verified on 2026-09-24.

## Host

| Check on `media-01`, 2026-09-24 | Result |
| --- | --- |
| `docker ps -a \| grep -i weebarr` | Empty |
| `docker images \| grep -i weebarr` | Empty |
| `docker compose ls` | `media-stack` runs 8 containers from `/opt/media-stack/compose.yml`; none is `weebarr` |
| `grep -ril weebarr /opt /srv /home` (as `dkadi`, no sudo) | Empty |
| Listener on TCP 18080 | None |

The `/opt/media-stack/config/weebarr` settings directory was mode 0700. The `dkadi` search could not prove it is gone, only that nothing it could read names Weebarr.

## Remnants

| Remnant from the deployment | Live state | Checked |
| --- | --- | --- |
| NPM proxy host 33, `weebarr.alphasecunited.com` to `192.168.40.42:18080` | Soft-deleted (`is_deleted=1`); no conf file in `/data/nginx/proxy_host/`; 24 live hosts | 2026-09-24 |
| UniFi local DNS record `weebarr.alphasecunited.com` | Absent; 30 static records, none for Weebarr | 2026-09-24 |
| TCP 18080 in `Allow NPM to media-01 web UIs` | Absent; the policy allows TCP 5055, 7878, 8080, 8096, 8989 and 9696 from `192.168.85.2` to `192.168.40.42` | 2026-09-24 |
| Prometheus blackbox probe of `https://weebarr.alphasecunited.com/` | Absent; 57 targets, 57 up, no target references Weebarr | 2026-09-24 |

No remnant is still present on those four layers.

## Not checked

- The `weebarr` service in Dockhand's imported media-stack definition at `/opt/docker/dockhand/stacks/imported/media_01/media-stack/compose.yaml` on `docker-main`.
- The Weebarr admin item for `media-01` in my credential store.

## Records

The living records carry no Weebarr row: [Media Stack](../../../../../Platforms/Media%20Stack/README.md), its [configuration reference](../../../../../Platforms/Media%20Stack/Configuration/README.md) and the [services inventory](../../../../../Operations/Inventory/Galaxy/Services.md). The [platform README](../../README.md) and the [Compose fragment](../../Configuration/compose.fragment.yml) stay in the archive as the record of what ran.
