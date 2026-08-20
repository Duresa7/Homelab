# SSH Manager Sudo Password on Ten Guests

**Created:** 2026-08-20  
**Last updated:** 2026-08-20

**Change date:** 2026-08-20  
**Status:** Complete. `ssh_execute_sudo` reaches root on all eleven guests, `ssh_execute` still works on all eleven, and the credential exists in exactly one file  
**Scope:** Ten `SUDO_PASSWORD` entries in the SSH Manager MCP's env file on `ubuntu-dev`. No remote host was touched: no sudoers file, no account password, no key, no sshd setting. The five Proxmox nodes, `docker-main` and `ansible-01` have no entry on purpose

## Outcome

The SSH Manager can now answer a sudo prompt on the guests where `dkadi` has to authenticate. Before this, it could not: all seventeen server entries were key-only and carried no password of any kind, so `ssh_execute_sudo` worked only where `dkadi` still held a `NOPASSWD` drop-in. `Defaults rootpw` went on all eleven guests on 2026-08-20, so the prompt asks for root's password, and root's password is what the ten entries hold.

| Hosts | SSH Manager connects as | `sudo` before | `sudo` now | What answers the prompt |
| --- | --- | --- | --- | --- |
| `alpha-prod-01`, `app-01`, `edge-01`, `security-01`, `splunk-siem`, `docker-blue` | `dkadi` | fails, password required | reaches root | the configured entry |
| `docker-network`, `monitor-01`, `media-01`, `game-01` | `dkadi` | reaches root | reaches root | the `NOPASSWD` drop-in today, the configured entry once ticket 17 removes it |
| `ansible-01` | `ansible` | reaches root | reaches root | `NOPASSWD`, which that account keeps permanently |

This is the step that had to land before the four remaining `dkadi` drop-ins come off. Removing them first would have left privileged tooling with no path on any host at once.

## The env file the server actually reads

The plan for this work named `~/.ssh-manager/.env`, which is where the SSH Manager CLI writes and the second candidate in the server's own fallback chain. That is not the file the running server reads. The MCP registration sets `SSH_ENV_PATH`, which is the first candidate and overrides the rest, and it points at `~/.claude/ssh-manager.env`.

The two files disagree. The one the server reads holds seventeen servers and was last written on 2026-08-20. The CLI default holds twenty, still lists `kasm-01` and `supabase-01`, both retired, plus a `ubuntu-dev` entry, and was last written on 2026-08-14.

I wrote the ten entries to the file the server reads and left the stale one alone. Putting root's fleet password into a second file that nothing loads would widen the exposure and buy nothing. Anyone acting on this file later should read `SSH_ENV_PATH` out of the MCP registration rather than assuming the CLI default, which is `src/index.js`'s `resolveEnvFilePath()` in `mcp-ssh-manager`.

## State before the change

Read through the SSH Manager itself, between 8:20 and 8:30 AM:

- `ssh_list_servers` returned seventeen servers: the eleven guests, the five Proxmox nodes and `docker-main`. `ubuntu-dev` is not registered at all, which makes the plan's instruction to skip it moot rather than something to be careful about.
- Zero `SUDO_PASSWORD` keys in the file, and zero `PASSWORD` keys. Every entry was `HOST`, `USER`, `PORT`, `KEYPATH`, `PLATFORM` and `DESCRIPTION`, with a `PROXYJUMP` on `monitor-01`.
- Mode `0600`, owned by `ai-agent`.
- `ssh_execute_sudo` running `id -un` failed on `app-01`, `edge-01`, `security-01`, `splunk-siem` and `docker-blue` with `sudo: a password is required`, and returned `root` on `docker-network`, `monitor-01` and `media-01`. `alpha-prod-01` and `game-01` were not captured before the change; both were expected to match their group and both did after it.

## What I changed

Ten lines, one per host, of the form the loader expects:

```text
SSH_SERVER_<NAME>_SUDO_PASSWORD="<root password>"
```

Each went at the end of the server's existing block. The file gained a two-line comment under its header saying what the entries hold and why, because a bare password entry gives a later reader nothing to check the value against, and root's password is not the value a reader would guess a sudo entry holds.

The write went through a script that read the value on stdin, refused to run if it held a character unsafe for the quoting style, wrote to a temporary file in the same directory at mode `0600`, and moved it into place with `os.replace`. So there was no window where the file was truncated or world-readable, and no version of it on disk carrying a partial write.

**No restart was needed.** `ServerConfigManager.getServers()` compares the env file's modification time and size on every tool call and reloads when they differ, so the first `ssh_execute_sudo` after the write already had the entries. I confirmed that by using them without touching the MCP server.

## Why `ansible-01` has no entry

The plan said all eleven guests connect as `dkadi` and all eleven need an entry. That is wrong for `ansible-01`: the SSH Manager connects there as `ansible`, and `ansible` keeps `NOPASSWD` on all eleven by design, so it never sees a sudo prompt. It is the same exclusion the plan already applies to the five nodes and `docker-main`, for the same stated reason, and I owned it with the owner before writing the file.

There is a second reason not to configure a password where the account is `NOPASSWD`. The tool builds the elevated call as `echo "<password>" | sudo -S <command>`, and sudo reads stdin only when it actually needs to prompt. Where it does not prompt, the line is left on the child's stdin. Proved locally on `ubuntu-dev`, where `ai-agent` holds `NOPASSWD`:

```console
$ printf 'STDIN-PROBE-LINE\n' | sudo -S /bin/cat
STDIN-PROBE-LINE
```

So on a `NOPASSWD` host the password is handed to whatever command runs, and any command that echoes its stdin prints it. The tool masks the command it reports, not the output it returns. `ansible-01` would be in that state permanently. The four `dkadi` hosts that still hold drop-ins are in it too, and ticket 17 ends that when it removes them.

## Verification

Run between 9:14 and 9:22 AM, after the 9:13 AM write.

**`ssh_execute_sudo` running `id -un` returns `root`, exit code 0, on 11 of 11 guests.** Six of those are hosts where `dkadi` holds no `NOPASSWD` drop-in, and five of the six are hosts I watched the same call fail on an hour earlier. That is the proof the ticket asked for: the password path works and does not depend on the drop-ins ticket 17 removes. The sixth is `alpha-prod-01`, where I hold no pre-change capture of my own; it has no drop-in and `dkadi` was proven to authenticate there earlier the same day, so it belongs in the group either way.

```text
alpha-prod-01 root   app-01 root      edge-01 root        security-01 root
splunk-siem   root   docker-blue root docker-network root monitor-01  root
media-01      root   game-01 root     ansible-01 root
```

**`ssh_execute` without sudo still works on 11 of 11.** Each returned its own hostname and the expected login account, `dkadi` on ten and `ansible` on `ansible-01`. `security-01` answers to `wazuh-01`, which is the known host-versus-record deviation from 2026-08-15 and not something this change caused.

**The returned output masks the password.** The tool reports `Command: sudo id -un` where it actually ran `echo "..." | sudo -S id -un`. Worth knowing exactly how far that goes: the mask is a regular expression over the reported command line only, so it hides the credential in the command echo and does nothing to stdout or stderr. It is not a general guarantee that the value cannot appear in a result.

**The value in the file is the value in the credential item.** I parsed the file with the same `dotenv` release the server loads and compared a SHA-256 of each parsed entry against a SHA-256 of the field read straight out of the item: ten keys parsed, ten matching, and seventeen servers still parsing. Neither value was printed.

**Nothing else in the file changed.** A diff of the file against a copy taken before the write, with the added lines filtered out, is empty.

**Mode is still `0600`**, owned by `ai-agent`, 6270 bytes, 153 lines.

**The credential exists in exactly one file.** I scanned for the literal value across the SSH Manager's own log and command history, the CLI default env file, the shell history, this repository's two log files, both staging files, all 80 MCP transport logs for this server and all 11 session transcripts for this project, 101 files in total. One hit, which is the env file itself. The SSH Manager's log and history came back clean because `logger.logCommand` is wired into `ssh_execute` only; `ssh_execute_sudo` writes neither, which is what the source says and what the files confirm.

## How the credential was handled

The value never appeared in a command string, an argument, a log, a shell history or this repository. It was read with a secret reference and piped into the process that wrote it, so the only places it existed were the pipe and the destination file. Both staging scripts are gone, along with the pre-change copy of the env file.

Before writing, I checked without printing anything that the field came back non-empty and that it is byte-identical to the duplicate field the last ticket of this effort deletes. That matters here for one reason: reading the durable field rather than the duplicate means this entry does not point at a name that is scheduled to stop existing. Which fields those are stays in the unpublished [Linux Host Baseline Standard](../../Security/Hardening/Linux-Host-Baseline-Standard.md).

## What this weakens

**Root's password for the whole guest fleet now sits in plaintext in a file on `ubuntu-dev`.** That was accepted deliberately on 2026-08-15 so that privileged tooling keeps working, and it is the one thing in this effort that trades security away rather than adding it. The file is mode `0600` and owned by `ai-agent`, so it is readable by that account and by root on that host, and any process running as `ai-agent` can read it.

**The password crosses the wire inside the command.** `echo "<password>" | sudo -S` means the value is part of the command string sent over SSH and part of the remote shell's argument list for as long as the command runs, so it is visible to anything on the target that can read `/proc` for that instant. It is not written to a file on the target and not recorded in the remote shell history, because a non-interactive `ssh` exec keeps none.

**Two of those facts get worse before they get better.** Until ticket 17 removes the four `dkadi` drop-ins, `ssh_execute_sudo` on `docker-network`, `monitor-01`, `media-01` and `game-01` hands root's password to the command's stdin, where any command that reads stdin can see it. That is a consequence of doing this step before 17 rather than after, which was the right order for a different reason.

## Left open

**The stale env file on `ubuntu-dev`.** `~/.ssh-manager/.env` still lists twenty servers, including the retired `kasm-01` and `supabase-01`, and holds no sudo passwords. Nothing loads it while `SSH_ENV_PATH` is set. If that variable is ever dropped from the MCP registration, the server silently falls back to it and privileged access disappears at the same moment two dead hosts reappear in the inventory. Either reconcile it or delete it.

**`ai-agent` still has no sudo grant on ten of the eleven guests**, so the SSH Manager's path to root on those hosts is `dkadi` and nothing else. That gap belongs to the verification ticket, not to this one.

**Ticket 17 is unblocked.** The password path is proven on six hosts that have no drop-in, so removing the remaining four cannot leave privileged tooling without a route.
