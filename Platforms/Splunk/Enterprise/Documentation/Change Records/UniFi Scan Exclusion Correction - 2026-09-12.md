# UniFi Scan Exclusion Correction

**Created:** 2026-09-12  
**Last updated:** 2026-09-12  
**Implementation and verification:** 2026-09-12

I removed `192.168.40.179` from the scanning exclusion in the `UniFi - Intrusion detection blocked` saved search, so scan signatures from `ubuntu-dev` now reach Discord like any other host. The exclusion had never worked, and I chose to drop it rather than repair it.

## Why the exclusion never fired

The rule carried `NOT (rule="Scanning Activity" src IN ("ansible-01", "192.168.40.179"))`. It named `ansible-01` by client name and `ubuntu-dev` by address. The `src` field carries the UniFi client name whenever the controller has one, and `ubuntu-dev` has one, so the address literal never matched a single event. The `ansible-01` half works because that entry is already a name.

I found this while tracing a Discord alert for `ET SCAN Behavioral Unusually fast Terminal Server Traffic Potential Scan or Infection (Outbound)`, raised at 8:45:56 PM from `ubuntu-dev` to `192.168.65.10` on TCP 3389. That detection was my own RDP verification sweep during the [RDP enablement](../../../../Active%20Directory/Documentation/Change%20Records/Domain%20Machine%20RDP%20Enablement%20-%202026-09-12.md), not a host acting on its own. A later probe to the same address at 9:00:30 PM was allowed, and the interactive RDP session on `HQ-WS001` succeeded, so IPS is not interfering with ordinary Remote Desktop use.

## Change

I edited the `[UniFi - Intrusion detection blocked]` stanza in `unifi_insights/default/savedsearches.conf`:

- The search clause is now `NOT (rule="Scanning Activity" src="ansible-01")`.
- The stanza description records that `ubuntu-dev` sat in that exclusion as an address until 2026-09-12, why it never matched, and that I chose to alert on its scans rather than repair it.

I left `[UniFi - Outbound scanning activity]` alone. It excludes `ansible-01` by name, which works, and it carries no webhook, so it raises a notable rather than a Discord message.

There is no `local/savedsearches.conf` in the app, so the default file is the only layer.

## Verification

The file on `192.168.72.3` and the tracked copy under `Configuration/` both read `c93ac94d09665f4cbc4637c295bbacc7`, against `cb6125197256f4afb5fbf0f7bc20ae2e` before the edit. Ownership stayed `splunk:splunk`.

I restarted `Splunkd` at 11:33:09 PM. It reported active and answered TCP 8089 about twelve seconds later, and `unifi-flow-collector` stayed active across the restart. `splunk btool savedsearches list "UniFi - Intrusion detection blocked" --debug` resolves the search to the edited file and shows the single `ansible-01` exclusion, which confirms no other configuration layer overrides it.

I did not authenticate to Splunk. The restart was the reload mechanism, run as root on the host, so no Splunk credential was retrieved or handled.

## Remaining work

Every other rule in this file that names a host should be checked for the same name-versus-address mistake. `[UniFi - Intrusion detection not blocked]` carries `NOT (rule="Web Infrastructure Servers" src IN ("docker-network", "192.168.85.2"))`, which pairs a name with an address for the same host and would behave the same way if only the address were present. I did not audit the remaining rules in this change.
