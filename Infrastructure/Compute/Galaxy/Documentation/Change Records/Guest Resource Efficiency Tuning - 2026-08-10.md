# Guest Resource Efficiency Tuning

**Created:** 2026-08-10  
**Last updated:** 2026-08-10

**Change date:** 2026-08-10  
**Scope:** Seven running QEMU VMs and seven running LXCs  
**Status:** Complete

## Why I changed it

I reviewed the running guests against 14.8 days of Prometheus history and their live workloads. I wanted to stop assigning CPU and memory that the services did not use without cutting each guest to its theoretical minimum. The final values keep workload-specific headroom, preserve fixed memory where reclaiming it would create needless risk, and use ballooning only where a useful minimum-to-maximum range exists.

The configured maximum fell by 48.97 GiB across the reviewed guests: QEMU VM maximum memory moved from 90.53 GiB to 66 GiB, and LXC memory moved from 54.44 GiB to 30 GiB. Configured vCPU capacity moved from 36 to 34 across the reviewed VMs and from 27 to 18 across the LXCs. vCPU is scheduled rather than physically reserved, so the eleven-vCPU reduction reduces guest scheduling and contention exposure rather than freeing eleven dedicated cores.

## QEMU VM settings

The memory values below are the Proxmox GUI values in MiB. `Dynamic` means the VM has a maximum and a lower ballooning minimum. `Fixed` means ballooning is off.

| VMID | Guest | Before | Final vCPU | Final memory | Mode | Reason |
| ---: | --- | --- | ---: | --- | --- | --- |
| 102 | `db-13-dev` | 6 vCPU, 16 GiB fixed | 6 | 16,384 maximum; 12,288 minimum | Dynamic | The development workstation keeps its 16 GiB ceiling while Proxmox can reclaim 4 GiB when it is idle. |
| 109 | `splunk-siem` | 6 vCPU, 12 GiB fixed | 6 | 12,288 fixed | Fixed | Splunk indexing and JVM memory are steadier with the existing fixed allocation. |
| 116 | `app-01` | 6 vCPU, 16 GiB configured; 24 GiB still active before the stop/start | 4 | 8,192 maximum; 4,096 minimum | Dynamic | The Coolify stack had enough measured headroom at 8 GiB, and the stop/start cleared the stale 24 GiB QEMU process. |
| 121 | `edge-01` | 2 vCPU, 6.53 GiB fixed | 2 | 4,096 maximum; 2,048 minimum | Dynamic | Caddy and cloudflared use little memory, while a 2 GiB floor leaves recovery headroom. |
| 122 | `kasm-01` | 6 vCPU, 12 GiB fixed | 6 | 12,288 fixed | Fixed | Kasm sessions can rise quickly, so I kept the established fixed memory and CPU. |
| 200 | `security-01` | 4 vCPU, 12 GiB fixed | 4 | 10,240 maximum; 8,192 minimum | Dynamic | Wazuh keeps an 8 GiB floor and a narrow 2 GiB expansion range for indexing. |
| 401 | `alpha-prod-01` | 6 vCPU, 16 GiB fixed | 6 | 4,096 maximum; 2,048 minimum | Dynamic | The voice and game-service host had low measured memory demand. Its CPU remains at six vCPUs; this change did not claim a CPU reduction for VM 401. |

The five dynamic VMs provide 14 GiB of reclaim range between their combined 66 GiB maximum and 52 GiB combined minimum. I did not change swap inside any VM. Proxmox exposes VM maximum memory and ballooning minimum in the Hardware view, while VM swap remains an operating-system setting inside the guest.

I left stopped VM 106 `kali-pen`, stopped VM 117 `supabase-01`, and templates 101 and 9000 unchanged.

## LXC settings

LXC memory and swap are direct Proxmox GUI fields. Final values are exact MiB readings from the cluster API.

| CTID | Guest | Before vCPU / memory / swap | Final vCPU | Final memory | Final swap | Reason |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 100 | `ansible-01` | 1 / 1 GiB / 0.50 GiB | 1 | 1,024 MiB | 512 MiB | The controller was already conservatively sized. |
| 104 | `monitor-01` | 2 / 2 GiB / 1 GiB | 2 | 2,048 MiB | 1,024 MiB | Prometheus, Grafana, and the exporters fit while retaining monitoring headroom. |
| 107 | `docker-network` | 2 / 4 GiB / 1 GiB | 2 | 2,048 MiB | 1,024 MiB | NetBird and Nginx Proxy Manager did not need the extra 2 GiB. |
| 108 | `docker-blue` | 2 / 4 GiB / 1 GiB | 1 | 1,024 MiB | 512 MiB | RustDesk relays and the edge agent have a small steady workload. |
| 110 | `docker-main` | 10 / 23.44 GiB / 15.71 GiB | 4 | 8,192 MiB | 4,096 MiB | The Docker application host keeps the largest general-purpose LXC allocation without retaining its former workstation-sized reservation. |
| 123 | `game-01` | 6 / 12 GiB / 2 GiB | 6 | 12,288 MiB | 2,048 MiB | The game server keeps burst headroom for players and Java workloads. |
| 842 | `media-01` | 4 / 8 GiB / 1 GiB | 2 | 4,096 MiB | 1,024 MiB | The media stack retained enough memory for playback and automation while cutting idle capacity in half. |

## KSM and swap decisions

I made no manual KSM change. `ksmtuned` remains enabled and active on all five Proxmox nodes. KSM was idle on Blue, Green, Grey, and Red at the final check and active on Purple, where Kasm creates the strongest same-page sharing opportunity. This leaves Proxmox in control instead of forcing KSM continuously.

I kept LXC swap as an emergency buffer rather than using it as normal working memory. The final LXC swap allocation is 10 GiB across all seven containers, down from the previously documented 22.21 GiB. VM guest swap was outside this Proxmox GUI change and remained untouched.

## Verification

After the required guest restarts, the cluster API reported all fourteen reviewed guests running with the final values above. The five-node cluster remained quorate. The intentionally stopped Kali and Supabase VMs and the two templates remained stopped.

I checked the primary workloads after the restarts. The Docker stacks, Coolify, Caddy and cloudflared, Wazuh, Splunk, Kasm, media services, game services, Semaphore, and monitoring exporters were running. No post-change OOM event appeared. Prometheus ultimately reported 52 active targets with zero unhealthy targets and all 20 blackbox probes passing after I repaired its separate restart-policy problem in [Container Remained Stopped After monitor-01 Restart - 2026-08-10](../../../../../Platforms/Prometheus/Documentation/Troubleshooting/Container%20Remained%20Stopped%20After%20monitor-01%20Restart%20-%202026-08-10.md).

The remaining capacity observations are not failures from this change. Grey's `hddpool-1` was about 81 percent used, and Purple's host memory remained high because Kasm keeps a fixed 12 GiB allocation. Several container guests also report `openipmi.service` failed because IPMI is unavailable inside an LXC; their application workloads are unaffected.

No standalone command transcript was retained for this GUI-led change. I re-read every final CPU, memory, ballooning, and LXC swap value from the Proxmox cluster API on 2026-08-10 and recorded the observed state above.

## What remains open

No resource setting is waiting on another restart. VM 401 still has six vCPUs in the final state, while its memory changed to the 4,096 MiB maximum and 2,048 MiB minimum shown above. Reducing its vCPU count would be a separate future choice. The storage and Purple memory observations remain capacity items rather than blockers for the completed sizing work.
