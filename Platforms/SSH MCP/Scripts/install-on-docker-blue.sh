#!/bin/sh
# Install or refresh ssh-mcp under /opt/docker/ssh-mcp on docker-blue. Run as root.
#
#   install-on-docker-blue.sh <stage dir>
#
# The stage dir holds Dockerfile, docker-compose.yml, config.toml and pin-host-keys.py from
# this platform folder. On the first run it also holds `bearer`, a mode-0600 file with the
# bearer token from my password manager, which is moved into ssh-mcp.env and shredded.
#
# The first run took the SSH key, the sudo passwords and known_hosts from the SSH Manager
# service it replaced, so no secret left docker-blue. Later runs keep the existing key,
# env file and known_hosts and only rewrite the config.
set -eu

stage=${1:?stage dir}
dest=/opt/docker/ssh-mcp
umask 077

install -d -m 0755 "$dest"
install -m 0644 "$stage/Dockerfile" "$stage/docker-compose.yml" "$dest/"
install -m 0644 "$stage/config.toml" "$dest/config.unpinned.toml"
install -d -m 0700 -o 65532 -g 65532 "$dest/config" "$dest/keys" "$dest/data"

if [ ! -s "$dest/known_hosts" ]; then
  install -m 0644 /var/lib/docker/volumes/ssh-manager-state/_data/ssh/known_hosts "$dest/known_hosts"
fi

if [ ! -s "$dest/keys/id_ed25519" ]; then
  docker inspect mcp-ssh-manager --format '{{range .Config.Env}}{{println .}}{{end}}' \
    | sed -n 's/^SSH_PRIVATE_KEY_B64=//p' | base64 -d > "$dest/keys/id_ed25519"
  chown 65532:65532 "$dest/keys/id_ed25519"
  chmod 0400 "$dest/keys/id_ed25519"
fi

if [ ! -s "$dest/ssh-mcp.env" ]; then
  {
    printf 'SSH_MCP_BEARER_TOKEN='
    cat "$stage/bearer"
    docker inspect mcp-ssh-manager --format '{{range .Config.Env}}{{println .}}{{end}}' \
      | sed -n 's/^SSH_SERVER_\(.*\)_SUDO_PASSWORD=/SSH_MCP_\1_SUDO_PASSWORD=/p'
  } > "$dest/ssh-mcp.env"
  chmod 0600 "$dest/ssh-mcp.env"
fi
[ -f "$stage/bearer" ] && shred -u "$stage/bearer"

python3 "$stage/pin-host-keys.py" "$dest/config.unpinned.toml" "$dest/known_hosts" > "$dest/config/config.toml.new"
chown 65532:65532 "$dest/config/config.toml.new"
chmod 0600 "$dest/config/config.toml.new"
mv "$dest/config/config.toml.new" "$dest/config/config.toml"
chown 65532:65532 "$dest/data"

echo "profiles: $(grep -c '^\[\[profiles\]\]' "$dest/config/config.toml")"
echo "pins: $(grep -c '^trustedHostKey = "SHA256:' "$dest/config/config.toml")"
echo "sudo passwords: $(grep -c '_SUDO_PASSWORD=' "$dest/ssh-mcp.env")"
echo "key bytes: $(wc -c < "$dest/keys/id_ed25519")"
