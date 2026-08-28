# Dashboard Tooling

**Created:** 2026-08-27  
**Last updated:** 2026-08-27

Every dashboard under `Configuration/grafana/dashboards/` is generated. Do not hand-edit the JSON — change
the source here and re-run the builder, or the next build overwrites the edit.

```bash
cd Platforms/Prometheus
python3 Tools/build_dashboards.py
```

That writes 27 dashboards and `Tests/allow-empty.json`, and prints a panel count per dashboard. It needs no
network access and nothing but the standard library.

## The three files

| File | What it holds |
|---|---|
| `dashlib.py` | Panel constructors, the shared thresholds and colours, and the `Grid` that places panels |
| `inventory.py` | The 18 hosts, what each one is, and which collectors it actually runs |
| `build_dashboards.py` | One function per dashboard, plus `node_dashboard()` for the per-host set |

## Making a change

**Change how everything looks.** Edit a constant in `dashlib.py`. `PCT_USED` is the amber-at-80,
red-at-95 threshold used by every capacity panel; `TS_CUSTOM` is the line weight and fill; `LEGEND_TABLE` is
the legend shape. One edit moves all 27 dashboards together, which is the reason they are generated.

**Add a panel to every node dashboard.** Add it to `node_dashboard()` in `build_dashboards.py`. If it only
applies to some hosts, gate it on a flag: `if n["zfs"]:`. Do not gate it on the hostname.

**Add a host.** Add a dict to `NODES` in `inventory.py` and add the target to `prometheus.yml`. The node
dashboard, its entry in both header dropdowns, and its row in every fleet table all follow.

**Add a whole dashboard.** Write a function returning `dashboard(uid, title, grid, tags=[...])`, add it to
the `topic` list in `main()`, and tag it `homelab` so it appears in the header dropdown.

## Capability flags

`inventory.py` records which collectors each host actually runs — `zfs`, `nvme`, `smart`, `temp`, `psi`,
`conntrack`, `systemd`, `cpufreq`, `apt`, `docker`, `ups`. They were read off the live Prometheus on
2026-08-27.

They exist because a panel built for a collector a host does not run draws an empty rectangle, and an empty
rectangle reads as *fine* rather than *not applicable* — which is the worse of the two failures.

Two flags are deliberately narrower than the data. `temp` and `cpufreq` are true only on the five nodes, even
though the seven LXC guests also report both: an LXC shares its node's kernel, so `/sys/class/hwmon` and the
cpufreq tree belong to the machine underneath it. Showing them on a container's dashboard would put another
machine's temperature under that container's name.

If a flag drifts from reality the panel it generated goes empty and `assert_dashboard_queries.py` fails, which
is how you find out.

## After building

```bash
python3 Tests/assert_dashboard_layout.py Configuration/grafana/dashboards
python3 Tests/assert_dashboard_queries.py Configuration/grafana/dashboards http://192.168.73.2:9090
```

The first is offline and checks the grid. The second runs all 1,394 queries against Prometheus and fails on
any that error or return nothing unexpectedly. Run both before deploying.

## Deploying

Dashboard JSON alone needs no restart — Grafana re-reads both directories every 30 seconds:

```bash
tar czf /tmp/d.tgz -C Configuration/grafana dashboards
scp /tmp/d.tgz dkadi@192.168.73.2:/tmp/
ssh dkadi@192.168.73.2 'cd ~/monitoring/grafana && tar xzf /tmp/d.tgz && \
  find dashboards -type f -exec chmod 0644 {} \;'
```

Changing `provisioning/dashboards/homelab.yaml` does need `docker restart grafana`, because provider
configuration is read at startup.
