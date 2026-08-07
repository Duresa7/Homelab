# Single-File Bind Mount Retained the Old Inode

**Created:** 2026-07-22  
**Last updated:** 2026-08-06

> Cause removed on 2026-08-06. I replaced the single-file bind mount with a directory mount, so the failure described below can no longer happen. The third recurrence is what finally justified the change; see the bottom of this record.

The live Prometheus configuration is a single host file bind-mounted into the container. My candidate configuration passed `promtool` and replaced the host path, and Prometheus accepted a HUP signal, but the target API still returned the old jobs. Replacing the path had created a new inode while the existing container mount stayed attached to the former inode.

I ran a controlled `docker restart prometheus`, which rebound `/etc/prometheus/prometheus.yml` to the validated host file. The service returned ready, `promtool` passed inside the restarted container, and the automated target assertion found exactly the seven expected jobs, all `UP`. The temporary container validation file needed root removal because the container normally runs unprivileged, so I removed it with `docker exec --user 0`.

## Recurrence on 2026-07-28

The same inode failure recurred when I added the Kasm blackbox target with host-side `sed -i`. The host path held all 20 real internal names, while the running container retained an older inode with 19 placeholder names. Prometheus reported `up=1` because blackbox_exporter answered its scrape request, but `probe_success` returned `0` for those 19 placeholder targets. Only the new Kasm target returned `probe_success=1`.

I copied the validated host file through the existing writable mount without replacing the mounted inode:

```sh
docker exec -i -u 0 prometheus sh -c 'cat > /etc/prometheus/prometheus.yml' < /home/dkadi/monitoring/prometheus.yml
```

The host and container SHA-256 digests then matched at `6c552c06b9109f146b5d02b6bd68db35d8fcc19b8ed815f8356d907fe97a5924`. `promtool` passed, Prometheus reloaded on `SIGHUP`, & a check against the 20 active target labels found 20 `probe_success=1` results and no failure. I did not restart the container.

For later single-file changes, I write through the existing inode or recreate the container. I don't use `sed -i`, `mv`, or another path-replacement operation on a file bind-mounted into a running container.

## Third recurrence on 2026-08-06, and the fix

It happened again while I removed the Syncthing blackbox probe. I edited the host file with `sed -i`, and the reload reported success twice while Prometheus kept serving the old target list. `POST /-/reload` returned HTTP 403 with `Lifecycle API is not enabled`, and `SIGHUP` changed nothing. Only a container recreate applied the edit.

Three occurrences of one failure is a design problem, not an operator problem. The rule at the end of the section above had been written down since 2026-07-28 and did not prevent the third one, because the trap is silent and the workaround depends on remembering it at the moment of the edit.

So I removed the cause. `prometheus.yml` moved to `/home/dkadi/monitoring/prometheus-config/`, and the Compose volume became a directory mount:

```yaml
- ./prometheus-config:/etc/prometheus:ro
```

A directory mount resolves names at access time rather than pinning one inode at container start, so a replaced file is visible immediately. I proved it with the operation that used to fail: `sed -i` changed the global `scrape_interval` from 15s to 20s, `docker kill -s HUP prometheus` applied it with no restart, `/api/v1/status/config` reported `scrape_interval: 20s`, and I reverted the same way. The target assertion returned 48 of 48 targets up across 29 scraped exporters and 19 blackbox services.

I did not enable the lifecycle API to fix the 403. `/-/reload` and `/-/quit` would then be reachable without authentication by anything that can load the Prometheus web interface, which includes the internal NPM route that carries no added authentication. `SIGHUP` costs one command and adds no exposed endpoint.
