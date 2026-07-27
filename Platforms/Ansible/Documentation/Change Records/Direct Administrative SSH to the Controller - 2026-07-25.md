# Direct Administrative SSH to the Controller

**Created:** 2026-07-25  
**Last updated:** 2026-07-25

**Implementation date:** 2026-07-25  
**Systems:** `ansible-01` LXC 100, `192.168.40.36`  
**Status:** Complete

## Scope

I added my two workstation keys to `ansible-01`, so I reach the controller over TCP 22 instead of routing every command through `pct exec 100` on grey-server. I changed nothing about the controller's outbound automation, its inventory, Semaphore, or sudo.

## Starting State

`/home/ansible/.ssh/authorized_keys` held exactly one line, `SHA256:7sgrdr0LDOx+QyFwDZSsOOV7PTrbqFtG9KkK0Rn6qc8`, comment `ansible-control`. That's the controller's own public key, the same fingerprint as `/home/ansible/.ssh/id_ed25519.pub`, so the only trusted key was the outbound fleet key looping back.

`/root/.ssh/authorized_keys` didn't exist, & sshd runs `PermitRootLogin prohibit-password` with `PasswordAuthentication no`. No human key could authenticate. `~/.ssh/config` on jedi-pc already carried an `ansible-01` block pointing at `192.168.40.36` as user `ansible`, so the client half had been set up for a key that was never installed.

## Actions and Results

| Step | Action | Observed result |
|---|---|---|
| S01 | Read the two admin keys out of grey-server's `/root/.ssh/authorized_keys` by comment | Matched 2 lines, `jedi-pc` & `mac-air3-<YOUR_ADMIN_USERNAME>` |
| S02 | Appended both to `/home/ansible/.ssh/authorized_keys` with a duplicate check, then reset owner to `ansible:ansible` & mode to `0600` | File is 367 bytes holding 3 keys: `ansible-control`, `mac-air3-<YOUR_ADMIN_USERNAME>`, `jedi-pc` |
| S03 | Logged in from jedi-pc with `ssh -o BatchMode=yes ansible-01` | Returned `ansible-01`, `ansible`, & `ansible [core 2.21.2]` |

I copied `authorized_keys` to a `.bak` file before editing & removed that copy before running S03, so the login test ran against the only remaining copy. `ls -a /home/ansible/.ssh/` now matches on nothing containing `bak`, `tmp`, or `admin-keys`, & the staging file `/tmp/admin-keys.pub` is gone from both grey-server & the container.

## Post-Change Verification

`ssh -v` from jedi-pc reports `Server accepts key: SHA256:pcjlugUJER60YblfoAOfzZYKHJ1pHVTeqGm7Vwquj/4` & `Authenticated to 192.168.40.36 ([192.168.40.36]:22) using "publickey"`. The `mac-air3-<YOUR_ADMIN_USERNAME>` line carries `SHA256:QyNF8ipQ5F/1KV69opH2QHuVVclpfNnZFGhDYZL38rM`, the same fingerprint that line has in grey-server's `/root/.ssh/authorized_keys`. I haven't logged in from the Mac itself.

The file is 3 lines & 367 bytes with 0 duplicate key bodies. Line 1 still carries `from="192.168.40.36",no-agent-forwarding,no-port-forwarding,no-X11-forwarding,no-pty`; my two lines carry no options. Directory mode is `0700` & the file is `0600`, both owned `ansible:ansible`.

`sudo -n true` succeeds over the new SSH session, so either workstation key now reaches root on the controller through `/etc/sudoers.d/90-ansible` without a password prompt.

Outbound automation is unaffected. The controller's own key still authenticates to `ansible@192.168.40.36`, & `ansible all -m ping` returns `pong` from all 13 running targets: the four Proxmox nodes plus docker-main, docker-network, docker-blue, media-01, alpha-prod-01, app-01, edge-01, security-01, & splunk-siem. Five inventory hosts returned UNREACHABLE, every one of them powered off or absent before this change. Four are stopped guests on grey-server: supabase-01 (VM 117), ai-bravo-02 (LXC 105), ws-dc-1 (VM 300), & ws-dc-2 (VM 301). The fifth, obi-pc at 192.168.65.102, is a physical workstation, not a guest; it answers no ICMP from grey-server or purple-server. 192.168.65.10 also times out on TCP 22 from jedi-pc, which matches ws-dc-1 being stopped rather than a VLAN 65 routing fault.

## Deviation From the Account Rollout

Decision 5 of the [dedicated account rollout](Dedicated%20Ansible%20Account%20and%20Fleet%20Expansion%20-%202026-07-25.md) keeps human identities out of `/home/ansible/.ssh/authorized_keys` & resolves them to root or administrative-user files instead. The controller can't honor that rule as built: `ansible` (UID 1000) is its only non-system account, it's the only member of group `sudo`, & `/home` holds no other directory. Putting my keys anywhere else meant creating a second account first.

Two consequences follow. My keys sit in the same file as the automation key, so a future identity audit that treats that file as machine-only will flag them. The controller key carries `from="192.168.40.36"` plus no-agent-forwarding, no-port-forwarding, no-X11, & no-PTY restrictions; my two lines carry none of those, because a restricted line can't open an interactive shell.

## Rollback

Remove the `jedi-pc` & `mac-air3-<YOUR_ADMIN_USERNAME>` lines from `/home/ansible/.ssh/authorized_keys` through `pct exec 100` on grey-server. The `ansible-control` line must stay: deleting it breaks the controller's own loopback identity. Access reverts to `pct exec`, which never depended on this change.
