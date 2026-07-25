# Kasm Workspaces

**Created:** 2026-07-24  
**Last updated:** 2026-07-25

Kasm Workspaces 1.19.0 Community Edition runs on `kasm-01` (VM 122) at `192.168.80.30`, on `grey-server`. It streams throwaway containerized desktops & browsers to a browser tab. I rebuilt it from scratch on 2026-07-24 after tearing down an earlier over-built version.

Community Edition caps me at 5 concurrent sessions & one named user. That cap drove every sizing decision here.

## What's built & what isn't

The platform itself is live: 8 containers healthy, HTTPS on TCP 443, admin login verified. Nothing else is wired up yet. The isolated lab VLANs exist on the UniFi side but `kasm-01` has a single NIC on SERVERS-A, so no session currently lands in an isolated segment.

On 2026-07-24 I launched three workspaces to see how Kasm behaves, which pulled their images: `forensic-osint` at 10.3 GB, `vs-code` at 6.42 GB, & `terminal` at 4.83 GB. That was me testing the product, not a catalog decision. Disk went from 13 GiB to 26 GiB of 96 GiB because of it. No session was running when I checked at 2026-07-25 07:49 EDT.

Deliberately not done yet:

- No second or third NIC for the lab VLANs 74, 77, & 79.
- No workspace catalog chosen. Every image other than the three test pulls above still downloads on first launch.
- No reverse-proxy entry, so no `kasm.<YOUR_BASE_DOMAIN>` hostname. Reach it by IP.
- Self-signed certificate from the installer, so browsers warn on first visit.

## Layout

| Path | Contents |
|---|---|
| `Documentation/Deployment.md` | The 2026-07-24 build: VM spec, baseline, install commands, verification output |

## Access

SSH as `<YOUR_ADMIN_USERNAME>@192.168.80.30` with any of the four fleet keys, or `ssh kasm-01` from Jedi PC. The web UI is `https://192.168.80.30/`. Administrator credentials came from the installer & are not stored in this repository.

`kasm-01` sits on VLAN 80 SERVERS-A, inside the <YOUR_ORG_NAME>-Servers firewall zone. The existing "Allow Internal to <YOUR_ORG_NAME>-Servers" & "Allow VPN to <YOUR_ORG_NAME>-Servers" policies already cover it, so I added no firewall rules for this deployment.

## Related records

- [Isolated Security Lab architecture](../../Architecture/Isolated-Security-Lab.md)
- [Kasm lab network simplification (2026-07-23)](../../Infrastructure/Network/UniFi/Documentation/Change%20Records/Kasm%20Lab%20Network%20Simplification%20-%202026-07-23.md)
- [Kasm lab Proxmox teardown (2026-07-23)](../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Kasm%20Lab%20Proxmox%20Teardown%20-%202026-07-23.md)
- [Linux Host Baseline Standard](../../Security/Hardening/Linux-Host-Baseline-Standard.md)
