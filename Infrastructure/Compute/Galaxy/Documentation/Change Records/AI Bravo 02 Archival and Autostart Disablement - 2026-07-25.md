# ai-bravo-02 Archival & Autostart Disablement

**Created:** 2026-07-25  
**Last updated:** 2026-07-25

**Implementation date:** 2026-07-25  
**Scope:** Galaxy LXC 105, TNIO records, SSH automation, local SSH state, & deletion scheduling  
**Status:** Archive complete; guest deletion scheduled for 2026-08-15

## Starting State

CT 105 `ai-bravo-02` existed on `grey-server` with a 100 GiB `ssd-lvm1` root volume, 6 vCPU, 24,384 MiB memory, seven NVIDIA device mappings, VLAN 40 address `192.168.40.38/24`, & `onboot: 1`. Proxmox reported the guest stopped.

The active tree still held the TNIO platform, walkthrough, diagrams, full CT inventory tables, Ansible host entry, Termix candidate, three live identity targets, local SSH alias, & three known-host keys.

## Scope

I archived the guest configuration & every tracked TNIO file. I removed current-state automation & local SSH references, disabled CT 105 autostart, & scheduled deletion for 2026-08-15. I did not start or delete the guest, remove its 100 GiB disk, or change its workload files.

## Decisions

- I disabled autostart because a `grey-server` reboot could otherwise start an archived guest before its deletion date.
- I kept CT 105 & `vm-105-disk-0` intact until 2026-08-15 so the deletion checklist can verify the archive & identify any external backup.
- I kept dated TNIO, Ansible, Termix, & governance records unchanged. Historical records retain the state observed when I wrote them.
- I retained the SSH Manager server definition for deletion-day cleanup because the stopped guest doesn't provide a live SSH connection.

## Step 1: Disable CT 105 Autostart

I connected to `grey-server` through the SSH Manager MCP, required `pct status 105` to report `stopped`, set `onboot` to `0`, & required the guest to remain stopped. The command returned exit code 0 with `ct=105 status=stopped onboot=0`.

The follow-up check at `2026-07-25T15:44:36-04:00` reported configuration modification time `2026-07-25 15:31:53 -0400`, `status: stopped`, `hostname: ai-bravo-02`, `onboot: 0`, & the unchanged root volume `ssd-lvm1:vm-105-disk-0,size=100G`.

Evidence: [S01 autostart transcript](../../Evidence/AI%20Bravo%2002%20Archival%20and%20Autostart%20Disablement%20-%202026-07-25/Logs/S01-Disable-Autostart-2026-07-25.txt).

## Step 2: Archive the Guest & TNIO Tree

I moved the 50-file `Platforms/TNIO AI Bot/` tree, walkthrough, SVG, & Excalidraw source into matching `Archive/` paths. I copied the former CT 105 configuration, storage, device, & network tables into the [archived guest record](../../../../../Archive/Operations/Inventory/Galaxy/AI%20Bravo%2002%20Archived%20Guest%20-%202026-07-25.md).

Commit `ececdf9` records the archive moves as 53 renames plus the guest record & current index changes. I retained no separate terminal transcript because the commit records every moved path & Git detected the unchanged files at 100% similarity.

## Step 3: Remove Current-State Access & Schedule Deletion

I removed `ai-bravo-02` from the repository & deployed Ansible inventory, Termix candidate group, Mac/Jedi/Termix identity target lists, local SSH alias, active known-host file, & known-host backup. The live validator returned 4 identities, 15 supported hosts, 2 unknown hosts, & 18 Semaphore templates. All five SSH playbooks passed syntax checks.

I added the 2026-08-15 deletion date to the root TODO, Galaxy checklist, & Mission Control backlog. Commits `6decbfa` & `ef02f94` keep automation cleanup separate from deletion scheduling.

I retained no separate Step 3 terminal transcript because the cleanup touched controller configuration & my per-user SSH client state. I kept those private files out of repository evidence. Commit `6decbfa` records the source inventory change; the read-only verification results below record the post-change state without copying the private files.

## Resulting Configuration

CT 105 remains defined on `grey-server`, stopped, with `onboot: 0` & its 100 GiB root volume attached. The active repository has no TNIO platform directory, active TNIO walkthrough, or `ai-bravo-02` Ansible target.

The archive holds all 50 former TNIO platform files, the walkthrough, both diagrams, exact guest tables, & this change record. The SSH Manager server definition remains until the deletion checklist closes.

## Verification

- `pct status 105` returned `stopped`; `pct config 105` returned `onboot: 0`.
- The live & repository validators each reported 15 supported SSH hosts.
- All five deployed SSH automation playbooks passed syntax checks.
- The controller inventory & three live identity files contain no `ai-bravo-02` or `192.168.40.38` match.
- The active TNIO platform & walkthrough paths are absent; their archive paths contain the same 50 platform files.
- The local SSH config, `known_hosts`, & `known_hosts.old` contain no hostname or address match.
- The root TODO, Galaxy backlog, & Mission Control each name 2026-08-15.

## Rollback Points

1. Set `pct set 105 --onboot 1` only if I decide CT 105 should return to service before deletion.
2. Move the TNIO platform, walkthrough, & diagrams back to their original paths & restore the active indexes if the workload resumes.
3. Restore `ai-bravo-02` to the Ansible inventory & approved identity target lists only after the guest is running & SSH is verified.
4. Recreate the local SSH alias & accept the host key after comparing its fingerprint with a trusted record.

## Remaining Work

On 2026-08-15 I will complete the [Galaxy deletion checklist](../TODO.md), delete CT 105 & `vm-105-disk-0`, remove the SSH Manager server definition, verify cluster, storage, DNS, DHCP, SSH, & automation state, then update the guest record from archived to retired.
