# Legacy Controller Project

**Created:** 2026-07-29  
**Last updated:** 2026-07-29

**Captured:** 2026-07-29

These four files are what was left of the first Ansible project on `ansible-01`, from 2026-04-09. It predates both tracked projects and every piece of the current design. I archived it here on 2026-07-29 and deleted the files from the controller.

## Why it had to go

The config and inventory describe a fleet that no longer exists and an access model I deliberately replaced.

`ansible.cfg` sets `remote_user = root`. `hosts.ini` connects as `root` on the LXC and management groups and as the admin account on the VMs. The whole point of the [dedicated account work](../../../../Platforms/Ansible/Documentation/Change%20Records/Dedicated%20Ansible%20Account%20and%20Fleet%20Expansion%20-%202026-07-25.md) on 2026-07-25 was to stop doing that: every host now connects as `ansible` with its own restricted key, and I moved the controller key out of the root and admin key stores.

`distribute_keys.yml` is the part that actually worried me. It adds three authorized keys to `root` on the LXC and management hosts and to the admin account on the VMs. Running it would put keys back into exactly the stores that work removed. Nothing referenced it, but it sat one directory below Semaphore's checkout path where someone could reasonably mistake it for live automation.

The inventory also lists hosts that are gone or renamed: `nas-family` is retired, and `docker-red`, `db-13-test`, and `security-01` at `192.168.70.20` don't describe anything current.

## What I checked before deleting

Semaphore is active on this controller and its `tmp_path` is `/home/ansible/ansible/playbooks`, so the directory itself is live and stays. Only these four files left. Semaphore has one repository, `/home/ansible/ssh-key-automation`, and all 18 of its templates run `playbooks/ssh-key-*.yml` or `playbooks/ssh-identity-onboard.yml` from inside that repository. None reference `distribute_keys.yml` or `hosts.ini`. Outside the directory, nothing under `/etc`, the Semaphore config, or any systemd unit mentions the path. The only other reference anywhere was a line in the account's shell history.

Ansible doesn't search parent directories for `ansible.cfg`, so this copy only ever applied to commands run from that working directory. Semaphore runs from its own checkout directories, which is why a stale config sitting in the parent never affected a template run.

## The two inventory files

`hosts.ini.bak.security-a-20260712-215740` is a backup taken during the [Security-A migration](../../../../Infrastructure/Network/UniFi/Documentation/Change%20Records/Security-A%20Migration%20-%202026-07-12.md) on 2026-07-12. It differs from `hosts.ini` in two lines and nothing else: `security-01` was at `192.168.70.20` before the migration and `192.168.72.2` after, and `splunk-siem` at `192.168.72.3` didn't exist yet. That's the migration, visible in one diff.

## The 2026-07-14 controller backups

`/home/ansible/backups/` held two files taken before the SSH identity automation went in. Both are gone as of 2026-07-29 and neither needed to be kept.

`ansible-before-ssh-identity-automation-2026-07-14.tar.gz` was a tarball of this same legacy directory. I extracted it and hashed every file inside: all four are byte-identical to the four archived here, so the tarball held nothing new. I didn't commit the tarball itself, because the files inside it carry the real admin username and full authorized-key bodies, which are exactly what the copies here redact.

`known_hosts-before-ssh-identity-automation-2026-07-14` is here with each host key body replaced by `<REDACTED_HOST_KEY>`. That makes it a record of controller trust on 2026-07-14, not a restore source, and it doesn't need to be one. Both files are hashed with different salts, so hostnames can't be compared between them, but key bodies are salt independent: all 24 of its host keys are still present in the live `known_hosts`, which now holds 75. Nothing in it was missing, so there was nothing to restore. The five comment lines survive intact and name the addresses and OpenSSH versions probed at the time.

The [SSH Identity Automation record](../../../../Platforms/Ansible/Documentation/Change%20Records/SSH%20Identity%20Automation%20-%202026-07-14.md) and the [Runbook](../../../../Platforms/Ansible/Documentation/Runbook.md) both named those two paths as recovery references. I updated both to point here instead.

## Redaction

I replaced the admin username with `dkadi` and each authorized-key body with `<REDACTED_PUBLIC_KEY>`, keeping the key comments so it stays clear which three identities the playbook pushed. Internal addresses are unchanged. The pre-redaction copies matched the controller at these hashes:

```text
94a221220aaedb693bad43b89c0f62b5fb32b5fe5d07c0b95fd01b60732a143c  ansible.cfg
4a39276b36d31a18438b2daede3cb1d2292d9c57f26cbda1274057305c011dc1  distribute_keys.yml
4a3e65697b05103b5703d873e4d0ce47b2fb2bd0d8ce8c4ae6cc6ab0dff8f235  hosts.ini
217e04824fd7a6da1082e048ef96c929d50ed9544499a32424e067b813539e30  hosts.ini.bak.security-a-20260712-215740
6d52ead629fb1d29cb1180c26c99a0a891664dd8cd066172b37e04190bfb9870  known_hosts-before-ssh-identity-automation-2026-07-14
```

The current projects are [fleet-updates](../../../../Platforms/Ansible/Source/fleet-updates/README.md), [monitoring-exporters](../../../../Platforms/Ansible/Source/monitoring-exporters/README.md), and `ssh-key-automation`.
