# ubuntu-dev X11 Forwarding Enabled

**Created:** 2026-10-12  
**Last updated:** 2026-10-12

**Implementation date:** 2026-10-12  
**Status:** Complete  
**Affected systems:** VM 105 `ubuntu-dev` on `grey-server`: `/etc/ssh/sshd_config.d/99-hardening.conf`

On 2026-10-12 I turned SSH X11 forwarding back on for `ubuntu-dev`. It was the only host I checked with it off.

## Why it was off

On 2026-08-08 I hardened `debian-dev` with a six-line `99-hardening.conf`: the four lines my [Linux host baseline](../../../../../Guides/Linux-Host-Baseline.md) now requires, plus `X11Forwarding no` and `AllowUsers ai-agent` ([record](../../../../../Archive/Infrastructure/Compute/Galaxy/Documentation/Change%20Records/debian-dev%20Workstation%20Baseline%20and%20Toolchain%20Build%20-%202026-08-08.md)). That record gives no reason for the X11 line. `ubuntu-dev` replaced `debian-dev` on 2026-08-13, and its copy of the file is dated 10:02 PM that evening with the same six lines. The baseline written on 2026-08-15 took only the four core lines. On 2026-10-12 `sshd -T` read `x11forwarding yes` on all 16 other Linux hosts I could reach: the five nodes, `docker-main`, `docker-blue`, `docker-network`, `media-01`, `monitor-01`, `ansible-01`, `splunk-siem`, `security-01`, `alpha-prod-01`, `edge-01` and Andor-ParrotOS-PC. `app-01` and `parrot_os_mac` were unreachable.

## What changed

I deleted the `X11Forwarding no` line from `99-hardening.conf`. The file is now five lines, 122 bytes, `0644 root:root`:

```text
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
AllowUsers ai-agent
```

The main `sshd_config` carries `X11Forwarding yes` at line 113, so it now takes effect. `sshd -t` passed. `ssh.socket` owns port 22 here, so I restarted `ssh.service` rather than reloading it, at 1:36 PM Eastern. Both units are `active`.

## Verification

- `sshd -T` reads `x11forwarding yes` and `x11uselocalhost yes`. The other five settings are unchanged: `permitrootlogin no`, `pubkeyauthentication yes`, `passwordauthentication no`, `kbdinteractiveauthentication no`, `allowusers ai-agent`.
- After the restart, `ssh_execute` through the SSH Manager returned `ubuntu-dev as ai-agent`.
- `xauth` is installed, which `sshd` needs to set up a forwarded display.
- **End to end:** shortly after 1:40 PM Eastern I ran `ssh -X -v` from Andor-ParrotOS-PC, using its KDE Wayland session's display (`DISPLAY=:0`), into `ai-agent@192.168.40.179`. It authenticated with the `andor-parrotos-pc` key, the client logged `Requesting X11 forwarding with authentication spoofing.`, and the remote shell printed `DISPLAY=localhost:10.0`, the forwarded display. I deleted the test script from `/tmp` on the PC afterwards.

## Note

My first `ssh -X` attempt failed because the PC was unreachable. The PC had not crashed. KDE's power management suspended it at 1:34 PM Eastern (`PrepareForSleep(true)`, `AutoSuspendAction=1` on AC), and it resumed at 1:40 PM when I woke it. It had been up since 1:08 PM. I reran the test after it resumed.

## Rollback

Add `X11Forwarding no` back to `99-hardening.conf` above `AllowUsers`, run `sshd -t`, and restart `ssh.service`.
