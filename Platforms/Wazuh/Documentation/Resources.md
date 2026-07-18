# Wazuh Resource Specification

**Created:** 2026-07-13  
**Last updated:** 2026-07-17

## VM 200 `security-01`

| Resource | Verified value |
|---|---|
| vCPU | 4 cores, host CPU type, 1 socket |
| Memory | 12,288 MiB; balloon minimum 6,144 MiB |
| Root disk | 100 GiB on `ssd-lvm1`, discard/iothread enabled |
| Firmware/machine | OVMF, q35 |
| NIC | VirtIO on `vmbr0`, VM firewall enabled, VLAN tag 72 |
| Address | `192.168.72.2/24` |

## Wazuh Packages

`wazuh-manager`, `wazuh-indexer`, and `wazuh-dashboard` were all verified at package version `4.14.5-1` on 2026-07-13. The manager runtime reported Wazuh `v4.14.5` revision `rc1`.

At final verification, the VM root filesystem was 30% used and memory use was approximately 25%. The generic EFI-variable pseudo-filesystem warning does not represent root-disk pressure.
