# Evidence Index

**Created:** 2026-09-09  
**Last updated:** 2026-09-09

I built this forest through a shell, so the retained captures are command output rather than images. This index reserves the screenshot slots that are worth filling, names each file exactly, and says what has to be blacked out before the image is committed.

Drop a file into `Screenshots/` using the filename in the table, then allowlist it in the root `.gitignore` under the block for this folder. The guide already carries the matching image line for each slot, commented out directly beneath the step it belongs to, so publishing a screenshot is a matter of dropping the file in and removing the comment markers.

## Slots

| File | What it should show | Redact before committing |
|---|---|---|
| `S01-Proxmox-HQ-DC01-Hardware-2026-09-09.png` | VM 301 hardware in Proxmox: OVMF firmware, TPM 2.0 v2.0, virtio-scsi-single, VLAN 65 | The `net0` MAC address |
| `S02-Forest-Promotion-Result-2026-09-09.png` | The promotion result for `HQ-DC01`, showing the forest and domain name and the functional level | Nothing, provided no credential prompt is on screen |
| `S03-OU-Tree-2026-09-09.png` | Active Directory Users and Computers with the tiered organisational unit tree expanded | Nothing |
| `S04-Sites-And-Subnets-2026-09-09.png` | Sites and Services: site `HQ` with the three mapped subnets | Nothing |
| `S05-DNS-Zones-2026-09-09.png` | DNS Manager on `HQ-DC01` with the three zones, the forwarder, and scavenging | Nothing |
| `S06-Group-Policy-Objects-2026-09-09.png` | Group Policy Management showing the three custom policies and their links | Nothing |
| `S07-LAPS-Password-Retrieved-2026-09-09.png` | `Get-LapsADPassword` returning a managed password for `HQ-MGT01`, proving the end-to-end path | **The password itself and the account name field.** Leave the expiry visible; that is the part worth showing |
| `S08-MGT01-Local-Administrators-2026-09-09.png` | `ALPHASEC\ADM-T1-ServerAdmins` inside the local `Administrators` group on `HQ-MGT01`, applied by policy | Nothing |
| `S09-Password-Policies-2026-09-09.png` | The default domain password policy and `PSO-Admins` side by side | Nothing |

## Standing redaction rules

These apply to every image in this folder, not only the slots above.

- No password, DSRM password, recovery key, or API token in any frame, including a partially typed field or a shell scrollback.
- No MAC address, drive serial, or WWN.
- No WAN address.
- Nothing naming the password manager, including a browser tab, an extension icon, or a window title.
- Internal hostnames, internal IPv4 addresses, the domain, the organisation name, usernames, and my own name are all published on purpose and do not need masking.

Black out by painting over the region, not by cropping alone when the value sits mid-frame, and not by blurring. A blur can be reversed.
