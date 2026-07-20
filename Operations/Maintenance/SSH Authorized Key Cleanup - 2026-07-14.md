# SSH Authorized Key Cleanup

**Created:** 2026-07-14  
**Last updated:** 2026-07-20

**Change date:** 2026-07-14  
**Status:** Complete with two unreachable Windows targets  
**Scope:** SSH authorized-key cleanup, three-key fleet baseline, fingerprint verification for `K05` and `K07` through `K10`, and reachability retest

## Outcome

I removed two identified ED25519 keys from every readable authorized-key scope where they existed, then rescanned all 15 reachable targets and found zero remaining matches. I matched the private and public halves of Termix identity `K05` and Proxmox identities `K07` through `K10` against their known fingerprints.

I recorded the resulting machine-to-key mapping and the complete public keys in a separate working inventory.

## Three-Key Fleet Baseline

I normalized all 15 inspectable SSH Manager targets to contain exactly one copy of each approved ED25519 identity: `mac-air3-<YOUR_ADMIN_USERNAME>`, `ansible-control`, and `jedi-pc`. The `jedi-pc` key blob and fingerprint did not change; only its comment changed from the previous label. `supabase_01` was the only target missing `mac-air3-<YOUR_ADMIN_USERNAME>`, so I added that line.

I updated the four Proxmox nodes once through `/etc/pve/priv/authorized_keys`, then verified the result independently on every node. Linux files passed `ssh-keygen` validation with mode `0600`; the Windows administrator key file retained its ACL. My follow-up SSH commands confirmed access to every changed target. The two unreachable Windows systems remain Unknown; I did not change them.

The live Ansible distribution playbook in LXC 100, the Linux host baseline, and both Windows SSH bootstrap scripts now carry the same three exact lines. The Ansible playbook passed `ansible-playbook --syntax-check` under the container's available UTF-8 locale.

## Authorized-Key Changes

| Key | Fingerprint | Removed from | Authorized-key path | Observed result |
|---|---|---|---|---|
| `<RETIRED_ROOT_KEY_LABEL>` | `<RETIRED_ROOT_KEY_FINGERPRINT>` | `docker_main` / `root` | `/root/.ssh/authorized_keys` | One exact match removed; zero remained |
| `<RETIRED_USER_KEY_LABEL>` | `<RETIRED_USER_KEY_FINGERPRINT>` | `alpha_prod_01` / `<YOUR_ADMIN_USERNAME>` | `/home/<YOUR_ADMIN_USERNAME>/.ssh/authorized_keys` | One exact match removed; zero remained |

I replaced each file atomically, confirmed it still parsed as valid SSH public-key syntax, and rescanned it after the change. My follow-up SSH commands succeeded on both changed hosts, confirming that management access remained available.

## Verification Coverage

- Complete host-wide standard-path coverage: `grey_server`, `purple_server`, `blue_server`, `red_server`, `docker_main`, `docker_network`, and `ws_dc_1_main`.
- Connected-account coverage: `alpha_prod_01`, `app_01`, `supabase_01`, `ai_alpha_01`, `<YOUR_TNIO_HOST>`, `edge_01`, `security_01`, and `splunk_siem`.
- Both removed key blobs returned zero matches in all 15 readable scopes.
- I kept Kali Pen explicitly out of scope.

Connected-account coverage does not prove the absence of keys in protected accounts or nonstandard `AuthorizedKeysFile` locations that the configured account cannot read.

## Retained Identity Verification

| Key | Verified fingerprint | Result |
|---|---|---|
| `K05` | `<K05_FINGERPRINT>` | Private and public halves matched |
| `K07` | `<K07_FINGERPRINT>` | Private and public halves matched |
| `K08` | `<K08_FINGERPRINT>` | Private and public halves matched |
| `K09` | `<K09_FINGERPRINT>` | Private and public halves matched |
| `K10` | `<K10_FINGERPRINT>` | Private and public halves matched |

## Windows Retest

| Target | Account | Result |
|---|---|---|
| `ws_dc_2_secondary` | `Administrator` | Connection reset during the SSH handshake |
| `obi_pc` | `<YOUR_REMOTE_USERNAME>` | Timed out connecting to TCP/22 |

Neither Windows target exposed an authorized-key file during this retest, so both remain Unknown in the inventory.
