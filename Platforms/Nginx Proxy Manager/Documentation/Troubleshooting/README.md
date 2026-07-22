# Nginx Proxy Manager Troubleshooting

**Created:** 2026-07-11  
**Last updated:** 2026-07-22

I record NPM-specific operational problems here. My authoritative cross-system narrative for the initial `docker-network` deployment is the [NetBird troubleshooting index](../../../Netbird/Documentation/Troubleshooting/README.md).

I keep one dated Markdown record per problem in this folder. The index links to the complete symptom, tests, cause, correction, & verification for each issue.

## Issue Index

| # | Step | Symptom | Resolution | Status |
|---:|---|---|---|---|
| <a id="1-first-http-probe-raced-npm-initialization"></a>[1](First%20HTTP%20Probe%20Raced%20NPM%20Initialization%20-%202026-07-10.md) | S05 | First HTTP probe returned `000` during initialization | Automatic retry returned `200`; health became `healthy` | Resolved |
| <a id="2-unsaved-proxy-host-modal-closed-during-advanced-navigation"></a>[2](Unsaved%20Proxy-Host%20Modal%20Closed%20During%20Advanced%20Navigation%20-%202026-07-11.md) | S07 | Unsaved proxy-host modal closed during Advanced navigation | Saved the basic host first, then reopened it and applied Advanced configuration | Resolved |
