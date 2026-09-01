# Portainer 2.45.0 Upgrade

**Created:** 2026-09-01  
**Last updated:** 2026-09-01

**Implementation date:** 2026-08-31  
**Final verification:** 2026-09-01  
**Status:** Complete  
**Affected systems:** `docker-main`, `alpha-prod-01`, `docker-blue`, `docker-network`, `media-01`

## Change

I advanced the Portainer server from 2.39.5 to 2.45.0 through its existing `portainer/portainer-ce:latest` policy. I moved the shared Edge Agent pin from `portainer/agent:2.39.1` to `portainer/agent:2.45.0` and reconciled all four remote deployments through the Ansible Compose fleet play.

The change retained `portainer_data`, each host's `portainer_agent_data`, the four stored Edge credential pairs, environment registrations, mounts, restart policies, and the existing firewall paths. I changed no environment ID, Edge ID, Edge key, or Portainer setting.

## Verification

- The unauthenticated local status endpoint on `docker-main` returned Portainer version 2.45.0.
- `portainer_edge_agent` ran from `portainer/agent:2.45.0` on `alpha-prod-01`, `docker-blue`, `docker-network`, and `media-01`.
- The live Compose file on each of the four hosts names the 2.45.0 agent image.
- The Portainer API returned endpoint status 1 and type 4 for all four remote environments.
- The 24-project fleet play passed every running and health assertion, and its 2026-09-01 rerun reported no change.

I created no snapshot or backup. Rolling back means restoring the previous Edge Agent pin from Git and reconciling the four agent projects. The server tracks `latest`; a server rollback would require selecting an explicit older image that can read the retained `portainer_data` schema, so I did not claim that as a tested path. I retained no standalone command or API capture; the verification bullets above record the live results I observed.

The wider project update and inventory correction are in [Compose Fleet Maintenance](../../../Ansible/Documentation/Change%20Records/Compose%20Fleet%20Maintenance%20-%202026-08-31.md).

## Remaining Work

None for this upgrade. The four environments are operational.
