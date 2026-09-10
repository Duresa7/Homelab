# HQ-WS001 Workstation Join

**Created:** 2026-09-10  
**Last updated:** 2026-09-10

I built `HQ-WS001`, a Windows 11 Pro test workstation, and joined it to `ad.alphasecunited.com` on 2026-09-10. The point was not the workstation. It was to prove that the Tier 2 local-administrator policy and Windows LAPS actually reach a client, which until now had only been demonstrated on a member server.

Both claims are proven. The evidence is at the end.

## The guest

VM 310 on `grey-server`, cloned from nothing: this is a fresh install from `Win11_25H2_English_x64.iso`, not from the Windows Server 2025 template.

| Setting | Value |
|---|---|
| Address | `192.168.65.20/24`, gateway `192.168.65.1` |
| DNS | `192.168.65.10` then `192.168.65.11` |
| Firmware | OVMF with a TPM 2.0 device, which Windows 11 requires |
| Disk | 80G on `ssd-lvm1`, virtio-scsi |
| Memory | 4 GiB |
| Organisational unit | `OU=Standard,OU=Workstations` |

Memory is 4 GiB rather than 8 because `grey-server` was running 51 GiB of its 62 GiB when I built this. An 8 GiB guest would have left about 2 GiB of headroom on the hypervisor. Windows 11 runs acceptably on 4 GiB for a policy test.

## Windows 11 25H2 rejects a scripted DiskPart answer file

The first answer file drove partitioning with a hand-written DiskPart script executed through `RunSynchronous` in the `windowsPE` pass. Setup failed with `0x80070103 - 0x40031`, which is `ERROR_NO_MORE_ITEMS`, after partitioning had already succeeded and before the image was applied.

I confirmed the disk really had been partitioned by reading the partition table off the volume from the hypervisor rather than trusting the installer:

```
sfdisk -l /dev/ssd-lvm1/vm-310-disk-1
```

It returned the intended layout: a 260 MB EFI system partition, a 16 MB Microsoft reserved partition, a 78.2 GB Windows partition, and a 1.5 GB recovery partition. So DiskPart ran, and the virtio storage driver had loaded, since DiskPart could see the disk at all.

Two hypotheses were wrong, and both were cheap to test:

- **Duplicate edition selection.** The file specified both a product key and an `InstallFrom` image name. I confirmed `Windows 11 Pro` really is in the media, at index 6 of 11, by reading the XML resource out of the `install.wim` header. Removing the duplicate changed nothing.
- **Twelve driver paths across three drive letters,** only one of which is the virtio disc. Cutting it to three `vioscsi` entries changed nothing.

What settled it was booting Setup with the answer file detached. It reached the normal language screen, which proved the media, firmware, TPM and disk were all fine and the fault was entirely in the answer file.

Rebuilding the file on the documented `DiskConfiguration` element, with `WillWipeDisk` and declared partitions instead of scripted DiskPart, installed on the first attempt. **On this Windows build, use `DiskConfiguration`. Do not script DiskPart through `RunSynchronous` in `windowsPE`.**

## Three traps that cost time

**The boot prompt expires.** `Press any key to boot from CD or DVD` times out in a few seconds and then falls through to `No bootable option or device was found`. Nothing presses that key on an unattended build, so the VM sits at a dead firmware prompt looking like a broken disk. Send keys immediately after start:

```bash
qm start 310
for i in $(seq 1 30); do qm sendkey 310 ret; qm sendkey 310 spc; sleep 1; done
```

**A hot-plugged CD-ROM does not appear until the VM is power-cycled.** I attached the join package as a SATA disc while the guest was running and then restarted the guest from inside. The guest kept showing the previous disc's contents, because a guest-initiated reboot does not rebuild the emulated device model. A full `qm stop` and `qm start` is required. That is the one place a power cycle is correct.

**Install the QEMU guest agent at first logon, not later.** The answer file installs the virtio guest tools as its first first-logon command, before anything else. That single installer brings the network driver, the balloon driver and the guest agent together. It mattered: the OpenSSH Server capability never installed on this machine, so `qm guest exec` was the only channel into it for the entire build. Without the agent there would have been no way in except the console.

OpenSSH is still absent. `Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0` returns `NotPresent` after running, and `Get-WindowsCapability -Online` itself hangs long enough to exceed a 60-second timeout while the servicing stack is busy. A pending reboot left over from the guest-tools install blocked servicing initially; clearing that did not fix the capability install. The machine has working outbound HTTPS, confirmed with a `200` from a live request, so this is not a network path problem. It is unresolved and recorded as such.

## Joining without a domain administrator password

A normal `Add-Computer` needs a credential, and any value passed to `qm guest exec` lands in the Proxmox task log. So I used an offline domain join instead, which needs no administrator password anywhere.

The domain controller provisions the join package in its own machine context, running as `NT AUTHORITY\SYSTEM` through the guest agent:

```powershell
djoin.exe /provision /domain 'ad.alphasecunited.com' /machine 'HQ-WS001' `
  /machineou 'OU=Standard,OU=Workstations,DC=ad,DC=alphasecunited,DC=com' `
  /savefile 'C:\Windows\Temp\ws001odj.txt' /reuse
```

Pass the arguments from PowerShell variables. Sending that command through `cmd /c` mangled the quoting around the organisational unit path, whose commas `cmd` treats as delimiters, and it failed with `0x57`, the parameter is incorrect.

I then moved the package to the workstation on a virtual disc rather than through a command line, so the machine password never appeared in an argument or a log. The package is read off the controller through the API and decoded straight to a file, never printed:

```bash
pvesh get /nodes/grey-server/qemu/301/agent/file-read --file 'C:\Windows\Temp\ws001odj.b64' --output-format json \
  | python3 -c 'import sys,json,base64; d=json.load(sys.stdin); open("/root/odj/ws001odj.txt","wb").write(base64.b64decode(d["content"].strip()))'
genisoimage -J -R -o /var/lib/vz/template/iso/ws001-odj.iso /root/odj/ws001odj.txt
```

The workstation consumes it with `djoin /requestODJ /loadfile <drive>:\ws001odj.txt /windowspath C:\Windows /localos` and a reboot. Afterwards every copy was shredded: the file on the controller, the decoded copy on the hypervisor, and the disc image.

The join package is single use and is invalidated once the machine joins, so it is a far smaller thing to move around than a Tier 0 credential. That is the reason to prefer this route, not convenience.

## A hard power-off rolled the join back

The first attempt failed in a way worth recording. After applying the join I used `qm stop`, which is a power cut rather than a shutdown, to detach the disc. The machine came up in Automatic Repair reporting `Your PC did not start correctly`. A restart recovered it, but the repair had rolled back the pending transaction: the machine was back in `WORKGROUP` with the join undone.

The computer object in Active Directory survived, so re-provisioning with `/reuse` and repeating the join worked. The second time I used `qm shutdown` for the power cycle and `Restart-Computer` from inside the guest to complete the join. **Never hard-stop a Windows guest between applying an offline join and its completing reboot.**

## Verification

Read back on 2026-09-10 after the join.

From the workstation, through the guest agent:

| Check | Result |
|---|---|
| Domain membership | `PartOfDomain=True`, domain `ad.alphasecunited.com` |
| Secure channel | `Test-ComputerSecureChannel` returned `True` |
| Site | `HQ`, resolved from the subnet mapping |
| Time source | `HQ-DC02.ad.alphasecunited.com` |
| Applied policy | `C-CMP-LAPS`, `C-WKS-LocalAdmins`, `Default Domain Policy` |
| Local `Administrators` | `ALPHASEC\ADM-T2-WorkstationAdmins`, `ALPHASEC\Domain Admins`, `HQ-WS001\Administrator` |

From `HQ-DC01`, reading the computer object:

| Check | Result |
|---|---|
| Location | `CN=HQ-WS001,OU=Standard,OU=Workstations` |
| Operating system | `Windows 11 Pro`, self-registered |
| `msLAPS-EncryptedPassword` | populated |
| Password expiry | 2026-10-10, which matches the 30-day rotation in `C-CMP-LAPS` |

**Both claims hold.** `ALPHASEC\ADM-T2-WorkstationAdmins` is in the local `Administrators` group because `C-WKS-LocalAdmins` put it there, and Windows LAPS manages this workstation's local administrator password. The Tier 2 model and LAPS both reach a client, not only a member server.

The temporary local administrator password that the answer file set is now irrelevant: LAPS generated and stored a new one when the policy applied, so the directory holds the authoritative value.

## Activation

Later on 2026-09-10 I activated Windows 11 Pro on `HQ-WS001` with a retail key and rebooted it. Read through the guest agent afterwards, `SoftwareLicensingProduct` reports `LicenseStatus` `1`, which is Licensed, on the `Retail` channel, with the last boot at 12:07 the same day. The key itself is a credential and is not recorded here.

## Open

OpenSSH Server is not installed, so `HQ-WS001` is not in SSH Manager. The guest agent is the working management channel. This is the only unfinished item.
