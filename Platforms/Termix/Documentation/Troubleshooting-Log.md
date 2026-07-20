# Termix Troubleshooting Log

**Created:** 2026-07-13  
**Last updated:** 2026-07-20

## Quick Index

| # | Date | Symptom | Root cause | Status |
|---:|---|---|---|---|
| 1 | 2026-07-13 | Password-reset logs said a code was generated but showed no code | Deployed Termix 2.2.1 omitted the generated value from its logger template; upgraded to 2.5.0 | Resolved |
| 2 | 2026-07-14 | Termix timed out connecting to all four Galaxy Proxmox nodes | Proxmox `pve_mgmt` permitted `docker-main` on TCP/8006 as a service client, then explicitly dropped its TCP/22 traffic | Resolved |

## 2. Termix Timed Out on All Proxmox SSH Connections

**Date:** 2026-07-14  
**Targets:** Termix on `docker-main`; `grey-server`, `purple-server`, `blue-server`, and `red-server`  
**Impact:** The four hosts were saved in Termix and had the correct public key, but Termix could not establish SSH sessions. Five non-Proxmox hosts connected successfully.

### Symptom

Termix's `/metrics/start/:id` endpoint timed out for host IDs 1 through 4. Independent TCP/22 probes from both the `docker-main` host and the Termix container also timed out against `192.168.70.10` through `192.168.70.13`.

### Investigation

| Hypothesis | Test | Result |
|---|---|---|
| Termix credential or username was wrong | Compared with five successful hosts using the same credential and inspected the public-key deployment result | Unlikely; the shared credential authenticated successfully elsewhere and the exact key was present on all four nodes |
| Docker container routing was missing | Ran `ip route get 192.168.70.10` on `docker-main` and repeated probes from host and container | Route existed through `192.168.40.1`; both scopes timed out |
| UniFi blocked Personal-A to MGMT-A | Inspected the matching user policies, Docker Main client MAC, and UniFi Traffic Flows | Ruled out; an existing Docker Main rule covered Proxmox admin ports, the MAC matched, and SSH flows were recorded as `allowed` |
| Proxmox host firewall rejected the source | Read the cluster `pve_mgmt` group and its IPSets | Confirmed; Docker Main was in `pve_svc_clients`, whose allow covered TCP/8006 only, followed by an explicit TCP/22 drop |

### Root Cause

The Galaxy datacenter firewall applies `pve_mgmt` to every node. `docker-main` (`192.168.40.35`) was authorized as a dashboard/API client on TCP/8006, but no SSH allow matched it. The later `DROP SSH` rule silently discarded TCP/22 after UniFi had forwarded the traffic.

### Corrective Action

I backed up `/etc/pve/firewall/cluster.fw` to mode-0600 `/root/cluster.fw.pre-termix-2026-07-14` on `grey-server`. I created cluster IPSet `pve_termix` with the single member `192.168.40.35`, then added an inbound TCP/22 `ACCEPT` from `+pve_termix` to `pve_mgmt`. The new rule is evaluated before the existing SSH drop and does not grant TCP/8006 or any other port.

### Verification

Live TCP/22 probes from `docker-main` returned open for all four node addresses. Termix then returned HTTP 200 for each host, with final stages `Authenticating with SSH key`, `SSH connection established successfully`, and `Metrics session established`.

See [Termix SSH Host Onboarding - 2026-07-14](Change%20Records/Termix%20SSH%20Host%20Onboarding%20-%202026-07-14.md).

## 1. Password Reset Code Was Not Shown

**Date:** 2026-07-13  
**Target:** `docker-main`, container `termix`  
**Impact:** The local user `<YOUR_ADMIN_USERNAME>` could initiate password recovery, but the six-digit code was unavailable through either location named by the application. The service otherwise remained healthy.

### Symptom

Termix logged the successful reset request without the value:

```text
[11:27:57 PM] [INFO] Password reset code generated for user <YOUR_ADMIN_USERNAME> (expires at 7/13/2026, 11:42:57 PM). Check admin panel or database settings table for code.
```

The API response also instructed the user to check Docker logs for a code that was not present.

### Investigation

I tested these hypotheses in order:

| Rank | Hypothesis | Test | Result |
|---:|---|---|---|
| 1 | The deployed logger template never includes the generated value | Inspected the compiled reset route and ran the same static assertion twice against the observed event | Confirmed; both assertions reported `RED:code-absent` |
| 2 | The admin UI provides the value instead | Searched the deployed `AdminSettings` asset and backend settings routes | Ruled out; no reset-code field or lookup exists in the admin bundle, and the settings routes are feature-specific |
| 3 | The value failed to persist | Decrypted a separate in-memory copy of the persisted encrypted SQLite file and queried only for row existence | The persisted file contained no reset row; the route wrote to the live in-memory database without calling the save trigger |
| 4 | Browser cache served an old frontend | Compared the deployed package and image with the registry's current manifest and upstream release source | Not causal to the missing log value; the backend itself was old and defective |

The deployed compiled route creates `resetCode`, inserts it into `settings`, and then logs only the username and expiry. Because the insert completed before the log line, the reset row existed in the live process. The encrypted database file on disk had last been written on 2026-07-07 and did not contain `reset_code_<YOUR_ADMIN_USERNAME>`; that is why an offline database check could not recover it. Reset codes are short-lived process state in this path.

The `AdminSettings` bundle contained one general password-reset status reference but zero `reset_code_`, `reset code`, or `resetCode` references. The only backend routes with `settings` in their path were the terminal-session and Guacamole feature settings; no generic admin settings-table reader was exposed.

### Root Cause

`docker-main` was running Termix package version 2.2.1 from an image created on 2026-05-13. Although the mutable image tag was `latest`, the local repository digest was `sha256:577c0e7024fa7767ffbd00e19a1e0ce28fb0027aab37c3f7d49e2c18bc001210`. The registry's current `latest` index was `sha256:4d3371311087d6757aa9d1c94117e854d749b1c5e8fd07bd36e7a99e0686d26c`, so the running tag was stale.

The defect is corrected in [Termix 2.5.0's password-reset route](https://github.com/Termix-SSH/Termix/blob/release-2.5.0-tag/src/backend/database/routes/user-password-reset-routes.ts), which includes the six-digit value in the Docker log message. [Termix 2.5.0](https://github.com/Termix-SSH/Termix/releases/tag/release-2.5.0-tag) was released on 2026-06-30.

### Corrective Action

I chose a direct Compose upgrade and deliberately took no backup. From `/opt/docker/termix`, I upgraded the existing project with `docker compose pull`, `docker compose down`, and `docker compose up -d`. Both `termix` and `guacd` were recreated; the named `termix_termix-data` volume was retained. I changed no Compose file or environment setting.

I also chose not to initiate a password-reset request during this work. Verification therefore inspected the corrected 2.5.0 logger template without generating or retaining a code.

### Verification

Termix now reports package version 2.5.0 and repository digest `sha256:4d3371311087d6757aa9d1c94117e854d749b1c5e8fd07bd36e7a99e0686d26c`. Its health check is `healthy`, HTTP port 8080 returns `200`, restart count is zero, and the startup-error scan returned zero. The deployed logger template contains the reset-code variable.

`guacd` logged that it was listening on TCP 4822. Its manual health command passed, Termix established a TCP connection to `guacd:4822`, and Docker's first scheduled five-minute health probe exited zero and changed the container to `healthy`. Both containers remained healthy with zero restarts in the final Compose check.

The earlier 2026-07-13 reset code was scheduled to expire at 23:42:57 UTC and was invalidated by the restart because that code existed only in the former process's in-memory database. I need to initiate a fresh reset when ready.

The completed upgrade is recorded in [Termix Upgrade 2.2.1 to 2.5.0 - 2026-07-13](Change%20Records/Termix%20Upgrade%202.2.1%20to%202.5.0%20-%202026-07-13.md).
