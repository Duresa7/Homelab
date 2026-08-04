# S01 Green Extended SMART and Metadata Wipe

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

**Capture time:** 2026-07-31 09:47 through 10:27 EDT  
**Target:** Green's unused Hitachi HTS723232A7A364 SATA HDD  
**Mechanism:** SSH Manager through `grey-server`, root Bash on Green  
**Published redaction:** The exact by-id serial and serial comparison are replaced with contextual placeholders.

## Extended Test Result

I captured the full `smartctl -x` report before writing any metadata. The material result was:

```text
SMART overall-health self-assessment test result: PASSED
Reallocated_Sector_Ct=0
Power_On_Hours=43950
Current_Pending_Sector=2
Offline_Uncorrectable=0
UDMA_CRC_Error_Count=0
# 1 Extended offline Completed: read failure 60% 43950 246502720
```

The top-level assessment did not detect the failed read. I classified the disk from the completed self-test and the increase from one pending sector to two.

## Guarded Wipe Command

```bash
set -euo pipefail
disk_id=<REDACTED_GREEN_HDD_BY_ID>
expected_serial=<REDACTED_GREEN_HDD_SERIAL>
expected_bytes=320072933376
disk=$(readlink -f "$disk_id")
serial=$(lsblk -dn -o SERIAL "$disk" | xargs)
bytes=$(lsblk -bdn -o SIZE "$disk" | xargs)
type=$(lsblk -dn -o TYPE "$disk" | xargs)
mounts=$(lsblk -nr -o MOUNTPOINTS "$disk" | sed '/^[[:space:]]*$/d' || true)
lvm_refs=$(pvs --noheadings -o pv_name 2>/dev/null | xargs -n1 | grep -E "^${disk}([0-9]+|p[0-9]+)?$" || true)
zfs_refs=$(zpool status -P 2>/dev/null | grep -F "$disk" || true)
config_refs=$(grep -RFn "$disk" /etc/pve/storage.cfg /etc/fstab 2>/dev/null || true)
swap_refs=$(swapon --noheadings --raw --show=NAME 2>/dev/null | grep -E "^${disk}([0-9]+|p[0-9]+)?$" || true)
test "$disk" = /dev/sda
test "$serial" = "$expected_serial"
test "$bytes" = "$expected_bytes"
test "$type" = disk
test -z "$mounts"
test -z "$lvm_refs"
test -z "$zfs_refs"
test -z "$config_refs"
test -z "$swap_refs"
if smartctl -a "$disk_id" | grep -q 'Self-test routine in progress'; then
    echo 'Refusing wipe while SMART self-test is active' >&2
    exit 50
fi
sgdisk --zap-all "$disk"
wipefs --all --force "$disk"
blockdev --rereadpt "$disk"
udevadm settle
test -z "$(wipefs --no-act "$disk")"
test -z "$(blkid "$disk" 2>/dev/null || true)"
test -z "$(lsblk -nr -o PTTYPE,FSTYPE "$disk" | tr -d '[:space:]')"
```

```text
validated_target=<REDACTED_GREEN_HDD_BY_ID> model=HTS723232A7A364 serial_suffix=G91N bytes=320072933376 in_use=no
GPT data structures destroyed! You may now partition the disk using fdisk or other utilities.
verification=blank_no_pttype_no_fstype_no_signature
NAME TYPE   SIZE PTTYPE FSTYPE MOUNTPOINTS
sda  disk 298.1G
Exit code: 0
```

## Post-Wipe Verification

```text
SMART overall-health self-assessment test result: PASSED
Current_Pending_Sector=2
# 1 Extended offline Completed: read failure 60% 43950 246502720
lsblk: no PTTYPE, FSTYPE, or mount on /dev/sda
wipefs: no signature
Green local: active
Green local-lvm: active
Galaxy: 5 expected votes, 5 total votes, Quorate: Yes
Prometheus: green-server up=1
Exit code: 0
```

The metadata wipe did not repair or hide the SMART failure. The disk is blank and remains unsuitable for storage.

