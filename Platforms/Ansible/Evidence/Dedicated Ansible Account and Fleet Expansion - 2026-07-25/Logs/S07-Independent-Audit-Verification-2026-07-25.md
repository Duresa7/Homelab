# Independent Audit Verification

**Created:** 2026-07-25  
**Last updated:** 2026-07-25

I required two independent read-only reviews after the rollout: one compared the live controller and nine hosts with the approved plan, and one inspected the repository, archives, documentation, tests, commits, & worktree.

## First Pass

The live review found no unresolved account, sudo, SSH, Docker, inventory, check-mode, service-health, or VPN-path problem.

The repository review found six items:

1. POSIX onboarding and retirement tasks selected a custom authorized-key path for reads but didn't pass that path to their writes.
2. The key-state parser could count a commented authorized-key line as active.
3. The fleet validator didn't enforce the exact account, project names, paths, or profile list.
4. One edited historical record credited an automation tool for implementation fixes.
5. The retired OpenClaw platform left an empty active directory.
6. Two pre-existing root README incident links pointed at superseded paths.

## Resolution and Verification

I passed `ssh_effective_authorized_keys_path` to both POSIX write operations, disabled parent-directory management for the selected path, rejected commented lines before normalizing keys, & added regression assertions for those contracts. I strengthened the fleet validator to require all nine `ansible` users, the exact five Compose hosts and sixteen projects, their paths, the media `vpn` profile, & one consistent substituted deployment username.

I removed the authorship reference and empty active directory, then corrected both incident links. The updated source passed both local validators, `git diff --check`, the changed-document link and authorship checks, the secret-pattern scan, & all 825 Mission Control checks.

I deployed the task and validator changes to `ansible-01`. Both deployed validators passed, and all seven playbooks passed syntax checks. The nine-host `ansible-control` onboarding run passed in check mode with no change, unreachable host, or failure. A second check-mode onboarding run against `grey-server` exercised `/etc/pve/priv/authorized_keys`. The nine-host identity audit still passed, and I removed every temporary deployment file.

## Focused Second Pass

The same two independent reviews repeated their checks after remediation.

- The live review reported no unresolved finding across the controller, nine accounts, restricted key, key-only SSH, sudo, Docker access, deployed projects, RustDesk, the media stack, endpoints, & qBittorrent's Gluetun path.
- The repository review reported no unresolved finding across all six remediations, archive completeness, active inventories, links, secrets, documentation standards, tests, commit grouping, Mission Control, & separation of unrelated worktree changes.

No package, image, container, guest power state, 1Password value, or unrelated user file changed during either review.
