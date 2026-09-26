# Shared Folder Share

**Created:** 2026-09-25  
**Last updated:** 2026-09-25

**Change date:** 2026-09-14  
**Status:** Complete; no persistent client mount configured  
**Host:** `ubuntu-dev` (`192.168.40.179`)

## What changed

I created `/home/ai-agent/Documents/shared-folder`, owned by `ai-agent` with mode `0700`, and added the writable `shared-folder` share. It uses the existing Samba login `dkadi` and performs file operations as `ai-agent`. It has no client-host restriction: any machine with network access and the SMB credentials can use it, subject to the upstream UniFi policy. The existing `ai-agent` home share stayed configured.

## Verification

- `testparm -s` validated the configuration, `smbcontrol all reload-config` reloaded it, and `smbd` stayed active.
- An authenticated SMB test against `192.168.40.179`, run on `ubuntu-dev`, uploaded a temporary file, downloaded it, compared its bytes, and deleted it.
- Through SSH Manager, `docker-blue` opened TCP 445 to `192.168.40.179`.
- I installed `smbclient` on `docker-blue` using the gateway's configured sudo authentication, after ordinary execution and passwordless sudo failed. The installation exited 0. I added no persistent mount and no stored SMB credential there.

## Open

- I did not run an authenticated transfer from `docker-blue`. From there, `smbclient //192.168.40.179/shared-folder -U dkadi` prompts for the SMB password, and its `put` and `get` commands move files.
- A persistent client mount remains unconfigured.
