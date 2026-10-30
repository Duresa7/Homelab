#!/bin/sh
# Install the Actions Runner Controller (scale-set mode) on ci-k3s-01. Run as root.
# No scale set and no GitHub credential is created here.
set -e
ARC_VERSION=${ARC_VERSION:-0.15.1}
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
kubectl -n kube-system wait --for=condition=Ready pod --all --field-selector=status.phase!=Succeeded --timeout=300s
helm upgrade --install arc --namespace arc-systems --create-namespace \
  oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller \
  --version "$ARC_VERSION" --wait --timeout 5m
kubectl -n arc-systems get pods
kubectl get crd | grep actions.github.com
