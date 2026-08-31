# Splunk Universal Forwarder on security-01

**Created:** 2026-08-29  
**Last updated:** 2026-08-29

The two files the forwarder actually needs. Both live at
`/opt/splunkforwarder/etc/system/local/` on `security-01`.

The forwarder runs as `splunkfwd`, which is a member of the `wazuh` group.
That is the whole reason it can read the alert stream without running as root:
every level of `/var/ossec/logs/alerts/alerts.json` is group-readable by
`wazuh`, so group membership is sufficient and root is unnecessary.

Its admin credential is held in the password manager under `Splunk Universal Forwarder - security-01`.
The forwarder has no web interface; that account exists only for local CLI and
the management port.

Version is pinned to the indexer's: **10.4.0, build f798d4d49089**. A forwarder
must never be newer than the indexer it sends to, which is the same constraint
that governs the Wazuh agent holds.
