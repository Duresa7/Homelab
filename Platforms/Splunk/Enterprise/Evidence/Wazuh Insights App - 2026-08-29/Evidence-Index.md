# Wazuh Insights App Evidence

**Created:** 2026-08-30  
**Last updated:** 2026-08-31

Supports [Wazuh Insights App - 2026-08-29](../../Documentation/Change%20Records/Wazuh%20Insights%20App%20-%202026-08-29.md).

Step numbers run S01 to S21 across six evidence folders. This folder holds S09, S10 and S21, which is the last step because the malware test is what proves the whole chain. All captures are headless, so no pointer appears in any of them.

| Step | Capture | What it shows |
|---:|---|---|
| 9 | [Dashboard glance tiles](Screenshots/S09-Wazuh-Insights-Dashboard-Glance-Tiles-2026-08-30.png) | The finished dashboard above the fold: seven tiles, the alert timeline by machine, the VirusTotal lookup budget, and three tables. Malware found reads 4 and watched files changed reads 227, against 2,941 and 2,958 before the corrections in the record. |
| 10 | [Dashboard full page](Screenshots/S10-Wazuh-Insights-Dashboard-Full-Page-2026-08-30.png) | The whole page including "Every alert, newest first". The stream at the top of this capture is PAM and sshd session events on `docker-network` from my own login, which is what a normal minute on this fleet looks like once the noise is gone. The rule breakdown that found the `red-server` service failures is [S07](../../../../Wazuh/Evidence/Alert%20Forwarding%20to%20Splunk%20-%202026-08-29/Screenshots/S07-Splunk-Wazuh-Rule-Breakdown-2026-08-29.png). |
| 21 | [EICAR detected twice independently](Screenshots/S21-Splunk-EICAR-Detected-Twice-Independently-2026-08-30.png) | The proof the chain works. Two alerts one second apart on the same file: rule 87105 with VirusTotal reporting 64 of 67 engines, and rule 100200 from the local hash list, both level 12. One is a network lookup and one is not, so neither depends on the other. |
