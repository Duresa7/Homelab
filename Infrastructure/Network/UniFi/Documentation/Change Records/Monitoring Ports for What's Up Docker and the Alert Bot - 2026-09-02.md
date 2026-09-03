# Monitoring Ports for What's Up Docker and the Alert Bot

**Created:** 2026-09-03  
**Last updated:** 2026-09-03

**Implemented:** 2026-09-02  
**Status:** Complete  
**Affected systems:** the UniFi gateway's firewall policies and one port group

## Change

Three edits through the UniFi MCP, each shown as a proposed change before it was applied.

**`PG-Node-Exporter` gained port 9102.** The port group held 9100 for `node_exporter` and 9101 for cAdvisor. What's Up Docker publishes on 9102 on the six Compose hosts, and the four monitoring policies that reference the group carry it at once: `Allow Monitor to Personal-A monitoring`, `Allow Monitor to A-Servers monitoring`, `Allow Monitor to Security monitoring`, and by extension anything else that names the group.

**`Allow Monitor to A-Access monitoring` gained 9102 inline.** That policy names its ports directly, `9100, 9101, 443`, rather than through the group, so it needed its own edit. It now reads `9100, 9101, 9102, 443`. The living table had recorded this policy as `Allow Monitor to AlphaSec-Access monitoring`; the controller's name is `Allow Monitor to A-Access monitoring` and the table now matches.

**A new policy, `Allow splunk-siem to alert bot`.** Splunk's webhook alert action posts to the Discord alert bot on `monitor-01`. Both hosts sit in `AlphaSec-Observability`, on Security-A and MONITOR-A, and the path did not exist. The policy admits `192.168.72.3` to `192.168.73.2` on TCP 8080 only, logs matches, permits the response path, and sits at index 10002. Its controller description reads `Splunk webhook alert actions post to the Discord alert bot on monitor-01. Added 2026-09-02.` I used direct selectors: one source, one destination, one port, and a reusable object would widen nothing and could widen something later.

The user-defined policy count moved from 67 to 68: 61 allows and seven blocks.

## Verification

- The controller returns `PG-Node-Exporter` as a port group with members `9100`, `9101`, `9102`.
- `Allow Monitor to A-Access monitoring` reads back with destination ports `9100,9101,9102,443`, protocol TCP, source `OBJ-Monitor-Collector`, destination `OBJ-Reverse-Proxy`.
- `Allow splunk-siem to alert bot` reads back enabled, `ALLOW`, TCP, source `192.168.72.3`, destination `192.168.73.2` port `8080`, logging on, `create_allow_respond` true, index 10002. At 2:10 AM on 2026-09-03 it had 25 hits, the test and real posts from Splunk to the bot.
- Prometheus on `monitor-01` reports all six `wud` targets up, which it did not before the port was admitted.
- The bot logged a `POST /splunk` from `192.168.72.3` at 2:06 AM on 2026-09-03, and a 403 for the same payload sent from `192.168.40.179`, so the path is open to the one host and the bot rejects the rest.

The consumer records are [Textfile Collectors and What's Up Docker](../../../../../Platforms/Ansible/Documentation/Change%20Records/Textfile%20Collectors%20and%20What's%20Up%20Docker%20-%202026-09-02.md) and [Class Styling, Condensed Embeds and Splunk Endpoint](../../../../../Platforms/Discord%20Alert%20Bot/Documentation/Change%20Records/Class%20Styling,%20Condensed%20Embeds%20and%20Splunk%20Endpoint%20-%202026-09-02.md).
