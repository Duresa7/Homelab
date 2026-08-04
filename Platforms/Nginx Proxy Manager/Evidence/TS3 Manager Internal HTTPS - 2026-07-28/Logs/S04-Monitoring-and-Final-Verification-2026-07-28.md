# Step 4 Monitoring and Final Verification

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Capture time:** 2026-07-28 09:55 EDT  
**Targets:** `monitor-01`, NPM, UniFi DNS, Cloudflare public DNS  
**Mechanism:** SSH Manager, local PowerShell, UniFi Network MCP

## Prometheus

The candidate added one line:

```text
https://ts3-manager.alphasecunited.com/
```

`promtool check config` returned:

```text
SUCCESS: /etc/prometheus/prometheus.yml is valid prometheus config file syntax
```

I wrote the candidate into the existing live inode, sent container `prometheus` signal `HUP`, & confirmed:

```text
Prometheus Server is Ready.
```

The target assertion finished with exit code 0:

```text
blackbox|https://ts3-manager.alphasecunited.com/|up|none
ASSERTION: 46 expected targets present and all UP (27 scraped exporters, 19 blackbox services)
ASSERTION: stale addresses absent
```

The intended pre-change copy failed because the backup directory did not exist. I later removed the reconstructed rollback file, deployment candidate, temporary validator copy, & empty backup directory at the owner's request. No backup or temporary file from this deployment remains on `monitor-01`.

## Client paths

UniFi DNS:

```text
ts3-manager.alphasecunited.com A 192.168.85.2
```

Cloudflare public DNS:

```text
NXDOMAIN or no A answer
```

All 20 enabled NPM hosts returned an expected application response after the controlled restart. TS3 Manager returned HTTP `200`; the validation loop reported:

```text
host_count=20
failed_count=0
```

UniFi reported:

```text
port_forward_count=0
```
