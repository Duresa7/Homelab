# Certificate, Drive Health and Update Alert Rules

**Created:** 2026-09-03  
**Last updated:** 2026-09-03

**Implemented:** 2026-09-02, with the delivery fault corrected 2026-09-03  
**Status:** Complete. 24 rules evaluate, and every class reaches Discord  
**Affected systems:** Grafana and Prometheus on `monitor-01`, the six Compose hosts, and the Discord alert bot

## Change

Grafana had 15 rules on 2026-09-02 and all of them described something already broken. Nothing told me a certificate was about to expire, a drive was failing, a container was flapping, or that a host had been carrying security updates for a week. I added nine rules in one evening, in two groups of work, and gave every rule a `class` label so the bot can colour and prefix a message by what kind of thing it is.

The decisions behind the set were made in one sitting the same day and are worth stating, because each one was made to keep the volume down. One Discord channel, the existing `#bots`, with colour and prefix by class rather than three channels. Grafana carries states, things that are true for a while and then stop, and Splunk carries events. Update alerts notify and never apply anything. An update alert fires once when the condition appears and once when it clears, with no reminder in between. The whole system should produce fewer than ten messages in a quiet week.

### Nine rules

| Group | Rule | Condition | Class |
|---|---|---|---|
| Availability | Container is restart-looping | More than three starts of the same container in 15 minutes, for 2 minutes | infrastructure |
| Network | TLS certificate is expiring | Blackbox reports a certificate ending inside 14 days, for 1 hour | infrastructure |
| Storage health | Drive failed its SMART health check | `smartmon_device_smart_healthy` below 0.5 on a hypervisor, for 15 minutes | infrastructure |
| Storage health | NVMe drive reports a critical warning | Any `nvme_critical_warning` bit set on a hypervisor, for 5 minutes | infrastructure |
| Storage health | NVMe drive is nearly worn out | `nvme_percentage_used_ratio` above 0.9 on a hypervisor, for 1 hour | infrastructure |
| Updates | Security updates are waiting | A host with a pending upgrade from a security origin, or any dnf security upgrade, for 30 minutes | updates |
| Updates | OS updates are waiting | A host with any pending upgrade and no security upgrade, for 1 hour | updates |
| Updates | Host needs a reboot | `node_reboot_required` above 0.5, for 30 minutes | updates |
| Updates | Container image has an update | A `wud_containers` series with `update_available="true"`, for 30 minutes | updates |

Storage health is a new group evaluated every 5 minutes. Updates is a new group evaluated every 15 minutes. The three drive rules and the whole Updates group set `noDataState: OK`, because their normal state is an empty filtered vector and a rule that treats that as missing data would sit in NoData forever. The drive rules are filtered to `role="hypervisor"` because the same SMART script inside a guest marks a virtio disk unhealthy for having no self-assessment, which the 2026-08-27 dashboard rebuild had already found.

The Updates rules read metrics that did not exist before the same evening. The node_exporter textfile collectors that publish `apt_upgrades_pending`, `dnf_upgrades_pending`, `node_reboot_required` and the drive metrics were rolled to the six hosts that lacked them, and What's Up Docker was deployed to the six Compose hosts, both from `ansible-01`. That work is in [Textfile Collectors and What's Up Docker](../../../Ansible/Documentation/Change%20Records/Textfile%20Collectors%20and%20What's%20Up%20Docker%20-%202026-09-02.md).

### One route for the Updates class

The root notification policy still delivers everything to `discord-bot`. A child route matches `class = updates` and changes three things: alerts are grouped by alert name rather than as one bundle, `group_wait` is 5 minutes and `group_interval` 30 minutes so a fleet-wide condition arrives as one message rather than eighteen, and `repeat_interval` is 8760 hours. Grafana displays that as one year. A host that carries updates for a month produces one message when the condition appears and one when it clears, and nothing in between. The infrastructure rules keep the root policy's 4-hour repeat.

### Prometheus

A `wud` job scrapes the six What's Up Docker instances on port 9102 every 5 minutes: `docker-main`, `docker-network`, `docker-blue`, `media-01`, `alpha-prod-01` and `monitor-01`. The header comment now says seven jobs. The target count moved from 50 to 56.

`Tests/assert_targets.py` gained the six entries. Its blackbox hostname parser also now strips a port, because `http://alert-bot:8080/health` had been parsed as host `alert-bot:8080` and reported as a mismatch since the bot was added.

## Deployment

I deployed the rule file and the contact-points file to `/home/dkadi/monitoring/grafana/provisioning/alerting/` on `monitor-01` and called Grafana's provisioning reload endpoint after each of the two batches. After the first batch Grafana's rule state API reported 20 rules and 0 unhealthy; after the second, 24 and 0. The Prometheus configuration was replaced through its directory mount and reloaded, and `promtool` accepted it. The bot's class handling was deployed and proven at the same time; that record is [Class Styling, Condensed Embeds and Splunk Endpoint](../../../Discord%20Alert%20Bot/Documentation/Change%20Records/Class%20Styling,%20Condensed%20Embeds%20and%20Splunk%20Endpoint%20-%202026-09-02.md).

The Updates rules fired for the first time at 10:27 PM Eastern on 2026-09-02, and the bot could not deliver them. Grafana's silence link carries one matcher per label, a `wud_containers` alert carries fifteen labels, and the resulting field passed Discord's 1024-character limit, so Discord rejected the whole message. Grafana retried every 30 minutes and every attempt failed until I fixed the bot at 2:01 AM on 2026-09-03. The full account is [Discord Rejected Every Updates Batch](../../../Discord%20Alert%20Bot/Documentation/Troubleshooting/Discord%20Rejected%20Every%20Updates%20Batch%20-%202026-09-03.md).

## Verification

- The rule file parses to six groups and 24 unique rule UIDs. Grafana's rule state API reported 24 rules and 0 unhealthy after the second reload on 2026-09-02.
- `/api/v1/provisioning/policies` shows one child route with matcher `class = updates`, `group_by` `alertname`, `group_wait` 5m, `group_interval` 30m, `repeat_interval` 1y.
- Prometheus reports 56 active targets and 56 up, six of them in the `wud` job.
- The drive rules have something to evaluate: 11 SMART health series and 5 NVMe critical-warning series carry `role="hypervisor"`.
- The update metrics cover the fleet. At 2:10 AM on 2026-09-03, 16 hosts reported at least one pending security upgrade, 17 reported some pending upgrade, none required a reboot, and two containers had a newer tag available: `forgejo` on `docker-main` and `playit-agent` on `alpha-prod-01`.
- `python3 Tests/assert_targets.py` passes against the live target set.

I created no snapshot or backup. The versioned files rebuild every rule and route, and Grafana's data volume holds only evaluation state.

## Known limits

**What's Up Docker suggests `16-rootless` for `forgejo:15`.** Its default tag matching treats any newer semver-looking tag as a candidate, and the rootless variant is a different image. The right fix is a `wud.tag.include` label on containers whose tag scheme needs one, and that is a per-Compose-project edit I have not made. Until then a tag-kind update for a variant tag is a prompt to look, not an instruction.

**Digest-pinned images and `lscr.io` images are not watched.** A digest-pinned image has nothing newer to match, and LinuxServer's registry needs a GitHub token, which I have not issued to six hosts for this. Those containers are counted but never report an update.

**Grafana's admin credential is not in the Compose environment.** Reading rule state through the API needs a credential I do not keep on the host, so after the 2026-09-03 bot fix I proved delivery from the bot's own log rather than from Grafana's state API.
