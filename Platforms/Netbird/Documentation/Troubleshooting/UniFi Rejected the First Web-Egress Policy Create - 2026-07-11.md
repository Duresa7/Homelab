# UniFi Rejected the First Web-Egress Policy Create

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Date:** 2026-07-11  
**Step:** S05A  
**Owner:** UniFi

**Symptom and exact error:** The first create request for the web-egress policy failed:

```text
api.err.FirewallPolicyCreateRespondTrafficPolicyNotAllowed
Firewall policy create respond traffic not allowed
```

**Failed attempt:** My initial payload used the tool's default `create_allow_respond: true` for an `<YOUR_ORG_NAME>`-Access-to-External policy. UniFi did not create the rule.

**Hypothesis and test:** Respond-traffic generation is not allowed for this policy direction. I previewed the same payload again with `create_allow_respond: false`.

**Corrective action:** I applied the corrected payload, then created the web, NTP, and catch-all block policies in this order:

1. `Allow docker-network Web Egress`: TCP 80 and 443 from `192.168.85.2`.
2. `Allow docker-network NTP Egress`: UDP 123 from `192.168.85.2`.
3. `Block <YOUR_ORG_NAME>-Access Other External Egress`: remaining IPv4 traffic.

All three policies have logging enabled.

**Verification:** UniFi returned the three policies at indexes 10000, 10001, and 10002. HTTP returned `200`, the Docker Registry HTTPS endpoint returned its expected unauthenticated `401`, and external TCP DNS to `<YOUR_EXTERNAL_DNS_IP>:53` timed out as intended. The final ordered rules show the two Allow policies above the catch-all Block:

![UniFi policy table showing Allow docker-network UDP 123, Allow docker-network TCP 80,443, and Block AlphaSec-Access All from the `<YOUR_ORG_NAME>`-Access zone to External](../../Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S05A-UniFi-Access-A-Egress-Policies-After-2026-07-11.jpg)
