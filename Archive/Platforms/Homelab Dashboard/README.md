# Homelab Dashboard

**Created:** 2026-09-26  
**Last updated:** 2026-09-27

I retired Homelab Dashboard from `docker-main` on 2026-09-26. It ran `ghcr.io/duresa7/homelab-dashboard-aio:latest` as `homelab-dashboard`, with host networking on TCP 3001 and data under `/opt/docker/homelab-dashboard-aio/data`.

I removed the deployment, data, images, imported Dockhand stack, unused network, proxy, DNS, dedicated firewall access, Proxmox account and monitoring entries. The unreachable alert cleared. I preserved the [Compose reference](Configuration/docker-compose.yml) and archived the [Forgejo source repository](https://forgejo.alphasecunited.com/dkadi/Homelab-Dashboard).

- [Retirement and verification](Documentation/Change%20Records/Retirement%20-%202026-09-26.md)
- [Final monitoring and HTTPS checks](Evidence/Retirement%20-%202026-09-26/Exports/Final-Verification.json)

On 2026-09-27 I deployed [Homarr](../../../Platforms/Homarr/README.md) as the replacement at `dashboard.alphasecunited.com`. This archive retains the retired application; its data and integrations were not migrated.
