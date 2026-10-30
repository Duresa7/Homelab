# CI Runners

**Created:** 2026-10-30  
**Last updated:** 2026-10-30

CI Runners is my self-hosted execution layer for GitHub Actions. GitHub keeps the repositories, workflow files, job queue, logs and releases. My hardware runs the jobs: Linux jobs as throwaway pods on a k3s cluster through Actions Runner Controller (ARC), and Windows jobs on `win11-dev`. macOS jobs stay on GitHub's `macos-latest` runners. Both machines sit on KUB-A, VLAN 82, an isolated network that reaches the internet and my monitoring and admin hosts and nothing else.

Phase 1 is built: the network, the k3s node, the ARC controller and the Windows runner account. No runner scale set exists yet and no repository is wired to `ci-k3s-01`. The design and the GitHub workflow timings it rests on are in [Cross-Platform CI Research](../../Architecture/Cross-Platform%20CI%20Research%20-%202026-10-28.md).

## Current state

| Component | Value |
|---|---|
| Network | KUB-A, VLAN 82, `192.168.82.0/24`, gateway `192.168.82.1`, DHCP `.100` to `.150`, zone `AlphaSec-Kube` |
| k3s node | `ci-k3s-01`, VM 820 on `green-server`, `192.168.82.10`, Ubuntu Server 26.04.1 LTS, 4 vCPU, 6 GiB, 120 GiB on `local-lvm` |
| k3s | v1.36.5+k3s1, single server node, bundled SQLite, Traefik and ServiceLB left at their defaults |
| ARC | `gha-runner-scale-set-controller` chart 0.15.1, Helm release `arc` in namespace `arc-systems`, Helm v4.3.1 |
| Runner scale sets | None yet |
| Windows runner host | `win11-dev`, VM 103 on `grey-server`, `192.168.82.11`, Windows 11 Pro, runner-only since 2026-10-30 |
| Windows runners | `windows-x64-1` for `Duresa7/app-portal`, service logs on as local administrator `gh-runner` |
| Access | SSH from `ubuntu-dev`, `ansible-01`, `docker-blue` and Jedi PC; k3s API 6443 from the same four; RDP to `win11-dev` from Jedi PC only |
| Management | SSH Manager entries `ci_k3s_01` and `win11_dev`; `ci-k3s-01` is in the host-access, SSH key, monitoring, Wazuh and fleet-update Ansible inventories |

## Trust model

Every job runs on my hardware, including pull requests to my public repositories. Four protections carry that decision:

1. Fork pull request workflows wait for my approval before they run. This is a per-repository GitHub setting and goes on when each repository is wired.
2. Fork pull requests receive no secrets, which is GitHub's default and stays that way.
3. Both runner hosts sit on KUB-A, which has no path to Personal-A, SERVERS-A, MGMT-A, IDENTITY-A or Splunk.
4. Privileged Docker-in-Docker, when I add it, is a separate scale set that only trusted triggers can select.

## Configuration

- [Autoinstall template for `ci-k3s-01`](Configuration/ci-k3s-01-autoinstall.yaml). The published copy carries three placeholders that were filled only in the seed ISO on Green during the install.

## Records

- [Phase 1 Build - 2026-10-30](Documentation/Change%20Records/Phase%201%20Build%20-%202026-10-30.md)
- [KUB-A VLAN 82 - 2026-10-30](../../Infrastructure/Network/UniFi/Documentation/Change%20Records/KUB-A%20VLAN%2082%20-%202026-10-30.md), the UniFi side
- [Memory Test Failures on green-server](../../Infrastructure/Compute/Galaxy/Documentation/Troubleshooting/Memory%20Test%20Failures%20on%20green-server%20-%202026-09-20.md), which cleared Green to carry a guest

## Open

- Wire the first repository: choose a GitHub App or token for ARC, decide repository-level or organization-level registration, create the first scale set, and turn on fork pull request approval.
- Add the Docker-in-Docker scale set for trusted triggers.
- Install the Windows toolchains the wired repositories need. Only Git is on `win11-dev`.
- Build the Grey heavy-job node, `ci-k3s-02`, for large, Unity and GPU pools, and decide which Grey guests to stop for it.
- Raise `ci-k3s-01` to 8 GiB once Green has a replacement memory module.
