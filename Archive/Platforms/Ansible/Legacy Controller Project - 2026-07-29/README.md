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

## Redaction

I replaced the admin username with `<YOUR_ADMIN_USERNAME>` and each authorized-key body with `<REDACTED_PUBLIC_KEY>`, keeping the key comments so it stays clear which three identities the playbook pushed. Internal addresses are unchanged. The pre-redaction copies matched the controller at these hashes:

```text
94a221220aaedb693bad43b89c0f62b5fb32b5fe5d07c0b95fd01b60732a143c  ansible.cfg
4a39276b36d31a18438b2daede3cb1d2292d9c57f26cbda1274057305c011dc1  distribute_keys.yml
4a3e65697b05103b5703d873e4d0ce47b2fb2bd0d8ce8c4ae6cc6ab0dff8f235  hosts.ini
217e04824fd7a6da1082e048ef96c929d50ed9544499a32424e067b813539e30  hosts.ini.bak.security-a-20260712-215740
```

The current projects are [fleet-updates](../../../../Platforms/Ansible/Source/fleet-updates/README.md), [monitoring-exporters](../../../../Platforms/Ansible/Source/monitoring-exporters/README.md), and `ssh-key-automation`.
