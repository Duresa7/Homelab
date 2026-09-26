# Alert Forwarding to Splunk

**Created:** 2026-08-29  
**Last updated:** 2026-08-31

## Date

I started this change on 2026-08-29 and finished it on 2026-08-30.

## Scope

I put a Splunk Universal Forwarder on `security-01` and pointed it at `splunk-siem` on port 9997, so every Wazuh alert lands in Splunk as well as in Wazuh's own indexer. This is the first of four changes that together give me one page in Splunk showing what my machines are reporting. The other three are [Wazuh Insights App](../../../Splunk/Enterprise/Documentation/Change%20Records/Wazuh%20Insights%20App%20-%202026-08-29.md), [File Integrity Monitoring Widening](File%20Integrity%20Monitoring%20Widening%20-%202026-08-29.md) and [Malware Detection](Malware%20Detection%20-%202026-08-29.md).

The four together are written up as one followable path in [Wazuh Alerts in Splunk](../../../../Guides/Wazuh-Alerts-in-Splunk.md), which is the guide a reader outside this lab would start from.

`security-01` is the manager at `192.168.72.2`, reachable through SSH Manager as `security_01`. `splunk-siem` is `192.168.72.3`.

I did not change any Wazuh rule, decoder or agent configuration here. I did not touch Wazuh's own indexer, which keeps its alerts on its own schedule.

## Decisions

**Everything gets forwarded, with no severity filter.** Filtering at the forwarder means deciding today what I will want to search for next month, and the wrong guess is unrecoverable because the event was never sent. The cost of sending everything is disk, and disk is bounded by retention instead.

**Thirty days of retention.** `frozenTimePeriodInSecs = 2592000` with `maxTotalDataSizeMB = 5120`, whichever comes first. Thirty days covers the question I actually ask, which is whether something changed recently and on which machine.

**No backfill.** The index starts from the day I turned it on. Wazuh's own indexer still holds the history, so nothing is lost, and replaying months of `alerts.json` through a new pipeline would have made the first day's numbers meaningless.

**Port 9997 rather than HEC.** Splunk was already listening on 8088 for HEC and 1514 for SC4S. A file monitor plus splunktcp needs no token management and survives a manager restart on its own, because the forwarder tracks its position in the file.

**Group membership rather than root.** `alerts.json` is `0640 wazuh:wazuh`, so the forwarder needs to be in the `wazuh` group. Running the forwarder as root to avoid one `usermod` would have given a log shipper write access to the whole manager.

## What I configured

On `security-01`, Splunk Universal Forwarder 10.4.0 build `f798d4d49089`:

```ini
# inputs.conf
[monitor:///var/ossec/logs/alerts/alerts.json]
index = wazuh
sourcetype = wazuh:alerts
```

```ini
# outputs.conf
[tcpout]
defaultGroup = splunk_siem

[tcpout:splunk_siem]
server = 192.168.72.3:9997
maxQueueSize = 64MB
useACK = true
```

`useACK` is on so the forwarder holds an event until the indexer confirms it was written. Without it a Splunk restart drops whatever was in flight.

Both files are committed at [Configuration/Splunk Forwarder](../../Configuration/Splunk%20Forwarder/).

The receiving side is in the `wazuh_insights` app on `splunk-siem`, covered in its own record, and it is what defines `[splunktcp://9997]`, the `wazuh` index and the 30-day retention.

## What went wrong on the way

**`splunk enable boot-start` reported failure and had already worked.** It printed `cannot operate systemd unit files` and returned non-zero, but the unit was written. `systemctl enable --now SplunkForwarder` completed normally against the unit it claimed it could not create. I record it because the error invites you to undo a step that succeeded.

**Forwarding needed disk that the machine appeared to have.** `splunk-siem` had 24 GB free on a volume group with nothing unallocated, so the 150 GB virtual disk I had already grown had nowhere to go. That is a separate change, [Root Filesystem Expansion](../../../Splunk/Enterprise/Documentation/Change%20Records/Root%20Filesystem%20Expansion%20-%202026-08-29.md), and it had to happen first.

## Verification

**The forwarder is running as the right user and is connected.**

```console
# systemctl is-active SplunkForwarder && systemctl is-enabled SplunkForwarder
active
enabled

# ps -o user= -C splunkd | sort -u
splunkfwd

# id splunkfwd
uid=1003(splunkfwd) gid=1003(splunkfwd) groups=1003(splunkfwd),110(wazuh)

# ss -tnp | grep 9997
ESTAB  0  0  192.168.72.2:60790  192.168.72.3:9997  users:(("splunkd",pid=1428990,fd=66))
```

The `wazuh` supplementary group is what lets it read `alerts.json`, which is `-rw-r----- wazuh wazuh`. I confirmed the read with `runuser -u splunkfwd -- head -1 /var/ossec/logs/alerts/alerts.json` rather than assuming the group was enough.

**Events arrive and parse.** Alerts appear in `index=wazuh` within seconds of the manager writing them. The end-to-end timing is in the malware record: a file written at 10:46:56 produced an alert that was searchable in Splunk before the next check ran.

**Every agent is represented.** All 16 agents, including the manager's own agent 000, have written alerts into the index. `agent_control -l` shows the same 16 as Active.

Captures are in [Evidence](../../Evidence/Alert%20Forwarding%20to%20Splunk%20-%202026-08-29).

## What this turned up

**A service on `red-server` has been failing every 25 seconds and nobody was watching.** In the first full window after the forwarder came up, 2026-08-29 12:02 AM to 2026-08-30 12:02 AM, `Systemd: Service exited due to a failure.` was 575 of 914 alerts, 62.9 per cent of everything the fleet said. The cause is `nut-driver@ups01.service`:

```console
Aug 30 10:45:26 red-server systemd[1]: Failed to start nut-driver@ups01.service ...
Aug 30 10:45:31 red-server upsd[2350]: Can't connect to UPS [ups01] (usbhid-ups-ups01): No such file or directory
```

The unit carries `RestartUSec=15s`, and with startup time on top that lands at one failure roughly every 25 seconds. Measured on the host on 2026-08-31, the journal held 3,422 `Failed to start` lines in 24 hours and `systemctl show` reported `NRestarts=8995`. `openipmi.service` is failed on the same host. The UPS is not attached to `red-server`, so this is a NUT configuration question rather than a Wazuh one, and it belongs with [PeaNUT](../../../PeaNUT/). I left it running and recorded it, because this is the first thing the new pipeline found and it had been true for a while before anyone could see it.

## Remaining work

- Alerting. Nothing here notifies me; the pipeline only makes the data searchable. The backlog entry is in the [Enterprise Security TODO](../../../Splunk/Enterprise%20Security/Documentation/TODO.md).
- Fix or mask `nut-driver@ups01.service` and `openipmi.service` on `red-server`.
