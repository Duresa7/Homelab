# Termix

**Created:** 2026-07-13  
**Last updated:** 2026-07-17

Termix is the homelab's self-hosted SSH and remote-desktop management platform. It runs on `docker-main` with a companion Guacamole daemon.

## Ownership and Deployment

| Item | Value |
|---|---|
| Owner | Homelab operator |
| Host | `docker-main` (`192.168.40.35`) |
| Compose project | `termix` |
| Compose file | `/opt/docker/termix/docker-compose.yml` |
| Application container | `termix` |
| Companion container | `guacd` |
| Persistent application data | Docker volume `termix_termix-data`, mounted at `/app/data` |
| Published application port | TCP 8080 |
| Current verified version | Termix 2.5.0; Guacamole daemon 1.6.0 |
| Current Termix image digest | `sha256:4d3371311087d6757aa9d1c94117e854d749b1c5e8fd07bd36e7a99e0686d26c` |

The application uses an encrypted SQLite file and operates on an in-memory database while running. Never retain database keys, reset codes, or decrypted database content in this workspace.

## Managed SSH Inventory

Termix currently has nine verified SSH hosts organized into four shallow folders: `Homelab/Docker`, `Homelab/Edge`, `Homelab/Servers`, and `Homelab/Proxmox`. The inventory contains the four Galaxy Proxmox nodes, `docker-main`, `alpha-prod-01`, `app-01`, `edge-01`, and `docker-network`. All use the reusable `Termix Homelab SSH` Ed25519 credential with per-host username override. Its private key remains encrypted in Termix; only the public key is installed on managed accounts.

Ten additional SSH Manager entries were unreachable during the 2026-07-14 onboarding and were intentionally not saved as unverified Termix hosts. Their current error states and the onboarding procedure are recorded in the change record below.

## Layout

- `Documentation/` — operational and troubleshooting records.
- `Evidence/` — secret-free evidence captured during bounded Termix work.

## Key Records

- [Troubleshooting Log](Documentation/Troubleshooting-Log.md)
- [Termix SSH Host Onboarding change record](Documentation/Change%20Records/Termix%20SSH%20Host%20Onboarding%20-%202026-07-14.md)
- [Termix Upgrade 2.2.1 to 2.5.0 change record](Documentation/Change%20Records/Termix%20Upgrade%202.2.1%20to%202.5.0%20-%202026-07-13.md)
- [SSH Host Onboarding evidence](Evidence/SSH%20Host%20Onboarding%20-%202026-07-14/Evidence-Index.md)
- [Password Reset Code Missing evidence](Evidence/Password%20Reset%20Code%20Missing%20-%202026-07-13/Evidence-Index.md)
