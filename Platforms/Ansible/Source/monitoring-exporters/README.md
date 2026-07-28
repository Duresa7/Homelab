# Monitoring Exporters

**Created:** 2026-07-25  
**Last updated:** 2026-07-28

I run two playbooks from `ansible-01` to keep Prometheus exporters installed across the fleet. `node-exporter.yml` puts `node_exporter` 1.9.0 on every running Linux guest that lacked it, and `cadvisor.yml` manages cAdvisor on all eight Docker hosts. Both use the same `ansible` account, the same key, & the same inventory style as `fleet-updates` next door.

## Scope

`node_exporter_targets` holds 9 hosts: docker-main, docker-network, docker-blue, media-01, alpha-prod-01, splunk-siem, ansible-01, monitor-01, & kasm-01. `kasm-01` joined on 2026-07-28 and is the only host that overrides the listen address: it binds `192.168.78.10:9100` through `node_exporter_listen_override` instead of every interface, because it also holds macvlan shim addresses inside three sealed lab lanes where a session container would reach an all-interfaces listener with no gateway in the path. A host setting that override must set `node_exporter_probe_override` to match, or the play verifies an address the exporter no longer answers on. Its dedicated `ansible` account was provisioned on 2026-07-28 with the same restricted controller key and 0440 sudoers drop-in as the rest of the fleet, so it needs no validator exception. That account is then deliberately weaker than the fleet's: it holds no supplementary groups, so no `sudo` and no `docker`, and its drop-in permits `(root)` rather than `(ALL:ALL)`. `docker` membership alone is root-equivalent through a host bind mount, and this play never touches Docker. The account exists to install and verify one exporter on a host that runs malware, so it gets nothing beyond that.

Command allowlisting is not achievable for any Ansible-managed account, here or elsewhere. Escalation runs `sudo -u root /bin/sh -c '<token>; python3'` with the module fed on stdin, so a sudoers rule permissive enough for a play to succeed is equivalent to full root, and sudoers wildcards on command arguments are unsafe by design. The controls that actually constrain this account are the `from="192.168.40.36"` restriction on its key, the disabled pty and forwarding, and the empty group list. It deliberately excludes the hosts that already export. The four Proxmox nodes got theirs in the 2026-07-13 baseline cleanup, `edge-01` & `security-01` have had theirs longer, and `app-01` runs a hand-installed `node_exporter.service` binary already bound to 9100. Adding the Debian package there would collide with a working listener, so the playbook leaves it alone and Prometheus just scrapes it.

`ansible-01` manages itself over `ansible_connection: local`, so the controller doesn't depend on its own key sitting in its own `authorized_keys`.

`cadvisor_targets` holds all eight Docker hosts: the six shared targets above plus `app-01` and `security-01`, both of which run containers but get their `node_exporter` elsewhere. `splunk-siem` is out because it runs Podman, and `ansible-01` because it runs no containers.

## One exporter version, two install methods

Every host ends on `node_exporter` 1.9.0, matching what the four Proxmox nodes already run. The dashboard aggregates across hosts, so a mixed exporter version would mean mixed metric and label sets.

Debian 13 trixie carries `prometheus-node-exporter` 1.9.0-1+b4, so trixie hosts stay APT-managed. Two hosts can't get there through their package manager. `docker-main` runs Debian 12 bookworm, whose only candidate is 1.5.0-1+b6 from December 2022. `splunk-siem` runs Rocky Linux 10.2, which carries no build in `baseos`, `appstream`, or `extras`. Both take the upstream release instead.

The playbook decides per host by reading the APT candidate version, not by looking at the package manager or the distribution release. When `docker-main` eventually moves to trixie, the next run switches it to the package with no edit here.

The upstream download is verified against the release's own `sha256sums.txt`, so no hash is hardcoded and nothing is trusted blind. `grey-server` has run a hand-installed 1.9.0 since before this project existed, so this matches existing practice rather than introducing a new one. I did not add EPEL to `splunk-siem`: pulling a third-party repository onto the host that holds the security logs to obtain one binary isn't a trade worth making.

The `prometheus-node-exporter-collectors` package is deliberately absent. Its `smartmon` script finds no block devices inside an LXC or behind a virtio disk, which would pin `node_textfile_scrape_error` at 1 and report a fault that isn't real.

## cAdvisor needs v0.60.5, not the image you'll find first

The pinned image is `ghcr.io/google/cadvisor:v0.60.5`, and both halves of that matter.

cAdvisor v0.52.1 can't resolve a container's read-write layer ID under Docker 29's default `overlayfs` driver, because it reads the old graphdriver `layerdb` path and the containerd snapshotter doesn't keep one. The lookup happens during registration rather than during collection, so the container is abandoned outright and only the root cgroup is emitted. From 2026-07-25 to 2026-07-26 this project ran cAdvisor on `docker-main` alone for that reason, since `docker-main` was the one host still on `overlay2`.

v0.60.5 handles the snapshotter. It lives on `ghcr.io/google/cadvisor`; `gcr.io/cadvisor/cadvisor` stops at v0.55.1 and never published v0.53.0, v0.54.0, or v0.55.0, which is how I convinced myself for a day that v0.52.1 was current. The original seven hosts reported all 50 containers they ran before I added `monitor-01` as the eighth target. After I moved the five-container monitoring project off `security-01` and started the six-container stack on `monitor-01`, the eight targets reported 51 named containers. Full account in the [troubleshooting record](../../../Prometheus/Documentation/Troubleshooting/cAdvisor%20Registers%20No%20Containers%20Under%20the%20Docker%2029%20overlayfs%20Driver%20-%202026-07-25.md).

The playbook no longer asserts on the storage driver, because that assert would have refused the version that fixes the problem. It reports the driver, and after installing it compares the containers cAdvisor registered against the containers Docker says are running, failing the play when a host with containers reports none. That catches this failure and any future one, whatever the cause.

cAdvisor publishes on 9101 instead of the usual 8080. `coolify-proxy` uses 8080 on `app-01`, and the NetBird server uses 8081 on `docker-network`. Port 9101 was available on all eight hosts and sits next to `node_exporter`.

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

# cAdvisor across all eight Docker hosts, then removal from one.
ansible-playbook playbooks/cadvisor.yml
ansible-playbook playbooks/cadvisor.yml -e target=media-01 -e cadvisor_state=absent
```

Both plays verify their own work. `node-exporter.yml` probes the exporter and asserts the version it reports matches the pinned one, so a silent drift fails the run rather than passing on the package manager's word. `cadvisor.yml` compares the containers cAdvisor registered against the containers Docker reports running, and fails the play on a mismatch instead of warning.

`node-exporter.yml` also refuses to overwrite an unmanaged listener. If something already answers on 9100 and neither the Debian package nor a managed `node_exporter.service` is present, the play stops and asks for `-e allow_port_takeover=true`. That guard exists because of `app-01`.

A `--check` run of `node-exporter.yml` fails its verification tasks on a host that has no exporter yet, since there's nothing to probe. That's expected; use it to preview package changes, not as a pass/fail gate.

## Adding a host

Add it under `node_exporter_targets` or `cadvisor_targets` with its `ansible_host` & `ansible_user`, confirm the controller key already reaches it, then update the matching `EXPECTED_*` set and `EXPECTED_IPS` in `tests/validate_project.py`. The validator is deliberately strict about both host sets so an unreviewed addition fails rather than quietly widening scope.

Scraping the new host also needs a UniFi policy from the collector's zone to the target, and possibly a rule in the Proxmox cluster firewall. Test reachability from the active Prometheus host before adding it to `prometheus.yml`.

## Relationship to fleet-updates

Separate projects on purpose. `fleet-updates` patches packages & compose stacks on a schedule; this one installs and verifies exporters. They share the `ansible` account and inventory style but not their host sets: `fleet-updates` covers 9 hosts including `edge-01`, `security-01`, & `app-01`, which this project excludes because they already export.

The cAdvisor compose project at `/opt/docker/cadvisor` is not in the `fleet-updates` compose inventory, so it isn't picked up by automated image updates. Its image is pinned, so that's the intended behavior rather than an oversight. It does mean upgrades are a deliberate act here: bump `cadvisor_image` and re-run, which is exactly how v0.52.1 became v0.60.5.
