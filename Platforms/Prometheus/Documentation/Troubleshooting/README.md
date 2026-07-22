# Prometheus Troubleshooting

**Created:** 2026-07-13  
**Last updated:** 2026-07-22

I keep one dated Markdown record per problem in this folder. The index links to the complete symptom, tests, cause, correction, & verification for each issue.

## Issue Index

| # | Date | Symptom | Resolution | Status |
|---:|---|---|---|---|
| <a id="1-single-file-bind-mount-retained-the-old-inode"></a>[1](Single-File%20Bind%20Mount%20Retained%20the%20Old%20Inode%20-%202026-07-13.md) | 2026-07-13 | A validated host-side configuration replacement and SIGHUP left the running container on the old target set | I restarted the Prometheus container so its single-file bind mount attached to the replacement inode; all seven intended targets then reported `UP` | Resolved |

