# Wazuh Agent Fleet Deployment Evidence

**Created:** 2026-08-03  
**Last updated:** 2026-08-03

| Step | Artifact | Result |
|---:|---|---|
| 1 | [S01 Live Preflight and Manager State - 2026-08-03](Logs/S01%20Live%20Preflight%20and%20Manager%20State%20-%202026-08-03.md) | Manager `4.14.6-1` was healthy; IDs 004 & 005 were active; seven requested paths couldn't reach TCP 1514/1515. |
| 2 | [S02 SSH Manager Registration - 2026-08-03](Logs/S02%20SSH%20Manager%20Registration%20-%202026-08-03.md) | Codex gained `docker_blue`, `media_01`, & `kasm_01`; Claude already carried all three. |
| 3 | [S03 Reachable Host Deployment - 2026-08-03](Logs/S03%20Reachable%20Host%20Deployment%20-%202026-08-03.md) | The first pass stopped before installation; the corrected play enrolled four hosts. |
| 4 | [S04 Active Agent and Idempotency Check - 2026-08-03](Logs/S04%20Active%20Agent%20and%20Idempotency%20Check%20-%202026-08-03.md) | IDs 006 through 009 became active, & the second playbook run changed nothing. |
| 5 | [S05 Shared Agent Policy Correction - 2026-08-03](Logs/S05%20Shared%20Agent%20Policy%20Correction%20-%202026-08-03.md) | The default group stopped monitoring a nonexistent WordPress path; only `edge-01` retained `/etc/cloudflared`. |
| 6 | [S06 UniFi Wazuh Policy Previews - 2026-08-03](Logs/S06%20UniFi%20Wazuh%20Policy%20Previews%20-%202026-08-03.md) | Four exact ALLOW policies validated before approval; no mutation occurred during the preview step. |
| 7 | [S07 dkadi Administrator Access - 2026-08-03](Logs/S07%20dkadi%20Administrator%20Access%20-%202026-08-03.md) | `dkadi` retained indexer `all_access` and gained the missing Wazuh server `administrator` mapping; a fresh authorization context passed an administrator-only API check. |
| 8 | [S08 Dashboard and Proxmox Group Verification - 2026-08-03](Logs/S08%20Dashboard%20and%20Proxmox%20Group%20Verification%20-%202026-08-03.md) | The in-app browser signed in as `dkadi`, showed all six current identities active, & showed the new empty `proxmox` group. |
| 9 | [S09 Firewall Application, Remaining Agent Deployment, and Final Verification - 2026-08-03](Logs/S09%20Firewall%20Application%2C%20Remaining%20Agent%20Deployment%2C%20and%20Final%20Verification%20-%202026-08-03.md) | Four approved rules passed their structural diffs; IDs 010 through 016 enrolled; the final seven-host run changed nothing; the dashboard showed 13 active agents & `proxmox (4)`. |
| 9 | [Wazuh endpoints page 1](Screenshots/S09%20Wazuh%20Endpoints%20Page%201%20-%202026-08-03.png) & [page 2](Screenshots/S09%20Wazuh%20Endpoints%20Page%202%20-%202026-08-03.png) | The cursor-free captures show IDs 004 through 016, 13 active agents, & zero disconnected, pending, or never-connected agents. |
| 9 | [Wazuh Proxmox group](Screenshots/S09%20Wazuh%20Proxmox%20Group%20-%202026-08-03.png) | The cursor-free filtered view shows Grey, Purple, Blue, & Red active in `default` & `proxmox`. |
| 10 | [S10 Green Node Enrollment and Final Fleet Verification - 2026-08-03](Logs/S10%20Green%20Node%20Enrollment%20and%20Final%20Fleet%20Verification%20-%202026-08-03.md) | The existing Galaxy rule gained source `.14`; Green enrolled as ID 017; its second run changed nothing; the dashboard showed 14 active agents & `proxmox (5)`. |
| 10 | [Wazuh endpoints page 1 with Green](Screenshots/S10%20Wazuh%20Endpoints%20Page%201%20with%20Green%20-%202026-08-03.png) & [page 2](Screenshots/S10%20Wazuh%20Endpoints%20Page%202%20with%20Green%20-%202026-08-03.png) | The cursor-free full-page captures show IDs 004 through 017, 14 active agents, & zero disconnected, pending, or never-connected agents. |
| 10 | [Wazuh Proxmox group with Green](Screenshots/S10%20Wazuh%20Proxmox%20Group%20with%20Green%20-%202026-08-03.png) | The cursor-free filtered view shows all five Galaxy nodes active in `default` & `proxmox`. |
