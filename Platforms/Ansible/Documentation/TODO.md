# Ansible TODO

**Created:** 2026-07-14  
**Last updated:** 2026-07-20

## Open Items

- [ ] Add the docker compose stacks on supabase-01 & the AI hosts to `fleet-updates` once I confirm each host's project paths with `docker compose ls`. supabase-01 runs a database stack, so I add & test it deliberately rather than sweeping it in.
- [ ] Decide how `os-update.yml` supplies a sudo password on the apt hosts where the admin account lacks passwordless sudo. On 2026-07-20 docker-network had passwordless sudo but alpha-prod-01 & app-01 did not. Either standardize passwordless sudo for the update account across the fleet, or store per-host `ansible_become_password` in an Ansible Vault file. Until then a fleet OS-update run needs `-K`.

Future controller runtime, Semaphore, SSH identity, or fleet-update tasks start here before I move them into an active change record.
