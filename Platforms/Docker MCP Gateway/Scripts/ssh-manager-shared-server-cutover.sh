#!/bin/sh
# Cutover of the SSH Manager MCP server from gateway-managed per-session containers to
# one persistent Compose service behind mcp-proxy. Written 2026-09-03; run as root on
# docker-blue with the new Dockerfile, Compose file, catalog and servers env already
# staged in /tmp/ssh-cutover/. Everything it does is logged; on a failed gateway start
# it restores the previous Compose file, catalog and image tag and brings the old
# layout back up.
set -eu
cd /opt/docker/mcp-gateway
stage=/tmp/ssh-cutover
rb=/tmp/ssh-cutover/rollback
log() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*"; }

# Kept from the first run so a re-run cannot overwrite the pre-cutover originals with
# already-installed files.
log "backing up live files to $rb"
mkdir -p "$rb"
[ -f "$rb/docker-compose.yml" ] || cp docker-compose.yml "$rb/docker-compose.yml"
[ -f "$rb/ssh-manager.yaml" ] || cp config/catalogs/ssh-manager.yaml "$rb/ssh-manager.yaml"
docker image inspect homelab/mcp-ssh-manager:pre-proxy-20260903 >/dev/null 2>&1 \
  || docker tag homelab/mcp-ssh-manager:latest homelab/mcp-ssh-manager:pre-proxy-20260903

rollback() {
  log "ROLLBACK: restoring previous compose, catalog and image"
  cp "$rb/docker-compose.yml" docker-compose.yml
  cp "$rb/ssh-manager.yaml" config/catalogs/ssh-manager.yaml
  docker tag homelab/mcp-ssh-manager:pre-proxy-20260903 homelab/mcp-ssh-manager:latest
  docker compose up -d --remove-orphans ssh-manager-gateway || true
  docker rm -f mcp-ssh-manager 2>/dev/null || true
  log "ROLLBACK complete"
  exit 1
}

log "installing staged files"
install -m 644 -o root -g root "$stage/Dockerfile.ssh-manager" Dockerfile.ssh-manager
install -m 644 -o root -g root "$stage/ssh-manager-servers.env" ssh-manager-servers.env
install -m 644 -o root -g root "$stage/ssh-manager.yaml" config/catalogs/ssh-manager.yaml
install -m 644 -o root -g root "$stage/docker-compose.yml" docker-compose.yml

if [ ! -f ssh-manager.env ]; then
  log "deriving ssh-manager.env from ssh-manager-secrets.env"
  umask 077
  sed -E 's/^ssh-manager\.private_key_b64=/SSH_PRIVATE_KEY_B64=/; s/^ssh-manager\.([a-z0-9_]+)_sudo_password=/SSH_SERVER_\U\1\E_SUDO_PASSWORD=/' \
    ssh-manager-secrets.env > ssh-manager.env
  chown root:root ssh-manager.env; chmod 600 ssh-manager.env
  umask 022
fi
log "ssh-manager.env keys: $(grep -o '^[A-Z_0-9]*=' ssh-manager.env | tr -d = | tr '\n' ' ')"

log "validating compose model"
docker compose config --quiet || rollback

log "building homelab/mcp-ssh-manager:latest"
if ! docker build --no-cache -f Dockerfile.ssh-manager -t homelab/mcp-ssh-manager:latest . >"$stage/build.log" 2>&1; then
  tail -30 "$stage/build.log"
  rollback
fi
docker run --rm --entrypoint sh homelab/mcp-ssh-manager:latest -c 'set -e; npm ls -g --depth=0 | grep mcp-ssh-manager; pip3 show mcp | grep ^Version; mcp-proxy --help >/dev/null; echo mcp-proxy-ok; node --version' || rollback

log "starting ssh-manager service"
docker compose up -d ssh-manager || rollback
i=0
until [ "$(docker inspect mcp-ssh-manager --format '{{.State.Health.Status}}' 2>/dev/null)" = healthy ]; do
  i=$((i+1))
  if [ $i -gt 30 ]; then
    docker logs mcp-ssh-manager 2>&1 | tail -30
    rollback
  fi
  sleep 2
done
log "ssh-manager healthy after $((i*2))s"

log "recreating ssh-manager-gateway"
docker compose up -d --remove-orphans ssh-manager-gateway || rollback
i=0
until [ "$(docker inspect ssh-manager-mcp-gateway --format '{{.State.Health.Status}}' 2>/dev/null)" = healthy ]; do
  i=$((i+1))
  if [ $i -gt 30 ]; then
    docker logs ssh-manager-mcp-gateway 2>&1 | tail -30
    rollback
  fi
  sleep 2
done
log "gateway healthy after $((i*2))s"
sleep 3
if docker logs ssh-manager-mcp-gateway 2>&1 | grep -q 'ssh-manager: (37 tools)'; then
  log "gateway listed 37 SSH Manager tools from the remote server"
else
  docker logs ssh-manager-mcp-gateway 2>&1 | tail -30
  rollback
fi

log "post-state"
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}' | grep -E 'ssh|mcp'
docker ps -a --filter label=docker-mcp-name=ssh-manager -q | wc -l | sed 's/^/managed containers: /'
cat /sys/fs/cgroup/system.slice/docker-$(docker inspect ssh-manager-mcp-gateway --format '{{.Id}}').scope/pids.current | sed 's/^/gateway pids: /'
docker logs ssh-manager-mcp-gateway 2>&1 | grep -E 'Connecting to remote|tools listed|Start streaming' | tail -5
log "CUTOVER OK"
