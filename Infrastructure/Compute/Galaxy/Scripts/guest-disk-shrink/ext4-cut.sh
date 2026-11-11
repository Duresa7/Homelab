#!/bin/bash
# usage: ext4-cut.sh <vmid> <disk-lv-name> <partno> <sizeGiB>
# Shrinks an ext4 partition that is the LAST partition on a GPT disk, then cuts the LV.
set -euo pipefail
V=$1; LV=ssd-lvm1/$2; N=$3; G=$4; DEV=/dev/$LV
LOOP=""
cleanup() { [ -n "$LOOP" ] && losetup -d "$LOOP" 2>/dev/null || true; }
trap cleanup EXIT
qm status "$V" | grep -q 'status: stopped' || { echo "VM $V not stopped"; exit 1; }
lvchange -ay "$LV"
TS=$(( G * 1024 * 1024 * 2 ))
LINE=$(sfdisk -d "$DEV" | grep -E "^${DEV}${N} :|^/dev/[^ ]*${N} :" | head -1)
START=$(echo "$LINE" | sed -E 's/.*start= *([0-9]+).*/\1/')
OLDSIZE=$(echo "$LINE" | sed -E 's/.*size= *([0-9]+).*/\1/')
LASTEND=$(sfdisk -d "$DEV" | awk -F'[=,]' '/start=/{e=$2+$4; if(e>m)m=e} END{print m}')
[ $(( START + OLDSIZE )) -eq "$LASTEND" ] || { echo "partition $N is not the last partition"; exit 1; }
NEWSIZE=$(( TS - 2048 - START ))
FSK=$(( NEWSIZE / 2 - 1048576 ))
echo "partition $N start=$START oldsize=$OLDSIZE newsize=$NEWSIZE fs-interim=${FSK}K"
echo "orig: $LINE"
qm snapshot "$V" preshrink --description 'Rollback point before disk shrink, 2026-11-11'
LOOP=$(losetup -fP --show "$DEV")
P=${LOOP}p${N}
blkid "$P"
set +e; e2fsck -f -p "$P"; RC=$?; set -e
[ $RC -le 1 ] || { echo "e2fsck rc=$RC, stopping"; exit 1; }
resize2fs "$P" "${FSK}K"
NEWLINE=$(echo "$LINE" | sed -E "s/^[^:]*: //; s/size= *[0-9]+/size=$NEWSIZE/")
echo "new:  $NEWLINE"
echo "$NEWLINE" | sfdisk --no-reread --no-tell-kernel -N "$N" "$LOOP"
losetup -d "$LOOP"; LOOP=""
LOOP=$(losetup -fP --show "$DEV"); P=${LOOP}p${N}
GOT=$(( $(blockdev --getsize64 "$P") / 512 ))
[ "$GOT" -eq "$NEWSIZE" ] || { echo "partition size $GOT != $NEWSIZE"; exit 1; }
resize2fs "$P"
set +e; e2fsck -f -n "$P"; RC=$?; set -e
[ $RC -eq 0 ] || { echo "post-resize e2fsck rc=$RC, stopping"; exit 1; }
blkid "$P"
losetup -d "$LOOP"; LOOP=""
sfdisk -d "$DEV" | grep -E 'start='
lvreduce -y --fs ignore -L "${G}g" "$LV"
sgdisk -e "$DEV"
sgdisk -v "$DEV"
qm rescan --vmid "$V"
qm config "$V" | grep -E '^scsi0'
lvs -o lv_name,lv_size,data_percent "$LV"
echo EXT4-CUT-DONE
