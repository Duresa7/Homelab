# First TFTP Request Fails After Restart

**Created:** 2026-09-12  
**Last updated:** 2026-09-12

I found this while verifying [ansible-01's move to Blue](../../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/ansible-01%20Blue%20Migration%20-%202026-09-12.md). `tftpd-hpa` 5.2+20240610-3 starts and binds UDP 69, but its first file request after a restart times out. The journal reports `socket: Address family not supported by protocol`.

I reproduced the timeout locally, which excludes routed firewall policy as its cause. Adding `--ipv4` did not fix it. A trace attached on Blue showed the first request's worker calling `socket(AF_UNSPEC, SOCK_DGRAM, 0)` and receiving `EAFNOSUPPORT`, then exiting 74. A subsequent request used `AF_INET` and completed. Blue was running kernel `7.0.14-15-pve`; I have not established whether the host kernel or the daemon causes the invalid family.

I restored `/etc/default/tftpd-hpa` to its original `--secure --create` options, restarted the daemon, and repeated a full transfer with one retry after a five-second initial timeout. The client downloaded all 300,032 bytes of `/srv/tftp/galaxy-ipxe.efi` and compared them byte for byte with the file. That check passed without tracing attached. No bare-metal boot or VLAN 5 provisioning test was performed.

The daemon remains active with its original configuration. The first-request defect is open; the transfer succeeds on retry. I did not retain full terminal transcripts from this investigation. I stopped the temporary `in.tftpd --help` process, detached the time-limited traces, and retained the reviewed original configuration in [Backups](../../../../Backups/ansible-01-tftpd-hpa-before-migration-2026-09-12.conf).
