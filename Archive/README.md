# Archive

**Created:** 2026-07-09  
**Last updated:** 2026-08-14

I keep retired records under their original category so the old owner & date remain obvious. Current records stay with their owner; this directory isn't a holding area for files that lack a clear location.

## Archived & Retired Systems

| System | Retained records |
|---|---|
| `ai-alpha-01` / OpenClaw | [Retired guest record](Operations/Inventory/Galaxy/AI%20Alpha%2001%20Retired%20Guest%20-%202026-07-25.md), [platform documentation](Platforms/Openclaw/Documentation/OpenClaw-Setup-Overview.md), & [walkthrough](Guides/OpenClaw.md) |
| `ai-bravo-02` / TNIO AI Bot | [Retired guest record](Operations/Inventory/Galaxy/AI%20Bravo%2002%20Archived%20Guest%20-%202026-07-25.md), [platform source & records](Platforms/TNIO%20AI%20Bot/README.md), & [walkthrough](Guides/TNIO-AI-Bot.md); the TNIO and OpenClaw-backed source, tests, configuration, and evidence remain archived after CT 105 and its root volume were deleted on 2026-08-09 |
| Windows Active Directory domain | Private plan, dated change record, and evidence under `Platforms/Windows Servers/`; all three guests and their backups were destroyed on 2026-07-27 |
| Termix web SSH | [Decommission record](Platforms/Termix/Documentation/Change%20Records/Termix%20Decommission%20-%202026-07-28.md), [platform records](Platforms/Termix/README.md), & [walkthrough](Guides/Termix.md); the service, its data, & both tarballs were destroyed on 2026-07-28 with no backup. Its five [Semaphore templates](Platforms/Termix/Configuration/Semaphore%20Templates%20-%202026-07-29.md) outlived it on `ansible-01` and came out on 2026-07-29 |
| `debian-dev` / persistent remote development | [Archived guest record](Operations/Inventory/Galaxy/Debian%20Dev%20Archived%20Guest%20-%202026-08-14.md), the [GNOME installation](Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Debian%20Dev%20GNOME%20Installation%20-%202026-07-15.md) & [workstation baseline](Infrastructure/Compute/Galaxy/Documentation/Change%20Records/debian-dev%20Workstation%20Baseline%20and%20Toolchain%20Build%20-%202026-08-08.md) records, two resolved troubleshooting logs, & the [research](Architecture/Remote-AI-Development-Research-2026-07-12.md) that selected the design. VM 102 was destroyed on 2026-08-14 after `ubuntu-dev` replaced it |
| Syncthing | [Decommission record](Platforms/Syncthing/Documentation/Change%20Records/Syncthing%20Decommission%20-%202026-08-06.md) & [platform records](Platforms/Syncthing/README.md); the service, its configuration, the 17-file server copy of the Obsidian vault, and its version history were destroyed on 2026-08-06 with no backup. The Windows vault was untouched and is now the only copy |

## Superseded Network Records

| Record | Replacement |
|---|---|
| [UniFi network segmentation plan](Infrastructure/Network/UniFi/Documentation/Network%20Segmentation%20Backlog.md) | The completed Access-A, Security-A, Cluster-Net, and MGMT-A work remains in dated change records under `Infrastructure/Network/UniFi/Documentation/Change Records/` |
| UniFi zone and object consolidation plan | [Zone and Object Consolidation - 2026-07-27](../Infrastructure/Network/UniFi/Documentation/Change%20Records/Zone%20and%20Object%20Consolidation%20-%202026-07-27.md) |
| 61-policy pre-consolidation inventory | [Current firewall inventory](../Infrastructure/Network/UniFi/Configuration/firewall.md) |
| Galaxy VM inventory before the Active Directory retirement | [Pre-decommission VM snapshot](Operations/Inventory/Galaxy/VMs%20-%20Pre-AD-Decommission%20-%202026-07-27.md) |

## Cancelled Plans

| Record | Why it stopped |
|---|---|
| [Galaxy cluster node rename](Infrastructure/Compute/Galaxy/Documentation/Change%20Plans/Galaxy%20Cluster%20Node%20Rename%20Rolling%20Replacement%20Plan%20-%202026-07-31.md) & its [Green pilot](Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Green%20Node%20Rolling%20Replacement%20-%202026-07-31.md) | I cancelled the `*-server` to `*-node` rename on 2026-07-31 and kept the current names. Clustered Proxmox node names can't be edited in place, and Galaxy has no shared storage, so four of five nodes would have needed a backup and restore cycle. The [preflight evidence](Infrastructure/Compute/Galaxy/Evidence/Galaxy%20Green%20Node%20Rolling%20Replacement%20-%202026-07-31/Evidence-Index.md) is a valid 2026-07-31 snapshot of Green |
| [Agent Sandbox](Platforms/Agent%20Sandbox/README.md) | I dropped the on-demand sandbox broker on 2026-08-06. The design was locked on 2026-07-20 and nothing was ever built, so there was no broker, no sandbox VLAN, no template, and no guest to remove |

## Superseded Automation Copies

| Record | Replacement |
|---|---|
| Nine working copies from the 2026-07-29 fleet maintenance: four `os-update.yml` backups from the reboot rework and five `.pre-final-review` files | [Fleet Updates Intermediate States](Platforms/Ansible/Fleet%20Updates%20Intermediate%20States%20-%202026-07-29/README.md); the live project is [fleet-updates](../Platforms/Ansible/Source/fleet-updates/README.md) |
| The first Ansible project on `ansible-01`, from 2026-04-09, connecting as `root` and pushing keys to root key stores | [Legacy Controller Project](Platforms/Ansible/Legacy%20Controller%20Project%20-%202026-07-29/README.md); superseded by the [dedicated account work](../Platforms/Ansible/Documentation/Change%20Records/Dedicated%20Ansible%20Account%20and%20Fleet%20Expansion%20-%202026-07-25.md) on 2026-07-25 |
