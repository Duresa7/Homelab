# CI Runners Runbook

**Created:** 2026-10-30  
**Last updated:** 2026-10-30

This is how I built phase 1 of the CI runners, written so I can repeat any part of it: a second k3s node, a rebuilt `ci-k3s-01`, or another Windows runner host. The account of the 2026-10-30 build, with its results and the two failures along the way, is the [Phase 1 Build](Change%20Records/Phase%201%20Build%20-%202026-10-30.md) record. The scripts referenced below are in [Scripts/](../Scripts/).

Every command runs from `ubuntu-dev` unless a step says otherwise. Secrets never appear in a command line, a file in this repository, or any output: passwords go from my password manager's CLI into an environment variable or a `0600` file that is shredded after use. `SP` below is the standard login password and `RP` is root's password; which fields hold them is in the unpublished Linux Host Baseline Standard. Read a section by its ID, not its title: the root password's section title contains parentheses, which the CLI rejects, and a failed read inside `$(...)` leaves the variable empty without stopping the script.

## Reach

| Host | How |
|---|---|
| `green-server`, `grey-server` | `ssh root@192.168.70.14`, `ssh root@192.168.70.10` |
| `ansible-01` | `ssh ansible@192.168.40.36`; projects live as plain copies under `~/<project>`, not a git checkout |
| `ci-k3s-01` | SSH Manager `ci_k3s_01`, `ssh dkadi@192.168.82.10`, or Ansible as `ansible` from `ansible-01` |
| `win11-dev` | SSH Manager `win11_dev`, `ssh dkadi@192.168.82.11` (default shell PowerShell, so chain with `;`) |
| `docker-blue`, `docker-main` | Ansible from `ansible-01` with `-i ~/ssh-key-automation/inventory/hosts.yml`; `docker-main` is in no other inventory, and Ansible exits 0 when a host matches nothing |

## 1. Network in UniFi

Through the UniFi MCP's `unifi_execute`, one call at a time:

1. `unifi_list_firewall_zones` and `unifi_list_networks`: confirm the zone name and VLAN are free.
2. `unifi_create_firewall_zone` with `name: AlphaSec-Kube`.
3. `unifi_create_network` with `network_data`: `name`, `purpose: corporate`, `vlan_enabled: true`, `vlan: 82`, `ip_subnet: 192.168.82.1/24`, DHCP start and stop, `dhcpd_leasetime: 86400`, `ipv6_interface_type: none`, `ipv6_ra_enabled: false`, `igmp_snooping`, `upnp_lan_enabled` and `network_isolation_enabled` false, `ipv6_setting_preference: manual`, `enabled: true`, `firewall_zone_id`. The tool rejects `mdns_enabled`, `networkgroup` and `setting_preference` on create.
4. `unifi_list_port_profiles`, then `unifi_update_port_profile` on `Proxmox-Trunk` with `excluded_networkconf_ids` minus the new network. The controller adds every new network to the exclusion list, and a node cannot carry the VLAN until it comes off.
5. `unifi_create_firewall_policy` for each policy in [KUB-A VLAN 82](../../../Infrastructure/Network/UniFi/Documentation/Change%20Records/KUB-A%20VLAN%2082%20-%202026-10-30.md), copying the field layout of an existing policy from `unifi_get_firewall_policy_details`. Create the external allows before the external block so the block gets the highest index.
6. `unifi_list_firewall_policies` with `limit: 1000`. A filtered or default page truncates at 50 and misses policies.

## 2. VM

On the node, download the ISO into `local` and check it against Ubuntu's `SHA256SUMS`:

```sh
cd /var/lib/vz/template/iso
curl -fsSLO https://releases.ubuntu.com/26.04/ubuntu-26.04.1-live-server-amd64.iso
curl -fsS https://releases.ubuntu.com/26.04/SHA256SUMS | grep live-server | grep 26.04.1
sha256sum ubuntu-26.04.1-live-server-amd64.iso
```

Build the seed ISO from `ubuntu-dev`, which renders [the template](../Configuration/ci-k3s-01-autoinstall.yaml) with the two public keys and a throwaway password hash and writes `ci-k3s-01-seed.iso` on the node:

```sh
Scripts/build-seed.sh        # prints placeholders_left=0
```

Create and start the VM on the node:

```sh
qm create 820 --name ci-k3s-01 --machine q35 --bios ovmf \
  --efidisk0 local-lvm:1,efitype=4m,pre-enrolled-keys=0 --cpu host --sockets 1 --cores 4 --numa 0 \
  --memory 6144 --balloon 0 --ostype l26 --agent 1 --scsihw virtio-scsi-single \
  --scsi0 local-lvm:120,discard=on,iothread=1,ssd=1,cache=writeback \
  --net0 virtio,bridge=vmbr0,firewall=1,tag=82 \
  --ide2 local:iso/ubuntu-26.04.1-live-server-amd64.iso,media=cdrom \
  --ide3 local:iso/ci-k3s-01-seed.iso,media=cdrom \
  --boot "order=scsi0;ide2" --onboot 1 --vga std
qm start 820
```

At the GRUB menu, add `autoinstall` to the kernel line so the installer does not stop to ask. Watch with `Scripts/console-shot.sh 820` and send keys from the node:

```sh
qm sendkey 820 e
for k in down down down end spc a u t o i n s t a l l; do qm sendkey 820 $k; done
qm sendkey 820 ctrl-x
```

The install takes about six minutes and powers the VM off. Then remove the media, delete the seed, and boot:

```sh
qm set 820 --delete ide3; qm set 820 --ide2 none,media=cdrom; qm set 820 --boot order=scsi0
rm -f /var/lib/vz/template/iso/ci-k3s-01-seed.iso; rm -rf /root/ci-k3s-01-seed
qm start 820
```

If the console shows `Malformed autoinstall`, a `late-commands` item is not a string. `build-seed.sh` asserts this before writing the seed.

## 3. Linux baseline

Add the host to the inventories and to the validators that pin host sets, in the repository first, then copy each changed `inventory/hosts.yml` and `tests/validate_project.py` to `~/<project>/` on `ansible-01` and run `python3 tests/validate_project.py` there:

| Project on `ansible-01` | Group |
|---|---|
| `host-access-baseline` | `ai_agent_targets` |
| `ssh-key-automation` | `linux_ssh_key_hosts`, with `ssh_authorized_key_user: dkadi`; also add the host to `target_hosts` in each file under `identities/`, which exist only on `ansible-01` |
| `monitoring-exporters` | `node_exporter_targets` |
| `fleet-updates` | `os_update_targets` |
| `wazuh-agent-deployment` | `wazuh_agent_targets` |

On `ansible-01`, accept the host key with `ssh-keyscan -H 192.168.82.10 >> ~/.ssh/known_hosts`, then from `~/host-access-baseline`:

```sh
I=inventory/hosts.yml
ansible -i $I ci-k3s-01 -b -m shell -a "export DEBIAN_FRONTEND=noninteractive; apt-get update -q && apt-get -y -o Dpkg::Options::=--force-confold full-upgrade"
ansible -i $I ci-k3s-01 -b -m shell -a "locale-gen en_US.UTF-8; update-locale LANG=en_US.UTF-8; timedatectl set-timezone America/New_York"
ansible -i $I ci-k3s-01 -b -m shell -a "update-alternatives --set sudo /usr/bin/sudo.ws"
ansible -i $I ci-k3s-01 -b -m shell -a "chmod 0700 /home/*; sed -i 's/^#\?DIR_MODE=.*/DIR_MODE=0700/' /etc/adduser.conf; sed -i 's/^HOME_MODE.*/HOME_MODE\t0700/' /etc/login.defs"
```

The `sudo.ws` switch is required on Ubuntu 26.04. Its default `sudo-rs` does not report `rootpw` through `sudo -l -U`, and `sudoers-rootpw.yml` fails its readback without it.

Stage the passwords from `ubuntu-dev` straight into a `0600` file on `ansible-01`, with `SP` and `RP` already in the environment:

```sh
[ -n "$SP" ] && [ -n "$RP" ] && [ "$SP" != "$RP" ] && \
SP="$SP" RP="$RP" python3 -c 'import json,os; print(json.dumps({"root_password":os.environ["RP"],"dkadi_password":os.environ["SP"],"ai_agent_password":os.environ["SP"]}))' \
  | ssh ansible@192.168.40.36 'install -d -m 700 ~/.hab-run; umask 077; cat > ~/.hab-run/vars.json'
unset SP RP
```

Then on `ansible-01`, in this order, one host only:

```sh
cd ~/host-access-baseline; export LANG=C.utf8 LC_ALL=C.utf8
ansible-playbook playbooks/ai-agent-account.yml   -e @$HOME/.hab-run/vars.json -e target=ci-k3s-01
ansible-playbook playbooks/account-passwords.yml  -e @$HOME/.hab-run/vars.json -e target=ci-k3s-01   # expect root=P root_auth=ok
ansible-playbook playbooks/sudoers-rootpw.yml     -e @$HOME/.hab-run/vars.json -e target=ci-k3s-01   # expect loginpw_refused=ok
shred -u -z ~/.hab-run/vars.json && rmdir ~/.hab-run

cd ~/ssh-key-automation
for i in jedi-pc mac parrot-os-mac andor-parrotos-pc ubuntu-dev ansible-control; do
  ansible-playbook playbooks/ssh-identity-onboard.yml -e ssh_identity=$i -e '{"ssh_target_hosts": ["ci-k3s-01"]}'
done

cd ~/monitoring-exporters
ansible-playbook playbooks/node-exporter.yml -e target=ci-k3s-01
ansible-playbook playbooks/textfile-collectors.yml -e target=ci-k3s-01

cd ~/wazuh-agent-deployment
ansible-playbook playbooks/deploy.yml --limit ci-k3s-01 -e wazuh_agent_version=<MANAGER_VERSION>
```

Pass the manager's exact package version, read with `dpkg-query -W wazuh-manager` on `security-01`; the playbook's own pin is older. The agent reads `Pending` on `agent_control -l` until its first keepalive, then `Active`.

Finish with `touch /etc/cloud/cloud-init.disabled` (the installer already writes it) and run [verify-baseline.sh](../Scripts/verify-baseline.sh) through Ansible's `script` module. Ad hoc `shell` commands containing `{{` fail in Ansible's templating, so anything with Go templates or braces goes in a script file.

## 4. SSH Manager

The SSH Manager key is one of the identities `ssh-key-automation` installs on `dkadi`, so no extra key is needed on a host that went through step 3. Compare the host's `ssh-keygen -lf /home/dkadi/.ssh/authorized_keys` with `docker-network`'s to confirm.

1. Build the entry on `ubuntu-dev` as a `0600` staging file: eight JSON-quoted lines `SSH_SERVER_<NAME>_HOST`, `_USER` (`dkadi`), `_SUDO_PASSWORD` (root's password), `_MODE` (`unrestricted`), `_PORT`, `_KEYPATH` (`/keys/id_ed25519`), `_PLATFORM`, `_DESCRIPTION`, eight-space indented and comma-separated, plus a plain `SSH_SERVER_<NAME>_SUDO_PASSWORD=<value>` line for `ssh-manager.env`. Check first that the value needs no quoting.
2. Copy the staging files through `ansible-01` to `/tmp/<dir>` (mode `0700`) on `docker-blue` and `docker-main` with Ansible's `copy` module.
3. On `docker-blue`, insert the block after the last server's `_DESCRIPTION` line in `/opt/docker/mcp-gateway/docker-compose.yml`, adding the comma; append the env line to `ssh-manager.env`; run `docker compose config -q`.
4. `ssh-keyscan -t rsa,ecdsa,ed25519 <host> | grep -v '^#' | docker exec -i mcp-ssh-manager sh -c 'cat >> /state/ssh/known_hosts'`. Windows hosts fail with `Host denied` unless all three key types are present.
5. Make the same insertion in Dockhand's copy, `/opt/docker/dockhand/stacks/imported/docker_blue/docker-mcp-gateway/compose.yaml` on `docker-main`, and confirm both files hash the same.
6. Shred every staging copy, then recreate detached so the recreate does not cut the session running it:

```sh
nohup sh -c 'cd /opt/docker/mcp-gateway && docker compose up -d --no-deps --pull never --no-build ssh-manager' > /tmp/sshm-recreate.log 2>&1 &
```

Verify with `ssh_list_servers`, `ssh_execute` (returns `dkadi`) and `ssh_execute_sudo` (returns `root`).

## 5. k3s and ARC

Look up versions from the node itself, which also proves its egress:

```sh
curl -fsS https://update.k3s.io/v1-release/channels | python3 -c 'import json,sys; [print(c["id"], c["latest"]) for c in json.load(sys.stdin)["data"] if c["id"]=="stable"]'
curl -fsS https://get.helm.sh/helm-latest-version
curl -fsS "https://api.github.com/repos/actions/actions-runner-controller/releases?per_page=10" | python3 -c 'import json,sys; print([x["tag_name"] for x in json.load(sys.stdin) if x["tag_name"].startswith("gha-runner-scale-set-")][:1])'
```

Then run [install-k3s-helm.sh](../Scripts/install-k3s-helm.sh) and [install-arc.sh](../Scripts/install-arc.sh) as root through Ansible's `script` module, overriding `K3S_VERSION`, `HELM_VERSION` or `ARC_VERSION` if needed. `/etc/rancher/k3s/k3s.yaml` is `0600 root`, so use `sudo kubectl` and `sudo helm` on the node.

Health check:

```sh
sudo kubectl get nodes -o wide
sudo kubectl get pods -A
sudo helm list -A
```

## 6. Windows runner host

On `win11-dev`, as `dkadi` (a local administrator):

1. **Account.** Generate a 32-character password on `ubuntu-dev`, store it in the password manager as its own item, and write it to a local `0600` file. `scp` that file to `ghr.txt` in `dkadi`'s profile, shred the local copy, copy [win11-gh-runner.ps1](../Scripts/win11-gh-runner.ps1) the same way, and run it with `powershell -NoProfile -ExecutionPolicy Bypass -File`. It creates `gh-runner` in Administrators, grants service logon, denies console and RDP logon, and moves every `actions.runner.*` service to it. Delete the script afterwards.
2. **Check.** The service's `StartName` is `.\gh-runner`, `Get-Process Runner.Listener -IncludeUserName` shows `WIN11-DEV\gh-runner`, and the newest `_diag\Runner_*.log` ends with `Listening for Jobs`.
3. **RDP.** Run [win11-rdp.ps1](../Scripts/win11-rdp.ps1).
4. **Network move.** Copy [win11-kub-a-move.ps1](../Scripts/win11-kub-a-move.ps1) to `C:\ProgramData\netmove.ps1` and register it:

```powershell
$a = New-ScheduledTaskAction -Execute powershell.exe -Argument '-NoProfile -ExecutionPolicy Bypass -File C:\ProgramData\netmove.ps1'
Register-ScheduledTask -TaskName NetMoveKubA -Action $a -User SYSTEM -RunLevel Highest -Force
Start-ScheduledTask NetMoveKubA
```

Within its 15-second wait, retag the NIC on Grey, keeping the MAC by editing the existing `net0` string:

```sh
n=$(qm config 103 | sed -n 's/^net0: //p'); qm set 103 --net0 "$(echo "$n" | sed 's/tag=40/tag=82/')"
```

Reach the VM at the new address, confirm the profile is Private, then `Unregister-ScheduledTask NetMoveKubA` and delete `C:\ProgramData\netmove.*`. Turn off the old UniFi reservation with `unifi_set_client_ip_settings` and `use_fixedip: false`, and repeat step 4's SSH Manager change for the new host address. Confirm the runner with `gh api repos/<owner>/<repo>/actions/runners`.

## 7. Monitoring

1. Add the target to [prometheus.yml](../../Prometheus/Configuration/prometheus-config/prometheus.yml) and [assert_targets.py](../../Prometheus/Tests/assert_targets.py), then follow the Prometheus runbook's target-set procedure: candidate file, `promtool check config`, write into place, `docker kill -s HUP prometheus`. Remove the in-container candidate with `docker exec -u 0`, because the container user cannot delete a root-owned file.
2. Add the host to `Platforms/Prometheus/Tools/inventory.py`. Leave it out of `_SYSTEMD` when the binary node exporter is installed, because it runs without the systemd collector. Run `python3 Tools/build_dashboards.py`, `Tests/assert_dashboard_layout.py` and `Tests/assert_dashboard_queries.py`, and deploy with the tar-and-scp step in the Tools README.
3. If the build changes boards for reasons unrelated to the new host, check out those boards from git before deploying.

## 8. Verify isolation

Run [check-isolation.sh](../Scripts/check-isolation.sh) on `ci-k3s-01`. Expect internet 80 and 443, gateway DNS, Wazuh and `win11-dev` open, and everything else blocked. Two KUB-A hosts on the same subnet reach each other regardless of the zone policies.

## Records to update

The node record, `VMs.md`, `Services.md`, `Galaxy Inventory.md`, the Galaxy README and cluster architecture, the UniFi configuration views and README counts, the Prometheus counts, the platform index, both TODO files, and the diagram specs in `Assets/Diagrams/Generator/specs/` (`galaxy_cluster.py`, `lab_map.py`, `homelab_overview.py`), rebuilt and checked with `python3 build.py --check`.
