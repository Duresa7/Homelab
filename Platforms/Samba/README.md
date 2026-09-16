# Samba

**Created:** 2026-09-14  
**Last updated:** 2026-09-14

I run Samba on `ubuntu-dev` (`192.168.40.179`), listening on TCP 445 on loopback and `ens18`. The versioned [configuration](Configuration/smb.conf) records the live shares.

On 2026-09-14 I created `/home/ai-agent/Documents/shared-folder`, owned by `ai-agent` with mode `0700`, and added the writable `shared-folder` share. It uses the existing Samba login `dkadi` and performs file operations as `ai-agent`. It has no client-host restriction; other machines with network access and the existing SMB credentials can use it. Upstream network policy still applies. The existing `ai-agent` home share remains configured.

I validated the configuration with `testparm -s`, reloaded it using `smbcontrol all reload-config`, and confirmed `smbd` remained active. An authenticated SMB test against `192.168.40.179` uploaded a temporary file, downloaded it, compared its bytes, and deleted it successfully. This test ran on `ubuntu-dev`; I did not perform an authenticated transfer from `docker-blue`.

Through SSH Manager, I verified `docker-blue` can open TCP 445 to `192.168.40.179`. I installed `smbclient` there using the gateway's configured sudo authentication after ordinary execution and passwordless sudo failed. Installation exited 0. No persistent mount or stored SMB credential was added on the client. These checks were observed in the task output; no separate raw transcript was retained.

Windows path: `\\192.168.40.179\shared-folder`. Linux/macOS file-manager address: `smb://192.168.40.179/shared-folder`.

From `docker-blue`, `smbclient //192.168.40.179/shared-folder -U dkadi` prompts for the existing SMB password. Its `put` and `get` commands upload and download files. A persistent client mount remains unconfigured.
