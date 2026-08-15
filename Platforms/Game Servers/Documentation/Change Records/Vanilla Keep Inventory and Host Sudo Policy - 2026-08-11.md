# Vanilla Keep Inventory and Host Sudo Policy

**Created:** 2026-08-11  
**Last updated:** 2026-08-11

**Implemented:** 2026-08-11  
**Owner:** Platforms / Game Servers  
**Host:** `game-01`, LXC 123 on `green-server`, `192.168.80.30`  
**Status:** Complete. Vanilla keeps player inventories after death, and `dkadi` has passwordless sudo on `game-01`.

## Change

I enabled keep-inventory behavior on the public Vanilla Minecraft 26.2 server and gave my normal `dkadi` SSH account passwordless sudo for my own convenience on this host. I did not restart the game server, disconnect its player, or change the retained Better Realism server.

The original host build deliberately left `dkadi` with the password-required Debian `sudo` group rule. The live state still matched that record: `sudo -l -U dkadi` showed only `(ALL : ALL) ALL`, while separate `90-ansible` and `90-ai-agent` drop-ins granted those accounts NOPASSWD access. The `ai-agent` account exists but has no authorized SSH key, so I kept its rule unchanged.

I added `/etc/sudoers.d/90-dkadi` as `root:root` at mode 0440 with this rule:

```sudoers
dkadi ALL=(ALL:ALL) NOPASSWD: ALL
```

I validated the temporary rule before installing it, then validated the complete sudoers configuration. The effective SSH policy remained public-key only with root login, password authentication, and keyboard-interactive authentication disabled.

Minecraft 26.2 rejected the legacy `keepInventory` name. Its current game-rule identifier is `keep_inventory`, so I sent these commands through Wings' authenticated loopback command endpoint:

```text
gamerule keep_inventory true
gamerule keep_inventory
save-all flush
```

The Wings token stayed on `game-01`: I loaded it from the existing mode-0600 configuration into a mode-0600 temporary curl configuration, used it only against `127.0.0.1:8080`, and shredded the temporary file after each request. No credential value was captured.

## Console path

A direct Docker console attach did not provide a safe bounded session. The write attempt exited without sending a command, and a later read-only attach client outlived its SSH timeout. I killed only the three orphaned attach-client processes with signal forwarding disabled and confirmed that the Minecraft container remained running. I then used Wings' own `POST /api/servers/<server-uuid>/commands` path, which returned HTTP 204 for each accepted command batch.

## Verification

| Check | Observed result |
|---|---|
| Sudoers syntax | The temporary `90-dkadi` rule and the complete configuration parsed successfully |
| Effective `dkadi` policy | `sudo -l -U dkadi` showed the existing `(ALL : ALL) ALL` group rule followed by the new `(ALL : ALL) NOPASSWD: ALL` |
| Normal SSH path | `sudo -n true` and `sudo -n docker ps` both exited 0 through the `game_01` SSH Manager target |
| Game-rule write | Console reported `Gamerule keep_inventory is now set to: true` |
| Game-rule read-back | Console reported `Gamerule keep_inventory is currently set to: true` |
| World persistence | `save-all flush` reported `Saving the game` followed by `Saved the game` |
| Runtime | The Vanilla container remained running throughout the change |
| Supporting services | `wings`, `docker`, `playit`, and `minecraft-playit-relay` were enabled and running |
| Public path | `minecraft.alphasecunited.com` returned Minecraft 26.2, protocol 776, one of 20 players, and `A Minecraft Server` in 223.4 ms through SRV discovery |

I created no snapshot or backup. This changed one saved game rule and one independently validated sudoers drop-in. No separate evidence transcript was retained; the observed results are recorded above.

## Open work

The game-rule change is finished. The sudo grant is not: it puts `game-01` outside the [Linux host baseline](../../../../Guides/Linux-Host-Baseline.md), where only unattended accounts carry `NOPASSWD`. The fleet sudo priority in the root [TODO](../../../../TODO.md) either approves this host as a documented exception or removes the drop-in with the other nonconforming grants. Until that decision lands, `game-01` is a known deviation I made deliberately rather than an oversight.
