# ubuntu-dev Workstation Access

**Created:** 2026-09-25  
**Last updated:** 2026-09-25

**Implementation date:** 2026-08-13  
**Status:** Complete; the policies are live  
**Affected systems:** policies `Device Access --> Proxmox`, `Allow ubuntu-dev to Proxmox`, `Allow Monitor to Personal-A monitoring`, and the CLI Proxy API policy

On 2026-08-13 I moved workstation access from `debian-dev` (`192.168.40.135`) to `ubuntu-dev` (`192.168.40.179`). I wrote this record on 2026-09-25 from the paragraphs the firewall view carried; no export was retained.

## What changed

1. **Proxmox access.** I swapped the client MAC in `Device Access --> Proxmox`. A MAC entry alone never produced a working rule for the new guest, so I added `Allow ubuntu-dev to Proxmox`, which admits `192.168.40.179` in Internal to `AlphaSec-Mgmt` on the same port group the MAC policy uses. That policy carries the access. The Proxmox cluster firewall also needed the new address in `pve_admins` before any node answered; see the [Galaxy Datacenter firewall](../../../../Compute/Galaxy/Configuration/Datacenter-Firewall.md).
2. **Exporter scrape.** I replaced `192.168.40.135` with `192.168.40.179` in the destination list of `Allow Monitor to Personal-A monitoring`.
3. **CLI Proxy API.** When CLI Proxy API moved hosts, I renamed `Allow NPM to debian-dev CLI Proxy API` to `Allow NPM to ubuntu-dev CLI Proxy API` and changed its destination from `192.168.40.135` to `192.168.40.179`. Source, port, protocol, action, logging and index stayed as they were, and the policy kept its 3,694 recorded hits. On 2026-08-19 it moved again, to `docker-main` as `Allow NPM to docker-main CLI Proxy API`. [Internal HTTPS](../../../../../Platforms/CLI%20Proxy%20API/Documentation/Change%20Records/Internal%20HTTPS%20-%202026-08-10.md), [Relocation to docker-main](../../../../../Platforms/CLI%20Proxy%20API/Documentation/Change%20Records/Relocation%20to%20docker-main%20-%202026-08-19.md).

This record supersedes the workstation entries of [VPN Management Access to DMZ](VPN%20Management%20Access%20to%20DMZ%20-%202026-08-08.md).
