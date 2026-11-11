# Executor 2 Container OOM Kills

**Created:** 2026-11-02  
**Last updated:** 2026-11-02  
**Status:** Cause found, no fix applied yet.

## Symptom

On 2026-11-02, Splunk raised three "Malware or high severity" alerts for `blue-server` from Wazuh rule 5108 (level 12, "System running out of memory. Availability of the system is in risk."), at 14:15:37, 15:44:07 and 17:41:16 EST. This is not malware. Rule 5108 matches the kernel's OOM-killer line, and the Splunk alert files every level-12 rule under that heading.

## Error

`journalctl -k` on `blue-server`, once per alert:

```text
Nov 02 14:15:36 blue-server kernel: Memory cgroup out of memory: Killed process 1879196 (workerd) total-vm:66934056kB, anon-rss:1070068kB ...
Nov 02 15:44:06 blue-server kernel: Memory cgroup out of memory: Killed process 2505912 (workerd) total-vm:92104868kB, anon-rss:1419152kB ...
Nov 02 17:41:15 blue-server kernel: Memory cgroup out of memory: Killed process 2638615 (workerd) total-vm:68245544kB, anon-rss:1259000kB ...
```

All three show `constraint=CONSTRAINT_MEMCG` with `oom_memcg=/lxc/108/ns/system.slice/docker-91e4dfe239d1....scope`. That scope belongs to the `executor-v2` container on `docker-blue` (CT 108). The node did not run out of memory: `blue-server` had 2,470 MB available at 18:12.

## What I checked

- **Which container.** `docker ps` on CT 108 put `91e4dfe239d1` on `executor-v2`, image `executor-selfhost:2.0.0-beta.34`. Its `RestartCount` is 3, and its last start, 22:41:16Z, is the third kill. Each kill takes the whole container down, Docker restarts it, and any MCP call in flight is dropped: the container log shows `httputil: ReverseProxy read error during body copy: unexpected EOF` and then `Executor: signal: killed`.
- **Limits.** The [Compose file](../../Configuration/docker-compose.yml) sets `mem_limit: 1536m`. Docker set `memory.swap.max` to 1.5 GiB, but CT 108's own swap (1,024 MiB) held 1,026,961,408 bytes, so it was full. The container had 536 MB in swap and could not swap any more. CT 108 has 2,048 MiB of RAM for nine containers.
- **Where the memory goes.** At 23:12Z, about 30 minutes after a restart, the container's `memory.peak` was 1,527,214,080 bytes against a limit of 1,610,612,736. The app-runtime `workerd` (`workerd.capnp`) held 629,824 kB of anonymous memory. The separate telemetry `workerd` (`motel.capnp`) held 106,188 kB. `memory.stat` showed 764 MB anonymous and 341 MB file. Every kill hit the app-runtime `workerd`.
- **History.** cAdvisor's `container_memory_working_set_bytes{name="executor-v2"}` in Prometheus, at a 15-minute step, rose from about 450 MiB on 2026-10-31 to about 900 MiB by the evening of 2026-11-01. From 2026-11-02 11:00Z it swung by 300 to 500 MiB within the hour. The 15-minute step misses the peaks that triggered each kill.
- **Load source.** The built-in telemetry store (`motel-data/motel/*.sqlite`, 1.08 GB plus a 174 MB WAL) held 194,618 spans covering 22:23Z to 23:15Z, about 60 spans a second. Of the spans carrying an app ID, 101,954 belong to `app_91eceaf1-d1f2-410b-9803-996db7e63798`, which `appManagement.list` names as `book-digest`. The next app, `ssh`, has 425. Nearly all of them are `query` operations. The HTTP spans come from Chrome 156 on Windows hitting `/_executor/api/subscribe` and `/_executor/api/query`, which means the `book-digest` app page was open in a browser. App pages went live that morning ([App Page Domain - 2026-11-02](../Change%20Records/App%20Page%20Domain%20-%202026-11-02.md)), at 07:17 EST, and the first kill came seven hours later.
- **Rising rate.** Counts of `app.dispatch` spans per five minutes after the 22:41Z restart: 355, 496, 897, 1,448, 1,794, 2,145, 2,254. The `subscribe` request count held at 32 to 50 per five minutes over the same windows, so each subscription is producing more queries the longer the page stays open.
- **Side effects.** Each window before a kill logged 500 to 1,600 `workerd/io/io-context.c++:1557: failed: script terminated for unknown reasons` errors. motel turned exports away with `queueFull` and HTTP 429 (`refusedBytes` reached 46,479,932 by 22:40Z).

## Root cause

The `executor-v2` container sits about 600 to 900 MiB below its 1.5 GiB limit even when idle. Its swap allowance does nothing, because CT 108's swap is already full. The `book-digest` app page, left open in a browser, drives a query rate that keeps climbing for as long as the page is open. Every query also writes about eight telemetry spans into motel. The app runtime's heap grows with that load until the cgroup limit is reached, the kernel kills `workerd`, and the container restarts. The cycle ran 89 and then 117 minutes.

The climbing per-subscription query rate is an inference from span counts. I have not yet read `book-digest`'s page code to confirm a re-subscribe or polling loop.

## Fix

Not applied. Options, cheapest first:

1. Close the `book-digest` tab and confirm the `app.dispatch` rate drops to the background level and the kills stop.
2. Fix `book-digest`'s page so a subscription does not multiply its queries.
3. Give the container room: raise CT 108's RAM and swap and `mem_limit` together. `blue-server` has 5,811 MB of RAM and was using 2,476 MB of swap at 18:12, so this is limited.

## Verification

Not done yet. After the fix: no new `Memory cgroup out of memory` lines on `blue-server`, `executor-v2` `RestartCount` stays at 3, and `memory.peak` stays below `memory.max` through a working day with the app page in use.
