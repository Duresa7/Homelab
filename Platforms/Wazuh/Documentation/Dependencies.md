# Wazuh Dependencies

**Created:** 2026-07-13  
**Last updated:** 2026-07-20

## Host and Service Dependencies

- VM 200 `security-01` on Galaxy Proxmox, with QEMU guest agent and VM firewall enabled.
- Security-A/VLAN 72 address `192.168.72.2`, gateway/DNS `192.168.72.1`.
- `wazuh-manager`, `wazuh-indexer`, and `wazuh-dashboard` systemd services.
- TCP 1514 from approved agent zones, TCP 1515 for controlled enrollment, HTTPS 443 for the dashboard, and HTTPS 55000 for the API.
- Valid system time and working local storage for manager queues, indexer data, and dashboard configuration.

## Cross-System Dependencies

- UniFi policies provide only the approved zone-to-Wazuh paths and return traffic.
- Galaxy/Proxmox supplies VM compute, storage, tagged VLAN 72, and guest firewall enforcement.
- Endpoint agents require a fresh manager registration.

No WAN-inbound policy or port forward is required or approved for Wazuh.
