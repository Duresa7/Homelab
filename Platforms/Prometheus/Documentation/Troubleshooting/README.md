# Prometheus Troubleshooting

**Created:** 2026-07-13  
**Last updated:** 2026-07-25

I keep one dated Markdown record per problem in this folder. The index links to the complete symptom, tests, cause, correction, & verification for each issue.

## Issue Index

| # | Date | Symptom | Resolution | Status |
|---:|---|---|---|---|
| <a id="1-single-file-bind-mount-retained-the-old-inode"></a>[1](Single-File%20Bind%20Mount%20Retained%20the%20Old%20Inode%20-%202026-07-13.md) | 2026-07-13 | A validated host-side configuration replacement and SIGHUP left the running container on the old target set | I restarted the Prometheus container so its single-file bind mount attached to the replacement inode; all seven intended targets then reported `UP` | Resolved |
| <a id="2-grafana-bootstrap-administrator-credential"></a>[2](Grafana%20Bootstrap%20Administrator%20Credential%20-%202026-07-22.md) | 2026-07-22 | Grafana's one-time bootstrap administrator value remained in the live Compose file | I removed the variable, recreated Grafana, rotated the credential, & verified health and authenticated access | Resolved; [incident](../../../../Security/Incidents/Grafana/Grafana-Incident-Report-2026-07-22-Plaintext-Administrator-Credential.md) closed |
| <a id="3-cadvisor-registers-no-containers-under-the-docker-29-overlayfs-driver"></a>[3](cAdvisor%20Registers%20No%20Containers%20Under%20the%20Docker%2029%20overlayfs%20Driver%20-%202026-07-25.md) | 2026-07-25 | cAdvisor answered on 9101 and emitted ~600 series on six of seven Docker hosts, all of it the root cgroup, reporting zero named containers | Docker 29's `overlayfs` driver moves layer metadata into containerd, so cAdvisor v0.52.1 can't resolve a read-write layer ID and abandons registration. I removed it from the six `overlayfs` hosts and kept it on `docker-main`, the one host still on `overlay2` | Worked around; open upstream |
