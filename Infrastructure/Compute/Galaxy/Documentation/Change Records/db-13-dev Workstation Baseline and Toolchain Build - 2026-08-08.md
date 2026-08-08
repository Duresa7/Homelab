# db-13-dev Workstation Baseline and Toolchain Build - 2026-08-08

**Created:** 2026-08-08  
**Last updated:** 2026-08-08

**Implementation date:** 2026-08-08  
**Status:** Complete, with two items carried forward  
**Primary owner:** Infrastructure/Compute/Galaxy (VM 102 `db-13-dev`)  
**Affected systems:** VM 102 guest OS, Wazuh manager on `security-01`, Prometheus on `monitor-01`, UniFi policy `Allow Monitor to Personal-A monitoring`, the `wazuh-agent-deployment` and `monitoring-exporters` Ansible projects on `ansible-01`

## Scope

VM 102 became the machine I develop on when I deleted `fedora-dev`, and it had never been baselined. The [Linux Host Baseline Standard](../../../../Security/Hardening/Linux-Host-Baseline-Standard.md) records `debian-dev` as unreachable during the 2026-08-05 fleet sweep, so the gap was known and untracked. This record covers three things: bringing the host up to the baseline, giving it the fleet services every other guest runs, and finishing the toolchains I had installed on it piecemeal.

Nothing here changed another guest. The Wazuh manager gained one group and one agent, Prometheus gained one target, and one UniFi policy gained one destination address.

## Starting state

`ai-agent` was the only real account. `dkadi` was a symlink at `/home/dkadi` pointing at `/home/ai-agent`, with no entry in `/etc/passwd`, and there was no `ansible` account. `NOPASSWD` for `ai-agent` sat on line 56 of `/etc/sudoers` itself, below `@includedir /etc/sudoers.d`, where `/etc/sudoers.d` held only its packaged `README`. `sshd` ran Debian defaults with `PermitRootLogin prohibit-password` and `X11Forwarding yes`, edited into the main config rather than a drop-in, and root carried a password.

The host ran no Wazuh agent, no node_exporter, and no unattended-upgrades. Prometheus was at 51 of 51 targets and the manager at 15 agents, neither of them counting this machine.

Two Node runtimes were installed & which one answered depended on the kind of shell. Debian's `.bashrc` returns early when the shell isn't interactive, and the nvm hook sat inside it, so my terminal got nvm's 24.19.0 while every agent-driven SSH command got apt's 20.19.2 with npm 9.2.0. A build could pass for me and fail for Codex on the same machine.

## Decisions

- **One account, on purpose.** I kept `ai-agent` as the only login rather than splitting into `dkadi`, `ansible`, and `ai-agent`. I sit at this machine and agents work on it in the same session, so a human account would have held a second copy of the same three keys. The cost is real: a stolen human key here is root, because `ai-agent` carries `NOPASSWD`. On a three-account host that key still has to type a password. I wrote the exception into the baseline standard rather than leaving the two to disagree.
- **No `from=` restriction on the keys.** Step 5 of the standard prefixes each key with a source lock. Over the Management VPN a device answers from `10.6.0.0/24` and not from its LAN address, so a source lock would close the path I use from outside the house. Key-only authentication, `AllowUsers ai-agent`, and `PermitRootLogin no` are what limit the account here.
- **One system-wide Node instead of nvm.** Putting 24.19.0 in `/usr/bin` means every shell resolves the same binary, which is the whole point. Per-project version switching is worth less to me than agents and I building against the same runtime.
- **Shared binaries go in `/usr/local/bin`.** A non-login SSH session gets `PATH=/usr/local/bin:/usr/bin:/bin:/usr/games` and reads no startup file. Anything an agent needs over SSH therefore has to live on that path, so Go, its four tools, and every Python linter went there rather than into a home directory. `/etc/profile.d/dev-toolchains.sh` carries only the variables build tools read.
- **The agent is pinned at 4.14.6-1, matching the fleet, not the 4.14.7-1 manager.** Every other agent is held at 4.14.6-1 and an agent must never lead its manager. Enrolling this one at 4.14.7-1 would have made it the only host on a different line for no benefit.
- **`db-13-dev` stays out of the cAdvisor job.** Its containers are throwaway development builds. Per-container history there is noise, and a second listener buys nothing.
- **Prometheus reloaded by signal, not restart.** `POST /-/reload` returned `403` because `--web.enable-lifecycle` isn't set, so `docker kill -s HUP prometheus` picked up the config with no downtime and no container restart.

## Actions and Observed Results

### Baseline

1. I checked what referenced `/home/dkadi` before removing it. Nothing under `/etc`, `/usr/local/etc`, or `/opt` matched. The only hits were Chrome and Codex log files, which record the old path as history and don't resolve it.

   **That check was incomplete, and removing the symlink broke `claude` and `codex`.** I searched file contents for the string. I never searched for symlinks whose *target* names `/home/dkadi`, which is what `find / -xdev -type l -lname "*/home/dkadi*"` returns in one command. Three links resolved through the old path: `~/.local/bin/claude`, `~/.local/bin/codex`, and `~/.codex/packages/standalone/current`. Both installers had written the path they saw at install time, which was the symlink rather than the real directory.

   The symptom is misleading. Bash reports a dangling symlink found on `PATH` as `command not found`, not as a missing file, so it reads like the directory left `PATH` rather than like a broken link. No data was lost: every target existed the whole time under `/home/ai-agent`. I repointed all three at their real paths with `ln -sfn`, and both commands returned their versions, `2.1.226` and `0.147.0`. The same `find` now returns nothing.

   The lesson generalises. Retiring a path that a home directory was once reachable through means checking link targets, not only file contents.
2. I wrote `/etc/sudoers.d/90-ai-agent` as `ai-agent ALL=(ALL:ALL) NOPASSWD: ALL`, root-owned at mode 0440, and `visudo -cf` parsed it. I then built a candidate `/etc/sudoers` with the inline line stripped, diffed it to confirm the change was that one line and nothing else, and validated the candidate before installing it. After install, `visudo -c` passed on all three files, `grep -c "^ai-agent" /etc/sudoers` returned `0`, and `sudo -l -U ai-agent` still reported `(ALL : ALL) NOPASSWD: ALL`.
3. I wrote `/etc/ssh/sshd_config.d/99-hardening.conf` with `PermitRootLogin no`, `PubkeyAuthentication yes`, `PasswordAuthentication no`, `KbdInteractiveAuthentication no`, `X11Forwarding no`, and `AllowUsers ai-agent`. The `Include` sits at line 12 of the main config, above `PermitRootLogin` at line 33, and sshd takes the first value it reads, so the drop-in wins. `sshd -t` passed and `sshd -T` returned all six.
4. I reloaded `ssh` and locked root. `passwd -S root` moved from `P` to `L`.
5. I proved the result from a third machine rather than from the session that made the change. From `ansible-01`, `ssh ai-agent@192.168.40.135` returned `debian-dev` and `ai-agent`, and `ssh root@192.168.40.135` was refused with `Permission denied (publickey)`.
6. I removed the `/home/dkadi` symlink.

### Fleet services

7. I created the `workstation` group on the manager with `agent_groups -a -g workstation`. The manager went from three groups to four: `default`, `edge`, `proxmox`, `workstation`.
8. I added `db-13-dev` to `wazuh-agent-deployment/inventory/hosts.yml` with `ansible_user: ai-agent` and `wazuh_agent_groups: default,workstation`, taking that inventory to 14 hosts, and ran `deploy.yml --limit db-13-dev`. The play finished `ok=22 changed=9 failed=0` and its final assert block passed: package `4.14.6-1`, service enabled and active, a non-empty `client.keys`, and an established TCP 1514 session.
9. `agent_control -l` on the manager then listed the manager plus IDs `004` through `019`, all Active. `db-13-dev` is ID `019` in `default (16)` and `workstation (1)`.
10. I added `db-13-dev` to `monitoring-exporters/inventory/hosts.yml` under `node_exporter_targets` only, and ran `node-exporter.yml --limit db-13-dev`. It reported `os=Debian 13.6 method=apt version=1.9.0 listen=:9100`.
11. TCP 9100 from `monitor-01` timed out at that point, while 1514 and 1515 to the Wazuh manager already worked. `Allow Internal to AlphaSec-Security` covers the whole zone, but `Allow Monitor to Personal-A monitoring` matches named addresses. I added `192.168.40.135` to that policy's destination list through the plugin's preview-then-confirm flow, taking it from four addresses to five. `curl` from `monitor-01` then returned metrics.
12. I appended the target to `prometheus.yml` with `labels: {host: db-13-dev, role: workstation}`, `promtool check config` returned `SUCCESS`, and `docker kill -s HUP prometheus` loaded it. Prometheus went to 52 of 52 targets `up`, with the node job at 19.
13. I installed `unattended-upgrades` and wrote `/etc/apt/apt.conf.d/20auto-upgrades`, which the package doesn't create on its own. Without it the service is enabled but never invoked. `unattended-upgrade --dry-run -v` then ran clean and `apt-daily-upgrade.timer` is armed.

### Toolchains

14. I ran a full `apt-get full-upgrade`, which left `0` packages upgradable, and installed `clang-format`, `clang-tidy`, `clang-tools`, `lld`, `lldb`, `cppcheck`, `bear`, `shfmt`, and `hyperfine`.
15. I removed apt's `nodejs`, `npm`, and `golang-go`, added the NodeSource repository, and installed Node `24.19.0` with npm `11.17.0`. I set the global npm prefix to `/usr/local` in `/usr/etc/npmrc`, so future global installs land on the default `PATH` instead of inside dpkg's tree, and so the existing `mcp-ssh-manager` path stays valid. I then deleted `~/.nvm` and its 24.19.0 tree, and stripped the nvm hook plus a duplicated `~/.local/bin` PATH export from `.bashrc`.
16. I installed Go `1.26.5` from `go.dev` to `/usr/local/go`, verifying `sha256` `5c2c3b16caefa1d968a94c1daca04a7ca301a496d9b086e17ad77bb81393f053` against the published value before extracting, and symlinked `go` and `gofmt` into `/usr/local/bin`. Apt's Go was `1.24.4`.
17. I installed `gopls`, `dlv` `1.27.1`, `staticcheck` `2026.1`, and `golangci-lint` `2.12.2` with `GOBIN=/usr/local/bin`.
18. I installed `ruff` `0.16.2`, `mypy` `2.3.0`, `pre-commit` `4.6.1`, `poetry` `2.4.1`, `ansible-lint` `26.6.0`, `yamllint` `1.38.0`, `ipython` `9.16.1`, and `httpie` with `pipx install --global`, which puts each on `/usr/local/bin`. Python here is externally managed, so `pip3 install` refuses and pipx was installed with nothing in it.
19. Rust was already current at `1.97.1`, but `rust-analyzer` was not actually installed. The shim existed in `~/.cargo/bin`, which is what misled me on the first pass, while `rust-analyzer --version` failed with `Unknown binary 'rust-analyzer' in official toolchain`. `rustup component add rust-analyzer` fixed it.
20. I wrote `/etc/profile.d/dev-toolchains.sh` setting `GOPATH`, `GOBIN`, `JAVA_HOME`, `EDITOR`, and `VISUAL`, with a guarded `PATH` append so re-sourcing can't duplicate an entry. `JAVA_HOME` had never been set, with OpenJDK 21 and Maven 3.9.9 installed.

### Editors

21. I installed VS Code `1.132.0` from Microsoft's APT repository and Neovim `0.12.4` from the upstream GitHub release to `/opt/nvim-linux-x86_64`, symlinked into `/usr/local/bin`.
22. I cloned the LazyVim starter, wrote `lazyvim.json` with 20 extras before the first sync so everything installed in one pass, and ran `Lazy! sync`. It installed 57 plugins.
23. Mason's tool installs were cut off the first two times, because Neovim exited while they were still running. `+MasonInstall` at startup fails outright with `E492: Not an editor command`, since mason is lazy-loaded and the command doesn't exist yet. A Lua script that loads `mason.nvim` first, issues the install, then blocks on `vim.wait` against `mason-registry.is_installed` finished the job. Mason now holds 15 packages.
24. I installed JetBrainsMono Nerd Font, 48 faces, so LazyVim's glyphs render.
25. `checkhealth` on `lazy`, `vim.lsp`, and `vim.treesitter` returned 46 `OK` lines and no `ERROR` or `WARNING`.

### Leftovers

26. I removed `~/.zshrc`, which held a direnv hook for a shell that isn't installed; `~/sda-parttable-backup-2026-08-08.txt`; and `~/.venv`, an empty virtualenv containing only pip.
27. I pointed the `editor` alternative at `/usr/local/bin/nvim`, replacing nano.

## Verification

Read back on 2026-08-08, after every change:

| Check | Result |
|---|---|
| `sshd -T` | `permitrootlogin no`, `pubkeyauthentication yes`, `passwordauthentication no`, `kbdinteractiveauthentication no`, `x11forwarding no`, `allowusers ai-agent` |
| `ssh ai-agent@192.168.40.135` from `ansible-01` | `debian-dev`, `ai-agent` |
| `ssh root@192.168.40.135` from `ansible-01` | `Permission denied (publickey)` |
| `passwd -S root` | `L` |
| `visudo -c` | `/etc/sudoers`, `/etc/sudoers.d/90-ai-agent`, `/etc/sudoers.d/README` all parsed OK |
| `agent_control -l` | manager plus IDs `004` through `019`, all Active |
| `agent_groups -l` | `default (16)`, `edge (1)`, `proxmox (5)`, `workstation (1)` |
| Prometheus `/api/v1/targets` | 52 of 52 up; `db-13-dev` up with `role=workstation` |
| `promtool check config` | SUCCESS |
| `apt list --upgradable` | 0 |
| `unattended-upgrade --dry-run -v` | ran clean; `apt-daily-upgrade.timer` armed |
| `nvim --headless +checkhealth` | 46 OK, no ERROR, no WARNING |
| Non-login SSH `node -v` | `v24.19.0`, matching the login shell for the first time |
| Non-login SSH tool sweep | 27 of 27 binaries resolved: node, npm, go, gofmt, gopls, dlv, staticcheck, golangci-lint, ruff, mypy, pre-commit, poetry, ansible-lint, yamllint, ipython, nvim, code, clang, clang-format, clang-tidy, shellcheck, shfmt, cppcheck, bear, docker, gh, git |

## What I did not do

- **I did not checksum-verify the Neovim tarball.** The release publishes no checksum asset at either conventional path: `shasum256.txt` and `nvim-linux-x86_64.tar.gz.sha256sum` both returned `404`. The download came over HTTPS from the GitHub release, and I re-downloaded and re-extracted once to confirm the tree came from that artifact. Go, by contrast, was verified against its published `sha256` before extraction.
- **I did not get a real `delve` package into Mason.** `mason-registry.is_installed("delve")` returns true, but no `packages/delve` directory exists. I stopped chasing it because `dlv` `1.27.1` is on `/usr/local/bin` and `nvim-dap-go` takes `dlv` from `PATH`, so Go debugging works. The Mason entry would be a duplicate.
- **I did not confirm the GitHub signing key.** The `gh` token carries `gist`, `read:org`, `repo`, and `workflow`, and listing signing keys needs `admin:ssh_signing_key`, so `gh api /user/ssh_signing_keys` returned `404`. The key was added through the web UI, and I have no way to read that back from here.
- **I did not register the `db-13-dev` identity in `ssh-key-automation`.** That remains open in the [Ansible TODO](../../../../Platforms/Ansible/Documentation/TODO.md). The key works on every reachable host; the project simply doesn't know the identity exists, so `ssh-key-audit.yml` won't report on it.

## Related records

- [Linux Host Baseline Standard](../../../../Security/Hardening/Linux-Host-Baseline-Standard.md), which now names this host's single-account exception. Not published.
- [Galaxy VM inventory](../../../../Operations/Inventory/Galaxy/VMs.md) and [service inventory](../../../../Operations/Inventory/Galaxy/Services.md).
- [Wazuh configuration reference](../../../../Platforms/Wazuh/Configuration/README.md) for the new group and agent `019`.
- [UniFi firewall policies](../../../Network/UniFi/Configuration/firewall.md) for the monitoring destination change.
