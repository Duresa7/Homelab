# Kasm Session Limit Exemption

**Created:** 2026-08-01  
**Last updated:** 2026-08-01

**Implemented:** 2026-08-01  
**Owner:** Platforms / Kasm Workspaces  
**Status:** Implemented and verified

## Result

My `dkadi` account no longer has a session time limit. An active session now runs until I end it, survives a closed browser tab for seven days, and won't be disconnected for sitting idle. The `alpha` account kept its one-hour cap, its three-session ceiling, and every containment setting, so nothing about the lab lanes changed.

The fix wasn't setting a limit to zero. Kasm 1.19.0 treats a `session_time_limit` of `0` as present rather than absent, and a present value stops the keepalive from being extended at all. I had to remove the setting from every group `dkadi` belongs to, which meant moving the limit onto `alpha` instead of relaxing it on the group both accounts share.

I then lifted the eight `Lab Sessions` restrictions on my account as well, so download, clipboard in both directions, seamless clipboard, printing, sharing, microphone, and user storage mappings all work on every tile including the malware and review lanes. `alpha` keeps every one of them.

## Scope

This change covered twelve `group_settings` rows, one new group, and one group membership. It didn't touch workspace definitions, Docker networks, DNS overrides, UniFi policy, the Proton route, VM sizing, or persistent profile paths. The network containment is untouched: the lanes, the blackholed resolvers, and the firewall rules apply to both accounts exactly as before. What changed is data egress from inside a session, which is no longer enforced on my account.

## How Kasm Resolves a Group Setting

`get_setting_value` in `/src/api_server/data/model.pyc` walks every group the user belongs to, keeps the value from the group with the numerically lowest `priority`, and starts its comparison at 4096. One group wins outright. There's no merge and no most-restrictive rule, so a permissive value in a priority 1 group beats a restrictive value in a priority 100 group.

The three groups were `Administrators` at priority 1, `Lab Sessions` at 100, and `All Users` at 1000. `Administrators` is a system group holding only `dkadi`, which makes it the natural place for anything that should apply to me alone.

## The Zero-Versus-Absent Trap

Two functions read `session_time_limit` and they disagree about what counts as unset.

`client_api._keepalive` tests `user.get_setting_value('session_time_limit', None) is not None`. When that passes it logs `User has a session_time_limit of (%s) defined. Will not promote keepalive` and returns without extending `expiration_date`. `provider_manager.get_keepalive_expiration` tests the same value for truthiness instead, so it falls through to `keepalive_expiration` when the value is `0`.

Setting `session_time_limit` to `0` on `Administrators` would therefore have made things worse in a way that looks like a fix. The initial expiry would come from `keepalive_expiration`, the keepalive would never extend it, and the session would die on a hard clock instead of a sliding one. An empty value isn't an option either: `casted_value` runs a bare `int(self.value)` for any row whose `value_type` is `int`, so a blank string raises `ValueError`.

Absent is the only state that means unlimited. Kasm's own migration `513964618cf2` seeds the default at `'0'`, which is why the zero reading is tempting and wrong.

## Step-Based Walkthrough

### Step 1: Read the live state and back up the database

`dkadi` resolved to `session_time_limit` 3600 from `Lab Sessions`, `keepalive_expiration` 3600 and `keepalive_expiration_action` `delete` from `All Users`, `idle_disconnect` 20 minutes from `All Users`, and `max_kasms_per_user` 3 from `Lab Sessions`. No workspace row carried its own `session_time_limit`, so the group value was the only clock.

`pg_dump` produced 1,756,363,737 bytes, which gzip reduced to 234 MB at `/home/dkadi/kasm-db-backup-2026-08-01.sql.gz`. The `logs` table accounts for 1556 MB of that, against 424 kB for `servers` and 224 kB for `kasms`.

### Step 2: Move the limit onto alpha rather than off the shared group

`Lab Sessions` grants the 19 lane-assigned tiles and carries no egress, file, storage, or permission mappings, so pulling `dkadi` out of it would only have cost tile access. I left the membership alone anyway, because staying in the group keeps the download and clipboard restrictions applied to my own sessions.

Instead I created `Lab Session Time Limit` at priority 50, added `alpha` to it, gave it the single row `session_time_limit` 3600, and deleted that row from `Lab Sessions`. Priority 50 beats `Lab Sessions` at 100, so `alpha` resolves to the same 3600 it did before. `dkadi` now belongs to no group that defines the setting.

### Step 3: Set the remaining timers on Administrators

Three rows went onto `Administrators`, which only `dkadi` can reach:

| Setting | Value | Effect |
| --- | --- | --- |
| `keepalive_expiration` | 604800 | A closed tab holds the session for seven days |
| `idle_disconnect` | 525600 | Idle disconnect pushed out to a year, measured in minutes |
| `max_kasms_per_user` | 3 | Unchanged from what `Lab Sessions` gave me |

I used 525600 minutes rather than `0` for `idle_disconnect` because I couldn't confirm which way Kasm reads zero. Migration `f8471782d553` documents the field as minutes and seeds it at 20, and the RDP gateway path computes `inactivity_timeout` as `int(idle_disconnect) * 60`, but nothing in the code says whether `0` disables the timer or fires it immediately. A large number gets the same outcome without depending on that answer.

### Step 4: Reject my own concurrency number

I'd planned `max_kasms_per_user` 10 and it was wrong for this host. `free -h` reports 11 GiB total with 9.7 GiB available, and 30 of the 33 enabled workspace rows request 2.70 GiB each in `images.memory_bytes`. Ten concurrent desktops is 27 GiB against 9.7 GiB available and 4 GiB of swap.

Three desktops is 8.1 GiB and fits. A fourth doesn't, which matches the ceiling already recorded in the README. I set the row to 10, caught the arithmetic, and corrected it to 3.

I settled on 5 after checking the host. `images.memory_bytes` becomes a Docker `--memory` ceiling rather than a reservation, so an idle Terminal session doesn't hold 2.70 GiB and five light sessions do fit. Five busy desktops don't. Five is also the Community Edition cap, so the group setting now stops refusing launches that the licence would refuse anyway, and memory pressure decides the real limit.

### Step 5: Lift the eight remaining restrictions

`Lab Sessions` at priority 100 was still beating `All Users` at 1000 for eight boolean settings on my account. I added all eight to `Administrators` with `value_type` `bool` and value `True`, matching the descriptions Kasm ships on the `All Users` rows:

`allow_kasm_clipboard_down`, `allow_kasm_clipboard_seamless`, `allow_kasm_clipboard_up`, `allow_kasm_downloads`, `allow_kasm_microphone`, `allow_kasm_printing`, `allow_kasm_sharing`, `allow_user_storage_mapping`.

`casted_value` lowercases a `bool` row before comparing, so `True` and `true` both work; I used `True` to match every existing row. I left `allow_kasm_gamepad` and `allow_kasm_webcam` at `False`, because those come from `All Users` rather than `Lab Sessions` and were never part of the lab containment.

### Step 6: Verify

I restarted `kasm_api` and `kasm_manager` after each write. All eight services returned healthy and `https://localhost/api/__healthcheck` returned `200`.

Replaying the priority rule against the live database gives:

| Setting | `dkadi` | Won from | `alpha` | Won from |
| --- | --- | --- | --- | --- |
| `session_time_limit` | absent | none | 3600 | `Lab Session Time Limit` (50) |
| `keepalive_expiration` | 604800 | `Administrators` (1) | 3600 | `All Users` (1000) |
| `keepalive_expiration_action` | `delete` | `All Users` (1000) | `delete` | `All Users` (1000) |
| `idle_disconnect` | 525600 | `Administrators` (1) | 20 | `All Users` (1000) |
| `max_kasms_per_user` | 5 | `Administrators` (1) | 3 | `Lab Sessions` (100) |
| the eight boolean permissions | `True` | `Administrators` (1) | `False` | `Lab Sessions` (100) |

All eight services returned healthy after the second write as well, and the health endpoint returned `200` again.

## Final State

- `dkadi` has no `session_time_limit` in any group, so `_keepalive` extends `expiration_date` by 604800 seconds on every client keepalive.
- A `dkadi` session ends when I delete it, when the host runs out of memory, or seven days after the last keepalive.
- Download, clipboard both ways, seamless clipboard, printing, sharing, microphone, and user storage mappings work for `dkadi` on all 33 tiles.
- `alpha` is unchanged in every effective value: 3600 seconds, three sessions, and all eight restrictions.
- Group priorities are `Administrators` 1, `Lab Session Time Limit` 50, `Lab Sessions` 100, `All Users` 1000.
- Network containment is untouched. The four macvlan lanes, the blackholed VLAN 77 and 79 resolvers, and every UniFi policy behave the same for both accounts.

## What This Costs

A session that never expires holds up to 2.70 GiB until I remember it. Three busy desktops is 8.1 GiB of the 9.7 GiB available, the fourth and fifth reach the 4 GiB swap file, and the idle disconnect that used to clean up after 20 minutes is a year out. The `keepalive_expiration_action` is still `delete`, so the seven-day timer is the only automatic reclaim left.

The bigger cost is data egress. I can now copy text out of a `REMnux - Malware` session and download a file from a `Debian - Review` session straight to my own machine. The lane still can't reach the Internet and still can't resolve a name, so a sample can't call home; the path that opened is the one through my browser, which was always the one the group settings existed to close. Nothing stops me from carrying a live sample to my desktop by hand now except knowing not to. `alpha` remains the account to use when I want that enforced rather than remembered.

`baseline-parrot-2026-07-30` predates this change. Rolling VM 122 back to it reverts Kasm's database and restores the one-hour limit, because the snapshot contains the old `group_settings` rows. The documented practice is to replace the baseline after a settings change; I left the existing snapshot in place rather than delete the only recovery point, so that replacement is outstanding.

## Guest Restart Mid-Change

Proxmox ran `qmshutdown` on VM 122 at 11:04:32 and `qmstart` at 11:05:35 local, both as `root@pam`, recorded in `/var/log/pve/tasks/index` on `purple-server`. The guest journal shows a clean `systemd-poweroff`. All eight Kasm services came back healthy on their own and I carried on reading the database.

That was the fleet kernel upgrade, not a fault. [Galaxy Cluster PVE 9.2.6 Upgrade and SSH Host Key Seeding](../../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Cluster%20PVE%209.2.6%20Upgrade%20and%20SSH%20Host%20Key%20Seeding%20-%202026-08-01.md) records `purple-server` as the second node rebooted onto `7.0.14-8-pve`, with `kasm-01` down 80 seconds. The 63 seconds between the two Proxmox tasks sits inside that window.

Worth keeping in mind for the settings this change makes: a node reboot destroys every running session regardless of a seven-day keepalive window, so "unlimited" means unlimited until the next kernel update.

## Rollback

To restore the one-hour limit on `dkadi`, put the row back on the group that both accounts share and drop the exemption group:

```sql
INSERT INTO group_settings (name, value, value_type, description, group_id)
SELECT 'session_time_limit', '3600', 'int',
       'If enabled, sessions are limited to the defined value in seconds.', group_id
FROM groups WHERE name = 'Lab Sessions';
DELETE FROM groups WHERE name = 'Lab Session Time Limit';
DELETE FROM group_settings gs USING groups g
WHERE gs.group_id = g.group_id AND g.name = 'Administrators'
  AND gs.name IN ('keepalive_expiration','idle_disconnect','max_kasms_per_user');
```

To restore the eight restrictions on my account without touching the timers, drop just those rows so `Lab Sessions` wins again:

```sql
DELETE FROM group_settings gs USING groups g
WHERE gs.group_id = g.group_id AND g.name = 'Administrators'
  AND gs.name IN ('allow_kasm_clipboard_down','allow_kasm_clipboard_seamless',
                  'allow_kasm_clipboard_up','allow_kasm_downloads','allow_kasm_microphone',
                  'allow_kasm_printing','allow_kasm_sharing','allow_user_storage_mapping');
```

Deleting the group cascades to its `user_groups` and `group_settings` rows. Restart `kasm_api` and `kasm_manager` afterwards. The full database rollback is `/home/dkadi/kasm-db-backup-2026-08-01.sql.gz`, taken before any write.

## Linked Records

- [Session workflows](../Session-Workflows.md)
- [Kasm Workspace Build-Out](Kasm%20Workspace%20Build-Out%20-%202026-07-28.md)
- [Kasm Parrot Workspace Build-Out](Kasm%20Parrot%20Workspace%20Build-Out%20-%202026-07-30.md)
- [Kasm Workspaces TODO](../TODO.md)
