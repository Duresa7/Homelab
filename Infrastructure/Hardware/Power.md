# Power Equipment Inventory

**Created:** 2026-07-22  
**Last updated:** 2026-09-25

I use two APC Back-UPS units for the workstation, Galaxy nodes, UniFi core, and Verizon fiber handoff. Each unit is rated for 1500 VA / 900 W at 120 V and provides 10 NEMA 5-15R outlets.

## UPS Units

| Inventory ID | Manufacturer and model | Rating | Role | Connected loads |
| --- | --- | --- | --- | --- |
| UPS-01 | APC Back-UPS Pro BR1500MS2 | 1500 VA / 900 W | Workstation | Jedi PC |
| UPS-02 | APC Back-UPS RS 1500MS2 | 1500 VA / 900 W | Network core and cluster nodes | Ahsoka Gateway, Ubiquiti Cloud Gateway Fiber (`UCG-Fiber`); Bane Switch POE, Ubiquiti Switch Pro Max 16 PoE (`USW-Pro-Max-16-PoE`); `grey-server`; `blue-server`; `red-server`; Verizon ONT |

`UPS-01` and `UPS-02` are inventory identifiers. I haven't recorded matching physical labels.

On 2026-08-28 I moved `red-server` from `UPS-01` to `UPS-02`, which is the unit the other Galaxy nodes already sit on. That resolves the conflict this file carried from 2026-07-22, when the connected-load statement listed `red-server` on both units and I retained it rather than guess. `red-server` is on `UPS-02`, confirmed by me on 2026-08-31. `UPS-01` now carries the workstation alone.

The model in the `UPS-02` row is what the device reports over NUT: `ups.model` returns `Back-UPS RS 1500MS2`, not the `Back-UPS Pro BR1500MS2` this file claimed for both units through 2026-08-31. I have not read `UPS-01`'s model off the device, because it has no data path, so its row still carries the value I recorded by eye on 2026-07-22.

## Verification Limits

I haven't recorded the physical location, purchase date, battery installation date, exact outlet, battery-backed versus surge-only bank, or measured wattage for either unit. This inventory doesn't claim those details.

## Monitoring

| UPS | USB data owner | NUT endpoint | Latest verified reading |
| --- | --- | --- | --- |
| UPS-01 | None since 2026-08-28 | None | 2026-07-22: Online; 100% charge; 58% load; 675-second estimated runtime |
| UPS-02 | `grey-server` | `ups02@192.168.70.10:3493` | 2026-08-31: Online (`OL`); 100% charge; 19% load; 2,424-second estimated runtime |

**`UPS-01` is unmonitored.** Its USB data cable came off `red-server` during the 2026-08-28 move and is plugged into no host, so nothing reads its charge, load, or runtime and nothing will report it going to battery. The unit still powers the workstation. Its 2026-07-22 reading is kept above as the last one I have, not as current state. On 2026-09-07 I decided it stays unmonitored: the unit powers only the workstation, and reconnecting it is not tracked anywhere. Should it ever be reconnected, the [restart loop record](../../Platforms/PeaNUT/Documentation/Troubleshooting/ups01%20NUT%20Driver%20Restart%20Loop%20After%20the%20UPS%20Swap%20-%202026-08-31.md) lists the NUT, Prometheus and PeaNUT entries to re-enable.

`UPS-02`'s load rose from 17 to 19 percent and its estimated runtime fell from 2,895 to 2,424 seconds between 2026-07-22 and 2026-08-31, which is `red-server` arriving on the unit.

PeaNUT 6.0.0 displays the live feed at `http://192.168.73.2:8090`, and Prometheus scrapes it through `prometheus-nut-exporter` on the `nut` job. Both carried `UPS-01` until 2026-08-31, when I disabled that entry in each. The [deployment record](../../Platforms/PeaNUT/Documentation/Change%20Records/UPS%20Dashboard%20Deployment%20-%202026-07-22.md) records the original configuration and verification, the [relocation record](../../Platforms/PeaNUT/Documentation/Change%20Records/Relocation%20to%20monitor-01%20-%202026-07-26.md) covers the move to `monitor-01`, and [ups01 NUT Driver Restart Loop After the UPS Swap](../../Platforms/PeaNUT/Documentation/Troubleshooting/ups01%20NUT%20Driver%20Restart%20Loop%20After%20the%20UPS%20Swap%20-%202026-08-31.md) covers the disconnection and what it broke. These readings are point-in-time values, not rated or guaranteed runtime.

## Product References

- [APC BR1500MS2 product page](https://www.apc.com/us/en/product/BR1500MS2/)
- [Ubiquiti Cloud Gateway Fiber specifications](https://techspecs.ui.com/unifi/cloud-gateways/ucg-fiber)
- [Ubiquiti Switch Pro Max 16 PoE specifications](https://techspecs.ui.com/unifi/switching/usw-pro-max-16-poe)
