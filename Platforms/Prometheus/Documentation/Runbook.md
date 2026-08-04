# Prometheus Runbook

**Created:** 2026-07-13  
**Last updated:** 2026-08-04

## Health Check

On `monitor-01`, the stack is healthy when the Compose project's five containers run, readiness succeeds, the configuration passes `promtool`, and both assertions exit zero. cAdvisor is the sixth container on the host and belongs to the Ansible project at `/opt/docker/cadvisor`, so `docker compose ps` here won't list it. Check it with `docker ps` or through its target in the assertion.

```bash
sudo docker compose -f ~/monitoring/docker-compose.yml ps
curl -fsS http://127.0.0.1:9090/-/ready
curl -fsS http://127.0.0.1:3000/api/health
sudo docker exec prometheus promtool check config /etc/prometheus/prometheus.yml
curl -fsS http://127.0.0.1:9090/api/v1/targets | python3 assert_targets.py
python3 assert_dashboard_queries.py ~/monitoring/grafana/dashboards/homelab-overview.json
```

[assert_targets.py](../Tests/assert_targets.py) checks that all 49 expected targets are present and `up`, keyed on scrape URL with the `job` and `host` labels verified. [assert_dashboard_queries.py](../Tests/assert_dashboard_queries.py) runs all 65 dashboard queries and fails on any that error or return no series. It walks into collapsed rows, so the `Per-host detail` panels are covered, and it resolves `$host` to `.*` so they are tested against every host at once rather than one. Upload both temporarily and remove the remote copies afterward.

Do not treat a successful file copy or a HUP signal as proof of reload. Verify the target API.

## Change the Target Set

1. Edit [Configuration/prometheus.yml](../Configuration/prometheus.yml) first.
2. Upload it to a candidate path under `/home/dkadi/monitoring/`.
3. `docker cp` the candidate into the container and run `promtool check config` against it.
4. Confirm a dated backup of the live file exists.
6. Write the candidate into the live file with `cat candidate > prometheus.yml`, not `mv`.
7. Restart the `prometheus` container.
8. Wait at least one scrape interval for the job in question, then run the target assertion and remove candidate files.

Step 6 matters. `prometheus.yml` is a single-file bind mount, and `mv` replaces the inode while the container stays attached to the old one, which is what cost the 2026-07-13 change a reload. Redirecting into the existing file keeps the inode and removes the failure mode. Restart anyway, because Prometheus still has to re-read the file.

Adding a target on another VLAN needs a UniFi policy from `AlphaSec-Monitor` to that zone, and may need a rule in the Proxmox cluster firewall as well. Both layers enforce independently: on 2026-07-25 the UniFi policy for NUT was in place and the path stayed blocked until `/etc/pve/firewall/cluster.fw` was addressed on 2026-07-26. Build a `cluster.fw` candidate outside `/etc/pve`, check it before installing, then `pve-firewall compile`; new accepts must sit above the trailing `IN DROP` rules. Check the `pve_svc_clients` IPSet too when the Proxmox exporter moves. Test reachability from `monitor-01` with `curl` before adding the target, so a failure is a firewall problem rather than a mystery.

## Change a Dashboard

1. Edit the JSON under [Configuration/grafana/dashboards/](../Configuration/grafana/dashboards/).
2. Validate it parses, then upload it to `~/monitoring/grafana/dashboards/` on `monitor-01`.
3. Wait 30 seconds. Grafana re-reads the provisioning directory on its own interval, so no restart is needed.
4. Run `assert_dashboard_queries.py` against the new file.

Only the first install needed a container recreate, to add the mounts. Provisioned dashboards are read-only in the browser by design. To experiment there, use Save As for a scratch copy, then fold the change back into the versioned JSON so the repository stays authoritative.

Adding a provisioning subdirectory means adding a placeholder file to it. The Compose file mounts the whole `provisioning` directory over the image's, so a subdirectory absent from the mount is absent from the container, and Grafana logs an error per start for each one it expects.

## Rollback

The relocation deleted the old host-side backups with the retired stack. Roll back the current service by rebuilding from [Configuration](../Configuration/) on a prepared host, creating a new untracked mode-0600 `pve.yml`, and starting the Compose project. Then check readiness, run `promtool`, and verify the intended target set.

`GF_DATABASE_WAL=true` sits in the Compose file but has no effect on Grafana 13.1.1. I confirmed that on 2026-08-04: the variable was `true`, SQLite header bytes 18 and 19 were `1 1`, and only `grafana.db` existed, with no `-wal` or `-shm` sidecar. `grafana.db` is therefore the whole current database and restoring it on its own is complete. Check before you rely on that: if `grafana.db-wal` and `grafana.db-shm` exist beside it, WAL is on and all three files travel together, or you stop the container first so SQLite checkpoints the log back into the main file. The measured history is in [issue 4](Troubleshooting/Grafana%20SQLite%20Locks%20Under%20Its%20Own%20Housekeeping%20-%202026-07-26.md).

The old `grafana.db` and Prometheus TSDB were deleted by design during the relocation and have no project backup. Rebuilding starts with a fresh database and the provisioned datasource and dashboard from git. To roll back only the current provisioning layer, restore the prior versioned files and recreate Grafana.

The complete relocation and rebuild rollback are in [Monitoring Relocation to monitor-01 - 2026-07-26](Change%20Records/Monitoring%20Relocation%20to%20monitor-01%20-%202026-07-26.md#rollback).

## Exporter Rollout

Exporters are installed from `ansible-01`, not by hand:

```bash
cd /home/ansible/monitoring-exporters
export LANG=C.utf8 LC_ALL=C.utf8

python3 tests/validate_project.py
ansible-playbook playbooks/node-exporter.yml --check
ansible-playbook playbooks/node-exporter.yml
ansible-playbook playbooks/cadvisor.yml
```

Both playbooks are idempotent and verify what they installed rather than trusting the package manager: `node-exporter.yml` asserts the version the running exporter reports, and `cadvisor.yml` compares the containers cAdvisor registered against the containers Docker reports running, failing on a mismatch. Pass `-e target=<host>` for a single host and `-e cadvisor_state=absent` to remove cAdvisor.

cAdvisor is pinned to `ghcr.io/google/cadvisor:v0.60.5`. Do not move it back to `gcr.io/cadvisor/cadvisor`: that registry stops at v0.55.1, and anything before v0.60.5 registers zero containers on the six hosts using Docker's `overlayfs` driver. Full detail is in the [project README](../../Ansible/Source/monitoring-exporters/README.md).

## User Endpoints

- Homelab Overview: `https://grafana.alphasecunited.com/d/homelab-overview`
- Prometheus: `https://prometheus.alphasecunited.com/`; direct fallback `http://192.168.73.2:9090/`
- Grafana: `https://grafana.alphasecunited.com/`; direct fallback `http://192.168.73.2:3000/`

Exporter endpoints on 9100, 9101, 9115, 9221, and 9995 are backend services. Query them through Prometheus except during diagnostics.

Prometheus starts with `--web.external-url=https://prometheus.alphasecunited.com`. Grafana uses `GF_SERVER_DOMAIN`, `GF_SERVER_ROOT_URL`, & HTTP behind NPM. NPM at 192.168.85.2 is the routine cross-zone source to TCP 3000 and 9090 on `monitor-01`; Jedi PC has the separate break-glass path. Port 443 to `security-01` remains for Wazuh.

The Grafana administrator credential is held outside this repository. Retrieve it through the credential-retrieval skill; Prometheus itself has no authentication.
