# Galaxy PXE

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

I run Galaxy PXE as the dedicated bare-metal provisioning service for Galaxy Proxmox nodes. `ansible-01` hosts the service, but the machine registry, installer policy, first-boot behavior, tests, operating records, and evidence belong here because they form one deployed service.

## Live Deployment

- Host: `ansible-01`, `192.168.40.36`
- TFTP: UDP 69 through `tftpd-hpa`
- HTTP: TCP 8080 through `galaxy-pxe.service`
- Provisioning lane: `Server-Provision`, VLAN 5
- Current deployed node: Proxmox node `green-server`; UniFi alias `green-node`
- Completed attempt: `complete` at 2026-07-31 12:41:27 UTC
- Physical memory requirement: at least 12 GiB; 16 GiB preferred
- Installed physical memory: 16 GB across two 8 GB DDR4-2667 SODIMMs
- Install disk: `/dev/nvme0n1`
- Preserved secondary disk: `/dev/sda`
- Cluster join peer: `grey-server`, `192.168.70.10`
- Post-cutover callback: `OBJ-Proxmox-Nodes` to `192.168.40.36:8080` through `Allow Proxmox Nodes to Galaxy PXE`

I installed Green through the one-use PXE path on 2026-07-31. Proxmox reported `/dev/nvme0n1` as the only boot disk and `/dev/sda` as the other disk. The first-boot state reached `complete` after Galaxy reported five nodes, quorum, and four connected peers on Corosync links 0 and 1. Bane port 4 now uses `Proxmox-Trunk` with no native VLAN; Green remains online on tagged VLANs 70 and 71.

## Layout

| Location | Purpose |
|---|---|
| `Source/` | Versioned service, machine-registry example, Ansible deployment, templates, and tests |
| `Documentation/Change Records/` | Dated deployment and repair history |
| `Documentation/Troubleshooting/` | Operational issue index and investigation records |
| `Evidence/` | Sanitized command results and validation summaries |

The deployed project remains `/home/ansible/proxmox-pxe-provisioning` on `ansible-01`. Ansible is the deployment mechanism, not the owner of this service.

## Key Records

- [Source and operations](Source/README.md)
- [Deployment and repair record](Documentation/Change%20Records/Galaxy%20PXE%20Provisioning%20Service%20-%202026-07-30.md)
- [Green PXE stall investigation](Documentation/Troubleshooting/Green%20PXE%20Install%20Stalls%20Before%20Reboot%20-%202026-07-31.md)
- [Repair evidence](Evidence/Galaxy%20PXE%20Repair%20-%202026-07-31/Evidence-Index.md)
