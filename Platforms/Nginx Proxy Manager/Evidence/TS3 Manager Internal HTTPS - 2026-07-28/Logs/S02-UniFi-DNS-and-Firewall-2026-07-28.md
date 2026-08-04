# Step 2 UniFi DNS and Firewall

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Capture time:** 2026-07-28 09:55 EDT  
**Target:** UniFi Network controller, site `default`  
**Mechanism:** UniFi Network MCP preview, confirm, & readback

## Preview

Firewall preview:

```text
name=Allow NPM to alpha-prod-01 TS3 Manager
action=ALLOW
protocol=tcp
source zone=AlphaSec-Access
source IP=192.168.85.2
destination zone=AlphaSec-Servers
destination IP=192.168.80.118
destination port=9000
logging=true
schedule=ALWAYS
```

DNS preview:

```text
key=ts3-manager.alphasecunited.com
value=192.168.85.2
record_type=A
enabled=true
ttl=300
```

Both previews returned `requires_confirmation: true`. The approved calls were then repeated with `confirm: true`.

## Applied result

```text
firewall policy ID=6a68b26e052792cd2140bfd9
DNS record ID=6a68b26f052792cd2140bfdc
```

The final policy search returned one enabled match with exact source `192.168.85.2`, exact destination `192.168.80.118`, TCP 9000, & logging enabled. The final DNS list returned the enabled TTL-300 record pointing at `192.168.85.2`.

Follow-up backend check from `docker-network`:

```text
backend_tcp=open
backend_http=200
```
