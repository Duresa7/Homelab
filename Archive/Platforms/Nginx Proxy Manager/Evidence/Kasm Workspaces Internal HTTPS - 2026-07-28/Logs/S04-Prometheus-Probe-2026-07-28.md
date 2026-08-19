# S04 Prometheus Probe

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Captured:** 2026-07-28 23:47-23:49 EDT  
**Target:** Prometheus 3.13.1 on `monitor-01`  
**Mechanism:** SSH Manager MCP

I added `https://kasm.alphasecunited.com/` after the TS3 Manager target, then ran:

```sh
docker exec prometheus promtool check config /etc/prometheus/prometheus.yml
docker kill --signal=SIGHUP prometheus
```

`promtool` returned `SUCCESS`, Prometheus logged `Completed loading of configuration file`, & the status API contained the Kasm target. The host-side `sed -i` replaced the bind-mounted file's inode, so the running container retained an older inode containing 19 placeholder targets. `up=1` proved the exporter answered, but `probe_success=0` proved each of those 19 URL probes failed.

I copied the complete validated host file through the existing writable mount:

```sh
docker exec -i -u 0 prometheus sh -c 'cat > /etc/prometheus/prometheus.yml' < /home/dkadi/monitoring/prometheus.yml
```

The host and container SHA-256 digests matched at `6c552c06b9109f146b5d02b6bd68db35d8fcc19b8ed815f8356d907fe97a5924`. I reran `promtool` and sent `SIGHUP` again.

The target API then listed 20 active blackbox targets. Its first Kasm scrape returned:

```text
up{job="blackbox",instance="https://kasm.alphasecunited.com/"} 1
```

The final queries returned 48 of 48 scrape targets `up`. I then iterated the 20 active blackbox target labels and queried `probe_success` for each exact instance; all 20 returned `1`, with no failed active target.
