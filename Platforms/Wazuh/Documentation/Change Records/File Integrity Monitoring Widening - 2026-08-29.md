# File Integrity Monitoring Widening

**Created:** 2026-08-29  
**Last updated:** 2026-08-31

## Date

I started this change on 2026-08-29 and finished it on 2026-08-30.

## Scope

I gave the `workstation` and `edge` agent groups real file-integrity configuration, then corrected both the `workstation` and `default` groups after the first version buried every real alert under noise. I also gave the `proxmox` group its first configuration.

This is one of four changes behind the Wazuh dashboard in Splunk. The others are [Alert Forwarding to Splunk](Alert%20Forwarding%20to%20Splunk%20-%202026-08-29.md), [Malware Detection](Malware%20Detection%20-%202026-08-29.md) and [Wazuh Insights App](../../../Splunk/Enterprise/Documentation/Change%20Records/Wazuh%20Insights%20App%20-%202026-08-29.md).

The four together are written up as one followable path in [Wazuh Alerts in Splunk](../../../../Guides/Wazuh-Alerts-in-Splunk.md), which is the guide a reader outside this lab would start from.

Phase one covers two machines: `ubuntu-dev`, agent 020, the workstation I sit at, and `edge-01`, agent 005, the only host reachable from the Internet. The other 14 agents keep the `default` group, which I also changed, so the rootcheck part of this record applies to all of them.

All four group configurations are committed at [Configuration/Agent Groups](../../Configuration/Agent%20Groups/).

## What each group watches

**`workstation`,** on `ubuntu-dev`. This is the one machine where a file arrives because a person chose to download it, so it is the first place to widen and the place a VirusTotal lookup has something to look up.

- `/home/ai-agent/Downloads`, realtime, with `report_changes`
- `/tmp` and `/var/tmp`, realtime, restricted by filename
- `/usr/local/bin` and `/opt`, realtime, with `report_changes`, since nothing else audits binaries installed outside the package manager
- `/home/ai-agent/.ssh`, realtime, with `report_changes`
- `/home/ai-agent/.config/systemd/user` and `/etc/systemd/system`, because a user-level timer survives a reboot the same as a root one

**`edge`,** on `edge-01`: `/etc/cloudflared`, `/etc/caddy`, `/tmp`, `/var/tmp`, `/usr/local/bin`, `/home/dkadi/.ssh` and `/etc/systemd/system`.

**`proxmox`,** on the five nodes: no new watches, only ignores. Explained below.

**`default`,** on all 16: unchanged watches, plus the rootcheck correction. Explained below.

## The correction that made this usable

The first version watched all of `/tmp` on the workstation. In one day that produced **2,334 alerts from a single scratch directory**, and the file-integrity feed looked like this:

| Directory | Alerts | What it is |
|---|---|---|
| `/tmp/executor-research.<random>` | 2,334 | Tooling working directory |
| `/tmp/scoped_dir<random>` | 124 | Browser scratch |
| `/tmp/<reverse-dns>.<random>` | 60 | Desktop application session state |
| `/etc/lvm` on `grey-server` | 198 | A real change, from my own LVM work |
| `/etc/pve` across five nodes | 133 | Proxmox cluster state |

Roughly 97 per cent of it was the machine describing its own housekeeping. That was not merely untidy. Every one of those files was submitted to VirusTotal, and the integration answered **2,697 of those lookups with "Public API request rate limit reached"**. The noise consumed the daily quota, so the one thing the group exists to catch would have been refused a verdict. A monitor that disables the detection it feeds is worse than no monitor.

`/tmp` is still watched, because a payload dropped into world-writable space is a real case. It is now restricted by filename:

```xml
<directories check_all="yes" realtime="yes"
  restrict="\.sh$|\.bash$|\.py$|\.pl$|\.rb$|\.php$|\.elf$|\.bin$|\.run$|\.out$|\.so$|\.ko$|\.exe$|\.dll$|\.ps1$|\.jar$|\.deb$|\.rpm$|\.appimage$|\.zip$|\.tar$|\.tgz$|\.gz$|\.bz2$|\.xz$|\.7z$|\.rar$|\.iso$">/tmp</directories>
```

A script, an executable, an archive or a package is worth a hash and a lookup. A browser's cookie file is not.

The ignore list alongside it matches by shape rather than by product, including reverse-DNS scratch directories, which desktop applications name after their own bundle identifier. Matching the shape stops the list becoming something I have to maintain per application, and keeps a vendor's name out of an alert that ends up in a screenshot.

## Two groups I corrected for the same reason

**`proxmox` had no configuration at all,** so `/etc/pve` was being watched by Wazuh's stock `/etc` rule. On a Proxmox node `/etc/pve` is not an ordinary directory: it is pmxcfs, a FUSE filesystem backed by the cluster database, and the cluster rewrites its status files every few seconds. Each of `.rrd`, `.version`, `ha/crm_commands`, `ha/manager_status` and each node's `lrm_status` was reporting **533 changes**. Five nodes doing that produced 5,570 alerts of nothing.

The group now ignores the parts of `/etc/pve` that are state and leaves watched the parts that are configuration: `corosync.conf`, `storage.cfg`, `user.cfg`, the firewall rules and the guest definitions. It also ignores `/etc/pve/priv/authkey.key`, which Proxmox rotates on a schedule.

**`default` now turns off rootcheck's trojan check fleet-wide.** It works by grepping system binaries for strings a trojaned copy might contain, and on Debian the ordinary setuid binaries contain them:

| File | Alerts |
|---|---|
| `/bin/chfn` | 1,046 |
| `/bin/chsh` | 1,043 |
| `/bin/passwd` | 1,040 |
| `/usr/bin/chsh` | 1,039 |
| `/usr/bin/passwd` | 1,039 |
| `/usr/bin/chfn` | 1,029 |

Over 22,000 "Trojaned version of file detected" alerts, and **not one of them was a real finding**. A check with a hundred per cent false-positive rate is worse than no check, because it is the noise every real alert has to be found inside.

Nothing is left uncovered. A modified system binary still shows as a file-integrity change, and a file that is actually malicious is caught by its hash, locally or through VirusTotal. Those look at what the file is rather than guessing from a string match. `check_dev` stays on, because a file hidden under `/dev` is a real technique, with `/dev/.lxc` ignored since it exists inside every LXC container.

## Verification

**Every configuration was validated before and after it was installed.** Locally with an XML parse, on the manager against the staged file in `/tmp` before `install`, and then with `verify-agent-conf`:

```console
# /var/ossec/bin/verify-agent-conf
verify-agent-conf: Verifying [etc/shared/workstation/agent.conf]
verify-agent-conf: OK
verify-agent-conf: Verifying [etc/shared/default/agent.conf]
verify-agent-conf: OK
verify-agent-conf: Verifying [etc/shared/proxmox/agent.conf]
verify-agent-conf: OK
verify-agent-conf: Verifying [etc/shared/edge/agent.conf]
verify-agent-conf: OK
```

The order matters and I got it wrong once. My first attempt used `set -e` with `install` before the validation, so a broken file was already in place by the time anything checked it. The break was `--` inside an XML comment, which is illegal and which I had written twice, in `workstation-agent.conf` and in `local_rules.xml`. Every configuration in this record now has a check for it.

**The agents picked the configuration up.** `merged.mg` on `ubuntu-dev` contains the `restrict` expressions, and `wazuh-agent` stayed active across the push.

**The feed is legible now.** File-integrity alerts in the last 24 hours went from 2,958 to 227. What is left is real: the EICAR test file at the top of the most-changed list, the deployment artifacts I wrote to `/tmp` myself, `/etc/cups`, `/etc/apt`. `agent_control -l` reports all 16 agents Active.

Captures are in [Evidence](../../Evidence/File%20Integrity%20Monitoring%20Widening%20-%202026-08-29/).

## Remaining work

- Phase two: widen beyond `ubuntu-dev` and `edge-01`. The 14 remaining agents still carry only `/etc/ssh` and `/etc/cron.d`.
- Rootcheck still reports "Files hidden inside directory '/tmp'" on `ubuntu-dev`, 36 events, from the dot-directories desktop applications create. Low volume, so I left it.
