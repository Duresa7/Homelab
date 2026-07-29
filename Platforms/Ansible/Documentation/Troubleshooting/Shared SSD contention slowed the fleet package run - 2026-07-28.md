# Shared SSD contention slowed the fleet package run

**Created:** 2026-07-28  
**Last updated:** 2026-07-29

**Investigated:** 2026-07-28 to 2026-07-29

## Symptom

The first live OS update started all 10 remote guests together. security-01's package transaction slowed enough that the calling SSH tool reached its five-minute timeout, although the Ansible process on ansible-01 kept running.

There was no Ansible package failure. The retained play transcript later finished with exit code 0 and reported zero failed or unreachable hosts.

## Failed attempt

The existing normal-run default was full-fleet concurrency. That first setting was unsafe for guests sharing grey-server's SATA workload disk, even though the play itself was correct.

I did not restart the update or kill `apt`, `dpkg`, or Ansible after the client timeout. A second package manager against the same database would have turned slow I/O into a damaged transaction.

## Hypotheses and tests

I checked whether security-01 was waiting on a package prompt or making progress. Its active work included `dpkg`, ext4 journal activity, & flush workers, while guest I/O pressure was near 99 percent. That ruled out an unanswered interactive prompt.

I then checked grey-server without changing it. Several active guests shared the Crucial BX500 SATA SSD at `/dev/sda`; a five-second disk-stat sample during the slowdown worked out to about 338 ms per read & 32 ms per write. The disk, not CPU or Ansible control flow, was the common bottleneck.

I did not retain the temporary process and disk samples as a separate artifact. The Ansible transcript retains the package run, its complete recap, & exit code.

## Root cause

Ten simultaneous package runs created random read, write, journal, & flush traffic on shared storage. grey-server's `/dev/sda` could not service that queue at normal latency, so security-01's package transaction progressed slowly until the queue drained.

## Corrective action

I allowed the original Ansible process to finish. I then changed the normal OS play default from full-fleet concurrency to `serial: 2`; automatic reboots remain limited to `serial: 1`.

I did not update or reconfigure grey-server. All four Proxmox nodes & `kasm-01` remained outside the maintenance target set.

## Verification

The remote run finished with exit code 0. The next OS pass, using two-guest batches, completed with zero failed or unreachable targets. Its apt task still reported cache or cleanup changes on 3 hosts.

Final direct checks returned `0 upgraded, 0 newly installed, 0 to remove and 0 not upgraded` on all 10 apt guests. Rocky Linux returned `dnf_check_update_rc=0`.

Evidence: [remote update transcript](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S02a-remote-guest-os-updates.log), [OS idempotency](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S04a-os-idempotency.log), & [final package checks](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S07-final-service-verification.log)
