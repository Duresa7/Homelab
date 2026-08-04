# edge-01 Package Source and Fleet Agent Holds

**Created:** 2026-08-04  
**Last updated:** 2026-08-04

**Change date:** 2026-08-04  
**Targets:** `edge-01`, `app-01`  
**Mechanism:** Ansible from `ansible-01`, `fleet-updates` inventory, `become` to root  
**Status:** Complete, with the agent upgrade deliberately not performed

## Why

`edge-01` had no Wazuh package source, so nothing would ever carry its agent forward. I [decided](../TODO.md) to add the source rather than treat that host's upgrades as a manual act, accepting a third-party package source and signing key on my edge ingress host.

I set out to upgrade the agent in the same job. I did not, and that is the most useful part of this record.

## What I changed

**The signing key.** Rather than download it onto the edge host, I copied the key already trusted by `app-01`, which has been pulling from the same source successfully. Fetched to `ansible-01` and confirmed byte-identical by SHA-256 before it went anywhere:

```text
app-01      /usr/share/keyrings/wazuh.gpg   root:root 644  2279 bytes
sha256      13300425f3e8cf17c8af92f895ba49b7d6621796b01ab5d2c348933a7d6ac174
ansible-01  /tmp/wazuhkey/wazuh.gpg         same sha256
```

That means both hosts provably trust the identical key, and nothing was fetched from the internet onto the ingress host.

**The source.** One line, identical to `app-01`:

```text
deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main
```

I ran both file changes with `--check --diff` first. The dry run showed two new files and nothing modified.

**The hold on `edge-01`.** Applied with the same `dpkg_selections` the deployment play uses, freezing the agent at `4.14.5-1`.

**The hold on `app-01`.** Not planned. See below.

## Why I did not upgrade the agent

I intended to move `edge-01` from `4.14.5-1` to the fleet's `4.14.6-1`. After `apt update` the repository showed something I had not expected:

```text
wazuh-agent:
  Installed: 4.14.5-1
  Candidate: 4.14.7-1
  Version table:
     4.14.7-1 500  https://packages.wazuh.com/4.x/apt stable/main amd64 Packages
```

The repository carries **only** `4.14.7-1`. It publishes the current package for a release line, not a back catalogue, so `4.14.6-1` is no longer installable from it. Meanwhile `security-01` runs manager `4.14.6-1`, and a Wazuh agent must never be newer than its manager.

So the only version I could install was the one version I must not install. I stopped and held the package instead.

This corrects the reasoning behind the original decision. Adding a source does not carry an agent forward by itself: the reachable version is capped by the manager, and the repository will not offer the capped version once it moves on. **The manager has to be upgraded first, and every agent in the fleet is gated behind that.**

## What adding the source exposed

Surveying every host for the version, the hold, and the source turned up a live risk that had nothing to do with `edge-01`.

`app-01` carried the source with **no hold**. Simulating a fleet run proved what would have happened:

```text
Inst wazuh-agent [4.14.6-1] (4.14.7-1 4.x/apt stable:stable [amd64])
```

The next ordinary package run would have upgraded `app-01` past the manager into an unsupported pairing. I applied the hold, which is reversible and changed no package:

```text
apt-mark showhold            -> wazuh-agent
apt-get -s upgrade           -> "The following packages have been kept back: linux-image-amd64 wazuh-agent"
dpkg-query wazuh-agent       -> installed=4.14.6-1
systemctl is-active          -> active
```

`app-01` and `edge-01` are the two hosts outside the twelve-target deployment inventory, which is why neither had been held: the play that applies holds never ran against them. That also explains the empty `apt-mark showhold` results I saw earlier and had briefly taken for a documentation error.

`docker-main` runs agent `4.14.0-1` with no source and no hold, the widest gap in the fleet. I left it alone and tracked it, because it needs the same manager upgrade first.

## Verification

`edge-01` after the change:

```text
apt-mark showhold                    -> wazuh-agent
dpkg-query wazuh-agent               -> installed=4.14.5-1
systemctl is-active wazuh-agent      -> active
apt-get -s upgrade                   -> "kept back: linux-image-amd64 wazuh-agent"
apt-get -s dist-upgrade              -> 0 lines matching "^Inst wazuh-agent"
```

I checked the hold against both `upgrade` and `dist-upgrade` because naming a package explicitly on the command line can bypass a hold, so a single simulated `upgrade wazuh-agent` would have been a misleading test. The fleet play uses `ansible.builtin.apt` with `upgrade:`, which respects holds.

The agent stayed active throughout. No package was installed, removed, or upgraded on either host, and no service was restarted.

## What remains open

- Upgrade manager `security-01` from `4.14.6-1` before any agent moves.
- Then move `edge-01` off `4.14.5-1` and `docker-main` off `4.14.0-1`, and give `docker-main` a source and a hold.
- The holds are deliberate and must stay until the manager moves. Removing one re-creates the overshoot.
