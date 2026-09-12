# Azure Arc

**Created:** 2026-09-12  
**Last updated:** 2026-09-12

I connected `HQ-MGT01` to Azure Arc through the Windows Server setup wizard on 2026-09-12. Arc represents that server in Azure while it continues running in Proxmox. Enrollment of other domain machines has not been configured.

| Item | Verified value |
|---|---|
| Machine | `HQ-MGT01`, `192.168.65.12` |
| Agent status | Connected |
| Agent version | `1.67.03504.3207` |
| Resource group | `rg-homelab-arc` |
| Region / cloud | `eastus` / `AzureCloud` |
| Other controllers | `HQ-DC01` and `HQ-DC02` have no `himds` service as of the September 12 check |

I verified these values through SSH Manager using `azcmagent show -j`, selecting only the status and resource metadata fields. The [readback](../../Security/Incidents/UniFi/Evidence/Action1%20RPC%20Alert%20-%202026-09-12/Readback.json) was captured while investigating a separate Action1 RPC alert. No successful Arc Run Command execution was verified during that investigation.

I intend to use the free core inventory and management features. Azure subscription billing, Defender plans, and inherited deployment policies have not been inspected in this record; Connected status is not proof of zero charges. [Microsoft's pricing](https://azure.microsoft.com/en-us/pricing/details/azure-arc/core-control-plane/) distinguishes the free core service from paid add-ons.

Arc Run Command currently requires Azure CLI, PowerShell, or the REST API; the portal link opens documentation. Microsoft's [Run Command reference](https://learn.microsoft.com/en-us/azure/azure-arc/servers/run-command) documents that limitation. [Group Policy deployment](https://learn.microsoft.com/en-us/azure/azure-arc/servers/onboard-group-policy-powershell) is an available batch-enrollment method, but I have not deployed it here.
