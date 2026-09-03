# Discord Alert Bot Troubleshooting

**Created:** 2026-09-03  
**Last updated:** 2026-09-03

I keep one dated Markdown record per problem in this folder. The index links to the complete symptom, cause, correction and verification for each issue.

## Issue Index

| # | Date | Symptom | Resolution | Status |
|---:|---|---|---|---|
| <a id="1-discord-rejected-every-updates-batch"></a>[1](Discord%20Rejected%20Every%20Updates%20Batch%20-%202026-09-03.md) | 2026-09-02 to 2026-09-03 | Every Grafana webhook for the Updates group failed with `Invalid Form Body` for three and a half hours, and the first Splunk post failed on its URL | The silence link exceeded Discord's 1024-character field limit because a `wud_containers` alert carries fifteen labels, and Splunk's results link used a host with no dot. The bot now measures fields, trims the embed to 6000 characters and validates URLs; Splunk builds its links from the published FQDN | Resolved |
