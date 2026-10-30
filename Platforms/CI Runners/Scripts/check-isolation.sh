#!/bin/bash
# Probe what a KUB-A host can reach. Run on ci-k3s-01 (any user).
t(){ if timeout 4 bash -c "</dev/tcp/$1/$2" 2>/dev/null; then echo "OPEN    $3 ($1:$2)"; else echo "blocked $3 ($1:$2)"; fi; }
t github.com 443 "internet HTTPS"
t deb.debian.org 80 "internet HTTP"
t 1.1.1.1 53 "internet DNS (expect blocked)"
t 1.1.1.1 22 "internet SSH (expect blocked)"
t 192.168.82.1 53 "gateway DNS"
t 192.168.72.2 1514 "Wazuh"
t 192.168.72.3 514 "Splunk (expect blocked)"
t 192.168.40.36 22 "ansible-01 Personal-A (expect blocked)"
t 192.168.80.118 22 "alpha-prod-01 SERVERS-A (expect blocked)"
t 192.168.70.10 8006 "grey MGMT-A (expect blocked)"
t 192.168.65.10 389 "HQ-DC01 Identity (expect blocked)"
t 192.168.82.11 22 "win11-dev, same VLAN (open: L2, no gateway)"
