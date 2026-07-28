# Portainer Edge Agent Fleet Expansion

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Implementation date:** 2026-07-28  
**Status:** Complete  
**Primary owner:** Portainer  
**Affected systems:** `docker-main`, `docker-blue`, `media-01`, `docker-network`, UniFi gateway

## Scope

I expanded `docker-main` from one remote environment, `alpha-prod-01`, to three more Edge Agent registrations: `docker-blue`, `media-01`, & `docker-network`. Each target got the same Portainer Agent 2.39.1 compose project and its own stored Edge ID & key.

All three environments now check in & accept Portainer tunnel requests. Portainer listed 4 containers on `docker-blue`, 10 on `media-01`, & 5 on `docker-network` during the final 2026-07-28 verification.

## Starting State

Portainer CE 2.39.1 ran as `portainer_ce` on `docker-main`. It published TCP 9443 for the UI, API, & Edge polling, plus TCP 8000 for reverse tunnels. The existing `alpha-prod-01` agent used `portainer/agent:2.39.1`, restart policy `always`, four mounts, a named data volume, & `EDGE_INSECURE_POLL=1`.

None of the three targets had `/opt/docker/portainer-edge-agent`, a Portainer agent container, or a Portainer environment. `docker-blue` & `media-01` could reach `192.168.40.35` on TCP 8000 and 9443. `docker-network` could reach 9443 but not 8000 because its Access-zone policy permits web egress before the catch-all block and has no path to the Internal zone's Portainer tunnel listener.

## Decisions

**I copied the live `alpha-prod-01` pattern.** All three targets use the same pinned agent version, mounts, volume, restart policy, & environment-variable names. One versioned compose file now represents the pattern; host-specific values stay outside git.

**I restored stored Edge IDs before creating the environments.** Portainer's `EnforceEdgeID` setting was off, so my first `docker-blue` registration received an Edge key but no Edge ID. I removed that incomplete record before any agent used it, enabled `EnforceEdgeID`, & recreated all three. Environment IDs 7, 8, & 9 now each carry an Edge ID and key.

**I stored one credential pair per environment.** Each environment has its own login item outside git, holding that environment's Edge ID & key. Neither the vault nor the item names are published. I compared each stored value to Portainer in memory without printing it.

**I stopped before disruptive changes.** The UniFi firewall workflow required confirmation after preview. Updating Docker on `docker-blue` restarted RustDesk `hbbs`, `hbbr`, & cAdvisor, so I preserved their pre-change state and waited for approval before touching the runtime.

**I changed one runtime variable first.** I updated Docker Engine & CLI from 29.5.3 to 29.6.2, containerd from 2.2.4 to 2.2.6, & the bundled runc from 1.3.5 to 1.3.6. The original minimal test passed immediately, so I did not add `keyctl=1` or restart CT 108.

## Actions and Observed Results

### Step 1: Inspect the working pattern

I read the live server & agent state through SSH Manager. `docker-main` reported Portainer CE 2.39.1 with TCP 8000 and 9443 published. `alpha-prod-01` reported one running `portainer_edge_agent` container using image 2.39.1, restart policy `always`, the expected four mounts, & only the five expected environment-variable names.

[Preflight and pattern evidence](../../Evidence/Portainer%20Edge%20Agent%20Fleet%20Expansion%20-%202026-07-28/Logs/S01-Preflight-and-Pattern-2026-07-28.md)

### Step 2: Register the three environments

I authenticated to the Portainer API with the stored login. After restoring `EnforceEdgeID`, I created Docker Edge Agent environments 7 `docker-blue`, 8 `media-01`, & 9 `docker-network`. The API returned a 36-character Edge ID and 123-character Edge key for each registration; the evidence records only presence and length.

I created three login items through JSON templates on standard input, so no value passed through a command line. A second comparison returned a match for all six protected values.

[Registration and credential-storage evidence](../../Evidence/Portainer%20Edge%20Agent%20Fleet%20Expansion%20-%202026-07-28/Logs/S02-Portainer-Registrations-and-Credential-Storage-2026-07-28.md)

### Step 3: Deploy the common compose project

I installed the compose file as `root:root` mode 0644 and `.env` as `root:root` mode 0600 under `/opt/docker/portainer-edge-agent` on all three hosts. `docker compose config --quiet` returned exit 0 everywhere before startup.

`media-01` & `docker-network` pulled `portainer/agent:2.39.1`, created the named network and data volume, & started the agent. Their existing application containers stayed running. I removed all local and remote secret-bearing staging files after installation.

[Deployment and running-state evidence](../../Evidence/Portainer%20Edge%20Agent%20Fleet%20Expansion%20-%202026-07-28/Logs/S03-Agent-Deployment-and-Verification-2026-07-28.md)

### Step 4: Diagnose `docker-blue`

`docker-blue` created the agent container but returned:

```text
failed to create task for container: failed to create shim task: ttrpc: closed
```

The containerd journal shows `containerd-shim-runc-v2` panicking at `runc.(*Container).Cgroup` under containerd 2.2.4. Starting a fresh container from the already-running cAdvisor image failed with the same error, as did variants using the host cgroup namespace and `user.slice`. This rules out the Portainer image, bind mounts, compose network, & named volume.

`media-01` starts the same Portainer compose project under Docker 29.6.2, containerd 2.2.6, & runc 1.3.6. `docker-blue` runs Docker 29.5.3, containerd 2.2.4, & runc 1.3.5; APT offers the same newer versions already running on `media-01`. The LXC also lacks `keyctl=1`, which the working `media-01` and `docker-network` guests carry. A runtime update is the first repair to test because it changes the component that panics and has an exact working comparison.

[docker-blue failure evidence](../../Evidence/Portainer%20Edge%20Agent%20Fleet%20Expansion%20-%202026-07-28/Logs/S04-docker-blue-Containerd-Failure-2026-07-28.md)  
[Troubleshooting record](../Troubleshooting/docker-blue%20Cannot%20Start%20New%20Docker%20Tasks%20Under%20containerd%202.2.4%20-%202026-07-28.md)

### Step 5: Open the `docker-network` tunnel path

I previewed the exact policy again after approval, then created logged policy `6a68eb3f052792cd2140c9ad`. It permits only source `192.168.85.2` in the Access zone to destination `192.168.40.35` in the Internal zone over the existing `Portainer Edge Agents` TCP port group for 8000 & 9443.

The controller readback retained the source IP, destination IP, TCP protocol, IPv4 scope, port-group reference, logging, & enabled state. A Bash TCP test from `docker-network` reached both ports. Portainer environment 9 then returned all 5 containers through the Edge tunnel.

[Firewall and tunnel evidence](../../Evidence/Portainer%20Edge%20Agent%20Fleet%20Expansion%20-%202026-07-28/Logs/S05-docker-network-Firewall-and-Tunnel-2026-07-28.md)

### Step 6: Repair `docker-blue` & verify the fleet

The APT simulation proposed four upgrades and no removals: `docker-ce`, `docker-ce-cli`, `docker-ce-rootless-extras`, & `containerd.io`. I installed exact Docker 29.6.2 and containerd 2.2.6 package versions. The package restart brought `hbbs`, `hbbr`, & cAdvisor back automatically.

The exact cAdvisor test that had returned exit 125 now returned 0. I started `portainer_edge_agent` from `/opt/docker/portainer-edge-agent`; it reported `running`, restart policy `always`, & image `portainer/agent:2.39.1`. A final Portainer API check returned status 1, a nonzero check-in, a reachable tunnel, & the expected container list for environments 7, 8, & 9.

I added the three new compose projects to the fleet-update inventory and deployed that inventory to `ansible-01`. Its validator reports 9 OS-update hosts, 5 compose hosts, & 18 managed projects. Both playbooks pass `ansible-playbook --syntax-check`.

[Runtime repair and fleet verification evidence](../../Evidence/Portainer%20Edge%20Agent%20Fleet%20Expansion%20-%202026-07-28/Logs/S06-docker-blue-Runtime-Repair-and-Fleet-Verification-2026-07-28.md)

## Resulting Configuration

| Host | Portainer environment | Compose state | Check-in | Tunnel API |
|---|---:|---|---|---|
| `media-01` | 8 | Running | Observed | Reachable; 10 containers |
| `docker-network` | 9 | Running | Observed | Reachable; 5 containers |
| `docker-blue` | 7 | Running | Observed | Reachable; 4 containers |

The versioned compose reference is [docker-compose.yml](../../Configuration/portainer-edge-agent/docker-compose.yml). Every live `.env` is mode 0600 & holds only `EDGE_ID` and `EDGE_KEY`; the container also receives `EDGE`, `EDGE_INSECURE_POLL`, & `PATH`.

`docker-blue` now runs Docker Engine 29.6.2, containerd 2.2.6, & runc 1.3.6. `docker-network` uses UniFi policy `6a68eb3f052792cd2140c9ad` for the exact TCP 8000/9443 path to `docker-main`.

## Verification

| Check | Result |
|---|---|
| Portainer registration | Environments 7, 8, & 9 are type 4 Edge Agent records with stored IDs and keys |
| Stored-credential comparison | All three Edge IDs & keys match their stored login items |
| Compose validation | Exit 0 on all three targets |
| `media-01` agent | Running, restart `always`, image 2.39.1, Portainer tunnel lists 10 containers |
| `docker-network` agent | Running, restart `always`, image 2.39.1, Portainer tunnel lists 5 containers |
| `docker-blue` runtime repro | The original cAdvisor `/bin/true` test exits 0 under containerd 2.2.6 |
| `docker-blue` agent | Running, restart `always`, image 2.39.1, Portainer tunnel lists 4 containers |
| `docker-blue` existing workloads | `cadvisor` returned healthy; `hbbs` & `hbbr` returned running |
| UniFi policy | Enabled readback matches one source IP, one destination IP, TCP, IPv4, & the 8000/9443 port group |
| Fleet-update inventory | Local and deployed validators pass with 18 projects; both playbooks pass syntax checks |
| Secret cleanup | Local staging directory removed; no secret is present in the workspace |

## Rollback

For one host, I can run `docker compose down -v` under `/opt/docker/portainer-edge-agent`, remove that directory, delete its Portainer environment, & remove its stored credential item. Removing `-v` retains the agent data volume.

For the network change, rollback is deletion of policy `6a68eb3f052792cd2140c9ad`. That removes only the `docker-network` Edge tunnel path; environment 9 will keep polling over 9443 through the existing web-egress rule.

For `docker-blue`, APT still publishes Docker 29.5.3 & containerd 2.2.4 as downgrade targets. I did not run autoremove or clean the package cache. A downgrade would require a Docker restart & the same four-container verification.

## Remaining Work

None. The three new environments are registered, running, reachable through their Edge tunnels, represented in the Galaxy service inventory, & included in the fleet-update compose inventory.
