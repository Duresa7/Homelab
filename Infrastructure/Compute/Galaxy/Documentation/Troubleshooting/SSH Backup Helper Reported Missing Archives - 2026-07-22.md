# SSH Backup Helper Reported Missing Archives

**Created:** 2026-07-22  
**Last updated:** 2026-07-23

## Symptom

I asked the SSH backup helper to archive Proxmox configuration from Grey, Purple, Blue, and Red before the Kasm deployment. The helper returned a success result and a small archive size for each node, but its own backup inventory returned zero entries. A direct search under `/var/backups` found no matching archive or metadata file.

## Tests

1. I listed the helper's default backup directory on all four nodes. It contained no new item.
2. I searched three levels below `/var/backups` for names containing `pre-kasm` or `ssh-manager`. The search returned no file.
3. I treated the helper response as unverified and did not use it as a recovery point.

## Finding

The helper's success response did not match remote filesystem state. I did not isolate whether the error came from path conversion, metadata handling, or result reporting. The returned path used backslashes even though the targets run Linux, which is consistent with a path-normalization defect but is not proof of the cause.

## Correction

I created an explicit root-only archive on each node under `/root/kasm-preflight-20260722`. Each archive contains `/etc/pve`, `/etc/network`, `/etc/apt`, `/etc/default`, and `/etc/kernel`. I set mode `0600`, computed SHA-256, listed every member, and recorded the result. The Kasm preflight evidence that held those results was removed from the repository on 2026-07-23; the archives themselves remain on each node under `/root/kasm-preflight-20260722`.

## Verification

All four direct archives returned exit code 0. Their file listings contained 213 through 224 entries, and their sizes ranged from 138,604 through 138,806 bytes. GNU tar printed expected xattr warnings for Proxmox's FUSE-backed `/etc/pve` filesystem, then completed and listed each archive successfully.

## Remaining Risk

The direct archives protect configuration on their source nodes. They are not guest backups and do not survive loss of the node's boot storage. I will not use them as the only recovery control for a Proxmox package update or reboot.
