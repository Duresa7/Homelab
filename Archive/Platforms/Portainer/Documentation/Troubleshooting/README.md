# Portainer Troubleshooting

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

I keep one dated record per Portainer problem in this folder. Each record holds the symptom, exact error, failed attempts, hypotheses, tests, correction, & observed verification.

## Issue Index

| # | Date | Symptom | Resolution | Status |
|---:|---|---|---|---|
| <a id="1-docker-blue-cannot-start-new-docker-tasks"></a>[1](docker-blue%20Cannot%20Start%20New%20Docker%20Tasks%20Under%20containerd%202.2.4%20-%202026-07-28.md) | 2026-07-28 | A new Portainer agent and a minimal cAdvisor test container both fail with `failed to create shim task: ttrpc: closed` | Updated Docker / containerd / runc from 29.5.3 / 2.2.4 / 1.3.5 to 29.6.2 / 2.2.6 / 1.3.6 | Resolved; the repro exits 0 & Portainer lists all 4 containers |
