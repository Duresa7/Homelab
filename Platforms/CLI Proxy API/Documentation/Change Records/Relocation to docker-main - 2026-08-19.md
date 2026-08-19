# Relocation to docker-main

**Created:** 2026-08-19  
**Last updated:** 2026-08-19

## Change

I moved the live CLI Proxy API Compose project from VM 105 `ubuntu-dev` at `192.168.40.179` to LXC 110 `docker-main` at `192.168.40.35`. The new project follows the existing Docker host layout at `/opt/docker/cli-proxy-api` and uses container restart policy `unless-stopped`.

I pinned the deployed image to `eceasy/cli-proxy-api@sha256:3f7a734784f4cc2c86f6268929caff1b0c178fe600fdaa12cefe884dc4cae841`. The running binary reports version `7.2.128`, commit `bd34cec`, matching the version and commit reported by the source deployment. Compose publishes the existing six listeners, and it bind-mounts `config.yaml`, the read-only custom `management.html`, `auths/`, `logs/`, and `plugins/`.

I staged the runtime files while the source was online, stopped the source container, and made a final encrypted host-to-host synchronization before starting the target. The source and target hashes matched for `config.yaml` and `management.html`. A checksum-mode dry run across `auths/` returned zero differences after startup. The target directory contains six credential-state files, while the application reports five loaded provider auth files and five clients.

I edited the existing network path rather than creating parallel objects:

- UniFi firewall policy `6a7a6060dee8c70a32dec069` is now named `Allow NPM to docker-main CLI Proxy API` and permits `192.168.85.2` to reach `192.168.40.35:8317` over TCP. The before-and-after comparison showed that only this policy changed.
- NPM proxy host ID 26 still owns `aiproxy.alphasecunited.com`, the wildcard certificate, Force SSL, HTTP/2, WebSocket support, exploit blocking, and its existing advanced timeouts. Its upstream changed from `192.168.40.179:8317` to `192.168.40.35:8317`.
- UniFi local DNS record `6a7a605fdee8c70a32dec053` did not change because it already resolves the service name to NPM at `192.168.85.2`.

After the production checks passed, I removed the stopped source container and Compose network, securely removed the old project files and migration cache from `ubuntu-dev`, and confirmed that none of the six former service ports remained open there.

## Verification

| Check | Result |
|---|---|
| Target Compose definition | `docker compose config --quiet` passed |
| Target container | Running on `docker-main`; restart policy `unless-stopped` |
| NPM backend reachability | `192.168.40.35:8317` returned HTTP `200` from `docker-network` |
| NPM generated configuration | `nginx -t` passed; proxy host 26 generated `192.168.40.35` and port `8317` |
| HTTPS root | HTTP `200`; certificate verification result `0` |
| HTTPS management page | HTTP `200`; certificate verification result `0` |
| Unauthenticated `/v1/models` | HTTP `401`; certificate verification result `0` |
| Authenticated `/v1/models` | HTTP `200`; response contained 14 model IDs |
| Provider state transfer | Six source files present on the target; checksum comparison returned zero differences |
| Source cleanup | Container, Compose network, project directory, migration cache, and listeners absent on `ubuntu-dev` |

I did not retain a terminal transcript or create an evidence folder for this change. I read each result live during the migration and recorded the resulting state here.

## Open Work

None.
