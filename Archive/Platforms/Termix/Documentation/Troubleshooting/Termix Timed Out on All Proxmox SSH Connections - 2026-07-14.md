# Termix Timed Out on All Proxmox SSH Connections

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Date:** 2026-07-14  
**Targets:** Termix on `docker-main`; `grey-server`, `purple-server`, `blue-server`, and `red-server`  
**Impact:** The four hosts were saved in Termix and had the correct public key, but Termix could not establish SSH sessions. Five non-Proxmox hosts connected successfully.

## Symptom

Termix's `/metrics/start/:id` endpoint timed out for host IDs 1 through 4. Independent TCP/22 probes from both the `docker-main` host and the Termix container also timed out against `192.168.70.10` through `192.168.70.13`.

## Investigation

| Hypothesis | Test | Result |
|---|---|---|
| Termix credential or username was wrong | Compared with five successful hosts using the same credential and inspected the public-key deployment result | Unlikely; the shared credential authenticated successfully elsewhere and the exact key was present on all four nodes |
| Docker container routing was missing | Ran `ip route get 192.168.70.10` on `docker-main` and repeated probes from host and container | Route existed through `192.168.40.1`; both scopes timed out |
| UniFi blocked Personal-A to MGMT-A | Inspected the matching user policies, Docker Main client MAC, and UniFi Traffic Flows | Ruled out; an existing Docker Main rule covered Proxmox admin ports, the MAC matched, and SSH flows were recorded as `allowed` |
| Proxmox host firewall rejected the source | Read the cluster `pve_mgmt` group and its IPSets | Confirmed; Docker Main was in `pve_svc_clients`, whose allow covered TCP/8006 only, followed by an explicit TCP/22 drop |

## Root Cause

The Galaxy datacenter firewall applies `pve_mgmt` to every node. `docker-main` (`192.168.40.35`) was authorized as a dashboard/API client on TCP/8006, but no SSH allow matched it. The later `DROP SSH` rule silently discarded TCP/22 after UniFi had forwarded the traffic.

## Corrective Action

I backed up `/etc/pve/firewall/cluster.fw` to mode-0600 `/root/cluster.fw.pre-termix-2026-07-14` on `grey-server`. I created cluster IPSet `pve_termix` with the single member `192.168.40.35`, then added an inbound TCP/22 `ACCEPT` from `+pve_termix` to `pve_mgmt`. The new rule is evaluated before the existing SSH drop and does not grant TCP/8006 or any other port.

## Verification

Live TCP/22 probes from `docker-main` returned open for all four node addresses. Termix then returned HTTP 200 for each host, with final stages `Authenticating with SSH key`, `SSH connection established successfully`, and `Metrics session established`.

See [Termix SSH Host Onboarding - 2026-07-14](../Change%20Records/Termix%20SSH%20Host%20Onboarding%20-%202026-07-14.md).
