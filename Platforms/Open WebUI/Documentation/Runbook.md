# Open WebUI Operations Runbook

**Created:** 2026-09-04  
**Last updated:** 2026-09-04

## Routine Check

I run these commands on `docker-main`:

```sh
cd /opt/docker/ollama
docker compose ps open-webui ollama
curl -fsS http://192.168.40.35:3002/health
docker exec open-webui curl -fsS http://ollama:11434/api/tags
docker inspect -f 'health={{.State.Health.Status}} restarts={{.RestartCount}}' open-webui
```

The expected health response is `{"status":true}`. The model response must contain only `qwen3.5:2b`, which proves the frontend container can reach the current Ollama inventory without exposing an additional API listener.

## Initial Administrator

I open `http://192.168.40.35:3002` from an approved internal client and register the first account. Open WebUI makes that account the administrator and automatically closes initial signup. I then sign out and back in before treating the account path as verified.

The intended HTTPS name is `openwebui.alphasecunited.com`. Its local DNS record and firewall path are staged, but I do not use the name until NPM has a saved proxy host forwarding HTTP to `192.168.40.35:3002`, Force SSL and HTTP/2 are enabled, and the wildcard certificate validates.

## Models

Open WebUI reads the model inventory from Ollama. I can pull, select, and remove Ollama models from the administrator model controls, but I still check the 11 GiB GPU and 16 GiB LXC memory limits before adding a model. The Ollama CLI remains the recovery path:

```sh
docker exec ollama ollama list
docker exec ollama ollama pull <YOUR_MODEL>
docker exec ollama ollama rm <YOUR_MODEL>
```

## Logs and Restart

```sh
cd /opt/docker/ollama
docker compose logs --no-color --tail=200 open-webui
docker compose restart open-webui
docker compose ps open-webui ollama
```

Restarting Open WebUI does not restart Ollama. I repeat the health and model-discovery checks after any restart.

## Update

This deployment intentionally tracks Open WebUI's rolling `main` tag with `pull_policy: always`. Open WebUI documents `main` and `latest` as identical pointers to the newest main-branch build. Before an update, I record the current container image ID and registry digest, then run:

```sh
cd /opt/docker/ollama
docker compose config --quiet
docker compose pull open-webui
docker compose up -d --no-deps open-webui
```

I wait for the built-in health check, verify the login page, confirm `qwen3.5:2b` is visible through the container network, and confirm Ollama kept the same container ID and restart count.

Because `main` is mutable, recreating the service can install a different build without a Compose-file change. I record the new digest and `/api/version` response after every update.

## Recovery

If Open WebUI is unhealthy, I inspect its logs and verify `curl -fsS http://ollama:11434/api/tags` from inside the container. A successful direct Ollama API check with a failed container-network check points to Compose networking or `OLLAMA_BASE_URL`.

To remove only the frontend while preserving its data:

```sh
cd /opt/docker/ollama
docker compose stop open-webui
docker compose rm open-webui
```

The named volume remains. Removing `ollama_open-webui-data` deletes accounts, chats, and settings and is a separate destructive action.
