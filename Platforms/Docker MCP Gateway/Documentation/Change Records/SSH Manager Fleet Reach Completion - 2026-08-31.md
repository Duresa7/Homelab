# SSH Manager Fleet Reach Completion

**Created:** 2026-08-31  
**Last updated:** 2026-08-31

## Outcome

I cleared the six access failures left by the initial SSH Manager deployment. The dedicated SSH Manager gateway now reaches all eighteen configured servers through Executor. The five Galaxy nodes answer as root, and `ubuntu-dev` answers as `ai-agent` with noninteractive sudo to root.

This is privileged fleet access, not an unprivileged management path. Every SSH Manager catalog entry is in unrestricted mode. Five Proxmox nodes and `docker-main` authenticate as root, ten ordinary hosts carry a password for `ssh_execute_sudo`, `ansible-01` has passwordless sudo through its unattended account, and `ubuntu-dev` passed `sudo -n id -u`. Executor has no policy override for the SSH Manager connection, so none of the 37 SSH tools requires Executor approval.

## Changes

1. I created UniFi policy `Allow docker-blue SSH Manager to Proxmox`. It admits only `192.168.40.39` in `Internal` to the five node addresses in `AlphaSec-Mgmt` over TCP 22, logs matches, and creates the response path. The before snapshot was `firewall_20260901T014239Z.json`; the after snapshot was `firewall_20260901T015019Z.json`.
2. I added `192.168.40.39` as `docker-blue SSH Manager` to the Proxmox Datacenter `pve_admins` IPSet. The existing `pve_mgmt` security group supplies the node-side TCP 22 accept. UniFi still limits this source to TCP 22, so the broader 8006 and 3128 ports on the `pve_admins` group do not gain a network path from `docker-blue`.
3. I added the gateway identity to `ubuntu-dev`'s `ai-agent` authorized keys. Authentication then reached the gateway's strict host-key check instead of failing key authentication.
4. I compared the RSA, ECDSA, and ED25519 keys presented by `192.168.40.179` with `/etc/ssh/ssh_host_*_key.pub` on `ubuntu-dev`. All three SHA-256 fingerprints matched. I enrolled those three verified keys in the persistent `ssh-manager-state` volume rather than accepting an unknown key.
5. I changed the live Executor integration and connection descriptions from the obsolete 12-of-18 status to the verified all-18 state. Executor 1.6.7 exposes list and remove operations but no description update, so I used guarded SQLite updates against the exact old text; one integration row and one connection row changed.
6. I stopped fourteen managed SSH Manager containers left by interrupted verification sessions. Docker removed the disposable containers through `--rm`; the `ssh-manager-state` volume remained.

I did not create a snapshot or backup. The UniFi controller snapshots are state captures for the firewall skill, not rollback images, and remain outside this repository. The Proxmox change was one additive IPSet member through `pvesh`. Executor's guarded metadata update changed two descriptive fields and no credentials or integration configuration.

## Verification

- The UniFi snapshot comparison added exactly `Allow docker-blue SSH Manager to Proxmox`: one policy added, zero removed, and zero changed. Live readback returned the same source, five destinations, TCP 22, IPv4, logging, enabled state, and `ALLOW` action shown in the approved preview.
- All five nodes read `192.168.40.39` back from the shared `pve_admins` IPSet with the same digest. `pve-firewall status` returned `enabled/running` on Grey, Purple, Blue, Red, and Green.
- A managed SSH Manager container using the injected private key and `StrictHostKeyChecking yes` authenticated to all five node addresses and to `ai-agent@ubuntu-dev`.
- Executor initialized over HTTPS with MCP protocol `2025-06-18`. Its UniFi path resolved `unifi-mcp-gateway.user.unifiMcpGateway.unifi_tool_index` and returned 20 firewall matches across the server's 24 categories.
- The same fresh Executor session resolved the dedicated SSH path and ran `hostname && id -u` on all five Proxmox nodes. Each returned its expected hostname and UID `0`.
- The Executor SSH path ran `hostname && id -un && sudo -n id -u` on `ubuntu_dev`. It returned `ubuntu-dev`, `ai-agent`, UID `0`, and exit code `0`.
- `ssh_list_servers` through Executor returned all eighteen catalog entries.
- A complete Executor privilege sweep returned UID `0` with exit code `0` on all eighteen. The five Proxmox nodes and `docker_main` passed through their root logins; the other twelve passed through `ssh_execute_sudo`.
- The combined `docker-mcp-gateway` Executor integration, `dockerMcpGateway` connection, and live `mcp-secrets.env` are absent. The versioned combined secret template is deleted. The UniFi and SSH Manager connections remain separate, healthy, and encrypted.
- After the end-to-end and full privilege sessions closed, I stopped the one managed SSH Manager container each left behind. `docker-mcp-gateway`, `ssh-manager-mcp-gateway`, and `executor` remained running and healthy, with no managed SSH Manager container left.

No standalone transcript was retained. The results above are the live readbacks observed during the change.

## Current Boundary

The SSH Manager endpoint is bearer-protected internal HTTP at `192.168.40.39:8812`, but possession of that bearer credential through Executor reaches unrestricted root-capable SSH on all eighteen servers. The UniFi endpoint remains separate at `192.168.40.39:8811`; its create, update, and delete permissions remain disabled in the gateway catalog.

The later [agent client cutover](../../../Executor/Documentation/Change%20Records/Agent%20Client%20Cutover%20-%202026-08-31.md) retained no-approval behavior by request in both Codex and Claude Code. Network reach and the approval-policy choice are no longer open work in this record; the unrestricted boundary above is the accepted current state.

## Related Records

- [SSH Manager MCP integration](SSH%20Manager%20MCP%20Integration%20-%202026-08-31.md)
- [Executor integration separation](../../../Executor/Documentation/Change%20Records/MCP%20Integration%20Separation%20-%202026-08-31.md)
- [UniFi firewall policy reference](../../../../Infrastructure/Network/UniFi/Configuration/firewall.md)
- [Galaxy Datacenter firewall reference](../../../../Infrastructure/Compute/Galaxy/Configuration/Datacenter-Firewall.md)
