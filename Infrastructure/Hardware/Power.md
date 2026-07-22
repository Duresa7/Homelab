# Power Equipment Inventory

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

I use two APC Back-UPS Pro BR1500MS2 units for the workstation, Galaxy nodes, UniFi core, & Verizon fiber handoff. Each unit is rated for 1500 VA / 900 W at 120 V and provides 10 NEMA 5-15R outlets.

## UPS Units

| Inventory ID | Manufacturer & model | Rating | Role | Connected loads |
| --- | --- | --- | --- | --- |
| UPS-01 | APC Back-UPS Pro BR1500MS2 | 1500 VA / 900 W | Compute & workstation | `red-server`; Jedi PC |
| UPS-02 | APC Back-UPS Pro BR1500MS2 | 1500 VA / 900 W | Network core & cluster nodes | Ahsoka Gateway, Ubiquiti Cloud Gateway Fiber (`UCG-Fiber`); Bane Switch POE, Ubiquiti Switch Pro Max 16 PoE (`USW-Pro-Max-16-PoE`); `grey-server`; `blue-server`; `red-server` as reported; Verizon ONT |

`UPS-01` & `UPS-02` are inventory identifiers. I haven't recorded matching physical labels or serial numbers.

## Verification Limits

The 2026-07-22 connected-load statement lists `red-server` on both units. I retained that conflict instead of substituting `purple-server`; the physical connection needs confirmation. The [2026-07-20 HA incident record](../../Security/Incidents/Galaxy-HA-Local-Storage-Stranding-2026-07-20/Galaxy-HA-Local-Storage-Stranding-Incident-2026-07-20.md) said I was moving blue, purple, red, & grey onto a UPS, but it didn't identify the final outlet split.

I haven't recorded the physical location, purchase date, serial number, battery installation date, exact outlet, battery-backed versus surge-only bank, measured wattage, or runtime estimate for either unit. This inventory doesn't claim those details.

## Product References

- [APC BR1500MS2 product page](https://www.apc.com/us/en/product/BR1500MS2/)
- [Ubiquiti Cloud Gateway Fiber specifications](https://techspecs.ui.com/unifi/cloud-gateways/ucg-fiber)
- [Ubiquiti Switch Pro Max 16 PoE specifications](https://techspecs.ui.com/unifi/switching/usw-pro-max-16-poe)
