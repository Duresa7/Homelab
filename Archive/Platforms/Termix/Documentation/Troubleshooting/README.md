# Termix Troubleshooting

**Created:** 2026-07-13  
**Last updated:** 2026-07-22

I keep one dated Markdown record per problem in this folder. The index links to the complete symptom, tests, cause, correction, & verification for each issue.

## Issue Index

| # | Date | Symptom | Root cause | Status |
|---:|---|---|---|---|
| <a id="1-password-reset-code-was-not-shown"></a>[1](Password%20Reset%20Code%20Was%20Not%20Shown%20-%202026-07-13.md) | 2026-07-13 | Password-reset logs said a code was generated but showed no code | Deployed Termix 2.2.1 omitted the generated value from its logger template; upgraded to 2.5.0 | Resolved |
| <a id="2-termix-timed-out-on-all-proxmox-ssh-connections"></a>[2](Termix%20Timed%20Out%20on%20All%20Proxmox%20SSH%20Connections%20-%202026-07-14.md) | 2026-07-14 | Termix timed out connecting to all four Galaxy Proxmox nodes | Proxmox `pve_mgmt` permitted `docker-main` on TCP/8006 as a service client, then explicitly dropped its TCP/22 traffic | Resolved |

