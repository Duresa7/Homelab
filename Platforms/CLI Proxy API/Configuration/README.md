# CLI Proxy API Configuration

**Created:** 2026-08-10  
**Last updated:** 2026-08-19

The live Compose project is `/opt/docker/cli-proxy-api` on `docker-main`. This folder contains only safe, reader-editable references.

## Files

- `docker-compose.yml` mirrors the deployed service definition, including its pinned image digest and read-only management-page mount.
- `npm-advanced.conf` mirrors the Advanced configuration on NPM proxy host ID 26.

I do not version the live `config.yaml` or anything under `auths/` because those paths contain API, management, or provider credentials.
