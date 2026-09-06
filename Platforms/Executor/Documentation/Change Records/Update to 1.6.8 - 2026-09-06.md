# Update to 1.6.8

**Created:** 2026-09-06  
**Last updated:** 2026-09-06

**Date:** 2026-09-06  
**Status:** Complete  
**Affected systems:** `docker-blue`

## Outcome

I updated Executor on `docker-blue` from 1.6.7 to 1.6.8, the release the official container package published on 2026-09-05. The container is healthy, the HTTPS endpoint still rejects unauthenticated requests, and every connected integration answered a live call after the restart.

## Procedure

I followed the runbook's Updating section. The live Compose file at `/opt/docker/executor/docker-compose.yml` already matched the versioned reference and stayed on the `latest` tag, so no file changed. From that directory I ran `docker compose pull` and `docker compose up -d`, which recreated the container. MCP clients lost their connection for the few seconds the container took to restart.

## Verification

| Check | Result |
|---|---|
| Image label version | 1.6.8 |
| Manifest digest | `sha256:200315d519a8c19685de05e88aa9a3cf1e1cb9869a2b0aecf604f6ebf47c6ea1` |
| Container start | 2026-09-06 03:52 local, `healthy` |
| Direct health endpoint | `{"status":"ok"}` |
| HTTPS endpoint, unauthenticated | `401` |
| Claude profiles | Default and Claude Alt both reconnected |
| SSH Manager | `ssh_execute` against `docker_blue` and `grey_server` returned normally |
| UniFi | `unifi_list_networks` through `unifi_execute` returned `ok` |
| Wazuh | Search resolves the agent tools and the `localWazuh` connection reports healthy |
| Connections | All six user connections report healthy |

## Cleanup

The previous 1.6.7 image, digest `sha256:c8dd83a5dba8ac992dfe1ded4aa65ae4e7f52ec31fddbe2af5b49ffebe5bbfa7`, is still present on `docker-blue` as an untagged image. It costs disk only and is the rollback path if 1.6.8 misbehaves; I will prune it on the next image cleanup pass.
