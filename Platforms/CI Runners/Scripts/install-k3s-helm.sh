#!/bin/sh
# Install pinned k3s (defaults: Traefik and ServiceLB on) and Helm on ci-k3s-01. Run as root.
set -e
K3S_VERSION=${K3S_VERSION:-v1.36.5+k3s1}
HELM_VERSION=${HELM_VERSION:-v4.3.1}
curl -fsSL https://get.k3s.io -o /tmp/k3s-install.sh
INSTALL_K3S_VERSION=$K3S_VERSION sh /tmp/k3s-install.sh
rm -f /tmp/k3s-install.sh
cd /tmp
curl -fsSLO https://get.helm.sh/helm-$HELM_VERSION-linux-amd64.tar.gz
curl -fsSLO https://get.helm.sh/helm-$HELM_VERSION-linux-amd64.tar.gz.sha256sum
sha256sum -c helm-$HELM_VERSION-linux-amd64.tar.gz.sha256sum
tar -xzf helm-$HELM_VERSION-linux-amd64.tar.gz linux-amd64/helm
install -m 0755 linux-amd64/helm /usr/local/bin/helm
rm -rf linux-amd64 helm-$HELM_VERSION-linux-amd64.tar.gz*
k3s --version | head -1; helm version --short
