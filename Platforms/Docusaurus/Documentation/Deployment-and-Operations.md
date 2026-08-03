# Docusaurus Deployment & Operations

**Created:** 2026-08-02  
**Last updated:** 2026-08-02

## Current deployment

I serve Docusaurus 3.10.2 from Docker Main at `http://192.168.40.35:3010`. The Compose project is `docusaurus`, its one container is named `docusaurus`, & its health endpoint is `/healthz`.

The Dockerfile has two stages. Node.js 24.14.0 installs the locked npm graph and runs `docusaurus build`; Nginx 1.29.5 receives the generated `build/` directory. The running image contains no Node.js executable or npm dependency tree.

| Setting | Value |
| --- | --- |
| Host | `docker-main`, `192.168.40.35` |
| Remote source | `/opt/docker/docusaurus/Source` |
| Remote Compose file | `/opt/docker/docusaurus/Configuration/docker-compose.yml` |
| Published listener | TCP 3010 to container TCP 8080 |
| Image | `homelab/docusaurus:3.10.2` |
| Restart policy | `unless-stopped` |
| Limits | 0.50 CPU, 128 MiB memory, 100 PIDs |
| Runtime user | `nginx`, UID and GID 101 |
| Filesystem | Read-only root with a temporary `/tmp` filesystem |
| Linux capabilities | All dropped |

The Node and Nginx base images are pinned by multi-architecture digest in [the Dockerfile](../Source/Dockerfile). The final image built on 2026-08-02 is 62,720,008 bytes for `linux/amd64`.

## Edit & deploy

I edit Markdown or MDX under `Source/docs/`. The sidebar follows the directory automatically.

I deploy the versioned files to the matching directories on Docker Main, then run:

```bash
cd /opt/docker/docusaurus
docker compose -f Configuration/docker-compose.yml config --quiet
docker compose -f Configuration/docker-compose.yml build --pull
docker compose -f Configuration/docker-compose.yml up -d
```

I don't run the Docusaurus development server in production. The `npm start` path includes Webpack's development listener, while this deployment exposes only Nginx and static output.

## Verification

```bash
docker inspect docusaurus --format '{{.State.Health.Status}}'
curl -fsS http://127.0.0.1:3010/healthz
curl -fsSL -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3010/docs/intro
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3010/route-that-does-not-exist
docker logs --tail 50 docusaurus
```

The expected values are `healthy`, `ok`, HTTP `200` for the docs route, HTTP `404` for the missing route, & no Nginx `[error]` line. A request without the trailing slash must redirect with `Location: /docs/intro/`; [the 2026-08-02 redirect record](Troubleshooting/Nginx%20Directory%20Redirect%20Used%20Container%20Port%20-%202026-08-02.md) explains why `absolute_redirect off` stays in `nginx.conf`. [The unknown-route record](Troubleshooting/Unknown%20Routes%20Returned%20HTTP%20200%20-%202026-08-02.md) explains the explicit `=404` fallback.

## Backup & recovery

The service has no database or writable application volume. Git holds the source and configuration; rebuilding the image restores the site.

```bash
cd /opt/docker/docusaurus
docker compose -f Configuration/docker-compose.yml down
docker compose -f Configuration/docker-compose.yml build --pull --no-cache
docker compose -f Configuration/docker-compose.yml up -d
```

If a new build fails, I keep the existing container running and diagnose the build output. If a recreated container fails, I can tag the preceding image ID before another build and point the Compose `image` field at that retained tag.

## Dependency status

The 2026-08-02 lockfile audit initially reported one high-severity `serialize-javascript` advisory through the Docusaurus build graph. I pinned `serialize-javascript` 7.0.5 with an npm override, after which `npm audit --omit=dev --audit-level=high` exited `0`.

The lockfile still reports 18 moderate advisories through `webpack-dev-server`, `sockjs`, & `uuid`. Those packages exist in the discarded build stage, not in the Nginx runtime image. I will reassess them when a Docusaurus release updates that dependency chain.
