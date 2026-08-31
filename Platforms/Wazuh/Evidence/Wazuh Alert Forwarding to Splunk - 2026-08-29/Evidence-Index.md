# Alert Forwarding to Splunk Evidence

**Created:** 2026-08-30  
**Last updated:** 2026-08-31

Supports [Alert Forwarding to Splunk - 2026-08-29](../../Documentation/Change%20Records/Alert%20Forwarding%20to%20Splunk%20-%202026-08-29.md).

Step numbers run S01 to S21 across six evidence folders. This folder holds S06 to S08. All captures are headless, so no pointer appears in any of them.

| Step | Capture | What it shows |
|---:|---|---|
| 6 | [First Wazuh alerts received](Screenshots/S06-Splunk-First-Wazuh-Alerts-Received-2026-08-29.png) | `index=wazuh` returning events for the first time, which is the moment the forwarder proved out end to end. |
| 7 | [Rule breakdown](Screenshots/S07-Splunk-Wazuh-Rule-Breakdown-2026-08-29.png) | What the fleet actually reports, broken down by rule over 2026-08-29 12:02 AM to 2026-08-30 12:02 AM. `Systemd: Service exited due to a failure` is 575 of 914 events, 62.9 per cent, which is how the `red-server` fault surfaced. |
| 8 | [Receiving port 9997 enabled](Screenshots/S08-Splunk-Receiving-Port-9997-Enabled-2026-08-29.png) | Splunk's forwarding and receiving settings with 9997 configured, the listener the forwarder connects to. |
