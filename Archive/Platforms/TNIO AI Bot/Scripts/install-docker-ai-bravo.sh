#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get -o Acquire::ForceIPv4=true -o Acquire::http::Timeout=20 -o Acquire::https::Timeout=20 update
apt-get install -y docker.io fuse-overlayfs uidmap

install -d -m 0755 /etc/docker
cat >/etc/docker/daemon.json <<'JSON'
{
  "storage-driver": "fuse-overlayfs",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
JSON

usermod -aG docker aibravo
systemctl enable docker.service
systemctl restart docker.service

docker version
docker info
