# S02 Blue Extended SMART Result

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

**Capture time:** 2026-07-31 11:22 through 11:36 EDT  
**Target:** Blue's unused WDC WD5000LPVX-08V0TT5 SATA HDD, serial suffix `6NSN`  
**Mechanism:** SSH Manager `ssh_execute` on `blue_server`, root shell  
**Published redaction:** The retained capture replaces the drive serial and WWN with contextual placeholders.

## The Self-Test Log Showed a Stale Completed Entry

At 11:22 EDT the self-test log looked finished, and it wasn't:

```text
Num  Test_Description    Status                  Remaining  LifeTime(hours)  LBA_of_first_error
# 1  Vendor (0x50)       Completed without error       00%         0         -
```

That entry is a stale vendor-specific record with a `LifeTime` of 0 hours against a drive at 23,215 power-on hours. Reading `-l selftest` alone would have recorded a pass while the extended test was still writing. The authoritative field is the execution status:

```sh
smartctl -c /dev/sda | sed -n '/Self-test execution status/,+2p'
```

```text
Self-test execution status:      ( 241)	Self-test routine in progress...
					10% of test remaining.
```

Status `241` means running. I waited rather than recording a result.

## Completed Result

```sh
date; smartctl -c /dev/sda | sed -n '/Self-test execution status/,+2p'; smartctl -l selftest /dev/sda | tail -4
```

```text
Fri Jul 31 11:32:15 AM EDT 2026
Self-test execution status:      (   0)	The previous self-test routine completed
					without error or no self-test has ever 
					been run.
Num  Test_Description    Status                  Remaining  LifeTime(hours)  LBA_of_first_error
# 1  Extended offline    Completed without error       00%     23215         -
# 2  Vendor (0x50)       Completed without error       00%         0         -
```

The extended test covered the whole disk and logged no failing LBA. Entry `# 1` is the real result; `# 2` is the same stale vendor record, now pushed down the log.

## Post-Test Counters

```text
SMART overall-health self-assessment test result: PASSED
  5 Reallocated_Sector_Ct   200 200 140  Pre-fail  -  0
  9 Power_On_Hours          069 069 000  Old_age   -  23215
194 Temperature_Celsius     099 091 000  Old_age   -  44
196 Reallocated_Event_Count 200 200 000  Old_age   -  0
197 Current_Pending_Sector  200 200 000  Old_age   -  0
198 Offline_Uncorrectable   100 253 000  Old_age   -  0
199 UDMA_CRC_Error_Count    200 200 000  Old_age   -  0
```

All four critical counters read 0 after a full surface read. `Start_Stop_Count` is 7,833 and `Load_Cycle_Count` is 45,179, both high for a 23,215-hour drive but neither is a defect counter.

The drive ran hot under test. Its SCT table reports a 48 C peak this power cycle against a `Specified Max Operating Temperature` of 32 C, with a 52 C lifetime maximum. `Under/Over Temperature Limit Count` stayed at `0/0` because SCT sets that trip point at 60 C.

## Disk State After the Test

```sh
wipefs /dev/sda; blkid /dev/sda; lsblk /dev/sda; pvs
```

```text
DEVICE OFFSET       TYPE UUID LABEL
sda    0x200        gpt       
sda    0x7470c05e00 gpt       
sda    0x1fe        PMBR      
/dev/sda: PTUUID="c1b522dc-9a59-4887-8e23-427e44bdd4c6" PTTYPE="gpt"
NAME MAJ:MIN RM   SIZE RO TYPE MOUNTPOINTS
sda    8:0    0 465.8G  0 disk 
  PV             VG  Fmt  Attr PSize   PFree 
  /dev/nvme0n1p3 pve lvm2 a--  237.47g 16.00g
```

This contradicted [S03](../../../../../Security/Incidents/Galaxy-Blue-Server-Duplicate-VG-2026-07-30/Evidence/Logs/S03%20WDC%20Disk%20Wipe%20-%202026-07-31.md), which verified an empty `wipefs` read at about 00:00 EDT. The Proxmox task log explains the gap:

```sh
grep -riE "sda|initgpt|wipedisk" /var/log/pve/tasks/index | tail
```

```text
UPID:blue-server:00095631:00350E24:6A6C9ECD:wipedisk:sda:root@pam: 6A6C9ECF OK
UPID:blue-server:000956A9:00350FE2:6A6C9ED1:diskinit:sda:root@pam: 6A6C9ED3 OK
```

`journalctl` timestamps both at 09:10:37 and 09:10:39 EDT on 2026-07-31, nine hours after the S03 wipe. A `wipedisk` then `diskinit` pair from the Proxmox disk view wrote the fresh empty GPT. The partition table holds zero partitions, the disk carries no filesystem and no LVM PV, and `pvs` lists only `/dev/nvme0n1p3` in VG `pve`. Nothing regressed; the disk is one step further prepared than S03 recorded.

## Retained Capture

```sh
smartctl -x /dev/sda | sed -E 's/^Serial Number:.*/Serial Number: <YOUR_DRIVE_SERIAL>/; s/^LU WWN Device Id:.*/LU WWN Device Id: <YOUR_DRIVE_WWN>/'
```

The sanitized 202-line result is stored as [smartctl-a_WD5000LPVX_6NSN_2026-07-31.txt](../../../Components/Drives/HDD/smartctl-a_WD5000LPVX_6NSN_2026-07-31.txt). I confirmed the stored file carries no serial or WWN string and that its tab-delimited layout matches the drive's own output.

**Exit code:** `0` on every command above.
