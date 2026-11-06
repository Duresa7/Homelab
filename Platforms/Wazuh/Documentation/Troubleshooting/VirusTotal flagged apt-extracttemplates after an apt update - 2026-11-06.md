# VirusTotal Flagged apt-extracttemplates After an apt Update

**Created:** 2026-11-06  
**Last updated:** 2026-11-06

## Symptom

At 1:02 PM on 2026-11-06 the Discord security channel received a level 12 alert from `security-01`:

| Field | Value |
|---|---|
| Rule | 87105, level 12 |
| Description | VirusTotal: Alert - /usr/bin/apt-extracttemplates - 1 engines detected this file |
| SHA-256 | `c6a92a81dc5b26f12a2ae2ce0a6de3b3783d22ca0a8cf5d8c01807f34201f197` |

Two seconds earlier, at 1:02:16 PM, rule 550 (`Integrity checksum changed`) fired on the same path. Those were the only two alerts for that path in the manager's `alerts.json`, and no other agent raised one.

## Hypotheses and Tests

1. **Someone replaced the binary.** `dpkg -S` names `apt-utils` as the owner, and `dpkg --verify apt-utils apt` exited `0`. The file's MD5, `ffc919238aeb83d2372f1ea6e256cab0`, matches `/var/lib/dpkg/info/apt-utils.md5sums`. That checksum list sits on the same host, though, so an attacker with root could have rewritten it too. On its own, this test can't rule out a replaced binary.
2. **The package was tampered with before it reached the host.** I downloaded `apt-utils_2.8.4ubuntu0.1_amd64.deb` into a temporary directory. apt checks that download against the GPG-signed index. The `.deb` hashed to `244d4203093e4e47c40e7810bdecaace97501998487fc5fcd6c0a5fab6d223a3`, which is the SHA256 that `apt-cache show` lists for `pool/main/a/apt/apt-utils_2.8.4ubuntu0.1_amd64.deb`. The `apt-extracttemplates` extracted from it has the same SHA-256 as the flagged file. The installed binary is byte-identical to Ubuntu's signed build. I deleted the temporary directory afterwards.
3. **Something other than the normal update process changed the file.** `/var/log/apt/history.log` shows `/usr/bin/unattended-upgrade` upgrading `apt`, `libapt-pkg6.0t64`, `apt-transport-https` and `apt-utils` from 2.8.3 to 2.8.4ubuntu0.1 between 6:48:10 and 6:48:13 AM. The installed version is the noble-updates and noble-security candidate. The file's mtime of 2026-11-02 7:55 AM is the package build timestamp. The 1:02 PM rule 550 alert was the next file-integrity scan picking up the morning's upgrade.
4. **The detection is credible.** I looked up the hash with the VirusTotal v3 file API. The result was 1 malicious, 0 suspicious, 63 undetected and 11 type-unsupported. The only detection was Microsoft, engine 1.26100, with `Trojan:Script/Wacatac.C!ml`. The `!ml` suffix marks a machine-learning heuristic, not a signature, and Wacatac is Microsoft's generic family name for those verdicts. VirusTotal first saw the file at 7:03 PM on 2026-11-05, so the new build had been public for less than a day. The local MalwareBazaar list held no entry for the hash.

## Root Cause

This was a false positive. The morning's unattended upgrade replaced `apt-extracttemplates` with Ubuntu's new 2.8.4ubuntu0.1 build. File-integrity monitoring saw the checksum change, the VirusTotal integration looked up the new hash, and one machine-learning engine flagged a build it had not seen before. The installed file is identical to the copy inside Ubuntu's signed package.

## Corrective Action

None. Nothing on the host was changed. I did not add a suppression rule. A rule keyed to this path or this engine would also hide a real replacement of the same binary.

## Verification

Hash comparison against the archive copy, `dpkg --verify` and the apt history all agree. Every other Ubuntu 24.04 agent will receive the same `apt-utils` build through unattended upgrades and may raise the same 87105 alert on its next file-integrity scan. When that happens, the SHA-256 above settles it. A different hash on the same path needs a new investigation.
