#!/bin/sh
# Install Docker Engine and the Compose plugin on e2b-01 from Docker's own apt
# repository, and give ai-agent the docker group for Compose work. Run as root.
set -eu
export DEBIAN_FRONTEND=noninteractive
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
. /etc/os-release
printf 'Types: deb\nURIs: https://download.docker.com/linux/ubuntu\nSuites: %s\nComponents: stable\nSigned-By: /etc/apt/keyrings/docker.asc\n' "$VERSION_CODENAME" \
  > /etc/apt/sources.list.d/docker.sources
apt-get update -q
apt-get install -y -q docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
usermod -aG docker ai-agent
systemctl enable --now docker
docker version --format 'engine={{.Server.Version}}'
echo "compose=$(docker compose version --short)"
echo DONE
