# Monitoring Exporters

**Created:** 2026-07-25  
**Last updated:** 2026-07-25

I run two playbooks from `ansible-01` to keep Prometheus exporters installed across the fleet. `node-exporter.yml` puts `node_exporter` 1.9.0 on every running Linux guest that lacked it, and `cadvisor.yml` manages cAdvisor on the Docker hosts where it actually works. Both use the same `ansible` account, the same key, & the same inventory style as `fleet-updates` next door.

## Scope

`node_exporter_targets` holds 7 hosts: docker-main, docker-network, docker-blue, media-01, alpha-prod-01, splunk-siem, & ansible-01. It deliberately excludes the hosts that already export. The four Proxmox nodes got theirs in the 2026-07-13 baseline cleanup, `edge-01` & `security-01` have had theirs longer, and `app-01` runs a hand-installed `node_exporter.service` binary already bound to 9100. Adding the Debian package there would collide with a working listener, so the playbook leaves it alone and Prometheus just scrapes it.

`ansible-01` manages itself over `ansible_connection: local`, so the controller doesn't depend on its own key sitting in its own `authorized_keys`.

`cadvisor_targets` holds docker-main alone. That's a limitation, not a preference: see below.

## One exporter version, two install methods

Every host ends on `node_exporter` 1.9.0, matching what the four Proxmox nodes already run. The dashboard aggregates across hosts, so a mixed exporter version would mean mixed metric and label sets.

Debian 13 trixie carries `prometheus-node-exporter` 1.9.0-1+b4, so trixie hosts stay APT-managed. Two hosts can't get there through their package manager. `docker-main` runs Debian 12 bookworm, whose only candidate is 1.5.0-1+b6 from December 2022. `splunk-siem` runs Rocky Linux 10.2, which carries no build in `baseos`, `appstream`, or `extras`. Both take the upstream release instead.

The playbook decides per host by reading the APT candidate version, not by looking at the package manager or the distribution release. When `docker-main` eventually moves to trixie, the next run switches it to the package with no edit here.

The upstream download is verified against the release's own `sha256sums.txt`, so no hash is hardcoded and nothing is trusted blind. `grey-server` has run a hand-installed 1.9.0 since before this project existed, so this matches existing practice rather than introducing a new one. I did not add EPEL to `splunk-siem`: pulling a third-party repository onto the host that holds the security logs to obtain one binary isn't a trade worth making.

The `prometheus-node-exporter-collectors` package is deliberately absent. Its `smartmon` script finds no block devices inside an LXC or behind a virtio disk, which would pin `node_textfile_scrape_error` at 1 and report a fault that isn't real.

## cAdvisor covers one host, and why

cAdvisor v0.52.1 can't resolve a container's read-write layer ID under Docker 29's default `overlayfs` storage driver, so it abandons container registration and emits only the root cgroup. `docker-main` is the one Docker host still on the legacy `overlay2` driver, so it's the only one where cAdvisor reports real data: 14 containers, against roughly 46 fleet-wide.

The other six answered on 9101 with HTTP 200 and ~600 series each, all of it useless, so I removed them. The finding is in the tooling as well as in the [troubleshooting record](../../../Prometheus/Documentation/Troubleshooting/cAdvisor%20Registers%20No%20Containers%20Under%20the%20Docker%2029%20overlayfs%20Driver%20-%202026-07-25.md): the playbook reads `docker info --format {{.Driver}}` and refuses to install unless the driver is `overlay2`, and `tests/validate_project.py` fails if a `cadvisor_incompatible` host reappears as a target. Re-adding one by accident breaks loudly instead of silently collecting nothing.

cAdvisor publishes on 9101, not the usual 8080. 8080 is taken by termix on docker-main & coolify-proxy on app-01, and 8081 is taken by the NetBird server on docker-network. 9101 was free on all seven and sits next to `node_exporter`.

## Running the playbooks

```bash
cd /home/ansible/monitoring-exporters
export LANG=C.utf8 LC_ALL=C.utf8

# Structural check, contacts no host.
python3 tests/validate_project.py

# Preview, change nothing.
ansible-playbook playbooks/node-exporter.yml --check

# Install across the fleet.
ansible-playbook playbooks/node-exporter.yml

# One host.
ansible-playbook playbooks/node-exporter.yml -e target=splunk-siem

# cAdvisor, and removal.
ansible-playbook playbooks/cadvisor.yml
ansible-playbook playbooks/cadvisor.yml -e target=cadvisor_incompatible -e cadvisor_state=absent
```

Both plays verify their own work. `node-exporter.yml` probes the exporter and asserts the version it reports matches the pinned one, so a silent drift fails the run rather than passing on the package manager's word. `cadvisor.yml` counts named containers and prints a warning when it registered none.

`node-exporter.yml` also refuses to overwrite an unmanaged listener. If something already answers on 9100 and neither the Debian package nor a managed `node_exporter.service` is present, the play stops and asks for `-e allow_port_takeover=true`. That guard exists because of `app-01`.

A `--check` run of `node-exporter.yml` fails its verification tasks on a host that has no exporter yet, since there's nothing to probe. That's expected; use it to preview package changes, not as a pass/fail gate.

## Adding a host

Add it under `node_exporter_targets` with its `ansible_host` & `ansible_user`, confirm the controller key already reaches it, then update `EXPECTED_NODE_EXPORTER_HOSTS` and `EXPECTED_IPS` in `tests/validate_project.py`. The validator is deliberately strict about the host set so an unreviewed addition fails rather than quietly widening scope.

Scraping the new host also needs a UniFi policy from Security-A to its zone, and possibly a rule in the Proxmox cluster firewall. Test reachability from `security-01` before adding it to `prometheus.yml`.

## Relationship to fleet-updates

Separate projects on purpose. `fleet-updates` patches packages & compose stacks on a schedule; this one installs and verifies exporters. They share the `ansible` account and inventory style but not their host sets: `fleet-updates` covers 9 hosts including `edge-01`, `security-01`, & `app-01`, which this project excludes because they already export.

The cAdvisor compose project at `/opt/docker/cadvisor` is not in the `fleet-updates` compose inventory, so it isn't picked up by automated image updates. Its image is pinned, so that's the intended behavior rather than an oversight.
