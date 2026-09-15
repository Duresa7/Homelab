# Dashboard Tooling

**Created:** 2026-08-27  
**Last updated:** 2026-09-15

Every dashboard under `Configuration/grafana/dashboards/` is generated. Do not hand-edit the JSON; change
the source here and re-run the builder, or the next build overwrites the edit.

```bash
cd Platforms/Prometheus
python3 Tools/build_dashboards.py
```

That writes 27 dashboards and `Tests/allow-empty.json`, and prints a panel count per dashboard. It needs no
network access and nothing but the standard library.

## Source files

| File | What it holds |
|---|---|
| `dashlib.py` | Panel constructors, the shared thresholds and colours, and the `Grid` that places panels |
| `inventory.py` | The 17 hosts, what each one is, and which collectors it actually runs |
| `uptime.py` | Service inventory, freshness checks, status bars, sampled uptime and coverage for the Uptime dashboard |
| `build_dashboards.py` | One function per dashboard, plus `node_dashboard()` for the per-host set |

## Making a change

**Change how everything looks.** Edit a constant in `dashlib.py`. `PCT_USED` is the amber-at-80,
red-at-95 threshold used by every capacity panel; `TS_CUSTOM` is the line weight and fill; `TINT` is the six
resource colours a single-series graph and a neutral stat tile draw from. One edit moves all 27 dashboards
together, which is the reason they are generated.

**Write no prose into a dashboard.** `Grid.section()` takes a title and an optional `collapsed` flag, with
no prose parameter, and there is no text panel constructor. `desc=` exists for a value that is computed in a
way the title cannot say, such as memory measured against `MemAvailable`, or for a number that would
otherwise mislead, such as a tile that sits amber on a steady-state baseline. It is not for telling the
reader what to conclude or where to look next. Sixty-nine panels carry one of fifteen texts as of
2026-09-14.

**Add a panel to every node dashboard.** Add it to `node_dashboard()` in `build_dashboards.py`. If it only
applies to some hosts, gate it on a flag: `if n["zfs"]:`. Do not gate it on the hostname.

**Add a host.** Add a dict to `NODES` in `inventory.py` and add the target to `prometheus.yml`. The node
dashboard, its entry in the Nodes dropdown, and its row in every fleet table all follow. Node boards carry the
`node` tag and not `homelab`, so they appear in that one dropdown rather than both.

**Add a whole dashboard.** Write a function returning `dashboard(uid, title, grid, tags=[...])`, add it to
the `topic` list in `main()`, and tag it `homelab` so it appears in the header dropdown.

## Capability flags

`inventory.py` records which collectors each host actually runs, including `zfs`, `nvme`, `smart`, `temp`, `psi`,
`conntrack`, `systemd`, `cpufreq`, `apt`, `docker`, `ups`. They were read off the live Prometheus on
2026-08-27.

They exist because a panel built for a collector a host does not run draws an empty rectangle, and an empty
rectangle reads as *fine* rather than *not applicable*, which is the worse of the two failures.

Two flags are deliberately narrower than the data. `temp` and `cpufreq` are true only on the five nodes, even
though the six LXC guests also report both: an LXC shares its node's kernel, so `/sys/class/hwmon` and the
cpufreq tree belong to the machine underneath it. Showing them on a container's dashboard would put another
machine's temperature under that container's name.

If a flag drifts from reality the panel it generated goes empty and `assert_dashboard_queries.py` fails, which
is how you find out.

## After building

```bash
python3 Tests/assert_dashboard_layout.py Configuration/grafana/dashboards
python3 Tests/assert_dashboard_queries.py Configuration/grafana/dashboards http://192.168.73.2:9090
```

The first is offline and checks the grid. The second runs all 1,466 queries against Prometheus and fails on
any that error or return nothing unexpectedly. Run both before deploying.

## Deploying

Dashboard JSON alone needs no restart; Grafana re-reads both directories every 30 seconds:

```bash
tar czf /tmp/d.tgz -C Configuration/grafana dashboards
scp /tmp/d.tgz dkadi@192.168.73.2:/tmp/
ssh dkadi@192.168.73.2 'cd ~/monitoring/grafana && tar xzf /tmp/d.tgz && \
  find dashboards -type f -exec chmod 0644 {} \;'
```

Changing `provisioning/dashboards/homelab.yaml` does need `docker restart grafana`, because provider
configuration is read at startup.

The Uptime calculation and collector checks are in `Tests/test_uptime.py`. I run its unit tests directly, then generate the PromQL cases with `--promql-fixtures` and pass that output to `promtool test rules`. The cases cover failed probes, partial tunnel connectivity, stale collectors, unknown time, and a brief outage inside a history bar.
