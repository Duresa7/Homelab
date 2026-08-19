# CLI Proxy API Operations Runbook

**Created:** 2026-08-10  
**Last updated:** 2026-08-19

## Routine Check

I run these commands on `docker-main` from the live project:

```sh
cd /opt/docker/cli-proxy-api
docker compose ps
docker inspect -f 'status={{.State.Status}} restart={{.HostConfig.RestartPolicy.Name}}' cli-proxy-api
curl -sS -o /dev/null -w 'root=%{http_code}\n' http://127.0.0.1:8317/
curl -sS -o /dev/null -w 'management=%{http_code}\n' http://127.0.0.1:8317/management.html
curl -sS -o /dev/null -w 'unauthenticated_models=%{http_code}\n' http://127.0.0.1:8317/v1/models
curl -sS -o /dev/null -w 'https=%{http_code}\n' https://aiproxy.alphasecunited.com/
```

The expected baseline is a running container with restart policy `unless-stopped`, HTTP `200` for the root and management page, HTTP `401` for the unauthenticated model request, and HTTP `200` through the internal HTTPS name.

## Start, Stop, and Restart

```sh
cd /opt/docker/cli-proxy-api
docker compose start
docker compose stop
docker compose restart
docker compose ps
```

After a restart I test the local listener, the internal HTTPS route, and one authenticated API request. I also confirm that the provider authentication files still exist before expecting models.

## Provider Authentication

The `auths/` directory holds six credential-state files. The service loads five provider auth files and five clients at startup, which the container log reports as `5 clients (5 auth files ...)`. Adding a provider means repeating the login flow below.

I use `https://aiproxy.alphasecunited.com/management.html`, supply the existing management credential without placing it in a command or this repository, and complete the chosen provider's login flow. I then verify that a new file exists under `auths/` without reading its contents and that an authenticated `/v1/models` request returns the expected models.

## Logs

```sh
cd /opt/docker/cli-proxy-api
docker compose logs --no-color --tail=200 cli-proxy-api
```

I do not copy bearer tokens, API keys, management credentials, OAuth callback values, or provider files into evidence or documentation.

## Update

The Compose file pins the complete image digest, so an ordinary recreate keeps the same image. To update, I record the current digest, replace it with the selected tested digest in `docker-compose.yml`, and run:

```sh
cd /opt/docker/cli-proxy-api
docker compose pull
docker compose up -d
docker compose ps
```

I repeat the routine check and authenticated model check before treating an update as complete. If the new image fails, I restore the prior digest in `docker-compose.yml`, run `docker compose up -d`, and repeat the checks.

## Rollback

If NPM or UniFi routing fails, direct access remains at `http://192.168.40.35:8317`. I check NPM proxy host ID 26 and UniFi policy `6a7a6060dee8c70a32dec069` against the current upstream before changing either one. The UniFi DNS record `6a7a605fdee8c70a32dec053` continues to point at NPM and does not change when the backend host moves.
