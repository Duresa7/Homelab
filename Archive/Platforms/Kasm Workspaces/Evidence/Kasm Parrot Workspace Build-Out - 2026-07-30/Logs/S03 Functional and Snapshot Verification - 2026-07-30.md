# S03 Functional and Snapshot Verification

**Created:** 2026-07-30  
**Last updated:** 2026-07-30

**Capture time:** 2026-07-30 01:03 through 01:05 EDT  
**Target:** `purple-server`, VM 122 `kasm-01`  
**Mechanism:** SSH Manager MCP, Proxmox CLI, QEMU guest agent, Docker CLI

## Disposable lane tests

I started four short-lived containers with the same image, network, and DNS values held by the Kasm rows. Each used `--rm`.

```text
PARROT_FULL
eth0: 172.18.0.10/16
DNS: passed

PARROT_NORMAL
eth0: 192.168.75.208/24
DNS: passed
Egress: ordinary WAN

PARROT_VPN
eth0: 192.168.74.208/24
DNS: passed
Egress: Proton

DEBIAN_MALWARE
eth0: 192.168.77.208/24
DIRECT_TCP_BLOCKED
DNS_BLOCKED
```

I did not retain the public WAN or Proton addresses. The final container list held the eight Kasm service containers and no verification container.

## Replacement snapshot

Before the snapshot:

```text
VM 122: running
Snapshots: zero
ssd-lvm2: 67.45 percent data, 2.81 percent metadata
```

I created:

```text
baseline-parrot-2026-07-30
Created: 2026-07-30 01:05:48 EDT
Description: Verified Kasm baseline after Parrot Full, VPN, Normal and Debian Malware; automatic workspace image pulls disabled
```

Proxmox froze the guest filesystem, created the disk and EFI snapshot volumes, and thawed the filesystem. The pool remained at 67.45 percent.

Final verification:

```text
Snapshot count: one
Kasm service containers: eight running
Docker health checks: seven healthy
kasm_proxy: running, no health check
Local health response: {"ok": true}
Local health HTTP status: 200
Automatic image-pull log entries after restart: zero
```
