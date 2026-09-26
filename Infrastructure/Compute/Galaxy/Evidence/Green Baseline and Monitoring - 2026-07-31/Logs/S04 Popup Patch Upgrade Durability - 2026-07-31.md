# S04 Popup Patch Upgrade Durability

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

**Capture time:** 2026-07-31 11:44 through 11:58 EDT  
**Targets:** All five Galaxy nodes  
**Mechanism:** SSH Manager `ssh_execute` on Grey, Purple, Blue, and Red; Grey's key-only SSH path to Green

## The Gap

The patched state was correct on all five nodes and would not have survived the next `proxmox-widget-toolkit` upgrade on four of them. Only Grey had a re-apply hook:

```text
grey-server    kernels=6.14.11-9 6.14.8-2 6.17.13-19 7.0.14-6 7.0.2-6 running=7.0.14-6-pve nag-hook=yes
purple-server  kernels=7.0.14-6 7.0.2-6 running=7.0.14-6-pve nag-hook=NO
blue-server    kernels=7.0.14-6 7.0.2-6 running=7.0.14-6-pve nag-hook=NO
red-server     kernels=7.0.14-6 7.0.2-6 running=7.0.14-6-pve nag-hook=NO
green-server   kernels=7.0.14-8 7.0.2-6 running=7.0.2-6-pve nag-hook=NO
```

An upgrade replaces `proxmoxlib.js` with the stock file, which restores the nag. `S01`'s read-back proves the patch is applied now; it says nothing about whether the patch survives `apt`. Grey's existing `/etc/apt/apt.conf.d/no-nag-script` hook also carried an unguarded `sed` that would rewrite any file matching `/data\.status/`, including a future layout the tested script is written to refuse.

## The Hook

I installed the same `/etc/apt/apt.conf.d/99-galaxy-no-subscription-nag` on all five nodes. It calls the already-deployed script rather than repeating its `sed`:

```apt
// Re-applies the Galaxy subscription-popup patch after any package upgrade that
// replaces proxmoxlib.js. The script is idempotent and restarts pveproxy only
// when it actually changes the file.
DPkg::Post-Invoke { "if [ -x /usr/local/sbin/disable-proxmox-subscription-popup ]; then /usr/local/sbin/disable-proxmox-subscription-popup --apply || echo 'WARNING: Galaxy subscription popup patch needs review'; fi"; };
```

The `|| echo` matters. The script exits 3 on an unrecognized layout, and a non-zero `DPkg::Post-Invoke` makes `apt` report a failure. Swallowing the status keeps `apt` clean while still printing the reason to review.

## Five-Node Read-Back

```sh
printf "%-14s hook_sha=%s parsed=%s script=%s check=" "$(hostname)" \
  "$(sha256sum /etc/apt/apt.conf.d/99-galaxy-no-subscription-nag | cut -c1-12)" \
  "$(apt-config dump | grep -c disable-proxmox-subscription-popup)" \
  "$(test -x /usr/local/sbin/disable-proxmox-subscription-popup && echo ok || echo MISSING)"
apt-get check >/dev/null 2>&1 && echo pass || echo FAIL
/usr/local/sbin/disable-proxmox-subscription-popup --apply
```

```text
grey-server    hook_sha=d4384dc64be2 parsed=1 script=ok check=pass
purple-server  hook_sha=d4384dc64be2 parsed=1 script=ok check=pass
blue-server    hook_sha=d4384dc64be2 parsed=1 script=ok check=pass
red-server     hook_sha=d4384dc64be2 parsed=1 script=ok check=pass
green-server   hook_sha=d4384dc64be2 parsed=1 script=ok check=pass
proxmox-widget-toolkit 5.2.6: popup patch already present   (all five)
```

Identical hook hash on all five, `apt-config` parses exactly one instance, and `apt-get check` passes, so the hook is valid `apt` configuration rather than a file that merely exists.

## Removing Grey's Redundant Hook

```sh
mv /etc/apt/apt.conf.d/no-nag-script /root/no-nag-script.superseded-2026-07-31
apt-config dump | grep -c "proxmoxlib\|disable-proxmox-subscription-popup"
apt-get check
```

```text
=== BEFORE ===
99-galaxy-no-subscription-nag
no-nag-script
=== AFTER ===
99-galaxy-no-subscription-nag
=== HOOK COUNT (must be 1) ===
1
=== apt-get check ===
pass
```

I moved it rather than deleting it, so the original is recoverable at `/root/no-nag-script.superseded-2026-07-31`.

## End-to-End Proof on Green

A read-back proves the hook is installed, not that it fires. I reinstalled the package on Green, which has no guests, to make `apt` actually overwrite `proxmoxlib.js`:

```sh
DEBIAN_FRONTEND=noninteractive apt-get install --reinstall -y -o Dpkg::Use-Pty=0 proxmox-widget-toolkit
```

```text
=== BEFORE: patched markers ===
2
0 upgraded, 0 newly installed, 1 reinstalled, 0 to remove and 7 not upgraded.
Preparing to unpack .../proxmox-widget-toolkit_5.2.6_all.deb ...
Unpacking proxmox-widget-toolkit (5.2.6) over (5.2.6) ...
Setting up proxmox-widget-toolkit (5.2.6) ...
proxmox-widget-toolkit 5.2.6: popup patch applied
=== AFTER: stock markers (want 0) ===
0
=== AFTER: patched markers (want 2) ===
2
=== pveproxy ===
active
=== API reachable ===
401
```

`popup patch applied` came from the hook, not from me. The package replaced the file with the stock version and the hook re-patched it inside the same `apt` transaction. `pveproxy` stayed active and the unauthenticated local API returned the expected 401.

**Exit code:** `0` on every command above.
