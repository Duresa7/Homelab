# Kasm Session Isolation Implementation Results

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

## Compute

```text
VM 122 node: purple-server
VM 122 state: running
Storage: ssd-lvm2
Root disk: 100 GiB, thin data use 25.16%
Cluster: 4 of 4 votes, quorate
VM snapshots: current only
Grey VM 122 volumes: none
Backup archives created: none
```

## Kasm

```text
kasm_api                 healthy
kasm_db                  healthy
kasm_manager             healthy
kasm_agent               healthy
kasm_guac                healthy
kasm_proxy               running; no Docker health check
kasm_rdp_gateway         healthy
kasm_rdp_https_gateway   healthy
GET /api/__healthcheck   {"ok":true}
Administrator auth       token returned
```

The seven containers with a Docker health check reported `healthy`. All eight service containers were running.

The Kasm agent reported `lab74`, `lab77`, and `lab79` among its available Docker networks after the reboot.

## Network

```text
net0  VLAN 78  192.168.78.10/24
net1  VLAN 74  no host address
net2  VLAN 77  no host address
net3  VLAN 79  no host address
shim74 192.168.74.201/32 -> 192.168.74.208/28
shim77 192.168.77.201/32 -> 192.168.77.208/28
shim79 192.168.79.201/32 -> 192.168.79.208/28
kasm-lab-shims.service enabled, active
```

## Containment

```text
lab74 -> Internet: Proton 185.98.168.20
kasm-01 -> Internet: the home WAN address, not a Proton exit
lab74 -> lab77: allowed
lab77 -> lab74: blocked
lab74 -> lab79: blocked
lab77 -> lab79: blocked
lab79 -> lab74: blocked
lab79 -> lab77: blocked
lab77 DNS and Internet: blocked
lab79 DNS and Internet: blocked
```

Every lane failed the exact TCP probes to:

```text
192.168.78.10:443
192.168.80.10:22
192.168.70.10:8006
192.168.70.11:8006
192.168.71.10:22
192.168.72.2:443
192.168.73.2:9090
192.168.1.1:443
192.168.10.1:443
```

The host's probe to its own `192.168.78.10:443` listener was open. Its probes to the other eight protected addresses were blocked.

## Proton Failure

```text
VPN enabled, production endpoint: lab74 exit 185.98.168.20
VPN enabled, TEST-NET endpoint 192.0.2.1:51820: lab74 timed out
Same failure interval: kasm-01 retained ordinary WAN
Production endpoint restored: lab74 exit 185.98.168.20
```

## Cleanup

```text
Temporary containers: none
Temporary Alpine/hello-world images: none
Dangling legacy Kasm image IDs found by review: 8
Dangling image IDs after docker image prune: 0
Space reclaimed by final image prune: 4.373 GB
Temporary TEST firewall policies: none
Temporary Purple VLAN interface: none
Temporary trunk exception: none
Kasm containers/images remaining: 8 / 8
```
