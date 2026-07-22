# APC Back-UPS Pro Installation and Load Assignment

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Date:** 2026-07-22  
**Status:** Documented with one load-assignment conflict pending confirmation

## Scope

I added two APC Back-UPS Pro BR1500MS2 units, each rated for 1500 VA / 900 W, & recorded the equipment connected to each unit.

## Starting State

The hardware inventory had no UPS record. The [2026-07-20 HA incident record](../../../../Security/Incidents/Galaxy-HA-Local-Storage-Stranding-2026-07-20/Galaxy-HA-Local-Storage-Stranding-Incident-2026-07-20.md) mentioned a maintenance window to move `blue-server`, `purple-server`, `red-server`, & `grey-server` onto a UPS, but it didn't identify the UPS model, quantity, or final load split.

## Actions

I placed two BR1500MS2 units into service. I assigned `UPS-01` to `red-server` & Jedi PC. I assigned `UPS-02` to the Ahsoka Gateway, Bane Switch POE, Verizon ONT, `grey-server`, `blue-server`, & a node reported as `red-server`.

No command, controller export, UPS telemetry, photograph, or outlet map was retained for this work.

## Decisions

I used `UPS-01` & `UPS-02` as repository inventory identifiers because the two units have the same model and their serial numbers aren't recorded. I normalized the network product names to Ubiquiti Cloud Gateway Fiber (`UCG-Fiber`) & Switch Pro Max 16 PoE (`USW-Pro-Max-16-PoE`) using the manufacturer specifications.

I didn't replace the second `red-server` entry with `purple-server`. The supplied connection list names red twice, while the older maintenance record names all four Galaxy nodes. A physical check is required before the inventory can state which node is on the final UPS-02 outlet.

## Resulting Configuration

| UPS | Connected equipment |
| --- | --- |
| UPS-01 | `red-server`; Jedi PC |
| UPS-02 | Ahsoka Gateway (`UCG-Fiber`); Bane Switch POE (`USW-Pro-Max-16-PoE`); Verizon ONT; `grey-server`; `blue-server`; `red-server` as reported |

The current inventory is [Power.md](../../Power.md). The Galaxy node & Jedi PC specifications link their reported power sources.

## Verification

I checked the two UPS model ratings against APC's BR1500MS2 product page. I checked both Ubiquiti model names against the Ubiquiti technical specifications. The connected-load mapping comes from the 2026-07-22 owner statement; I didn't verify it through UPS telemetry or a physical outlet inspection.

## Rollback Points

This documentation pass changed no electrical connection or device configuration, so it has no runtime rollback action. A later physical load move needs a controlled maintenance window because the Verizon ONT, gateway, switch, & three listed cluster nodes share `UPS-02`; this record doesn't preserve a prior outlet layout.
