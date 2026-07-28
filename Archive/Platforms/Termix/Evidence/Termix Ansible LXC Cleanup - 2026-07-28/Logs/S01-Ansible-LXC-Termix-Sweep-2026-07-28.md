# Ansible LXC Termix Sweep

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Capture date:** 2026-07-28  
**Target:** `ansible-01` (`192.168.40.36`)  
**Execution:** SSH Manager MCP, Bash, starting in `/home/ansible`

## Step 1: Inspect the controller

I searched the Ansible account while excluding the ssh-key-automation Git object database. No Termix-named path remained. Two current monitoring-exporter files still used Termix to explain the cAdvisor port choice.

```bash
printf '%s\n' 'TERMIX PATHS'
find /home/ansible -iname '*termix*' -printf '%y %p\n' 2>/dev/null | sort
printf '%s\n' 'TERMIX CONTENT'
grep -RIn --exclude-dir=.git -i 'termix' /home/ansible 2>/dev/null | sort
```

```text
TERMIX PATHS
TERMIX CONTENT
/home/ansible/monitoring-exporters/README.md:38:cAdvisor publishes on 9101, not the usual 8080. 8080 is taken by termix on docker-main & coolify-proxy on app-01, and 8081 is taken by the NetBird server on docker-network. 9101 was free on all eight and sits next to `node_exporter`.
/home/ansible/monitoring-exporters/playbooks/cadvisor.yml:32:    # 8080 is taken by termix on docker-main and coolify-proxy on app-01, and
```

The pre-change project checks passed.

```bash
cd /home/ansible/monitoring-exporters
python3 tests/validate_project.py
ansible-playbook --syntax-check playbooks/cadvisor.yml
```

```text
Validation passed: 9 node_exporter hosts, 8 cAdvisor hosts.

playbook: playbooks/cadvisor.yml
```

## Step 2: Replace the two files

I sent the two repository files through SSH Manager as Base64 data, decoded them in a `mktemp -d` directory, rejected the transfer if either staged file still matched `termix`, & installed them over the two verified targets. The inline Base64 literals aren't retained here because they duplicate the version-controlled files and add no reviewable command detail.

```bash
install -m 0644 "$d/README.md" /home/ansible/monitoring-exporters/README.md
install -m 0664 "$d/cadvisor.yml" /home/ansible/monitoring-exporters/playbooks/cadvisor.yml
stat -c '%a %U:%G %n' /home/ansible/monitoring-exporters/README.md /home/ansible/monitoring-exporters/playbooks/cadvisor.yml
sha256sum /home/ansible/monitoring-exporters/README.md /home/ansible/monitoring-exporters/playbooks/cadvisor.yml
```

```text
644 ansible:ansible /home/ansible/monitoring-exporters/README.md
664 ansible:ansible /home/ansible/monitoring-exporters/playbooks/cadvisor.yml
26ac212c3de9800e03fc7d775e85c61a6cbcd09695391cc354ab3c8fd46dcd4b  /home/ansible/monitoring-exporters/README.md
c4d40cb718462e501279534e9873659ae02c216f9b4243d3e5b005e5038201c2  /home/ansible/monitoring-exporters/playbooks/cadvisor.yml
```

The temporary directory was removed by the command's exit trap.

## Step 3: Verify the Ansible account

```bash
find /home/ansible -path '/home/ansible/ssh-key-automation/.git' -prune -o -iname '*termix*' -print 2>/dev/null | sort
grep -RIn --exclude-dir=.git -i 'termix' /home/ansible 2>/dev/null | sort || true
cd /home/ansible/monitoring-exporters
python3 tests/validate_project.py
ansible-playbook --syntax-check playbooks/cadvisor.yml
cd /home/ansible/ssh-key-automation
python3 tests/validate_project.py
ansible-inventory --graph >/tmp/termix-cleanup-inventory-graph.txt
rm -f /tmp/termix-cleanup-inventory-graph.txt
```

```text
Validation passed: 9 node_exporter hosts, 8 cAdvisor hosts.

playbook: playbooks/cadvisor.yml
Validation passed: 3 identities, 14 supported hosts, 0 unknown hosts, 13 Semaphore templates.
```

The two search commands returned no path or content match. `ansible-inventory --graph` exited `0`, and the temporary graph file was removed.

## Step 4: Verify privileged Semaphore state

I used `sudo` for the directories & SQLite database that the `ansible` account can't read.

```bash
find /root /var/lib/semaphore /etc/semaphore -iname '*termix*' -print 2>/dev/null | sort
grep -RIl -i 'termix' /root/semaphore-backups /etc/semaphore /var/lib/semaphore 2>/dev/null | sort
if strings /root/database.sqlite 2>/dev/null | grep -qi termix; then
  echo 'termix string present'
  exit 1
else
  echo 'no termix string'
fi
systemctl is-active semaphore.service
```

```text
no termix string
active
```

The two path and content searches returned no match.

## Step 5: Verify repository state

I removed the same stale wording from the tracked monitoring-exporter source, the Ansible automation diagram, & the current homelab overview. Dated Ansible change records keep their 2026-07-14 through 2026-07-25 observations.

```text
No Termix matches in active Ansible source or diagrams.
No Termix matches in the current homelab overview diagram.
Two Excalidraw JSON files and two SVG XML files parsed.
Archive link check passed for 8 Markdown files.
Validation passed: 9 node_exporter hosts, 8 cAdvisor hosts.
```
