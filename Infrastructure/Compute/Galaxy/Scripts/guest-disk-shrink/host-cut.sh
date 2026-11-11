#!/bin/bash
# usage: host-cut.sh <vmid> <disk-lv-name> <sizeGiB>
set -euo pipefail
V=$1; LV=ssd-lvm1/$2; G=$3; DEV=/dev/$LV
qm status "$V" | grep -q 'status: stopped' || { echo "VM $V not stopped"; exit 1; }
lvchange -ay "$LV"
TS=$(( G * 1024 * 1024 * 2 ))
MAXEND=$(sfdisk -d "$DEV" | awk -F'[=,]' '/start=/{s=$2+0; z=$4+0; e=s+z; if(e>m)m=e} END{print m}')
echo "target sectors=$TS last partition end=$MAXEND"
[ "$MAXEND" -le $(( TS - 2048 )) ] || { echo 'partitions do not fit'; exit 1; }
qm snapshot "$V" preshrink --description 'Rollback point before disk shrink, 2026-11-11'
lvreduce -y --fs ignore -L "${G}g" "$LV"
sgdisk -e "$DEV"
sgdisk -v "$DEV"
qm rescan --vmid "$V"
qm config "$V" | grep -E '^scsi0'
lvs -o lv_name,lv_size,data_percent "$LV"
