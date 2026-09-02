# Wazuh Alerts in Splunk Walkthrough

**Created:** 2026-08-31  
**Last updated:** 2026-09-01

## What This Guide Covers

I already ran Wazuh & Splunk side by side, & neither one told me anything the other knew. This guide is the path I took to join them: a Universal Forwarder shipping the manager's alert stream into Splunk on 9997, the two Wazuh-side corrections that decide whether the stream is worth reading, malware detection built twice so it survives an API quota, & one dashboard whose top row is seven numbers that should read zero, or close to it.

The question I built it to answer is narrow. If somebody downloads a malicious file onto a machine in this lab, does a page in Splunk show it. Everything here exists because it was needed for that, & the panels that would have looked good but answered nothing aren't in it.

Two of the nine steps are corrections rather than construction. That ratio is honest. The first version of the file monitoring produced 2,334 alerts from one scratch directory in a day & burned the entire VirusTotal quota, so the detection this whole pipeline exists for got refused a verdict. Fixing that wasn't tidying up. It was the prerequisite.

## Current Status and Verified Versions

`security-01` at `192.168.72.2` runs Wazuh 4.14.7 with the manager, indexer & dashboard active, & 16 agents reporting Active including the manager's own agent 000. `splunk-siem` at `192.168.72.3` runs Splunk Enterprise 10.4.0 build `f798d4d49089` with Enterprise Security, listening on 8000, 8088, 8089, 1514 & 9997. The Universal Forwarder on `security-01` is 10.4.0, the same build, holding an established connection to `192.168.72.3:9997`. The host answered to `wazuh-01` until 2026-09-01, which is the name the screenshots & step checks below still show.

Both hosts sit on Security-A, VLAN 72, so this traffic never reaches the gateway & needed no UniFi firewall policy. Root on `splunk-siem` is 142 GB with 93 GB free. The `wazuh` index keeps 30 days or 5 GB, whichever comes first.

## What You Need

- A Wazuh manager writing `/var/ossec/logs/alerts/alerts.json`, & root on it.
- A Splunk indexer you can reach on TCP 9997, with at least 10 GB free on the volume holding `$SPLUNK_DB`. Splunk stops indexing below 5,000 MB free & tells you in a banner you have to be looking at.
- A Universal Forwarder package matching the indexer's build. A forwarder must never be newer than what it sends to.
- A free VirusTotal API key, which answers 500 lookups a day & 4 a minute.
- Somewhere to put a test file. I use the EICAR string, which is harmless by design.

## How the Pieces Fit Together

An agent writes a file. `syscheck` on that agent notices & sends a file-integrity event to the manager. The manager's rules turn it into an alert & append one JSON object to `alerts.json`. Two things then read that alert independently: `wazuh-integratord` submits the hash to VirusTotal, & rule 100200 checks the hash against a local CDB list that needs no network. Whatever comes out, the forwarder tails the same file & ships it to Splunk, where `props.conf` maps Wazuh's field names onto the Common Information Model so Enterprise Security can use them next to the UniFi data already in `netfw` & `netops`.

The forwarder runs as `splunkfwd`, a member of the `wazuh` group. `alerts.json` is `0640 wazuh:wazuh`, so group membership is the whole reason it can read the file. Running a log shipper as root to skip one `usermod` would give it write access to the entire manager.

## Walkthrough

### Step 1: Find the Disk Before Splunk Does

I had already grown the virtual disk to 150 GB in Proxmox & assumed that was the end of it. Splunk still had 24 GB free, because Rocky's installer had carved `sda3` into three logical volumes & left `VFree 0` on the volume group. Every byte I added landed in a group with nothing spare.

Half the disk was `rl-home` at 71.54 GB, holding 192 KB across three user directories. `df` reported 1.5 GB used, which is XFS metadata for a 71 GB filesystem rather than data. XFS can't be shrunk, so the volume had to be destroyed.

The obvious sequence fails in a way worth knowing. `fuser -vm /home` showed a login shell, a `dbus-broker` user session & my own SSH command chain all holding it, so it wouldn't unmount. Rebooting first is worse: `/home/dkadi/.ssh/authorized_keys` is what my key authenticates against, & removing the fstab entry then rebooting brings `/home` back as the bare empty directory underneath the old mount. No key, no way in.

The fix is to put the data on the root filesystem before the reboot, by bind-mounting `/` where the `/home` mount doesn't cover it:

```sh
mkdir -p /mnt/rootfs && mount --bind / /mnt/rootfs
rsync -aXAH --numeric-ids /home/ /mnt/rootfs/home/
diff <(cd /home && find . | sort) <(cd /mnt/rootfs/home && find . | sort) && echo IDENTICAL
umount /mnt/rootfs && rmdir /mnt/rootfs
```

`-X` carries the SELinux contexts, which matters on Rocky. With the copy in place under the mount, remove the `/home` line from `/etc/fstab`, reboot, then `lvremove -f /dev/rl/home`, `lvextend -l +100%FREE /dev/rl/root`, `xfs_growfs /`, & `restorecon -RF /home`. Root went from 70.00 GB to 141.54 GB & the data blocks from 18,350,080 to 37,104,640.

Check the number Splunk itself reads, not the one `df` prints, because Splunk's disk guard uses its own:

![Splunk reporting the root filesystem at 141.5 GB with 94.9 GB free](../Platforms/Splunk/Enterprise/Evidence/Root%20Filesystem%20Expansion%20-%202026-08-29/Screenshots/S04-Splunk-Root-Filesystem-After-Expansion-2026-08-29.png)

Then confirm nothing was lost. `netfw` at 359,396 events & `netops` at 20,687 carried straight through the reboot:

![Index event counts after the rebuild, with netfw and netops intact](../Platforms/Splunk/Enterprise/Evidence/Root%20Filesystem%20Expansion%20-%202026-08-29/Screenshots/S05-Splunk-Index-Counts-Intact-After-Rebuild-2026-08-29.png)

That capture also shows something I didn't expect. `_internal`, `_audit` & `_introspection` hold 22.1 GB between them; the UniFi data I actually collect is 99 MB. Splunk's own telemetry outweighs real data by more than 200 to 1, & it's what will eat the 94 GB I just recovered.

### Step 2: Open the Receiver on 9997

On the indexer, Settings, Forwarding and receiving, Configure receiving, New Receiving Port, 9997. Then check the listener rather than the form you just submitted:

```spl
| rest /services/data/inputs/tcp/cooked | table title index disabled connection_host
```

![The cooked TCP inputs: 9997 enabled, the older 1514 disabled](../Platforms/Wazuh/Evidence/Wazuh%20Alert%20Forwarding%20to%20Splunk%20-%202026-08-29/Screenshots/S08-Splunk-Receiving-Port-9997-Enabled-2026-08-29.png)

Both inputs read `index default`, & that is correct. The forwarder sets `index = wazuh` in its own `inputs.conf`, and the sender's index wins over the listener's.

I put the listener in the app rather than in `etc/system/local`, so the receiving port, the index & its retention travel together as one thing I can uninstall:

```ini
# wazuh_insights/default/inputs.conf
[splunktcp://9997]
disabled = 0
connection_host = ip
```

```ini
# wazuh_insights/default/indexes.conf
[wazuh]
homePath   = $SPLUNK_DB/wazuh/db
coldPath   = $SPLUNK_DB/wazuh/colddb
thawedPath = $SPLUNK_DB/wazuh/thaweddb
frozenTimePeriodInSecs = 2592000
maxTotalDataSizeMB = 5120
```

I chose 9997 over HEC because 8088 & 1514 were already carrying HEC & SC4S. A file monitor plus splunktcp needs no token management & survives a manager restart on its own, since the forwarder tracks its position in the file.

### Step 3: Install the Forwarder on the Manager

Install the package, then put the forwarder's user in the `wazuh` group so it can read the alert stream without running as root:

```sh
usermod -aG wazuh splunkfwd
```

Then write two files:

```ini
# /opt/splunkforwarder/etc/system/local/inputs.conf
[monitor:///var/ossec/logs/alerts/alerts.json]
index = wazuh
sourcetype = wazuh:alerts
disabled = 0
```

```ini
# /opt/splunkforwarder/etc/system/local/outputs.conf
[tcpout]
defaultGroup = splunk_siem

[tcpout:splunk_siem]
server = 192.168.72.3:9997
maxQueueSize = 64MB
useACK = true
```

`useACK` makes the forwarder hold an event until the indexer confirms it was written. Without it, a Splunk restart drops whatever was in flight.

Only the live file is monitored, deliberately. Wazuh rotates `alerts.json` at midnight into `logs/alerts/<year>/<month>/`, & pointing at the archive would replay months of history through a brand-new pipeline & make the first day's numbers meaningless. `crcSalt` stays unset: the file keeps its name across rotation, & Splunk's CRC of the first 256 bytes changes when a new day's file begins, so the new file is treated as new.

Two things to check rather than assume. Prove the forwarder can actually read the file as its own user, & prove the connection is up:

```sh
runuser -u splunkfwd -- head -1 /var/ossec/logs/alerts/alerts.json
ss -tnp | grep 9997
```

`splunk enable boot-start` printed `cannot operate systemd unit files` & returned non-zero on this host. It had already written the unit. `systemctl enable --now SplunkForwarder` completed normally against the unit it claimed it couldn't create, so don't undo a step that succeeded.

### Step 4: Look at What Actually Arrives

Count the distinct agents at the same time as the events, because a forwarder that works for one machine and not the rest looks identical to one that works:

```spl
index=wazuh | stats count as Alerts, dc(agent.name) as Agents, min(_time) as Earliest, max(_time) as Latest
```

![914 alerts from 13 agents in the first four hours](../Platforms/Wazuh/Evidence/Wazuh%20Alert%20Forwarding%20to%20Splunk%20-%202026-08-29/Screenshots/S06-Splunk-First-Wazuh-Alerts-Received-2026-08-29.png)

914 alerts from 13 agents in the first four hours. All 16 were represented by the following day.

Then break it down by rule, which is the step people skip:

```spl
index=wazuh | top limit=10 rule.description
```

![Wazuh alerts broken down by rule description](../Platforms/Wazuh/Evidence/Wazuh%20Alert%20Forwarding%20to%20Splunk%20-%202026-08-29/Screenshots/S07-Splunk-Wazuh-Rule-Breakdown-2026-08-29.png)

`Systemd: Service exited due to a failure` was 575 of 914 events, 62.9 per cent of everything the fleet said in that window. The cause is `nut-driver@ups01.service` on `red-server`, which carries `RestartUSec=15s` & lands at roughly one failure every 25 seconds once startup time is counted. On 2026-08-31 its journal held 3,422 `Failed to start` lines in 24 hours & `systemctl show` reported `NRestarts=8995`. The UPS it's configured for isn't attached to that node, & `openipmi.service` is failed on the same host.

That's the first real finding this pipeline produced, & it had been true for a while. It also justifies the hour of work in the next two steps, because a feed where one broken unit is nearly two thirds of the volume isn't a feed you'll read twice.

### Step 5: Decide What Each Group Watches

Wazuh's stock configuration watches almost nothing, so the widening is where the value is. Check the fleet first:

![The Wazuh Endpoints page with 15 remote agents active](../Platforms/Wazuh/Evidence/File%20Integrity%20Monitoring%20Widening%20-%202026-08-29/Screenshots/S11-Wazuh-Endpoints-All-Agents-Active-2026-08-30.png)

Groups are the unit of configuration, & putting a machine in its own group is what makes it safe to give that group aggressive settings:

![The four agent groups: default, proxmox, edge and workstation](../Platforms/Wazuh/Evidence/File%20Integrity%20Monitoring%20Widening%20-%202026-08-29/Screenshots/S12-Wazuh-Endpoint-Groups-2026-08-30.png)

![The workstation group holding only ubuntu-dev, agent 020](../Platforms/Wazuh/Evidence/File%20Integrity%20Monitoring%20Widening%20-%202026-08-29/Screenshots/S13-Wazuh-Workstation-Group-Membership-2026-08-30.png)

`workstation` holds one machine, `ubuntu-dev`, agent 020. It's the only machine where a file arrives because a person chose to download it, which makes it both the first place to widen & the only place a VirusTotal lookup has anything to look up. It watches `~/Downloads`, `/tmp`, `/var/tmp`, `/usr/local/bin`, `/opt`, `~/.ssh`, `~/.config/systemd/user` & `/etc/systemd/system`. That last pair is there because a user-level timer survives a reboot exactly like a root one.

Create the group, put the agent in it, & the manager writes the shared configuration to `/var/ossec/etc/shared/<group>/agent.conf`:

```sh
/var/ossec/bin/agent_groups -a -g workstation -q
/var/ossec/bin/agent_groups -a -i 020 -g workstation -q
```

An agent can be in several groups. Everything is in `default`, so `default` is where a fleet-wide setting goes and the specific group carries the rest. Edit the file directly on the manager, or from Endpoint Groups, Edit content:

![The workstation group agent.conf in the Wazuh editor](../Platforms/Wazuh/Evidence/File%20Integrity%20Monitoring%20Widening%20-%202026-08-29/Screenshots/S14-Wazuh-Workstation-Group-Agent-Config-2026-08-30.png)

Validate before you install, not after. My first attempt used `set -e` with `install` ahead of the check, so a broken file was already in place by the time anything looked at it. The break was `--` inside an XML comment, which is illegal, & I'd written it twice.

```sh
/var/ossec/bin/verify-agent-conf
```

That returns `OK` per group, & it's the only check that reads the file the way the manager will.

### Step 6: Cut the Noise, Because It Breaks the Detection

The first version watched all of `/tmp` on the workstation. In one day it produced this:

| Directory | Alerts | What it is |
|---|---|---|
| `/tmp/executor-research.<random>` | 2,334 | Tooling working directory |
| `/tmp/scoped_dir<random>` | 124 | Browser scratch |
| `/tmp/<reverse-dns>.<random>` | 60 | Desktop application session state |

Roughly 97 per cent of it was the machine describing its own housekeeping. Every one of those files went to VirusTotal, & the integration answered **2,697 of those lookups with "Public API request rate limit reached"**. The monitor disabled the detection it feeds.

Wazuh's own malware view is where that becomes obvious. 2,760 hits in 24 hours, of which exactly one is a verdict:

![Wazuh malware events: one VirusTotal detection buried under rule 87101 rate-limit errors](../Platforms/Wazuh/Evidence/Malware%20Detection%20-%202026-08-29/Screenshots/S20-Wazuh-Malware-Detection-Events-2026-08-30.png)

The top row is rule 87105 at level 12 on `ubuntu-dev`. Every row under it is rule 87101 at level 3 from `wazuh-01`, one every half second, & each of those is the integration saying it ran out of quota rather than saying anything about a file.

`/tmp` stays watched, because a payload dropped into world-writable space is a real case. It's restricted by filename instead:

```xml
<directories check_all="yes" realtime="yes"
  restrict="\.sh$|\.bash$|\.py$|\.pl$|\.rb$|\.php$|\.elf$|\.bin$|\.run$|\.out$|\.so$|\.ko$|\.exe$|\.dll$|\.ps1$|\.jar$|\.deb$|\.rpm$|\.appimage$|\.zip$|\.tar$|\.tgz$|\.gz$|\.bz2$|\.xz$|\.7z$|\.rar$|\.iso$">/tmp</directories>
```

A script, an executable, an archive or a package is worth a hash & a lookup. A browser's cookie file isn't. Wazuh's `sregex` isn't PCRE: it takes `\w`, `\d`, `\s`, `\.`, `+`, `*`, `^`, `$` & `|`, & it has no `?`, no `{}` & no character classes, so an expression that works in `grep -E` may silently match nothing.

Write the ignore list by shape rather than by product. Desktop applications name their `/tmp` working directories after their own bundle identifier, so two expressions cover all of them & the list never becomes something to maintain per application:

```xml
<ignore type="sregex">/tmp/\w+\.\w+\.\w+\.</ignore>
<ignore type="sregex">/tmp/\.\w+\.\w+\.\w+\.</ignore>
```

There's a second reason for shape over name. A vendor-named ignore puts that vendor's name into an alert, & an alert ends up in a screenshot.

Two other groups needed the same treatment. `proxmox` had no configuration at all, so `/etc/pve` was caught by Wazuh's stock `/etc` rule. On a Proxmox node `/etc/pve` is pmxcfs, a FUSE filesystem backed by the cluster database, & the cluster rewrites its status files every few seconds. Each of `.rrd`, `.version`, `ha/crm_commands`, `ha/manager_status` & each node's `lrm_status` reported 533 changes. Five nodes doing that is 5,570 alerts of nothing. The group now ignores the parts that are state & leaves watched the parts that are configuration: `corosync.conf`, `storage.cfg`, `user.cfg`, the firewall rules & the guest definitions.

`default` needed rootcheck's trojan check turned off fleet-wide. It works by grepping system binaries for strings a trojaned copy might contain, & on Debian the ordinary setuid binaries contain them. `/bin/chfn` at 1,046, `/bin/chsh` at 1,043 & `/bin/passwd` at 1,040 led a list of over 22,000 "Trojaned version of file detected" alerts, & not one was real.

```xml
<rootcheck>
  <check_trojans>no</check_trojans>
  <ignore>/dev/.lxc</ignore>
</rootcheck>
```

A check with a hundred per cent false-positive rate is worse than no check, because it's the noise every real alert has to be found inside. Nothing is left uncovered: a modified system binary still shows as a file-integrity change, & a malicious file is caught by its hash. `check_dev` stays on, because a file hidden under `/dev` is a real technique, with `/dev/.lxc` ignored since it exists inside every LXC container.

Wazuh's own file-integrity view is where you confirm the result. `ubuntu-dev` alone had produced 2,644 events in 24 hours before the correction. After it, the busiest agent on the fleet is `grey-server` at 201, which is my own LVM work on `/etc/lvm`, & `ubuntu-dev` sits second at 10:

![Wazuh File Integrity Monitoring module after the correction, with grey-server at 201 events](../Platforms/Wazuh/Evidence/File%20Integrity%20Monitoring%20Widening%20-%202026-08-29/Screenshots/S15-Wazuh-File-Integrity-Monitoring-Module-2026-08-30.png)

Fleet-wide, file-integrity alerts in 24 hours went from 2,958 to 227, & what's left is real.

### Step 7: Build Malware Detection Twice

Wazuh's malware view filters on three groups, `rootcheck`, `virustotal` & `yara`:

![The Wazuh Malware Detection module](../Platforms/Wazuh/Evidence/Malware%20Detection%20-%202026-08-29/Screenshots/S16-Wazuh-Malware-Detection-Module-2026-08-30.png)

The VirusTotal integration goes in `/var/ossec/etc/ossec.conf`, triggered by the `syscheck` group so it only ever runs on a file that appeared or changed:

```xml
<integration>
  <name>virustotal</name>
  <api_key>YOUR_KEY_HERE</api_key>
  <group>syscheck</group>
  <alert_format>json</alert_format>
</integration>
```

One mechanism isn't enough & the reason is the quota. 500 lookups a day & 4 a minute are low enough that a busy day exhausts them, & when it does the integration returns an error rather than a verdict. An unanswered lookup looks exactly like a clean one. So the second mechanism is a local CDB list, which analysisd compiles into a hash lookup, costs no network call, & can't be rate limited.

![The CDB lists on the manager, with known-bad-hashes among them](../Platforms/Wazuh/Evidence/Malware%20Detection%20-%202026-08-29/Screenshots/S17-Wazuh-CDB-Lists-2026-08-30.png)

![The known-bad hash list with the EICAR hash pinned first](../Platforms/Wazuh/Evidence/Malware%20Detection%20-%202026-08-29/Screenshots/S18-Wazuh-Known-Bad-Hash-List-2026-08-30.png)

CDB format is `key:value`, one per line, so each hash becomes its own key. The list is built from abuse.ch MalwareBazaar's recent feed, with EICAR's hash pinned as the first line permanently so the whole path can be proven on demand without going near real malware:

```sh
printf '%s\n' "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f:eicar-test-file" > "$TMP"

curl -sfL --max-time 120 "https://bazaar.abuse.ch/export/txt/sha256/recent/" \
  | tr -d '"\r' \
  | grep -Eio '^[a-f0-9]{64}$' \
  | tr 'A-F' 'a-f' \
  | sort -u \
  | sed 's/$/:malwarebazaar/' >> "$TMP"

install -o wazuh -g wazuh -m 660 "$TMP" /var/ossec/etc/lists/known-bad-hashes
```

The feed is the last 48 hours of samples, deliberately. A full MalwareBazaar dump is millions of hashes and costs more memory in analysisd than it's worth; recent samples are the ones a fresh download is plausibly going to match. Mine held 872 entries on 2026-08-31. Refuse to install a list with fewer than 2 entries, so a feed that returns nothing can't quietly empty your detection.

Declare it in `ossec.conf` as `<list>etc/lists/known-bad-hashes</list>`, then add the rule:

![Rule 100200 in local_rules.xml](../Platforms/Wazuh/Evidence/Malware%20Detection%20-%202026-08-29/Screenshots/S19-Wazuh-Local-Rule-Known-Bad-Hash-2026-08-30.png)

```xml
<group name="malware,known_bad_hash,">
  <rule id="100200" level="12">
    <if_sid>554,550</if_sid>
    <list field="sha256" lookup="match_key">etc/lists/known-bad-hashes</list>
    <description>Known-bad file hash found: $(file)</description>
    <mitre><id>T1105</id></mitre>
  </rule>
</group>
```

554 is a file added & 550 is a file modified, so the rule sees a download & an overwrite.

Two things don't work the way the documentation suggests. **`wazuh-makelists` doesn't exist in 4.14** & returns exit 127; analysisd compiles a CDB list when it starts, so a manager restart is what publishes a changed list. And **only decoded fields interpolate into a description**: my first version read `$(agent.name): $(file)` & produced `Known-bad file hash found on : /path`, because `agent.name` isn't a decoded field.

Refresh the list on a timer, & then check that the timer is running. I wrote `wazuh-hash-list.service` & `wazuh-hash-list.timer`, documented a weekly refresh, & never ran `systemctl enable`. It sat `disabled` for two days & didn't appear in `systemctl list-timers --all` at all. A stale list still matches EICAR on demand, so the one test I'd have run to check the mechanism would have passed for a year.

```sh
systemctl enable --now wazuh-hash-list.timer
systemctl list-timers wazuh-hash-list.timer --no-pager
```

### Step 8: Prove It With EICAR

Write the EICAR string into a directory the group watches in realtime, & let the chain run untouched:

```console
$ sha256sum eicar-test-2026-08-30.txt
275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f
```

![Both detection mechanisms firing on the same file one second apart](../Platforms/Splunk/Enterprise/Evidence/Wazuh%20Insights%20App%20-%202026-08-29/Screenshots/S21-Splunk-EICAR-Detected-Twice-Independently-2026-08-30.png)

| Time | Rule | Level | What it said |
|---|---|---|---|
| 10:46:56 | 87105 | 12 | VirusTotal: 64 of 67 engines detected this file |
| 10:46:57 | 100200 | 12 | Known-bad file hash found: `/home/ai-agent/Downloads/eicar-test-2026-08-30.txt` |

One second apart, on the same file, & genuinely independent. 87105 is a network lookup answered by VirusTotal; 100200 is a local hash comparison that would have produced the same result with the Internet unplugged. Both were searchable in Splunk about ten seconds after they were raised.

The same test had been refused a verdict earlier that day. It succeeded after the workstation group stopped submitting scratch files, which is the clearest evidence I have that Step 6 was a prerequisite rather than housekeeping.

Put the test file somewhere the purge won't reach. I'd already deleted my first successful verdict, because I purged the corrected `/tmp` alerts & that first test file had been written under `/tmp`. A purge scoped by path takes the true positives in that path too.

### Step 9: Map to CIM, Then Build One Page

`props.conf` for `[wazuh:alerts]` does the mapping. `KV_MODE = json` handles the nested extraction, `TRUNCATE = 32768` stops a long package list from cutting the JSON mid-object, & the timestamp comes from the alert rather than from Splunk guessing:

```ini
TIME_PREFIX = "timestamp":"
TIME_FORMAT = %Y-%m-%dT%H:%M:%S.%3N%z
```

Aliases put `agent.name` on `dest`, `data.srcip` on `src` & `rule.description` on `signature`. Event classes key on `rule.groups{}` rather than on rule IDs, because rule IDs change between Wazuh releases & when a local rule overrides a stock one, & group names don't.

Two mapping mistakes were invisible until I looked at what Enterprise Security did with the result.

`EVAL-object_category = "file"` was unconditional. Enterprise Security tags an event into the Endpoint Filesystem data model when `object_category` is `file`, so that put 905 of 925 non-file events into a filesystem model. It has to be conditional:

```ini
EVAL-object_category = case(isnotnull('syscheck.path'), "file", isnotnull('data.package'), "package", 1==1, null())
EVAL-status = case(isnotnull('syscheck.path') OR isnotnull('data.package'), "success", 1==1, null())
```

The malware macro counted VirusTotal's error messages as malware. Matching the whole `virustotal` group picks up 87101 for a rate-limit refusal & 87103 for a file the service has never seen, which are the integration reporting on itself. The tile read 2,941 when the true number was 2. Only 87105 carries `data.virustotal.malicious = 1`:

```ini
[wazuh_malware_found]
definition = index=wazuh sourcetype=wazuh:alerts ("data.virustotal.malicious"=1 OR "rule.groups{}"=known_bad_hash OR "rule.groups{}"=trojan OR "rule.groups{}"=rootkit)
```

The general lesson is that a product's own operational messages sit in the same group as its findings, & a group match can't tell them apart.

The dashboard's top strip is seven counts that should normally read zero, or close to it:

![The Wazuh Insights dashboard, seven glance tiles and the charts below them](../Platforms/Splunk/Enterprise/Evidence/Wazuh%20Insights%20App%20-%202026-08-29/Screenshots/S09-Wazuh-Insights-Dashboard-Glance-Tiles-2026-08-30.png)

| Tile | What it counts | Window |
|---|---|---|
| Machines gone quiet | Agents seen in 7 days that have said nothing for 24 hours | 7 days |
| Malware found | A local hash match, or VirusTotal reporting detections | 24 hours |
| Off-network logins | Successful logins from outside RFC1918 | 24 hours |
| Watched files changed | File-integrity events across every agent | 24 hours |
| Scheduled task changes | Changes under cron & systemd unit directories | 7 days |
| Software added or removed | Package manager activity | 7 days |
| Listening port changes | A machine started or stopped listening on a port | 7 days |

Four of the seven read zero in that capture. The three that don't are the point of the strip rather than a fault in it. Malware found reads 4: the same EICAR file caught on two separate occasions, each raising two independent alerts, which is 2 rather than 2,941 per occasion & the number the macro fix was chasing. Watched files changed reads 227 & software added or removed reads 3, & neither tile is ever meant to sit at zero on a fleet that is being worked on. For those two the question is whether the number moved, not whether it's zero.

Quiet agents can't be derived from alert volume, & that shaped one tile. A healthy machine with nothing to report sends nothing, so "no alerts" & "agent is down" look identical if you only count. The tile is "seen in the last 7 days, silent for the last 24", which separates a machine that stopped talking from one that was never enrolled.

Below the tiles: alerts over time by machine, the VirusTotal lookup budget, alerts by machine, the most-changed watched files, a login table, & the whole stream newest first.

![The full Wazuh Insights dashboard including the alert stream](../Platforms/Splunk/Enterprise/Evidence/Wazuh%20Insights%20App%20-%202026-08-29/Screenshots/S10-Wazuh-Insights-Dashboard-Full-Page-2026-08-30.png)

Three Dashboard Studio behaviours cost me time. A definition either parses or it doesn't, so one bad `input.multiselect` renders `Layout undefined is not defined` & takes the whole page down rather than that one control. A panel can pin its own time window by writing `earliest=-7d latest=now` in the SPL, & the job's messages say so out loud with `INFO Your timerange was substituted based on your search string`, so a saved search isn't needed for it. And `_time` renders as a formatted timestamp only while it's still called `_time`, so `| table _time | rename _time as Time` prints raw epochs. Use `eval Time=strftime(_time,"%Y-%m-%d %H:%M:%S")`, & sort before you table, because `sort - _time` after `| table` has no field left to sort on.

## What I Checked After Each Step

- Splunk's own partition reading, not `df`, showed `/` at 141.5 GB with 94.9 GB free, & `netfw` & `netops` counts carried through the reboot.
- `ss -tnp | grep 9997` showed an established connection from `192.168.72.2` to `192.168.72.3:9997`, & `id splunkfwd` showed group 110 `wazuh`.
- `runuser -u splunkfwd -- head -1 /var/ossec/logs/alerts/alerts.json` returned a line, so the group membership was proven rather than assumed.
- `/var/ossec/bin/verify-agent-conf` returned OK for all four groups, & `merged.mg` on `ubuntu-dev` contained the `restrict` expressions.
- File-integrity alerts in 24 hours fell from 2,958 to 227; the rootcheck trojan false positives went from 22,190 to 0.
- Two alerts, 87105 & 100200, both level 12, one second apart on the same file, searchable in `index=wazuh` about ten seconds later.
- All 16 agents Active, & the four Wazuh & forwarder units active on `wazuh-01`.

## Troubleshooting and Recovery

**`wazuh-integratord` returns exit 4, `ERR_NO_RESPONSE_VT`.** That reads like the service is unreachable & it usually isn't. Both the v2 & v3 APIs returned HTTP 200 from my manager & a direct EICAR lookup came back with 65 positives while the integration was failing. The exit code describes the symptom; the cause was in the integration's own log, nine times over, & it was the rate limit. Read `/var/ossec/logs/integrations.log` before you touch the key or the egress path.

**A malware tile that reads in the thousands.** Check whether the search matches the `virustotal` group rather than `data.virustotal.malicious=1`. Rule 87101 & 87103 are the integration talking about itself.

**A dashboard that renders no panels & says `Layout undefined is not defined`.** One malformed input takes the entire definition down. Remove inputs one at a time; the shape that works here is `layout` with `type`, `options`, `structure` & `globalInputs`, with `input.timerange` as the only global input.

**`| delete` reports success & removes nothing.** The `search/jobs/export` endpoint accepts it & does nothing. Submit a blocking job to `/services/search/jobs` instead. `admin` doesn't hold `can_delete` by default, & the grant takes a few seconds to take effect, so a delete run immediately after the grant fails with "insufficient privileges".

**A rebuilt CDB list that doesn't match.** `wazuh-makelists` was removed in 4.14. Restart the manager; analysisd compiles the list at startup.

## Known Limits

Nothing here alerts. A level 12 malware match changes a number on a page that somebody has to open, & there's no automatic response, so nothing quarantines or deletes a matched file. That's the next piece of work & the saved searches in the app exist for it, though no panel depends on them.

File monitoring is wide on two machines. `ubuntu-dev` & `edge-01` have real coverage; the other 14 agents carry `/etc/ssh` & `/etc/cron.d` & nothing else, which means the hash list & the VirusTotal integration have nothing to look at on them.

The listening-port panel is empty. Rules 533 & 534 only fire on a change & there hasn't been one, so an empty panel is the correct answer rather than a broken one.

Rootcheck still reports "Files hidden inside directory '/tmp'" on `ubuntu-dev`, 36 events, from the dot-directories desktop applications create. Low volume, so I left it.

## Source Records

- [Alert Forwarding to Splunk](../Platforms/Wazuh/Documentation/Change%20Records/Alert%20Forwarding%20to%20Splunk%20-%202026-08-29.md)
- [Root Filesystem Expansion](../Platforms/Splunk/Enterprise/Documentation/Change%20Records/Root%20Filesystem%20Expansion%20-%202026-08-29.md)
- [File Integrity Monitoring Widening](../Platforms/Wazuh/Documentation/Change%20Records/File%20Integrity%20Monitoring%20Widening%20-%202026-08-29.md)
- [Malware Detection](../Platforms/Wazuh/Documentation/Change%20Records/Malware%20Detection%20-%202026-08-29.md)
- [Wazuh Insights App](../Platforms/Splunk/Enterprise/Documentation/Change%20Records/Wazuh%20Insights%20App%20-%202026-08-29.md)
- [Agent group configurations](../Platforms/Wazuh/Configuration/Agent%20Groups/)
- [Local rules](../Platforms/Wazuh/Configuration/Rules/)
- [Forwarder configuration](../Platforms/Wazuh/Configuration/Splunk%20Forwarder/)
- [wazuh_insights app](../Platforms/Splunk/Enterprise/Configuration/wazuh_insights/)
- [Wazuh walkthrough](Wazuh.md), for manager health & agent enrollment
- [Splunk walkthrough](Splunk.md), for the indexer, HEC & SC4S underneath this
