# Step 5 docker-network Firewall and Tunnel

**Created:** 2026-07-28  
**Last updated:** 2026-08-04

**Capture date:** 2026-07-28  
**Execution mechanism:** UniFi Network MCP, SSH Manager MCP, & Portainer API  
**Targets:** UniFi gateway, `docker-network`, & `docker-main`

## Policy Preview and Creation

I previewed `unifi_create_firewall_policy` with `confirm=false`, compared the returned body to the approved scope, then sent the same `policy_data` with `confirm=true`.

```text
name=Allow docker-network to Portainer Edge
action=ALLOW
enabled=true
protocol=tcp
ip_version=IPV4
logging=true
schedule=ALWAYS
source_zone=Access
source_ip=192.168.85.2
source_port=ANY
destination_zone=Internal
destination_ip=192.168.40.35
destination_port_group=Portainer Edge Agents
destination_ports=8000,9443
```

```text
success=true
policy_id=6a68eb3f052792cd2140c9ad
index=10003
```

The follow-up policy-details request returned the same name, action, source IP, destination IP, TCP protocol, IPv4 scope, port-group ID, logging state, & enabled state.

## Source-Host Verification

```sh
for port in 8000 9443; do
  if timeout 3 bash -c "</dev/tcp/192.168.40.35/$port"; then
    echo "port${port}=reachable"
  else
    echo "port${port}=blocked"
  fi
done
```

```text
port8000=reachable
port9443=reachable
```

## Portainer Tunnel Verification

I authenticated to Portainer through `<REDACTED_SECRET_REFERENCE>`. The password and JWT remained inside the child process and were not printed.

```text
id=9
name=docker-network
status=1
last_checkin=2026-07-28 17:54:21Z
tunnel=reachable
containers=5
names=cadvisor,netbird-dashboard,netbird-server,nginx-proxy-manager,portainer_edge_agent
```

The agent inspection returned `running`, restart policy `always`, image `portainer/agent:2.39.1`, compose file mode 0644, & `.env` mode 0600.
