# Termix SSH Host Onboarding

**Created:** 2026-07-14  
**Last updated:** 2026-07-17

**Implementation date:** 2026-07-14  
**Status:** Complete for every SSH Manager target reachable during implementation  
**Primary owner:** Platforms/Termix  
**Affected systems:** Termix 2.5.0 on `docker-main`; nine managed SSH accounts; Galaxy Proxmox datacenter firewall

## Scope

Populate the previously empty Termix host manager with every machine that the configured SSH Manager could reach, give Termix an independent and least-privilege authentication path, and prove that Termix itself can establish each connection. Do not copy the SSH Manager's existing private keys into Termix.

## Starting State

- Termix 2.5.0 and `guacd` were healthy on `docker-main`.
- The Termix API returned zero hosts and zero reusable credentials for the active user.
- SSH Manager defined 19 targets: nine responded to a live SSH probe and ten were unreachable.
- `docker-main` could not reach TCP/22 on the four Proxmox nodes even though the same nodes were reachable through SSH Manager from the operator workstation.
- The Termix Chrome path was not required; the local API could perform and verify the change without exposing an account password or creating a durable API key.

## Decisions and Rationale

- Generate a dedicated Ed25519 credential inside Termix rather than export or copy an existing private key. Only the new public key left Termix, and it was installed through the already-approved SSH Manager connections.
- Use one reusable Termix credential with per-host username override because the reachable inventory contains both `root` and `REDACTED_USER_001` accounts.
- Add only targets that passed the source reachability probe. A saved host without a deployable and verified authentication path would look complete while remaining unusable.
- Diagnose the Proxmox timeouts across both network layers before changing policy. UniFi flow records proved those SSH attempts were allowed; the Proxmox datacenter firewall's explicit TCP/22 drop was the actual blocker.
- Give Termix a dedicated Proxmox IPSet and TCP/22-only accept instead of adding Docker Main to a broader admin or automation group that also permits TCP/8006.
- Take recovery copies before mutating Termix data and the Proxmox firewall because both stores are security-sensitive and authoritative.
- Keep the Termix folder hierarchy shallow and task-oriented: `Homelab/Docker`, `Homelab/Edge`, `Homelab/Servers`, and `Homelab/Proxmox`. This makes the sidebar easier to scan than the original compute/network hierarchy; `docker-network` belongs in Docker because its operational role is hosting Docker workloads.

## Actions and Observed Results

1. Inventoried all 19 SSH Manager targets and issued a live `echo TERMIX_SSH_OK` probe. Nine succeeded; ten returned either connection refused or timeout.
2. Confirmed the Termix host and credential inventories were empty through authenticated, secret-safe local API reads.
3. Created mode-0600 Termix data backup `/opt/docker/termix/backups/pre-host-import-2026-07-14T1900Z.tar.gz` on `docker-main`.
4. Used Termix's key generator to create credential ID 1, `Termix Homelab SSH`. Its Ed25519 public-key fingerprint is `REDACTED_SSH_FINGERPRINT_010`; the private key remained encrypted in Termix.
5. Idempotently added the public key to the nine reachable accounts' `authorized_keys` files and verified the exact entry on each target.
6. Created nine Termix host records with credential ID 1, per-host username override, terminal/tunnel/file-manager access, server statistics, and Docker or Proxmox integration flags where applicable.
7. Exercised Termix's SSH metrics connection path. Five hosts connected immediately; all four Proxmox nodes timed out.
8. Confirmed `docker-main` had a route to VLAN 70 but no TCP/22 path. UniFi policy and Traffic Flows showed the requests were allowed. The Proxmox `pve_mgmt` group allowed `docker-main` only through `pve_svc_clients` on TCP/8006 and then dropped TCP/22.
9. Backed up `/etc/pve/firewall/cluster.fw` to mode-0600 `/root/cluster.fw.pre-termix-2026-07-14` on `grey-server`. Created `pve_termix` with member `192.168.40.35` and an inbound TCP/22 accept in `pve_mgmt` before the existing SSH drop.
10. Repeated live TCP probes from `docker-main`; all four Proxmox ports opened. Repeated Termix-originated connection tests; all nine hosts completed SSH key authentication and established metrics sessions.
11. Created mode-0600 recovery archive `/opt/docker/termix/backups/pre-folder-reorganization-2026-07-14T1810Z.tar.gz`, replaced the original nested folder labels with the four shallow categories, and verified that names, addresses, ports, usernames, authentication type, and credential assignment did not change.
12. Repeated Termix-originated metrics connections after the folder change. All nine hosts returned HTTP 200 with `success: true`; the Termix container remained healthy with zero restarts.

## Resulting Termix Inventory

| ID | Host | Address | User | Folder | Verified from Termix |
|---:|---|---|---|---|---|
| 1 | `grey-server` | 192.168.70.10 | root | `Homelab/Proxmox` | Yes |
| 2 | `purple-server` | 192.168.70.11 | root | `Homelab/Proxmox` | Yes |
| 3 | `blue-server` | 192.168.70.12 | root | `Homelab/Proxmox` | Yes |
| 4 | `red-server` | 192.168.70.13 | root | `Homelab/Proxmox` | Yes |
| 5 | `docker-main` | 192.168.40.35 | root | `Homelab/Docker` | Yes |
| 6 | `alpha-prod-01` | 192.168.80.118 | REDACTED_USER_001 | `Homelab/Servers` | Yes |
| 7 | `app-01` | 192.168.80.10 | REDACTED_USER_001 | `Homelab/Servers` | Yes |
| 8 | `edge-01` | 192.168.90.10 | REDACTED_USER_001 | `Homelab/Edge` | Yes |
| 9 | `docker-network` | 192.168.85.2 | REDACTED_USER_001 | `Homelab/Docker` | Yes |

## Configured Targets Not Onboarded

| SSH Manager alias | Address | Observed blocker |
|---|---|---|
| `unifi_ashoka` | 192.168.1.1 | TCP/22 connection refused |
| `ai_alpha_01` | 192.168.40.37 | TCP/22 timed out |
| `REDACTED_OPERATIONAL_HOST` | 192.168.40.38 | TCP/22 timed out |
| `supabase_01` | 192.168.80.20 | TCP/22 timed out |
| `ws_dc_1_main` | 192.168.65.10 | TCP/22 timed out |
| `ws_dc_2_secondary` | 192.168.65.45 | TCP/22 timed out |
| `obi_pc` | 192.168.65.102 | TCP/22 timed out |
| `security_01` | 192.168.72.2 | TCP/22 timed out |
| `splunk_siem` | 192.168.72.3 | TCP/22 timed out |

These are deliberate exceptions, not silently skipped successes. When an endpoint becomes reachable, install the existing Termix public key through an approved administrative path, create its Termix host record with credential ID 1 and username override, and repeat the Termix-originated SSH verification.

## Verification

| Check | Observed result |
|---|---|
| Termix credential | ID 1 exists; type Ed25519; fingerprint recorded; no private material exposed |
| Public-key installation | Exact generated public key present on all nine reachable accounts |
| Termix host inventory | Nine expected records, IDs 1–9, no create failures |
| Non-Proxmox connections | Five of five returned HTTP 200 and `SSH connection established successfully` |
| UniFi diagnosis | Docker Main MAC and client identity matched; SSH flows to `grey-server` recorded as allowed |
| Proxmox firewall | `pve_termix` contains only `192.168.40.35`; TCP/22 accept precedes `DROP SSH` |
| Proxmox firewall compile | Exit 0; service `enabled/running` |
| Docker Main to Proxmox | `192.168.70.10–13:22` all returned open after the firewall change |
| Proxmox connections in Termix | Four of four returned HTTP 200 and established SSH metrics sessions |
| Final Termix connection set | Nine of nine onboarded hosts authenticated with the Termix credential |
| Simplified folder hierarchy | Exactly four folders remain: `Homelab/Docker`, `Homelab/Edge`, `Homelab/Servers`, and `Homelab/Proxmox` |
| Post-reorganization connection set | Nine of nine hosts returned HTTP 200 and `success: true` through Termix's metrics connection path |
| Termix runtime | Container `healthy`; restart count 0 |

No password, private key, JWT secret, ephemeral JWT, database key, or decrypted database content was printed or retained.

## Rollback

### Termix

To undo only the folder reorganization, restore the prior folder strings through the Termix host editor or stop Termix and restore the paired encrypted database and security material from `/opt/docker/termix/backups/pre-folder-reorganization-2026-07-14T1810Z.tar.gz`. To remove the onboarding entirely, delete host IDs 1–9 and credential ID 1 through Termix, then remove the corresponding public key fingerprint `REDACTED_SSH_FINGERPRINT_010` from the nine accounts. If application data is damaged rather than merely unwanted, the complete pre-onboarding archive remains `/opt/docker/termix/backups/pre-host-import-2026-07-14T1900Z.tar.gz`; do not restore the encrypted database independently of its matching security files.

### Proxmox

Remove the `+pve_termix` rule from `pve_mgmt`, remove member `192.168.40.35`, then remove IPSet `pve_termix`. The complete pre-change file remains at `/root/cluster.fw.pre-termix-2026-07-14` on `grey-server` as a manual recovery reference.

## Remaining Work

- Reassess the ten unreachable SSH Manager entries when they are online or SSH is enabled. They are not present in Termix today because working authentication could not be deployed or verified.
- The dedicated credential is intentionally reusable; do not create duplicate per-host private keys unless a later isolation requirement calls for them.

## Step Evidence

| Step | Evidence | Verification |
|---|---|---|
| S01 | [SSH inventory and reachability](../../Evidence/SSH%20Host%20Onboarding%20-%202026-07-14/Logs/S01-SSH-Inventory-And-Reachability-2026-07-14.md) | Nineteen configured targets classified; nine reachable |
| S02 | [Credential and host creation](../../Evidence/SSH%20Host%20Onboarding%20-%202026-07-14/Logs/S02-Termix-Credential-And-Host-Creation-2026-07-14.md) | Dedicated credential created; public key installed; nine records created |
| S03 | [Proxmox firewall correction](../../Evidence/SSH%20Host%20Onboarding%20-%202026-07-14/Logs/S03-Proxmox-Firewall-Correction-2026-07-14.md) | Root cause isolated; narrow TCP/22 path opened; rollback file retained |
| S04 | [Termix connection verification](../../Evidence/SSH%20Host%20Onboarding%20-%202026-07-14/Logs/S04-Termix-Connection-Verification-2026-07-14.md) | Termix established authenticated SSH sessions to all nine hosts |
| S05 | [Termix folder reorganization](../../Evidence/SSH%20Host%20Onboarding%20-%202026-07-14/Logs/S05-Termix-Folder-Reorganization-2026-07-14.md) | Four shallow categories applied; connection settings preserved; all nine hosts reverified |
