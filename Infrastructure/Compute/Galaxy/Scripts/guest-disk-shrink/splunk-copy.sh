#!/bin/bash
# Phase A, runs inside splunk-siem as root. New blank 100G disk must be /dev/sdb.
set -euo pipefail
NEW=/dev/sdb
OLDROOTUUID=505f66a7-ac00-42b9-9298-af0241dc7e05
SWAPUUID=22959ff4-00d5-41f6-8e7b-0454fa5ada7b
step() { echo "=== $(date +%T) $*"; }
step checks
[ "$(lsblk -bdno SIZE $NEW)" = 107374182400 ] || { echo "$NEW is not 100 GiB"; exit 1; }
[ -z "$(lsblk -no FSTYPE,PTTYPE $NEW | tr -d ' \n')" ] || { echo "$NEW is not blank"; exit 1; }
findmnt -no SOURCE / | grep -q '/dev/mapper/rl-root' || { echo "root is not rl-root"; exit 1; }
vgs rl_old >/dev/null 2>&1 && { echo "rl_old already exists"; exit 1; }
step partition $NEW
sfdisk $NEW <<PT
label: gpt
start=2048, size=1228800, type=C12A7328-F81F-11D2-BA4B-00A0C93EC93B, name="EFI System Partition"
start=1230848, size=4194304, type=BC13C2FF-59E6-4262-A352-B275FD6F7172
start=5425152, type=E6D6D379-F507-44C2-A23C-238F2A3DF928
PT
udevadm settle
sfdisk -d $NEW
step rename old VG and build new VG
vgrename rl rl_old
pvcreate -y ${NEW}3
vgcreate rl ${NEW}3
SWAPB=$(lvs --noheadings --units b --nosuffix -o lv_size rl_old/swap | tr -d ' ')
lvcreate -y -n swap -L ${SWAPB}b rl
lvcreate -y -n root -l 100%FREE rl
mkswap -U $SWAPUUID /dev/rl/swap
mkfs.xfs -q /dev/rl/root
lvs -o vg_name,lv_name,lv_size
mkdir -p /mnt/newroot
mount /dev/rl/root /mnt/newroot
step xfsdump to new root
xfsdump -l 0 -L splunkroot -M splunkroot -J - / | xfsrestore -J - /mnt/newroot
step fix fstab, devices file, initramfs
NEWUUID=$(blkid -s UUID -o value /dev/rl/root)
sed -i "s/UUID=$OLDROOTUUID/UUID=$NEWUUID/" /mnt/newroot/etc/fstab
grep -E '^UUID' /mnt/newroot/etc/fstab
rm -f /mnt/newroot/etc/lvm/devices/system.devices
for m in dev proc sys sys/fs/selinux run boot; do mount --bind /$m /mnt/newroot/$m; done
chroot /mnt/newroot restorecon -F /etc/fstab
chroot /mnt/newroot dracut -f --regenerate-all
chroot /mnt/newroot sh -c 'for f in /boot/initramfs-*.x86_64.img; do echo "$f: $(lsinitrd $f 2>/dev/null | grep -c system.devices) devices-file entries"; done'
for m in boot run sys/fs/selinux sys proc dev; do umount /mnt/newroot/$m; done
step compare
df -h / /mnt/newroot
du -sx --apparent-size -BM / /mnt/newroot 2>/dev/null
ls -Z /mnt/newroot/etc/shadow /mnt/newroot/etc/fstab
umount /mnt/newroot
sync
step SPLUNK-COPY-DONE
