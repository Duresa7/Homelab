# Node Root Password Reset - 2026-08-15

**Created:** 2026-08-15  
**Last updated:** 2026-09-25

**Implementation date:** 2026-08-15  
**Status:** Complete  
**Primary owner:** Infrastructure/Compute/Galaxy (node accounts)  
**Affected systems:** `root` on grey-server, purple-server, blue-server, red-server, green-server. No guest, no cluster file, no firewall, no sshd configuration

## Scope

I set `root`'s password on all five nodes to one known value taken from the credential entry that governs the nodes, and renamed that entry so it names the cluster instead of grey-server. The five nodes sit outside the Linux Server Standard that covers the guests, and this is the credential that replaces it for them.

The password is for the web interface at `:8006` and for the physical or IPMI console. It is not an SSH credential: `passwordauthentication` is `no` on all five nodes and stayed that way. Root SSH to the nodes remains key-only.

## Why

Every node already had a usable root password, but five different ones, none of them recorded. `passwd -S root` read `P` on all five with last-change dates spread across a year:

| Node | Last password change before this work |
|---|---|
| grey-server | 2025-08-23 |
| purple-server | 2026-05-27 |
| blue-server | 2026-05-27 |
| red-server | 2026-07-07 |
| green-server | 2026-07-31 |

A console credential nobody can look up is a credential that does not exist at the moment it is needed, which is a node that will not boot far enough to accept an SSH key.

The rename matters for the same reason. The entry was titled after grey-server while governing all five, and a title naming one node sends the next reader to the conclusion that the other four are covered somewhere else. Its `username: root` field and its `https://192.168.70.10:8006` URL are unchanged, since that address is still where I sign in.

## How the value was handled

The password never appeared in a command string, an argument, an inventory, or a log, on either end.

1. I read it from the credential store into a local file created under `umask 077`, by command substitution, so no process ever carried it in `argv`.
2. I transferred that file to each node over SFTP as `/root/.pw.stage` and set it to mode `0600`.
3. On each node I built the `chpasswd` input by concatenation and piped it in on stdin: `{ printf 'root:'; cat /root/.pw.stage; printf '\n'; } | chpasswd`.
4. I tested the result against the node's own PAM stack through the same API endpoint the web interface logs in with, passing the value from the file rather than from the command line: `curl -sk -d 'username=root@pam' --data-urlencode "password@/root/.pw.stage" https://127.0.0.1:8006/api2/json/access/ticket`.
5. I ran `shred -u` on the staged file on each node in the same command, and on the local copy afterwards.

Step 4 is what makes this record more than a claim that a command was issued. A `200` from `/access/ticket` means PAM accepted `root@pam` with the value now stored in the credential entry, which is the web interface login I set out to prove.

## Verification

All five checks below ran after the change, over key-based SSH, which is itself the proof that key login still works on every node.

| Check | grey | purple | blue | red | green |
|---|---|---|---|---|---|
| `chpasswd` exit code | 0 | 0 | 0 | 0 | 0 |
| `passwd -S root` | `P 2026-08-15` | `P 2026-08-15` | `P 2026-08-15` | `P 2026-08-15` | `P 2026-08-15` |
| `root@pam` login to `/access/ticket` | 200 | 200 | 200 | 200 | 200 |
| `sshd -T` `passwordauthentication` | no | no | no | no | no |
| Staged file removed | yes | yes | yes | yes | yes |

`pvecm status` on grey-server after the change: Quorate, 5 total votes. Nothing in this work touches Corosync, and the check is there to confirm that.

## Open

`permitrootlogin` is `yes` on purple-server and blue-server, against `without-password` on grey, red and green. Setting a root password does not create an exposure there while `passwordauthentication` is `no`, because the two nodes still accept keys only. Bringing those two into line with the other three is separate work and is not done here.

## Rollback

There is none worth writing. The previous passwords were five unrecorded values, so reverting would mean setting five new unknown ones. If this value has to change, it changes in the credential entry first and then on the nodes by the same five steps above.
