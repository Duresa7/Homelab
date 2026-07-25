# S01 Account and SSH Verification

**Created:** 2026-07-25  
**Last updated:** 2026-07-25

## Credential Record

| Check | Observed result |
|---|---|
| Vault | `the managed vault` |
| Item | `the console login entry` |
| Category and username | Login; `ansible` |
| Recipe | 32 characters with letters, digits, & symbols |
| Password disclosure | None; only length and recipe booleans were printed |

## Account Results

| Host | Platform path | Administrative group | Docker group | Result |
|---|---|---|---|---|
| ansible-01 | LXC 100 | sudo | No | Passed |
| docker-network | LXC 107 | sudo | Yes | Passed |
| docker-blue | LXC 108 | sudo | Yes | Passed |
| docker-main | LXC 110 | sudo | Yes | Passed |
| media-01 | LXC 842 | sudo | Yes | Passed after the recorded SSH service recovery |
| alpha-prod-01 | VM 401 | sudo | Yes | Passed |
| app-01 | VM 116 | sudo | No | Passed |
| edge-01 | VM 121 | sudo | No | Passed |
| security-01 | VM 200 | sudo | No | Passed after the effective password-authentication override was removed |
| splunk-siem | VM 109 | wheel | No | Passed through its existing SSH and sudo path because Guest Agent exec is disabled |

Each account reports an active password state. `/home/ansible/.ssh` is mode `0700`, `authorized_keys` is mode `0600`, both are owned by `ansible`, & `/etc/sudoers.d/90-ansible` passes `visudo -cf`.

## SSH Result

- Controller fingerprint: `SHA256:7sgrdr0LDOx+QyFwDZSsOOV7PTrbqFtG9KkK0Rn6qc8`.
- Every target has one key line restricted to source `192.168.40.36` with agent, port, X11, & PTY forwarding disabled.
- Fresh controller login as `ansible` passed before old-key removal on each guest.
- `sudo -n id -u` returned `0` on the controller and every guest.
- Password-only SSH was rejected on the controller and every guest.
- The exact controller key material has zero matches in the former root or `<YOUR_ADMIN_USERNAME>` authorized-keys file on all nine guests.
- Docker access as `ansible` passed on docker-main, docker-network, docker-blue, media-01, & alpha-prod-01.

## Secret Cleanup

I removed each remote console-credential file immediately after its host passed. I shredded the temporary splunk-siem sudo and console files, removed all bootstrap helpers from the Proxmox nodes and guests, then overwrote and deleted the two local secret staging files. Searches of the fixed staging locations returned no remaining file.
