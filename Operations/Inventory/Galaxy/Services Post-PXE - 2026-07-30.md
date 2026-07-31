# Galaxy Services Post-PXE Snapshot

**Created:** 2026-07-30  
**Last updated:** 2026-07-30  
**Snapshot date:** 2026-07-30

I captured the complete 13-guest workload inventory after adding the Galaxy PXE service to `ansible-01`. All workloads other than the two new provisioning listeners remain as recorded in the Post-Parrot snapshot.

## Guest Workloads

| Guest | Type | Node | Role | Key workloads |
| --- | --- | --- | --- | --- |
| ansible-01 | LXC 100 | grey-server | Automation and bare-metal provisioning | Ansible 14.2.0 / core 2.21.2; Semaphore 2.18.27; Galaxy PXE HTTP service; TFTP; SSH; cron; node_exporter |
| debian-dev | VM 102 | grey-server | Development workstation | GNOME Shell 48.7; GDM 48.0; Claude Desktop 1.21459.0; SSH |
| docker-main | LXC 110 | grey-server | Docker apps | Immich; Forgejo; Homelab Dashboard; Portainer; Syncthing; node_exporter; cAdvisor |
| monitor-01 | LXC 104 | blue-server | Infrastructure monitoring | Prometheus; Grafana; Proxmox exporter; blackbox exporter; NUT exporter; node_exporter; cAdvisor; PeaNUT |
| docker-network | LXC 107 | blue-server | Network access control plane | Nginx Proxy Manager 2.15.1; NetBird 0.74.4; Portainer Edge Agent 2.39.1; node_exporter; cAdvisor |
| docker-blue | LXC 108 | blue-server | Remote access | RustDesk; Portainer Edge Agent 2.39.1; node_exporter; cAdvisor |
| app-01 | VM 116 | grey-server | App platform | Coolify; Traefik; Postgres; Redis; Realtime; Wazuh agent 4.14.6; node_exporter; cAdvisor |
| edge-01 | VM 121 | grey-server | Edge ingress | Caddy; cloudflared; Wazuh agent 4.14.5 |
| kasm-01 | VM 122 | purple-server | Isolated disposable desktops | Kasm Workspaces 1.19.0 CE; Docker 29.6.2; VLAN 74, 75, 77, and 79 session lanes; node_exporter |
| security-01 / wazuh-01 | VM 200 | grey-server | Security monitoring | Wazuh 4.14.6; node_exporter; cAdvisor |
| alpha-prod-01 | VM 401 | grey-server | Voice and game services | TeamSpeak; TS3 Manager; Playit; Portainer Edge Agent; node_exporter; cAdvisor |
| splunk-siem | VM 109 | grey-server | SIEM | Splunkd; SC4S; node_exporter |
| media-01 | LXC 842 | red-server | Media automation and playback | Jellyfin; Seerr; Sonarr; Radarr; Prowlarr; FlareSolverr; qBittorrent through Gluetun; Portainer Edge Agent; node_exporter; cAdvisor |

## ansible-01 Provisioning Workloads

| Workload | Listener or path | Observed state |
| --- | --- | --- |
| Galaxy PXE HTTP service | TCP 8080; `galaxy-pxe.service` | Enabled and active; health returned `ok`; Green is `ready` and has not claimed the installer |
| TFTP | UDP 69; `tftpd-hpa.service` | Enabled and active; full 300,032-byte `galaxy-ipxe.efi` transfer matched SHA256 |
| Proxmox auto-install assistant | Package 9.2.7 | Generated Green answer parsed successfully |
| Proxmox installer | Proxmox VE 9.2-1 ISO under `/var/cache/galaxy-pxe` | Published SHA256 matched; prepared PXE assets under `/srv/galaxy-pxe` |
| iPXE source | Commit `404588d5f7c84815dfbf6c34912467b86a4376f4` | Custom UEFI loader installed under `/srv/tftp` |
| Ansible | Community 14.2.0 with ansible-core 2.21.2 | Existing control-node workload unchanged |
| Semaphore | 2.18.27 on TCP 3000 | Existing service unchanged |
| node_exporter | 1.9.0 on TCP 9100 | Existing service unchanged |

## Current Provisioning Boundary

Green is only an armed PXE target at this snapshot. It is not a Galaxy node or guest, so I did not add it to the physical node, VM, LXC, or exporter inventories. The registry targets only `nvme0n1`; its secondary SATA disk is absent from the generated answer. I will roll the hardware and node records forward after the first boot proves the joined state and disk layout.
