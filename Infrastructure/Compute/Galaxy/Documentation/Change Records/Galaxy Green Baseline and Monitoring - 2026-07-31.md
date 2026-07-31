# Galaxy Green Baseline and Monitoring

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

**Implementation date:** 2026-07-31  
**Status:** Complete except Green's pending kernel reboot  
**Primary owner:** Galaxy Proxmox cluster  
**Affected systems:** All five Galaxy nodes, Galaxy PXE on `ansible-01`, Prometheus on `monitor-01`

## Scope

I made the Proxmox subscription-popup change reproducible across all five nodes, added the same action to Galaxy PXE first boot, and added Green to the shared Prometheus node job. I also made that popup change survive package upgrades. The hardware tests and Green SATA wipe closed under the hardware change record; Green's reboot into the installed kernel is the only step still open.

## Starting State

Green had joined Galaxy as `green-server` on `192.168.70.14`, but the five nodes did not share a versioned popup-patch command. Green exported node, SMART, and NVMe metrics on TCP 9100, but Prometheus still had 48 targets and did not scrape it. The UniFi monitoring policy already used `OBJ-Proxmox-Nodes`, which contained `192.168.70.10` through `192.168.70.14`.

Green still ran the installer kernel `7.0.2-6-pve` even though `7.0.14-8-pve` was installed. I deferred its reboot because the extended SMART test on the separate Hitachi SATA disk was active.

## Decisions

I kept one idempotent script at `/usr/local/sbin/disable-proxmox-subscription-popup` on every node. It refuses an unknown JavaScript layout instead of changing a file it does not recognize. Galaxy PXE renders the same guarded change during first boot, so a new node receives the baseline without a separate manual pass.

I added Green to the existing `node` scrape job with `host: green-server`. I built the deployment candidate from the live Prometheus file so the private domain values stayed intact. I did not copy the scrubbed repository example over the live file.

I kept the UniFi policy group-based. `Allow Proxmox Nodes to Galaxy PXE` and the monitoring policies use `OBJ-Proxmox-Nodes`; I found no unreferenced or duplicate firewall group that could be removed without deleting an intentional object.

## Step 1: Build and Test the Popup Automation

I added [disable-proxmox-subscription-popup.sh](../../Scripts/disable-proxmox-subscription-popup.sh) and its [fixture test](../../Tests/test-disable-proxmox-subscription-popup.sh). The test covered the first patch, an idempotent second run, and rejection of a one-match source layout. Bash syntax and the fixture test passed. [S01 records the command and result](../../Evidence/Galaxy%20Green%20Baseline%20and%20Monitoring%20-%202026-07-31/Logs/S01%20Popup%20Automation%20and%20Fleet%20Verification%20-%202026-07-31.md).

## Step 2: Apply and Verify the Popup Baseline

I installed the script on Grey, Purple, Blue, Red, and Green, then ran it once on each node. Grey was already patched. The other four nodes changed to the same guarded sentinel.

The final read-back found the same script SHA-256 on every node, zero stock subscription checks, two patched checks, an active `pveproxy`, and HTTP 401 from the unauthenticated local API request. HTTP 401 is the expected answer and proves that the HTTPS listener responded. [S01 contains the five-node result](../../Evidence/Galaxy%20Green%20Baseline%20and%20Monitoring%20-%202026-07-31/Logs/S01%20Popup%20Automation%20and%20Fleet%20Verification%20-%202026-07-31.md).

## Step 3: Add the Baseline to Galaxy PXE

I updated Galaxy PXE first boot to require the known two-match stock or patched source layout, apply the `NoMoreNagging` sentinel, and restart `pveproxy` only when it changed the file. The 21 Python tests and Python compilation passed. I deployed the update to `ansible-01`; the final playbook run reported `changed=0`, `failed=0`, and `unreachable=0`. [S02 records the local and live checks](../../Evidence/Galaxy%20Green%20Baseline%20and%20Monitoring%20-%202026-07-31/Logs/S02%20PXE%20Baseline%20Integration%20-%202026-07-31.md).

## Step 4: Add Green to Prometheus

I inserted `192.168.70.14:9100` after the other four Galaxy nodes with `host: green-server` and `role: hypervisor`. `promtool` accepted the candidate before I changed the live file.

The first acceptance run exposed a stale test: `assert_targets.py` omitted the existing Kasm probe and expected 48 targets. The rollback restored the original file. I added Kasm to the expected set and tried again. The next acceptance check ran before the 60-second blackbox scrape cycle had completed, so nine existing probes were still `unknown`; that guard also rolled back. Neither failure left Green in the live config.

On the final run I checked Green separately, waited through a full scrape cycle, then required the whole target set. The live file kept inode `393283`, its SHA-256 matched `/etc/prometheus/prometheus.yml` inside the container, all 49 targets were up, and all 65 dashboard queries returned data. Green reported node_exporter 1.9.0, `up=1`, and 88 SMART or NVMe metric families. I retained `/home/dkadi/monitoring/prometheus.yml.bak.20260731T140158Z` and removed the three superseded rollback copies and temporary test files. [S03 records the rollout and final checks](../../Evidence/Galaxy%20Green%20Baseline%20and%20Monitoring%20-%202026-07-31/Logs/S03%20Green%20Prometheus%20Target%20-%202026-07-31.md).

## Step 5: Make the Popup Patch Survive Upgrades

Applying the patch is not the same as keeping it. Any `proxmox-widget-toolkit` upgrade replaces `proxmoxlib.js` with the stock file and brings the nag back, and only Grey had a re-apply hook; Purple, Blue, Red, and Green had none. Grey's hook was also an unguarded `sed` over any line matching `/data\.status/`, which would rewrite a future layout the tested script is built to refuse.

I installed the same `/etc/apt/apt.conf.d/99-galaxy-no-subscription-nag` on all five nodes. It calls `/usr/local/sbin/disable-proxmox-subscription-popup --apply` from `DPkg::Post-Invoke` and swallows the exit status behind a warning, so an unrecognized layout prints a review message instead of failing the `apt` run. All five nodes report the same hook SHA-256 prefix `d4384dc64be2`, one parsed instance in `apt-config dump`, and a passing `apt-get check`. I moved Grey's old hook to `/root/no-nag-script.superseded-2026-07-31` so exactly one hook remains.

Then I proved it fires rather than just existing. I reinstalled `proxmox-widget-toolkit` on Green, which has no guests. The package overwrote the file with the stock version and the hook printed `popup patch applied` inside the same `apt` transaction, ending at 0 stock markers and 2 patched markers with `pveproxy` still active. [S04 records the gap, the hook, and the reinstall proof](../../Evidence/Galaxy%20Green%20Baseline%20and%20Monitoring%20-%202026-07-31/Logs/S04%20Popup%20Patch%20Upgrade%20Durability%20-%202026-07-31.md).

## Resulting Configuration

| Item | Result |
|---|---|
| Popup automation | One guarded script with the same SHA-256 on all five nodes |
| Upgrade durability | Same `apt` `DPkg::Post-Invoke` hook on all five nodes, proven by a package reinstall on Green |
| PXE first boot | Applies the guarded popup baseline and restarts `pveproxy` when needed |
| Prometheus targets | 49 of 49 present and up |
| Green exporter | `node` job, `green-server`, `192.168.70.14:9100`, node_exporter 1.9.0 |
| Grafana validation | 65 of 65 queries returned data |
| UniFi selectors | Shared `OBJ-Proxmox-Nodes` object covers all five nodes |

## Rollback

For the popup change, I can remove `/etc/apt/apt.conf.d/99-galaxy-no-subscription-nag` and then reinstall `proxmox-widget-toolkit` to restore its stock JavaScript and restart `pveproxy`. Reinstalling without removing the hook first will simply re-patch the file, which S04 demonstrates. Grey's previous hook is recoverable at `/root/no-nag-script.superseded-2026-07-31`. The script refuses any source layout outside the exact stock or patched form.

For Prometheus, I can copy `/home/dkadi/monitoring/prometheus.yml.bak.20260731T140158Z` over the live file, restart the `prometheus` container, and rerun both assertions. The retained backup is the 48-target pre-Green state.

## Remaining Work

One item. Green still runs the installer kernel `7.0.2-6-pve` with `7.0.14-8-pve` installed, so it needs a reboot followed by a check of the kernel, quorum, both Corosync links, monitoring, and the popup patch. I held that reboot while the `*-node` rename was still open, since a reinstall would have made it redundant. I cancelled the rename on 2026-07-31, so nothing blocks the reboot now.

Both extended SMART results are captured, Green's SATA metadata is wiped, and the hardware and inventory records carry both nodes' final memory and drive state. The [hardware change record](../../../../Hardware/Documentation/Change%20Records/Galaxy%20Green%20and%20Blue%20Hardware%20Changes%20-%202026-07-31.md) closes that side of the work.

