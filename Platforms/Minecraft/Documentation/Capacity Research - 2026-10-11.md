# Capacity check

**Created:** 2026-10-11  
**Last updated:** 2026-10-11

I checked resource headroom at 5:48 PM Eastern through the SSH Manager MCP. I made no runtime changes and retained no full terminal transcripts for this check.

On `purple-server`, `free -m` reported 15830 MiB total memory, 6245 MiB available and no swap use. `lscpu` confirmed an Intel Core i5-8500T with six cores and six threads. VM 401 has six vCPUs, CPU type `host`, and 6144 MiB for both memory and balloon minimum. VM 121 `edge-01` is running with 4096 MiB configured; VM 116 `app-01` remains stopped with 8192 MiB configured.

Inside `alpha-prod-01`, `free -m` reported 5863 MiB usable memory, 3824 MiB available and no swap use. A single Docker sample showed Minecraft at 1.083 GiB and 0.22% CPU. The live container has a 3 GiB memory limit and matching combined memory/swap limit, no CPU quota and no CPU affinity restriction. Live server properties set both view distance and simulation distance to 10 chunks. The Compose reference retains a 2 GiB maximum Java heap. These lightly loaded samples do not establish capacity during gameplay.

My proposed first upgrade is an 8 GiB VM, with its balloon minimum also at 8 GiB, a 4 GiB maximum Minecraft heap, and a 5 GiB container memory limit with matching combined memory/swap limit. I would keep six vCPUs. This allocation fits the observed headroom while `app-01` stays stopped; I need to recheck capacity before restarting that VM. The image's [JVM documentation](https://docker-minecraft-server.readthedocs.io/en/latest/configuration/jvm-options/) distinguishes heap memory from container overhead.

For lower simulation load, I would trial view distance 8 and simulation distance 6, then compare gameplay before retaining them. The tradeoff is a shorter view and a smaller active area around players, including farms. The [property reference](https://docs.papermc.io/paper/reference/server-properties/) explains both distances. Adding virtual CPUs beyond the host's six hardware threads supplies no additional physical processing capacity; the [Paper performance notes](https://docs.papermc.io/paper/basic-troubleshooting/#low-cpu-usage) also explain the main tick thread's limits.

The next useful measurement is tick duration, memory pressure and network latency during actual play. I have not established a comfortable player count or a memory bottleneck. The earlier estimate of 5–10 comfortable players was not a benchmark. Applying the proposal would require the Proxmox memory change and an updated Dockhand stack; a VM restart would also interrupt TeamSpeak. The world reset is unrelated to this resource change and need not be repeated.
