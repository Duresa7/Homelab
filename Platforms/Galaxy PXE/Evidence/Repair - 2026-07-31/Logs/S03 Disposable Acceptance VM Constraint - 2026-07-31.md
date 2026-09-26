# S03 Disposable Acceptance VM Runs

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

**Capture date:** 2026-07-31  
**Targets:** `red-server`, disposable VM 999, `ansible-01`, and UniFi  
**Mechanisms:** SSH Manager, QEMU framebuffer capture, and UniFi controller readback  
**Transcript boundary:** I retained the exact VM, state, cleanup, and structured success results. The first packet capture and QEMU framebuffer text were inspected live, but their complete raw transcripts were not retained in the repository.

## Initial Blocked Test

The first disposable UEFI VM emitted VLAN 5 DHCP discovers, but no offer returned and `ansible-01` received no request. I destroyed that VM and returned its acceptance state to `disabled`.

Afterward I explicitly admitted `Server-Provision`/VLAN 5 as tagged traffic on `Proxmox-Trunk`. The live profile `698cc29d10cb5676c296c7c1` used `forward=customize`, excluded only Management, IoT, Trusted, DMZ, and Secure, and did not exclude network `6a6be56f052792cd21414a99`.

## VM Creation Command

I verified VM ID 999 was absent, then issued:

```bash
qm create 999 \
  --name pxe-acceptance \
  --description 'Disposable Galaxy PXE acceptance test' \
  --memory 7168 \
  --cores 2 \
  --cpu host \
  --machine q35 \
  --bios ovmf \
  --ostype l26 \
  --scsihw virtio-scsi-single \
  --scsi0 local-lvm:32,discard=on,iothread=1 \
  --efidisk0 local-lvm:1,efitype=4m,pre-enrolled-keys=0 \
  --net0 virtio=02:00:00:00:09:99,bridge=vmbr0,tag=5,firewall=0 \
  --boot 'order=net0' \
  --serial0 socket \
  --onboot 0
qm start 999
qm status 999
```

The command exited `0`. Proxmox created both logical volumes and returned `status: running`.

## Post-Change Run 1: 7 GiB Memory Failure

The VM claimed attempt `<PXE_ATTEMPT_ID_1>` at `05:36:42 UTC`. Its network counter reached 1.82 GB, proving the full PXE asset path crossed VLAN 5.

The inspected QEMU framebuffer showed:

```text
Initramfs unpacking failed: write error
dd: error writing '/etc/hostid': No space left on device
mount: mounting /dev/loop2 on /mnt/.installer failed: Invalid argument
[ERROR] mount /mnt/pve-installer.squashfs failed
```

The service remained at `installer_claimed` because the installer could not start far enough to request an answer. I stopped the VM and raised its memory to 12 GiB.

## Post-Change Run 2: Answer Value Failure

The 12 GiB VM claimed attempt `<PXE_ATTEMPT_ID_2>`, requested its answer, and moved to `answer_served`.

The inspected framebuffer then showed:

```text
ERROR: Autoinstaller setup error: TOML parse error at line 10, column 15
10 | reboot-mode = "poweroff"
unknown variant `poweroff`, expected `reboot` or `power-off`
Auto-installation failed (exit-code 1)
```

I corrected the acceptance answer to `reboot-mode = "power-off"`, reran its unit test, uploaded the change, and redeployed the service.

## Post-Change Run 3: Successful Install

The corrected 12 GiB VM claimed attempt `<PXE_ATTEMPT_ID_3>` at `05:46:56 UTC`. It moved to `answer_served` at `05:48:08 UTC` and posted this sanitized installer result at `05:50:08 UTC`:

```json
{
  "boot_disks": [
    "/dev/sda"
  ],
  "boot_info": {
    "mode": "efi"
  },
  "filesystem": "ext4",
  "fqdn": "pxe-acceptance.galaxy",
  "network_interfaces": [
    {
      "address": "192.168.5.143/24",
      "mac": "02:00:00:00:09:99",
      "name": "nic0"
    }
  ],
  "other_disks": [],
  "schema_version": "1.2"
}
```

The state moved to `installer_succeeded`. `qm status 999` returned:

```text
status: stopped
```

This proves the UEFI PXE path, DHCP, complete installer asset, answer fetch, automatic disk install, expected boot-disk check, post-installation webhook, and `power-off` behavior.

## Cleanup Command

After matching the stopped VM's name, I issued:

```bash
set -eu
test "$(qm status 999)" = "status: stopped"
test "$(qm config 999 | sed -n 's/^name: //p')" = "pxe-acceptance"
qm destroy 999 --purge 1 --destroy-unreferenced-disks 1
test ! -e /etc/pve/qemu-server/999.conf
! lvs --noheadings -o lv_name | grep -q 'vm-999-disk'
rm -f /tmp/pxe-acceptance.ppm /tmp/pxe-acceptance-12g.ppm
```

The complete output was:

```text
Logical volume "vm-999-disk-1" successfully removed.
Logical volume "vm-999-disk-0" successfully removed.
purging VM 999 from related configurations..
```

The command exited `0`. VM 999, both logical volumes, and both temporary remote captures are not recoverable. I returned acceptance MAC `02:00:00:00:09:99` to `disabled`.
