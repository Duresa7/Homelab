# Handcrafted NTP Probe Was Inconclusive

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Date:** 2026-07-11  
**Step:** S05A

**Symptom:** A handcrafted UDP NTP packet produced an empty response, so it could not prove either successful NTP egress or a firewall failure.

**Investigation:** Web egress and the expected blocked external DNS test behaved correctly, which narrowed the uncertainty to the test method rather than the overall ruleset. I did not treat an empty UDP result alone as proof.

**Corrective action:** I installed `ntpsec-ntpdig` and its `python3-ntp` dependency from Debian. The purpose-built client queried `time.cloudflare.com` over IPv4 with a five-second timeout.

**Verification:** `ntpdig` exited `0` and returned a valid response from `<YOUR_NTP_SERVER_IP>`, stratum 3, with measured delay. UDP 123 egress is therefore verified.
