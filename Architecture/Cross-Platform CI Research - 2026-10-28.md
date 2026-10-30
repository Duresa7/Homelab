# Cross-Platform CI Research

**Created:** 2026-10-28  
**Last updated:** 2026-10-28  
**Research date:** 2026-10-28  
**Status:** GitHub workflow and timing inspection complete; infrastructure remains a proposal

I want shorter build and test cycles for Windows, macOS and Linux software. I have excluded current hardware capacity from this design and can allocate a dedicated Mac. I inspected GitHub workflow definitions, historical job and step timings, and repository runner registrations on 2026-10-28. I have not benchmarked replacement runners, inspected the live Proxmox hosts, changed infrastructure or edited inventories. The measured findings below refine the initial design.

## Starting point

My scope is a reusable runner platform for current and future repositories, with on-demand workers that can scale to zero. I exclude GARM from the design and prioritize established, maintained orchestration. The [current platform direction](#current-platform-direction) supersedes the earlier fixed-pool prototype below. Existing projects provide benchmark workloads rather than defining the platform's limits.

I would keep GitHub Actions orchestration and move trusted Linux and Windows jobs onto separate disposable VMs on Proxmox, with a dedicated Mac for macOS jobs. GitHub supports self-hosted runners on all three operating systems and routes jobs by runner labels and groups. [GitHub runner reference](https://docs.github.com/en/actions/reference/runners/self-hosted-runners), [hosted runner choices](https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job).

I would use Linux VMs for Linux toolchains and container builds, Windows VMs for native Windows SDKs and tests, and macOS with Xcode for Apple builds. I would select explicit OS, CPU architecture and toolchain versions for each product. My macOS path remains separate from ordinary Proxmox hosts: Apple's macOS Tahoe 26 licence specifies Apple-branded systems and conditions for virtual instances. I would check the licence for the selected OS and hosting arrangement before implementing Mac virtualization. [Apple licence, sections 2–3](https://www.apple.com/legal/sla/docs/macOSTahoe.pdf).

## What could become faster

I distinguish execution time from orchestration time. More suitable CPUs, storage, preinstalled SDKs and dependency caches could shorten work on a runner. Additional available runners could reduce waits for matching capacity. Self-hosting still leaves GitHub dispatching jobs; it does not remove that service, workflow dependencies, concurrency limits or approval waits. GitHub documents that jobs queue when no matching runner is available. [Job routing](https://docs.github.com/en/actions/reference/runners/self-hosted-runners).

I would measure queue delay, VM startup, checkout, dependency restoration, compilation, tests and artifact transfers separately on the same commits. I would compare cold and warm caches and end-to-end completion over repeated runs. These are proposed measurements, not results. I cannot promise a speedup; VM startup, cache misses and network transfers could outweigh faster compilation. I would change orchestration only if measurements show it is the constraint.

## What each tool owns

| Tool | My proposed responsibility |
|---|---|
| Terraform or OpenTofu | Define VM resources, disks, networking and lifecycle through a Proxmox provider. I would choose one engine, protect its state and pin provider versions. These tools provision infrastructure; they do not schedule build jobs. [Terraform](https://developer.hashicorp.com/terraform/intro), [OpenTofu](https://opentofu.org/docs/intro/). |
| Proxmox provider | I would evaluate `bpg/proxmox` for Terraform/OpenTofu. It is maintained independently, not endorsed by Proxmox; compatibility and permissions need testing against my chosen versions. [Maintainer documentation](https://github.com/bpg/terraform-provider-proxmox). |
| Packer | Build versioned Linux and Windows VM templates with SDKs and runner prerequisites already installed. The Proxmox builder produces VM images. [Packer Proxmox builder](https://developer.hashicorp.com/packer/integrations/hashicorp/proxmox/latest/components/builder/iso). |
| Ansible | Configure packages, services and build tools in those images, and maintain the provisioning host. Windows needs its own connection and module configuration. I would apply my Linux host baseline before a Linux image carries jobs. [Windows management](https://docs.ansible.com/projects/ansible/latest/os_guide/intro_windows.html). |
| Docker | Package Linux build environments inside disposable Linux VMs. GitHub Docker container actions and service containers require Linux with Docker; a Linux container does not supply a native Windows or macOS test environment. [Container requirements](https://docs.github.com/en/actions/reference/runners/self-hosted-runners). |
| Kubernetes | Optional later for Linux runner autoscaling with Actions Runner Controller. I would add it only when the fleet warrants another control plane. Kubernetes supports Windows containers with constraints, but does not supply a universal Windows desktop/macOS build environment. [ARC](https://docs.github.com/en/actions/concepts/runners/actions-runner-controller), [Windows container support](https://kubernetes.io/docs/concepts/windows/intro/). |

I distinguish **Terraformer** from Terraform. Terraformer generates configuration and state from existing supported infrastructure; it is an import/reverse-engineering tool. Its repository says it was archived on 2026-03-16 and is deprecated. I would not use it as the foundation for new runner provisioning or assume it imports Proxmox. [Terraformer repository](https://github.com/GoogleCloudPlatform/terraformer).

## Disposable jobs and trust boundaries

I would use this lifecycle: clone a clean template, inject short-lived registration, accept one job, export permitted artifacts and logs, then destroy the VM and its writable disks. GitHub's ephemeral registration deregisters a runner after one job; **it does not wipe the machine**. [Ephemeral runners](https://docs.github.com/en/actions/reference/runners/self-hosted-runners).

I would keep a small pool of clean, unused VMs if startup time matters. A separate lifecycle controller must handle registration, cancellation, timeouts and orphan cleanup; Terraform alone is not that controller. A failed cleanup must quarantine the guest. Templates contain no runner identity or release credentials, and external caches are separated by trust level. Disposable job disks are not retained recovery snapshots.

I would leave public, untrusted pull requests on GitHub-hosted runners initially. GitHub warns that public-repository code can compromise self-hosted runners. If I later bring that work inside, it needs isolated disposable compute with no path to Proxmox management, identity systems, trusted caches or production. Deleting a VM afterward does not stop attacks while it runs. I would restrict runner access by repository/workflow policy as well as network policy; labels alone are not an authorization boundary. [GitHub security guidance](https://docs.github.com/en/actions/reference/security/secure-use).

I would separate ordinary builds from release signing and deployment. Only reviewed release workflows get signing or publishing access, using protected environments and narrowly scoped credentials. I would verify artifact provenance and identity before promotion, and never promote arbitrary PR artifacts into a privileged job. This separation also applies to cache writes. [GitHub security guidance](https://docs.github.com/en/actions/reference/security/secure-use).

## Alternatives

| Option | My assessment |
|---|---|
| GitHub Actions with my runners | My starting point: retain workflows and repository integration while changing execution capacity. GitHub still owns orchestration. |
| Buildkite | Managed orchestration with my own cross-platform build agents. I would evaluate it if pipeline scheduling and fleet control justify migration; it is not a fully self-hosted control plane. [Buildkite architecture](https://buildkite.com/docs/pipelines/architecture). |
| GitLab Self-Managed | A fully self-hosted forge and CI/CD control plane with Linux, Windows and macOS runners. I would accept responsibility for the GitLab service as well as workers, and budget for workflow migration. [Installation](https://docs.gitlab.com/install/), [GitLab Runner](https://docs.gitlab.com/runner/). |
| Existing Forgejo | Worth a compatibility pilot, not yet my three-platform recommendation. Forgejo documents host execution without isolation, and its binary installation instructions demonstrate Linux. I still need to verify maintained native Windows/macOS runner builds, shells, actions and disposable execution for the selected versions. Familiar workflow syntax does not guarantee GitHub Actions compatibility. [Runner installation](https://forgejo.org/docs/latest/admin/actions/installation/binary/), [host execution](https://forgejo.org/docs/latest/admin/actions/configuration/), [compatibility policy](https://forgejo.org/docs/latest/user/actions/github-actions/). |

My [service inventory](../Operations/Inventory/Galaxy/Services.md) records Forgejo 16.0.5, and the [2026-09-15 registry cutover](../Platforms/Dockhand/Documentation/Change%20Records/Registry%20and%20Agent%20Cutover%20-%202026-09-15.md) records its use for private container images. Those records establish prior use, not a verified CI runner fleet. I found no dedicated Forgejo platform record and made no live-state claim.

## Publishing and deployment

For desktop software, I would build and test per platform, then package, sign and publish installers, archives or store submissions through the release boundary. macOS distribution can include notarization. [Apple notarization documentation](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution).

For server software, I would publish a versioned artifact or container image and separately deploy it to a runtime such as a VM, Compose service or Kubernetes workload, followed by health checks. My [external ingress design](External-Service-Ingress.md) concerns that runtime path. It does not replace native desktop builds or desktop publishing.

Before implementation, I still need replacement-runner benchmarks, the final OS/CPU matrix, Mac GUI test requirements, and the release credential boundary. I would validate one disposable Linux job and one disposable Windows job before expanding the fleet or choosing another orchestrator.

## GitHub inspection on 2026-10-28

I inspected `Duresa7/app-portal`, `Duresa7/ESP32-TouchDeck`, `Duresa7/tools-and-scripts` and `Duresa7/Homelab`. I retained selected API fields and calculated durations in [workflow-timings.json](Evidence/CI%20Pipeline%20Audit%20-%202026-10-28/Exports/workflow-timings.json), including source commit IDs, run links, sample membership and step timings. This is a structured export, not a terminal transcript. Direct job-log downloads were unavailable, so I have no retained raw logs or internal timing breakdown of composite actions.

I sampled 55 runs: the latest ten successful runs of each active checked-in workflow where available, five successful App Portal manual gates, and recent or historical runs for the two repositories without current workflow files. Installer lifecycle had only four successful runs in the sample. I excluded the TouchDeck release rerun from aggregate timing because its job response included completed jobs from the previous attempt. Failed and cancelled runs are not represented by these successful-run medians.

I measure elapsed time from the attempt's `run_started_at` to the last successful job's `completed_at`, excluding skipped jobs. I do not add parallel jobs together or use the workflow's last-updated timestamp as its finish time. The samples cover different dates and code revisions, so this is a workload inventory, not a controlled hardware benchmark.

| Workflow | Successful first-attempt samples | Median elapsed | Observed range |
|---|---:|---:|---:|
| TouchDeck app checks | 10 | 16m 12.5s | 13m 14s–17m 33s |
| TouchDeck firmware | 10 | 4m 38.5s | 4m 11s–5m 19s |
| TouchDeck installer lifecycle | 4 | 26m 46s | 24m 38s–27m 47s |
| TouchDeck Windows release, including dry runs | 9 | 23m 47s | 20m 02s–29m 50s |
| App Portal recent CI | 10 | 4m 02s | 2m 27s–4m 27s |
| App Portal manual Windows gates | 5 | 6m 59s | 6m 47s–10m 30s |

Across 134 successful jobs from the sampled first-attempt TouchDeck and App Portal runs, job creation to runner start was a median 2 seconds, 90th percentile 3 seconds and maximum 13 seconds. This measures the timestamp interval GitHub exposes, not every possible workflow-level wait. It places the observed bottleneck inside execution rather than runner assignment.

### TouchDeck app and release work

In [app run 40691318939](https://github.com/Duresa7/ESP32-TouchDeck/actions/runs/40691318939), the Linux job took 16m 40s. Its e2e step consumed 11m 17s, about 68% of the job. The Windows job took 8m 47s, with 4m 17s in e2e. Across ten app runs, Linux e2e had a median 11m 10s and Windows e2e 4m 14s. Both jobs began within three seconds of the latest run's start.

The [WebdriverIO configuration](https://github.com/Duresa7/ESP32-TouchDeck/blob/8233f5913a0617810b5c68fcc85785ada17e7af0/app/e2e/wdio.conf.ts) fixes `maxInstances: 1`, uses one port and starts a native application for each session. The [update tests](https://github.com/Duresa7/ESP32-TouchDeck/blob/8233f5913a0617810b5c68fcc85785ada17e7af0/app/e2e/specs/update.spec.ts) deliberately exercise a 30-second timeout. I would profile per-spec startup, execution and teardown, then split independent specs into jobs with separate VMs, ports and profiles. I would preserve timeout coverage. I have not established that fixed sleeps or CPU speed explain the Linux/Windows difference.

In [release dry run 40680094834](https://github.com/Duresa7/ESP32-TouchDeck/actions/runs/40680094834), the Windows build job took 26m 09s, of which 25m 51s belonged to the composite build-and-verify action. Its separate installer-lifecycle job took 20m 31s. These jobs ran concurrently; their durations must not be summed as user waiting time.

The [composite build action](https://github.com/Duresa7/ESP32-TouchDeck/blob/8233f5913a0617810b5c68fcc85785ada17e7af0/.github/actions/windows-release-build/action.yml) installs Node 24, Python 3.13, Rust and pnpm, recursively clones ESP-IDF v6.1, installs its ESP32-S3 tools, builds the installer and matching firmware, and verifies the updater. It has no Rust or pnpm cache step, unlike the app-check workflow. Both release and lifecycle jobs invoke it, with distinct signing modes.

The [packaging script](https://github.com/Duresa7/ESP32-TouchDeck/blob/8233f5913a0617810b5c68fcc85785ada17e7af0/app/scripts/package_windows.py) sets `CARGO_TARGET_DIR` under the job's output directory and sets release-specific Rust flags. A cache for the app-check target directory alone would not cover this build. I would preinstall the exact ESP-IDF/toolchain versions and use a release-specific compilation cache, separated from untrusted jobs and keyed by platform, toolchain, lockfiles, target, features and flags. The API timing does not distinguish download, compilation, packaging and verification within the composite action, so their individual savings remain unmeasured.

In [firmware run 40677045210](https://github.com/Duresa7/ESP32-TouchDeck/actions/runs/40677045210), container initialization took 86 seconds and the firmware build took 138 seconds. A prepared Linux runner with the pinned ESP-IDF image available locally targets this repeated initialization cost. Firmware tests build for the ESP32-S3; these jobs do not require a physical board.

### App Portal and the other repositories

In [App Portal CI run 39081100821](https://github.com/Duresa7/app-portal/actions/runs/39081100821), Linux tests took 109 seconds of a 189-second job. In [manual gate 36504930972](https://github.com/Duresa7/app-portal/actions/runs/36504930972), Windows tests took 440 seconds of a 568-second job. The release-file build took 148 seconds and installer verification 109 seconds. These are different workloads from TouchDeck's Rust release builds.

GitHub's runner inventory reported `windows-x64-1` online and idle for App Portal, with `self-hosted`, `Windows` and `X64` labels. The manual gate used it for installer verification. TouchDeck's repository runner inventory was empty. Registration status does not verify the Windows machine's health or image contents.

The [App Portal workflow](https://github.com/Duresa7/app-portal/blob/22e46b5998d499f9b586560872fd1c4de81ca7b1/.github/workflows/ci.yml) explicitly preserves GitHub-hosted builds for SignPath and allows the installer verification runner to vary. SignPath's current OSS documentation requires GitHub-hosted jobs leading up to signing. I would keep the signed release build and prerequisite jobs on GitHub until the applicable signing policy is verified; the existence of a working local installer runner does not authorize moving the signing path. The sampled manual runs skipped signing, so they do not measure approval or signing-service waits. [SignPath integration requirements](https://docs.signpath.io/trusted-build-systems/github).

Neither tools-and-scripts nor Homelab had `.github/workflows/*.yml` or `.yaml` files in the inspected default-branch trees. Their active Actions entries were Dependency Graph. Tools-and-scripts retains a historical [CI run from 2026-07-20](https://github.com/Duresa7/tools-and-scripts/actions/runs/29744267038) that completed its successful jobs in 36 seconds. Homelab's listed [dependency-graph run](https://github.com/Duresa7/Homelab/actions/runs/34616322091) completed in 52 seconds. I would not size a runner fleet around those entries or describe them as current application deployment pipelines.

## Runner service I would build

I would retain GitHub repositories, workflow YAML, checks, artifacts and release publishing. I would supply the execution machines and their lifecycle. Blacksmith's documented model combines runner selection through `runs-on`, prepared machines and colocated caches; moving only the runner without the cache and image work would reproduce only part of that model. [Blacksmith runner documentation](https://docs.blacksmith.sh/blacksmith-runners/overview).

| Component | Proposed deployment |
|---|---|
| Runner lifecycle manager | One dedicated Linux VM. Maintain clean ready capacity, register one-job runners, replace completed guests, and quarantine failed cleanup. Keep Proxmox credentials out of build guests. |
| Linux workers | Disposable Ubuntu 24.04 VMs prepared for Tauri, Rust, Node 24, pnpm, Python 3.13, .NET 10, Docker and ESP-IDF workloads. Split images where upkeep or isolation warrants it. |
| Windows workers | Separate disposable VMs for build/test and privileged release/installer jobs, with Visual Studio build tools, Windows SDK, Rust, Node, Python, .NET, installer tools and ESP-IDF prepared. Native GUI tests need a tested desktop session arrangement. |
| Mac workers | Dedicated Apple hardware; start with the native GitHub runner, or pilot Tart/Tartelet for replaceable macOS VMs. No sampled workflow currently requests macOS, so this adds future coverage rather than accelerating an existing Mac job. |
| Build cache | Preserve dependency and compiler caches outside disposable job disks. Pilot sccache with local object storage for Rust, and explicit pnpm/NuGet and container cache strategies. Retain separate cache trust scopes for releases and PRs. |
| Image/provisioning automation | Packer templates, Ansible configuration and OpenTofu infrastructure declarations. None is the per-job scheduler. |

The current TouchDeck release can demand three Windows jobs and three Linux jobs at once, before publication. I would provide at least that capacity for one release without adding a queue, plus capacity for overlapping PR checks or proposed test shards. Exact CPU and memory allocations need measured trials; adding cores to a serial UI test does not make it parallel.

I evaluated [GARM](https://github.com/cloudbase/garm) and its community Proxmox integration, but exclude it from the selected architecture. My requirement is established orchestration without depending on that integration. GitHub's [scale-set client](https://github.com/actions/scaleset) is a controller-building library, not a complete Proxmox deployment package; its existence does not meet the requirement by itself.

[Tartelet](https://github.com/framna-dk/tartelet) provides a separate Mac-oriented lifecycle option. [sccache](https://github.com/mozilla/sccache) supports local and remote compiler caches. Neither automatically changes the cache locations or signing boundaries in my workflows. My repositories are under a personal GitHub account; initial registrations can be repository-scoped. Shared organization runner pools would require an organization design rather than assuming personal-account-wide runner registration.

I would first benchmark the TouchDeck Windows composite action on one prepared disposable VM, then the Linux app checks with per-spec timing. I would compare the same commit, output checks and cold/warm cache cases. I would add runner pools only after verifying artifact equivalence, cleanup and measured improvement. Faster hardware, caching and test sharding remain separate hypotheses until those comparisons run. Kubernetes is not needed for this first deployment.

## Earlier fixed-pool prototype, superseded

This bounded prototype records the earlier resource estimate. It is not the selected platform architecture: the current requirements add future repositories, on-demand creation, scale-to-zero workers and established orchestration without GARM.

I would start with two VMs on Proxmox: a persistent Linux management VM at 2 vCPU and 4 GB RAM, and one disposable Windows worker at 8 vCPU and 16 GB RAM. These are initial allocations to benchmark, not measurements of available cluster capacity or minimum requirements. Host placement, SSD capacity, Windows licensing and reserved host memory still need checking before provisioning. The allocation is 10 vCPUs and 20 GB guest RAM; it does not mean ten dedicated physical cores.

The management VM would maintain a fixed pool of one worker. It would clone a clean Windows template, register the native GitHub runner for one job, preserve the permitted results, destroy the completed VM and writable job disks, and create its replacement. A failed or cancelled job still requires cleanup. Failed cleanup must stop reuse. I would initially replace the worker after destruction rather than overlap old and new workers; a ready spare later requires another worker's RAM and disk allocation.

This fixed-pool replacement service would require custom automation, not an existing Proxmox feature or a verified packaged product. I have not selected it as a substitute for established orchestration. The guest must receive neither Proxmox management credentials nor long-lived GitHub registration credentials. GitHub's ephemeral setting only deregisters a runner; an external service must delete the guest.

I would prepare the Windows template with the toolchain needed by TouchDeck, including ESP-IDF v6.1, Rust, Node 24, Python 3.13 and native Windows build tools. Packer and Ansible can make that preparation repeatable later. The template contains no registered runner identity or signing material. Template clones are new working machines, not retained recovery snapshots.

I would first route a reviewed TouchDeck installer-lifecycle/test-signing benchmark to the new worker. GitHub would continue running the other jobs. Moving all three Windows jobs to one local worker would serialize them and could increase release elapsed time. The durable release-signing path remains separate during this pilot, as do external PRs and the existing App Portal SignPath workflow. The existing App Portal installer runner remains unchanged.

I would keep package and compiler caches outside the disposable guest, initially using GitHub cache storage or a small local cache service. The release target directory, flags and trust scope need explicit cache configuration. Fast local compiler caching is a second measured improvement, not an automatic property of self-hosting. Build logs, caches and release artifacts have distinct purposes and retention policies.

If the Windows pilot is useful, I would add one disposable Ubuntu 24.04 worker at 8 vCPU and 16 GB RAM. This brings the proposed guest allocation to 18 vCPUs and 36 GB RAM. Docker would run inside that Linux VM for jobs that need containers; the VM remains the disposable isolation boundary. I would profile TouchDeck's Linux UI tests before expecting the new worker to shorten them. More simultaneous workers would follow measured queueing and concurrency needs.

The dedicated Mac is available for a later macOS workflow. None of the inspected workflows currently requests macOS. Kubernetes, ARC, Argo CD, Terraform/OpenTofu and a self-hosted registry are not dependencies of this pilot. GitHub continues to store source, schedule jobs, display results, retain selected artifacts and publish releases. The existing Kubernetes learning design remains a separate future exercise.

## Current platform direction

I want a reusable service that new repositories can join by selecting an approved build environment, with configurable concurrency limits and clean workers created on demand. I would maintain versioned Linux, Windows and macOS environment definitions, add specialized toolchains where needed, and separate release access from untrusted builds. Repository-scoped registration can serve personal repositories; shared organization-level pools would need an explicit organization and access design. No repository moves or runner registrations have been made.

For GitHub Actions integration, I would evaluate the current Actions Runner Controller autoscaling runner sets for Linux jobs. GitHub maintains this ARC mode and documents its support boundary; the legacy community mode is different. ARC uses Kubernetes to create and remove ephemeral runner pods. Scale-to-zero runner pods does not mean Proxmox VMs or the Kubernetes cluster are deleted: node provisioning is a separate lifecycle. [GitHub ARC support](https://docs.github.com/en/actions/concepts/runners/support-for-arc), [scale-set deployment](https://docs.github.com/en/actions/how-tos/manage-runners/use-actions-runner-controller/deploy-runner-scale-sets).

Native Windows GUI/installer tests and macOS builds remain separate worker pools. I have not verified an established turnkey integration that automatically creates and destroys Proxmox Windows VMs and Mac VMs while preserving all current GitHub Actions workflows. I would not present ARC as solving that requirement or select a small unverified virtualization plugin merely because the surrounding CI product is established.

Jenkins is an alternative if I choose to change CI orchestration. Its Kubernetes plugin creates dynamic pod agents, and its pipelines are defined in Jenkinsfiles. Adopting it would require pipeline migration; Proxmox and Mac provisioning integrations still need their own validation. GitLab Runner is another established executor, but its documented first-party VM autoscaling providers target AWS, Google Cloud and Azure, so switching to it alone does not establish Proxmox support. [Jenkins Kubernetes agents](https://plugins.jenkins.io/kubernetes/), [Jenkins Pipeline](https://www.jenkins.io/doc/book/pipeline/), [GitLab autoscaling](https://docs.gitlab.com/runner/runner_autoscale/gitlab-runner-autoscaler/).

The next architecture choice is whether deleting runner containers while retaining Kubernetes nodes satisfies the Linux requirement, and which supported lifecycle will handle native Windows and Mac workers. GARM and a new custom controller are not the default implementation path. This remains a design, with no infrastructure or workflow changes.
