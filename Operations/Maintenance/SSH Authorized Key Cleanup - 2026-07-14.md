# SSH Authorized Key Cleanup

**Created:** 2026-07-14  
**Last updated:** 2026-07-18

**Change date:** 2026-07-14  
**Status:** Complete with two unreachable Windows targets  
**Scope:** SSH authorized-key cleanup, three-key fleet baseline, private-key custody for `K05` and `K07` through `K10`, and reachability retest

## Outcome

I removed two explicitly identified ED25519 keys from every readable authorized-key scope where they existed, then rescanned all 15 reachable targets and found zero remaining matches. I imported the dedicated Termix ED25519 identity `K05` and the four Proxmox RSA identities `K07` through `K10` into 1Password as SSH Key items after matching their private halves to the known public fingerprints.

I recorded the resulting machine-to-key mapping and the complete public keys in a separate working inventory.

## Three-Key Fleet Baseline

I normalized all 15 inspectable SSH Manager targets to contain exactly one copy of each approved ED25519 identity: `mac-air3-REDACTED_USER_001`, `ansible-control`, and `jedi-pc`. The `jedi-pc` key blob and fingerprint did not change; only its comment changed from the previous label. `supabase_01` was the only target missing `mac-air3-REDACTED_USER_001`, so I added that line.

I updated the four Proxmox nodes once through `/etc/pve/priv/authorized_keys`, then verified the result independently on every node. Linux files passed `ssh-keygen` validation with mode `0600`; the Windows administrator key file retained its ACL. My follow-up SSH commands confirmed access to every changed target. The two unreachable Windows systems remain Unknown; I did not change them.

The live Ansible distribution playbook in LXC 100, the Linux host baseline, and both Windows SSH bootstrap scripts now carry the same three exact lines. The Ansible playbook passed `ansible-playbook --syntax-check` under the container's available UTF-8 locale.

## Authorized-Key Changes

| Key | Fingerprint | Removed from | Authorized-key path | Observed result |
|---|---|---|---|---|
| `REDACTED_SSH_KEY_LABEL_001` | `REDACTED_SSH_FINGERPRINT_002` | `docker_main` / `root` | `/root/.ssh/authorized_keys` | One exact match removed; zero remained |
| `REDACTED_SSH_KEY_LABEL_002` | `REDACTED_SSH_FINGERPRINT_008` | `alpha_prod_01` / `REDACTED_USER_001` | `/home/REDACTED_USER_001/.ssh/authorized_keys` | One exact match removed; zero remained |

I replaced each file atomically, confirmed it still parsed as valid SSH public-key syntax, and rescanned it after the change. My follow-up SSH commands succeeded on both changed hosts, confirming that management access remained available.

## Verification Coverage

- Complete host-wide standard-path coverage: `grey_server`, `purple_server`, `blue_server`, `red_server`, `docker_main`, `docker_network`, and `ws_dc_1_main`.
- Connected-account coverage: `alpha_prod_01`, `app_01`, `supabase_01`, `ai_alpha_01`, `REDACTED_OPERATIONAL_HOST`, `edge_01`, `security_01`, and `splunk_siem`.
- Both removed key blobs returned zero matches in all 15 readable scopes.
- I kept Kali Pen explicitly out of scope.

Connected-account coverage does not prove the absence of keys in protected accounts or nonstandard `AuthorizedKeysFile` locations that the configured account cannot read.

## 1Password Custody

| Key | Verified fingerprint | 1Password item | Result |
|---|---|---|---|
| `K05` | `REDACTED_SSH_FINGERPRINT_010` | `REDACTED_1PASSWORD_ITEM_TITLE_004` | Imported as `SSH_KEY` |
| `K07` | `REDACTED_SSH_FINGERPRINT_009` | `REDACTED_1PASSWORD_ITEM_TITLE_005` | Imported as `SSH_KEY` |
| `K08` | `REDACTED_SSH_FINGERPRINT_005` | `REDACTED_1PASSWORD_ITEM_TITLE_006` | Imported as `SSH_KEY` |
| `K09` | `REDACTED_SSH_FINGERPRINT_006` | `REDACTED_1PASSWORD_ITEM_TITLE_007` | Imported as `SSH_KEY` |
| `K10` | `REDACTED_SSH_FINGERPRINT_007` | `REDACTED_1PASSWORD_ITEM_TITLE_008` | Imported as `SSH_KEY` |

I staged the private keys only in protected operating-system temporary directories, with inherited ACLs removed and access limited to my user account. I matched each source fingerprint before import. The 1Password SDK generated the public-key, fingerprint, and key-type fields from each imported private key; I then verified all five items active in the `REDACTED_1PASSWORD_VAULT` vault with the expected fingerprints and archived the incomplete CLI-created `K05` item. I overwrote the local staging files before removing them, shredded or removed both temporary `K05` copies on `docker_main` and inside the Termix container, and verified both absent. No private-key material was written to the workspace or this record.

## Windows Retest

| Target | Account | Result |
|---|---|---|
| `ws_dc_2_secondary` | `Administrator` | Connection reset during the SSH handshake |
| `obi_pc` | `REDACTED_USER_003` | Timed out connecting to TCP/22 |

Neither Windows target exposed an authorized-key file during this retest, so both remain Unknown in the inventory.
