# Splunk ES Troubleshooting

**Created:** 2026-07-02  
**Last updated:** 2026-07-22

I record Splunk Enterprise Security failures here with the cause, correction, & observed result. The [build log](../Build-Log.md) holds the installation sequence.

I keep one dated Markdown record per problem in this folder. The index links to the complete symptom, tests, cause, correction, & verification for each issue.

## Issue Index

| # | Where | Symptom | Root cause | Fix |
|:-:|---|---|---|---|
| <a id="1-es-installsetup-slow-initially-looked-disk-io-bound-2026-07-02"></a>[1](ES%20install-setup%20slow,%20initially%20looked%20disk%20I-O%20bound%20-%202026-07-02.md) | Step 1 | ES setup slow/stalled under load | VM undersized for ES (CPU-bound, not disk) | Increased vCPU 4 → 6 |

