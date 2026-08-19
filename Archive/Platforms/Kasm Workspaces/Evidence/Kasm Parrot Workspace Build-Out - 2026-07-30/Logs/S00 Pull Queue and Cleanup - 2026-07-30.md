# S00 Pull Queue and Cleanup

**Created:** 2026-07-30  
**Last updated:** 2026-07-30

**Capture time:** 2026-07-30 00:42 through 00:48 EDT  
**Target:** `purple-server`, VM 122 `kasm-01`  
**Mechanism:** SSH Manager MCP, Proxmox CLI, QEMU guest agent, Docker CLI

## Queue evidence

The agent log showed this sequence:

```text
04:22:35 UTC Pulling docker image kasmweb/terminal:1.19.0-rolling-daily
04:26:28 UTC Successfully pulled image kasmweb/terminal:1.19.0-rolling-daily
04:26:28 UTC Pulling docker image kcr.kasmweb.com/kasmweb/claude-code:1.19.0-rolling-daily
04:33:32 UTC Successfully pulled image kcr.kasmweb.com/kasmweb/claude-code:1.19.0-rolling-daily
04:33:32 UTC Pulling docker image kasmweb/forensic-osint:1.19.0-rolling-daily
```

Parrot was not present in `docker image inspect`, and its database row remained `available=false`. This was a catalog refresh, not one continuing Parrot pull.

## Safety stop

`ssd-lvm2` rose from 67.65 to 68.67 percent while Forensic OSINT was active. I stopped only `kasm_agent`. Docker canceled the incomplete pull and released temporary layers:

```text
ssd-lvm2 before agent stop: 68.67 percent
ssd-lvm2 after incomplete layers cleared: 61.61 percent
kasm_agent: exited
Other Kasm containers: seven running
```

## Dangling-image cleanup

I verified seven untagged images with zero container references. They were the superseded Terminal and Claude Code images plus older Kasm service-image layers. `docker image prune --force` removed only those dangling images:

```text
Total reclaimed space: 7.112GB
```

I then trimmed the guest:

```text
/boot/efi: 98.2 MiB trimmed
/boot: 0 B trimmed
/: 23.1 GiB trimmed
```

Final cleanup state:

```text
Guest ext4: 193G total, 116G used, 77G available
ssd-lvm2: 51.46 percent data, 2.35 percent metadata
vm-122-disk-1: 58.69 percent allocated
```

The deleted images were untagged and unused. They are recoverable by pulling the matching registry tags again.
