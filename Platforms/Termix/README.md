# Termix

**Created:** 2026-07-13  
**Last updated:** 2026-07-20

I run Termix 2.5.0 on `docker-main` with a Guacamole 1.6.0 companion daemon. The current inventory contains nine SSH hosts in four folders.

## Deployment

| Item | Value |
|---|---|
| Host | `docker-main` (`192.168.40.35`) |
| Compose project | `termix` |
| Compose file | `/opt/docker/termix/docker-compose.yml` |
| Application container | `termix` |
| Companion container | `guacd` |
| Persistent application data | Docker volume `termix_termix-data`, mounted at `/app/data` |
| Published application port | TCP 8080 |
| Current verified version | Termix 2.5.0; Guacamole daemon 1.6.0 |
| Current Termix image digest | `sha256:4d3371311087d6757aa9d1c94117e854d749b1c5e8fd07bd36e7a99e0686d26c` |

## Managed SSH Inventory

Termix currently has nine verified SSH hosts organized into `Homelab/Docker`, `Homelab/Edge`, `Homelab/Servers`, & `Homelab/Proxmox`. The inventory contains the four Galaxy Proxmox nodes, `docker-main`, `alpha-prod-01`, `app-01`, `edge-01`, & `docker-network`. All use the `Termix Homelab SSH` Ed25519 identity with per-host username overrides.

Ten additional SSH Manager entries were unreachable during the 2026-07-14 onboarding, and I intentionally did not save them as unverified Termix hosts. Their error states and the onboarding procedure are recorded in the change record below.

## Layout

- `Documentation/` holds the operational and troubleshooting records.

## Key Records

- [Troubleshooting Log](Documentation/Troubleshooting-Log.md)
- [Termix SSH Host Onboarding change record](Documentation/Change%20Records/Termix%20SSH%20Host%20Onboarding%20-%202026-07-14.md)
- [Termix Upgrade 2.2.1 to 2.5.0 change record](Documentation/Change%20Records/Termix%20Upgrade%202.2.1%20to%202.5.0%20-%202026-07-13.md)
