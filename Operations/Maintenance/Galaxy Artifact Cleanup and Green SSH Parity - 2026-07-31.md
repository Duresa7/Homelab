# Galaxy Artifact Cleanup and Green SSH Parity

**Created:** 2026-07-31  
**Last updated:** 2026-08-01

**Change date:** 2026-07-31  
**Status:** Complete. Of the three items left open below, I closed two on 2026-08-01  
**Scope:** Removal of working files left on `ansible-01`, `monitor-01`, & the five Galaxy nodes after the five-node expansion; reversal of the PXE registry rename; & the SSH client and key-trust parity fixes that brought `green-server` in line with the other four nodes

## Outcome

I cleared 23 leftover files & 4 directories across seven machines, reverted the one live change the cancelled node rename had made, and closed the two SSH parity gaps that kept Green from matching the other four. Galaxy still reports five expected votes, five total votes, & `Quorate`. All seven Proxmox services are active on all five nodes, all 19 guests are running, and Prometheus holds 49 of 49 targets up.

The count breaks down as `ansible-01` 5 files & 2 directories, `red-server` 8 files & 2 directories, `blue-server` 4 files, `purple-server` 2, `green-server` 2, `grey-server` 1, & `monitor-01` 1.

The rename reversal came first. I had changed the PXE machine registry from `green-server` to `green-node` before the rename was cancelled, so I restored `green-server` from the backup, redeployed with `ansible-playbook playbooks/deploy.yml` (`ok=31 changed=2 failed=0`), and confirmed `/etc/galaxy-pxe/machines.json` reads `green-server` with `nvme0n1` as the only install disk. The one-use state file was untouched: Green's record still holds attempt `60d0f991` at `complete` with `fqdn: green-server.galaxy`.

My first sweep only caught files newer than 2026-07-29, which hid four older items on Red, Purple, & Blue. Widening it to every file under `/root` turned those up. That is the same mistake the [2026-07-26 purge](Galaxy%20Host%20Backup%20Artifact%20Purge%20-%202026-07-26.md) records: a scan narrower than the problem reports a clean result it hasn't earned.

## What I Removed

| Machine | Path | What it was |
| --- | --- | --- |
| `ansible-01` | `/tmp/machines.json.pre-rename` | The registry backup I took before the rename edit |
| `ansible-01` | `monitoring-exporters/README.md.bak.20260730_094839`, `README.md.bak.20260730_095312`, `semaphore/task-templates.yml.bak.20260730_095312`, `tests/validate_project.py.bak.20260730_094839` | Four stale editing backups. The project is tracked at [Source/monitoring-exporters](../../Platforms/Ansible/Source/monitoring-exporters/README.md), so git already holds the history |
| `ansible-01` | `proxmox-pxe-provisioning/app/__pycache__`, `tests/__pycache__` | Python bytecode from the test runs |
| `purple-server`, `blue-server`, `red-server` | `/tmp/disable-proxmox-subscription-popup_<epoch>_<hash>.sh` | Three upload copies the SSH transfer left behind after the popup script ran |
| `green-server` | `/var/lib/proxmox-first-boot/proxmox-first-boot`, `/var/log/galaxy-pxe-first-boot.log` | The executed one-use first-boot script & its 59,635-byte log. I had already checked both for credentials, and the join key had removed itself at the end of the run |
| `blue-server` | `/etc/lvm/backup/pve-old-sata`, `/etc/lvm/archive/pve-old-sata_00000-1822880599.vg` | LVM metadata for a volume group that no longer exists. `vgs` returns only `pve` & `pvs` only `/dev/nvme0n1p3` |
| `monitor-01` | `/home/<YOUR_ADMIN_USERNAME>/monitoring/prometheus.yml.bak.20260731T140158Z` | The 48-target pre-Green rollback copy. Green is permanent now that the rename is cancelled, so rolling back to a config without it has no purpose |
| `grey-server` | `/root/no-nag-script.superseded-2026-07-31` | The unguarded subscription-nag hook the tested script replaced. Content preserved below |
| `purple-server`, `blue-server` | `/root/pvecm_add.log` | Nine-line cluster join transcripts from 2026-05-30. Content preserved below |
| `red-server` | `/root/clone-verify.log`, `/root/purple-clone/` | The 2026-07-25 boot-drive clone verification, six files. Content preserved below |
| `red-server` | `/root/` plus a space and a backslash | An empty directory created 2026-07-07 by a mistyped command. `ls` renders the name as `\\`, `find -name` & shell globs both missed it, and it took `os.listdir` returning `' \\'` to get the real two-character name |

## What I Kept, and Why

`/usr/local/sbin/disable-proxmox-subscription-popup` & `/etc/apt/apt.conf.d/99-galaxy-no-subscription-nag` stay on all five nodes. The hook calls the helper on every `dpkg` run, which is the only thing keeping a `proxmox-widget-toolkit` upgrade from restoring the nag. Removing either one undoes the patch on the next upgrade.

The PXE service stays whole: `/etc/galaxy-pxe/`, `/var/lib/galaxy-pxe/state.json`, & `/srv/tftp/galaxy-ipxe.efi`. So does the `galaxy-pxe-join` public key in Grey's `authorized_keys`, because its private half is what lets a newly installed node run `pvecm add --use_ssh`. That key is trusted on Grey alone and appears zero times in the cluster-wide key store, which matches `cluster_peer: 192.168.70.10` in the registry. Widening it to five nodes would be a downgrade.

I kept `proxmox-pxe-provisioning/tests/test_service.py` on `ansible-01` even though the repo carries the same file at [Source/tests](../../Platforms/Galaxy%20PXE/Source/tests/test_service.py). The deploy runs from that checkout, and those 21 tests are what gate a registry change before it reaches the service.

I left the UniFi controller's eight monthly `autobackup_*.unf` files alone. The controller generates them on its own schedule, they span 2025-09-03 through 2026-07-01, and they are the only restore path for the network configuration. Nothing in this work created them.

I also left the four `config-<epoch>.sql.gz` files under `/var/lib/pve-cluster/backup/` on Purple, Blue, Red, & Green. `pvecm add` writes those pre-join pmxcfs snapshots itself, they run 14 to 24 KB, and Grey has none because it created the cluster rather than joining it.

## Green SSH Parity

Green was the only node whose `/root/.ssh/config` was not the fleet standard. It carried a join-only block instead:

```text
Host 192.168.70.10
    User root
    IdentityFile /run/galaxy-pxe-join-key
    IdentitiesOnly yes
    BatchMode yes
    ConnectTimeout 5
    StrictHostKeyChecking accept-new
```

That block was dead. `/run/galaxy-pxe-join-key` no longer exists on any node, & `IdentitiesOnly yes` meant Green would offer only that missing key when reaching Grey. It also left Green without the cipher restriction the other four carry. I replaced it with the standard file. All five now hash to `a9b168c6` at mode 640 & 117 bytes:

```text
Ciphers aes128-ctr,aes192-ctr,aes256-ctr,aes128-gcm@openssh.com,aes256-gcm@openssh.com,chacha20-poly1305@openssh.com
```

The second gap was key trust, and it was on Grey rather than Green. Grey is the only node whose `/root/.ssh/authorized_keys` is a regular file; Purple, Blue, Red, & Green all symlink it to `/etc/pve/priv/authorized_keys`. That deviation is deliberate, because it is what scopes the PXE join key to Grey. The cost is that Grey's file is hand-maintained, and it was last touched at 01:15 on 2026-07-31, before Green joined. It held the root keys for Purple, Blue, & Red and not Green's, so `green-server` to `grey-server` root SSH failed with `Permission denied (publickey)` while the other three worked.

I appended Green's existing cluster root key, the same `ssh-rsa ... root@green-server` line already present in `/etc/pve/priv/authorized_keys`, to Grey's file. That is additive & trusts nothing new. Grey now lists ten keys, the join key still appears only there, and `green-server` to `grey-server` returns `grey-server`.

One related thing I did not fix, because it is fleet-wide rather than a Green defect: `/etc/pve/priv/known_hosts` holds a single entry and all five `/etc/pve/nodes/<node>/ssh_known_hosts` files are empty, so ad-hoc `ssh <peer> hostname` between members fails host key verification in both directions. Purple to Red fails the same way Green did. `pvecm updatecerts` ran cleanly on all five nodes and did not repopulate them. Cluster operations are unaffected, since the API path works and `pvesh get /nodes` from Green returns all five online.

## Preserved Content

### Grey's superseded nag hook

```text
DPkg::Post-Invoke { "if [ -s /usr/share/javascript/proxmox-widget-toolkit/proxmoxlib.js ] && ! grep -q -F 'NoMoreNagging' /usr/share/javascript/proxmox-widget-toolkit/proxmoxlib.js; then echo 'Removing subscription nag from UI...'; sed -i '/data\.status/{s/\!//;s/active/NoMoreNagging/}' /usr/share/javascript/proxmox-widget-toolkit/proxmoxlib.js; fi" };
```

The replacement refuses any source layout outside the exact stock or patched form. This one rewrote every line matching `/data\.status/`, so a future layout change would have been edited blind.

### Purple and Blue cluster join transcripts

Both ran on 2026-05-30 and differ only in the node name & snapshot epoch.

```text
copy corosync auth key
stopping pve-cluster service
backup old database to '/var/lib/pve-cluster/backup/config-1780124424.sql.gz'
waiting for quorum...OK
(re)generate node files
generate new node certificate
merge authorized SSH keys
generated new node certificate, restart pveproxy and pvedaemon services
successfully added node 'purple-server' to cluster.
```

Blue's is identical with `config-1780124480.sql.gz` & `'blue-server'`.

### Red's 2026-07-25 clone verification

These are the scripts & results behind [Purple Boot NVMe Replacement](../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Purple%20Boot%20NVMe%20Replacement%20-%202026-07-25.md). The first whole-disk compare failed at byte 529 because the GPT holds a disk-specific UUID, which is why the verification moved to per-partition compares.

```text
started 2026-07-25T00:35:13-04:00
/dev/sdb /dev/sdc differ: byte 529, line 2
EXIT=1 finished 2026-07-25T00:35:13-04:00
```

```sh
#!/bin/sh
exec > /root/purple-clone/verify.log 2>&1
echo "started $(date -Is)"
for n in 1 2 3; do
  echo "--- partition $n ($(blockdev --getsize64 /dev/sdb$n) bytes) ---"
  cmp /dev/sdb$n /dev/sdc$n
  rc=$?
  if [ $rc -eq 0 ]; then echo "p$n IDENTICAL"; else echo "p$n DIFFERS rc=$rc"; fi
  echo "  done $(date -Is)"
done
echo "finished $(date -Is)"
```

All three partitions matched on both runs. The WD copy finished at 01:16:19 and the Toshiba at 02:14:01, each comparing 1,031,168 bytes, 1,073,741,824 bytes, & 254,475,764,224 bytes:

```text
started 2026-07-25T01:34:39-04:00 - Toshiba THNSF5256GPUK ****TALT (sdb) vs verified WD copy (sdc)
--- partition 1 (1031168 bytes) ---
p1 IDENTICAL
--- partition 2 (1073741824 bytes) ---
p2 IDENTICAL
--- partition 3 (254475764224 bytes) ---
p3 IDENTICAL
finished 2026-07-25T02:14:01-04:00
```

The partition table it cloned, with the disk-unique UUID tails redacted:

```text
label: gpt
label-id: 7573A5D4-<REDACTED>
device: /dev/sdb
unit: sectors
first-lba: 34
last-lba: 500118158
sector-size: 512

/dev/sdb1 : start=          34, size=        2014, type=21686148-6449-6E6F-744E-656564454649
/dev/sdb2 : start=        2048, size=     2097152, type=C12A7328-F81F-11D2-BA4B-00A0C93EC93B
/dev/sdb3 : start=     2099200, size=   497022977, type=E6D6D379-F507-44C2-A23C-238F2A3DF928
```

`purple-clone/sdb-gpt.bin` was a 17,920-byte binary dump of the same table. I did not retain it, because `sdb.sfdisk` above is the same information in text and the drive it described is now Purple's boot device.

## Verification

```text
Quorate:          Yes
Expected votes:   5
Total votes:      5
```

```text
grey-server    strays=0 wtbak=0 firstboot=0 fblog=0 oldsata=0 | helper=ok hook=ok sshcfg=a9b168c6
purple-server  strays=0 wtbak=0 firstboot=0 fblog=0 oldsata=0 | helper=ok hook=ok sshcfg=a9b168c6
blue-server    strays=0 wtbak=0 firstboot=0 fblog=0 oldsata=0 | helper=ok hook=ok sshcfg=a9b168c6
red-server     strays=0 wtbak=0 firstboot=0 fblog=0 oldsata=0 | helper=ok hook=ok sshcfg=a9b168c6
green-server   strays=0 wtbak=0 firstboot=0 fblog=0 oldsata=0 | helper=ok hook=ok sshcfg=a9b168c6
```

Every node reports two `NoMoreNagging` markers in `proxmoxlib.js`. All seven of `pve-cluster`, `corosync`, `pvedaemon`, `pveproxy`, `pvestatd`, `pve-firewall`, & `pvescheduler` are active on all five. `pvesh get /nodes` lists all five online. Blue still runs CT 104, CT 107, & CT 108. `promtool check config` passes on `monitor-01` and the API reports 49 active targets with 49 up.

The `galaxy-pxe` & `tftpd-hpa` services are active on `ansible-01` and `/health` returns `ok` with HTTP 200.

## Still Open

Three items I did not act on. I closed the first two on 2026-08-01; see [Galaxy Cluster PVE 9.2.6 Upgrade and SSH Host Key Seeding](../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Cluster%20PVE%209.2.6%20Upgrade%20and%20SSH%20Host%20Key%20Seeding%20-%202026-08-01.md).

**Closed 2026-08-01.** Red still holds `PeaNUT-S03-NUT-Configure-red-server-2026-07-22.txt`, `PeaNUT-S03-NUT-Package-Install-red-server-2026-07-22.txt`, & `PeaNUT-S06-Verification-red-server-2026-07-22.txt` in `/root`, 91 lines across the three. The 65-line install transcript is almost entirely `apt` progress redraws. The [PeaNUT records](../../Platforms/PeaNUT/README.md) already carry the outcomes, including the exit code 3 that the configure transcript shows. I left all three rather than delete evidence from work I wasn't reviewing. Two of the three turned out to be byte-identical to transcripts already captured under undated filenames, so only the configure run needed keeping. I added it to the PeaNUT evidence index and deleted all three from Red.

**Closed 2026-08-01.** The empty `/etc/pve/priv/known_hosts` and `ssh_known_hosts` state described above needs a decision. It breaks ad-hoc root SSH between every pair of members, not just Green. I seeded the cluster store with 15 key lines covering all five nodes, which exposed two further gaps I'd missed here: the `/etc/ssh/ssh_known_hosts` symlink that reads that store existed only on Grey, and no node's `/etc/hosts` listed its peers. All 20 ordered pairs now verify by name and by IP.

Grey carries `.claude`, `.claude.json`, & `.codex` in `/root`. Those are agent configuration rather than artifacts of this work, and they predate it.
