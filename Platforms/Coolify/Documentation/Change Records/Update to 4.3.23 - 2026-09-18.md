# Update to 4.3.23

**Created:** 2026-09-18  
**Last updated:** 2026-09-18

**Change date:** 2026-09-18  
**Status:** Complete and verified  
**Host:** app-01, `192.168.80.10`

I updated Coolify from 4.3.21 to 4.3.23 with its official upgrade script. Coolify's CDN version feed and GitHub releases API both identified 4.3.23 as the latest stable release before the update. I confirmed the same release at the follow-up check at 12:13 PM Eastern.

## Installation and preflight

I found the official installer invocation twice in `/home/dkadi/.bash_history`, at lines 399 and 436:

```bash
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | sudo bash
```

The [self-hosting documentation](https://coolify.io/docs/start-with-self-hosted#choose-installation-method) recommends this automated installation method. The running container labels identified the core Compose files under `/data/coolify/source/` and a separate proxy Compose file under `/data/coolify/proxy/`. I did not determine the original install date or whether those files were subsequently edited by hand. No separate transcript was retained for that investigation.

Before updating, I verified all six Coolify containers healthy, `/login` returning HTTP 200, 42.8 GiB free on the root filesystem, and Docker Compose v5.5.1 available. A read-only query of `application_deployment_queues` found no rows with status `queued` or `in_progress`. Only the six Coolify containers and cAdvisor were running on app-01.

I reviewed the [4.3.22](https://github.com/coollabsio/coolify/releases/tag/v4.3.22) and [4.3.23](https://github.com/coollabsio/coolify/releases/tag/v4.3.23) release notes. Version 4.3.22 removes persistent-volume `host_path` configuration from the UI and rejects it in API requests. Version 4.3.23 adds preview deployment log retrieval and fixes whitespace handling in deployment output. I did not test volume-configuration API clients as part of this update.

The first script fetch through Python's HTTP client returned HTTP 403. Fetching with `curl -fsSL` succeeded for the upgrade script and all four configuration dependencies. I compared the CDN upgrade script with the script at GitHub tag `v4.3.23`; they matched. No separate preflight transcript was retained.

## Update

At 11:04 AM Eastern, I ran this command through SSH Manager's sudo operation on app-01:

```bash
bash -c 'set -o pipefail; curl -fsSL https://cdn.coollabs.io/coolify/upgrade.sh | bash -s -- 4.3.23 1.0.17 docker.io true'
```

The arguments select Coolify 4.3.23, helper 1.0.17, Docker Hub, and `SKIP_BACKUP=true`. I created no snapshot or backup, following the lab's no-backup policy. I used the upgrade script directly; I did not rerun the installation script.

The command exited 0 after downloading configuration, updating environment settings, pulling the required images, and starting the detached container restart. The script wrote `/data/coolify/source/upgrade-2026-09-18-11-04-17.log` on the host. I did not retain a separate repository transcript of that invocation. Its exit code confirmed that the restart was initiated; the checks below established completion.

## Verification

My first immediate verification hit `KeyError: 'Config'`: while the Coolify container was absent during recreation, an untyped `docker inspect coolify` resolved the network with the same name. I corrected the check to `docker inspect --type container` and verified the recreated containers. No separate transcript of the failed check was retained.

| Check | Observed result |
| --- | --- |
| Coolify image | `docker.io/coollabsio/coolify:4.3.23` |
| Core services | Coolify, PostgreSQL, Redis, and realtime running and healthy |
| Other containers | Traefik, Sentinel, and cAdvisor healthy; IDs unchanged across the update |
| Restart counters | Zero for all seven containers |
| Local dashboard | `http://127.0.0.1:8000/login`: HTTP 200 |
| Local API health | `http://127.0.0.1:8000/api/health`: HTTP 200 |
| Follow-up | Same healthy state at 12:13 PM Eastern; GitHub latest stable still 4.3.23 |
| Traefik runtime | 3.7.12, read from `traefik version` during follow-up |

I retained the [follow-up verification transcript](../../Evidence/Update%20to%204.3.23%20-%202026-09-18/Logs/Follow-up-Verification.txt), including the exact command, complete output, and exit code. I corrected the README and service inventory's stale Traefik 3.7.10 entries to the observed 3.7.12; I did not update or restart Traefik in this task.

No update failure remains open. These checks cover container health and local HTTP responses; I did not run a new application deployment or an authenticated browser test.
