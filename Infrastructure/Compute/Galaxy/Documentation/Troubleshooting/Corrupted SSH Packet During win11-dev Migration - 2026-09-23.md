# Corrupted SSH Packet During win11-dev Migration

**Created:** 2026-09-23  
**Last updated:** 2026-09-23

**Status:** Migration completed after checksum repair; underlying cause unconfirmed.

At 7:09:50 PM Eastern, the offline VM 103 migration from Green to Grey failed after about 48 GiB of its 120 GiB system disk had transferred. Green reported `Connection reset by peer`, `Broken pipe` and an export `dd` terminated by signal 13. Grey's SSH service recorded:

```text
Corrupted MAC on input.
ssh_dispatch_run_fatal: Connection from user root 192.168.70.14 port 54430: message authentication code incorrect
```

Here MAC means the SSH message authentication code. The destination rejected the corrupted packet and stopped the encrypted session.

I checked for an SSH timeout, a host or network interruption, and a process fault. Grey had stayed up for 53 days and still had 17,017 MiB available memory. Its effective SSH configuration had `channeltimeout none`, `unusedconnectiontimeout none` and `clientaliveinterval 0`. No matching kernel fault appeared in Green's inspected log window. The destination authentication error explains the session termination. It does not identify where the packet became corrupt. Green's [known memory fault](Memory%20Test%20Failures%20on%20green-server%20-%202026-09-20.md) remains a possible cause.

All source volumes and the stopped guest configuration remained on Green. Both nodes reported no active migration task. Proxmox had removed the completed destination EFI copy, but the incomplete 120 GiB system disk remained on Grey. I confirmed Grey had no guest configuration for VM 103, removed that incomplete volume and verified an empty VM 103 volume list.

I retried through compressed `pvesm export` and `pvesm import` streams over authenticated cluster SSH, keeping the original disks until checksum and boot verification. The streams completed, but SHA-256 comparison found four differing 4 GiB blocks in the system-disk copy. Two independent direct-I/O source reads agreed across all three original disks. The destination EFI and TPM copies matched; system-disk offsets 0, 8, 20 and 116 GiB did not.

I recopied just those four blocks using direct source reads and direct destination writes over the same compressed, encrypted connection. A fresh complete destination checksum pass then matched all 32 entries in both source manifests. I moved the guest configuration, started Windows on Grey, verified SSH, guest agent, Secure Boot, TPM and zero device errors, then deleted the old volumes from Green. The [migration record](../Change%20Records/win11-dev%20Grey%20Migration%20-%202026-09-23.md) links the retained manifests and Windows readback.

The difference between the buffered copy and stable direct reads is consistent with a faulty memory or caching path, but I did not isolate the physical component. Successful transfer and boot do not resolve Green's hardware fault. I did not weaken SSH integrity checks or change the hosts' SSH settings.

I used the failed migration and its matching source and destination logs as the failure evidence. I did not deliberately repeat a stress workload on the faulty host to obtain a smaller reproduction, and there is no isolated software regression test. These observations are summarized from live tool results; I did not retain separate full terminal transcripts.
