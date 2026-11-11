#!/bin/bash
# Phase B, runs on grey-server with VM 109 stopped. usage: splunk-cutover.sh <old-lv> <new-lv>
# Copies partitions 1 and 2 by byte offset, so the guest's LVM PV on partition 3 is never
# exposed to the host as a block device and cannot be auto-activated there.
set -euo pipefail
V=109; OLD=/dev/ssd-lvm1/$1; NEW=/dev/ssd-lvm1/$2
qm status $V | grep -q 'status: stopped' || { echo "VM $V not stopped"; exit 1; }
lvchange -ay "$OLD" "$NEW"
PO=$(sfdisk -d "$OLD" | grep 'start=' | sed -E 's/^[^:]*: //; s/, uuid=[^,]*//; s/, name=.*//' | head -2)
PN=$(sfdisk -d "$NEW" | grep 'start=' | sed -E 's/^[^:]*: //; s/, uuid=[^,]*//; s/, name=.*//' | head -2)
echo "old p1-p2: $PO"; echo "new p1-p2: $PN"
[ "$PO" = "$PN" ] || { echo "partition 1-2 layout differs"; exit 1; }
copy() { # start-sector size-sectors, both whole MiB (multiples of 2048)
  local s=$1 n=$2
  [ $(( s % 2048 )) -eq 0 ] && [ $(( n % 2048 )) -eq 0 ] || { echo "not MiB aligned: $s $n"; exit 1; }
  dd if="$OLD" of="$NEW" bs=1M skip=$(( s / 2048 )) seek=$(( s / 2048 )) count=$(( n / 2048 )) conv=notrunc,fsync status=none
  cmp -n $(( n * 512 )) -i $(( s * 512 )):$(( s * 512 )) "$OLD" "$NEW" && echo "sectors $s+$n copied and identical"
}
copy 2048 1228800
copy 1230848 4194304
sfdisk --no-reread --no-tell-kernel --disk-id "$NEW" "$(sfdisk --disk-id "$OLD")"
for p in 1 2 3; do sfdisk --no-reread --no-tell-kernel --part-uuid "$NEW" $p "$(sfdisk --part-uuid "$OLD" $p)"; done
echo "--- old"; sfdisk -d "$OLD" | grep -E 'label-id|start='
echo "--- new"; sfdisk -d "$NEW" | grep -E 'label-id|start='
blkid -p -O $(( 2048 * 512 )) "$NEW" | sed 's/^/new p1: /'
blkid -p -O $(( 1230848 * 512 )) "$NEW" | sed 's/^/new p2: /'
qm set $V --delete scsi0,scsi1
qm set $V --scsi0 "ssd-lvm1:$2,discard=on,iothread=1,ssd=1" --boot 'order=scsi0;net0'
qm config $V | grep -E '^(scsi|unused|boot)'
echo CUTOVER-DONE
