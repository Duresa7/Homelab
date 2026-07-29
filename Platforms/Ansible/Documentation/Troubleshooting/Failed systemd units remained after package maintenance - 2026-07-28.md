# Failed systemd units remained after package maintenance

**Created:** 2026-07-28  
**Last updated:** 2026-07-29

**Investigated:** 2026-07-29

## Symptom

The post-update readback returned `system_state=degraded` on 4 of 11 guests:

- docker-network: `wtmpdb-rotate.timer not-found failed`
- monitor-01: `wtmpdb-rotate.timer not-found failed`
- security-01: `fwupd-refresh.service loaded failed`
- splunk-siem: `mcelog.service loaded failed`

The Docker projects were still running, and the readback found no unhealthy or restarting container.

## Failed attempts

There was no failed repair attempt. I classified each failed unit before changing it because restarting a vanished timer or repeatedly starting an unsupported hardware logger would only recreate the failure.

## Hypotheses and tests

The two wtmpdb timer failures named a unit that no longer existed after package maintenance. Resetting the recorded failure was the available action; there was no unit file left to restart.

fwupd had failed while the shared storage queue was under load. Retrying `fwupd-refresh.service` completed successfully.

mcelog had failed before this job because splunk-siem's AMD processor family 23 is unsupported. Enabling the same mcelog unit again would return the same failure.

## Root cause

The four degraded states had three separate causes. Two were stale systemd records for removed timer units, one was a transient fwupd refresh failure during storage contention, & one was an incompatible mcelog service that had no working function on the guest's CPU.

## Corrective action

I reset the failed `wtmpdb-rotate.timer` state on docker-network & monitor-01. I reran the fwupd refresh on security-01, then reset its failure after the successful result. I disabled mcelog on splunk-siem and cleared its recorded failure.

I did not reboot these guests or touch `kasm-01`. No package command ran on a Proxmox node.

## Verification

All four corrected guests returned `system_state=running`. The final fleet readback then reported `failed_units=0` on all 11 in-scope guests.

Wazuh's three services returned active, Splunkd and SC4S returned active, & SC4S reported healthy. That separated the repaired systemd bookkeeping from the services the guests actually provide.

Evidence: [initial health readback](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S05-system-and-container-health.log), [systemd cleanup](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S06-systemd-cleanup.log), & [final service verification](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S07-final-service-verification.log)
