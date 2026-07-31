# Green PXE Install Stalls Before Reboot

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

**Investigation date:** 2026-07-31  
**Status:** Resolved  
**Affected system:** `green-server`, MAC `<GREEN_NODE_MAC>`

## Symptom

Green loaded the PXE path and fetched the complete Proxmox installer, answer, and bootstrap script. It never appeared at `192.168.70.14`, never joined Galaxy, and never sent a first-boot callback. The original service state stayed `installing` for more than 40 minutes.

There was no target-side error text during the failed run because the M920q was in the rack without a connected display and had no out-of-band controller.

## Exact Observed Failure

The server log showed the initial boot request at `03:38:18 UTC`. It then served `boot.ipxe`, `vmlinuz`, `initrd.img`, and the PXE ISO. Proxmox requested the answer and bootstrap at `03:39:46 UTC`.

No later request came from the installed system. The cluster stayed at four quorate nodes and Green did not answer on MGMT-A.

The retained server trace is summarized in [S01](../../Evidence/Galaxy%20PXE%20Repair%20-%202026-07-31/Logs/S01%20Green%20First-Run%20Failure%20Trace%20-%202026-07-31.md). I did not retain an exact console error or complete target-side installer log.

## Failed Attempts

- I could not remotely reboot the powered M920q because it had no established operating-system path, Intel AMT session, managed PDU, or other out-of-band control.
- My first disposable UEFI VM run on Red emitted VLAN 5 DHCP discovers but received no offer. After I admitted `Server-Provision` tagged on `Proxmox-Trunk`, the VM reached `ansible-01`.
- The next VM used 7 GiB and failed while unpacking initramfs with `No space left on device`. A 12 GiB rerun cleared that failure.
- The first 12 GiB answer failed because acceptance-only `reboot-mode = "poweroff"` is not valid. I corrected it to `"power-off"`.
- The original password/API cluster join path was not usable. Even if the disk installation had completed, that path did not provide a proven unattended join.

## Hypotheses and Tests

| Hypothesis | Test or evidence | Result |
|---|---|---|
| PXE or TFTP failed before Proxmox loaded | HTTP and TFTP delivery history | Rejected. Green fetched the kernel, initrd, full ISO, answer, and bootstrap. |
| The Proxmox installer rejected the disk or hardware | The original local installation booted and reported Proxmox on `/dev/nvme0n1` | Rejected. |
| The installer framebuffer hung on the M920q | The original local installation booted; the rerun also completed with `nomodeset` present | Rejected as the cause of the first failure. |
| The large in-memory install needed more time | Green reported 16 GB installed RAM and the original installation booted | Rejected. |
| First boot could not reach the PXE service from VLAN 5 | The retained first-boot log showed connection failure to `192.168.40.36:8080`; the path passed after the UniFi policy was added | Confirmed primary cause. |
| First boot could fail during a service restart or on an ICMP-only gate | The rerun stopped before `network_ready`; callback retry and SSH-path changes allowed the same cached run to finish | Confirmed secondary defects. |

## Root Cause

The original installation completed on `/dev/nvme0n1`, but its first-boot script could not reach the PXE callback service at `192.168.40.36:8080` from native VLAN 5. The missing `Server-Provision` callback policy was the primary cause.

The physical rerun exposed two secondary first-boot defects. Callback fetches did not retry a refused connection while the PXE service restarted, and ICMP failure could block the sequence even when the required key-only SSH path worked. The earlier state machine and unattended join defects also remained valid findings from the service review.

## Corrective Action

- Added timestamped attempt IDs and ordered installer and first-boot states.
- Added Proxmox's post-installation webhook and sanitized boot-disk validation.
- Added `failed` reporting with the last phase and detail.
- Delayed `complete` until network, cluster, service, SSH, and storage checks pass.
- Replaced the old join path with a dedicated SSH key and `pvecm add --use_ssh`.
- Installed approved Galaxy root public keys through the answer and enforced key-only root SSH during first boot.
- Required `/dev/nvme0n1p3` as the LVM physical volume and rejected `/dev/sda`.
- Added `nomodeset` to the generated automated installer kernel line.
- Added eight regression tests, taking the suite from 13 to 21.
- Added a 12 GiB disposable acceptance install. It reported only `/dev/sda` through the success webhook and powered off.
- Added a confirmed UniFi allow from `OBJ-Proxmox-Nodes`, including `192.168.70.14`, to `192.168.40.36:8080` so state callbacks survive the MGMT-A cutover and scale to later Galaxy nodes.
- Added a confirmed UniFi allow from the `Server-Provision` network to `192.168.40.36:8080` for the pre-cutover callback.
- Added retries to the bootstrap and join-key fetches so a short service restart cannot end first boot.
- Removed the ICMP gates and used a successful key-only SSH connection to Grey as the required path check.
- Added explicit checks for both local VLAN addresses, five cluster nodes, and four connected peers on each Corosync link.
- Added reason-coded failure reporting for network, join, convergence, service, SSH-policy, and storage failures.

## Verification

The 21 tests passed locally and on `ansible-01`. Python compilation, Ansible syntax, rendered first-boot shell syntax, and Proxmox answer validation passed. The disposable installer completed at 12 GiB, posted schema 1.2 results for `/dev/sda`, and powered off. Both PXE services are enabled and active.

The physical rerun installed Proxmox to `/dev/nvme0n1`, reported `/dev/sda` only as an other disk, and reached `complete` at `2026-07-31T12:41:27+00:00`. Galaxy reported five nodes and quorum. Both Corosync links showed four connected remote peers, required Green services were active, and root SSH was key-only.

## Remaining Test

No PXE test remains for this incident. Extended SMART testing and the planned wipe of Green's separate `/dev/sda` are tracked as hardware work, not as a PXE failure.
