# AeroStruct S.A. — Meeting Notes & Initial Brief

*Pre-sales meeting — March 2026*
*Attendees: Jean-Marc Duval (VP Operations), Nadia Bensaïd (Head of Production Planning), Thomas Keller (IT Systems Lead)*

## Company context

AeroStruct is a Tier-1 aerostructures manufacturer (fuselage sections, wing components) for major aircraft OEMs. 3 production sites in France and Germany, ~2,400 employees. SAP is their ERP backbone for production planning, work order management, and shop floor execution. They migrated to the latest SAP version in 2024.

## What they told us

**Jean-Marc (VP Ops):** *"Our biggest issue is visibility. When something goes wrong on the line — a machine breakdown, a quality hold, a delayed supplier delivery — we can't see what it does to the rest of the schedule. We have 200-300 active work orders at any time, each with 10-40 operations, with complex dependencies. Today, the planners recalculate the impact manually. It takes 3-4 days to produce a revised schedule after a major incident. By then, we've already made bad decisions."*

**Nadia (Planning):** *"SAP gives us scheduling within a single work order, but not across work orders. When an operation slips on one work order, I need to know: which downstream operations are affected? Across which other work orders? Which aircraft delivery is at risk? SAP doesn't connect these dots — we do it in Excel, cross-referencing with the master schedule."*

*"We also have resource contention. Our NDI station and the autoclave are shared across programs. When one work order takes longer on the autoclave, it cascades to others. But the cascade is invisible until it's too late."*

**Thomas (IT):** *"SAP does forward/backward scheduling within a single work order. For cross-work-order dependencies, the previous module had network scheduling, but it was decommissioned during our migration. The replacement doesn't cover operation-level dependencies across work orders yet."*

*"We also have a data quality concern. Our operation sequences in SAP are supposed to define predecessor/successor relationships, but only about 60% are properly maintained. The rest default to purely sequential."*

## Additional context

- Nadia's priority is what-if simulation: *"if operation X slips by 3 days, show me the new critical path and which deliveries are impacted."*
- Thomas asked whether the dependency logic could eventually be exposed through their current analytics tool, provided the computation sits outside SAP. He insists they don't want to replace SAP — they want a visibility layer alongside.
- OEM pressure to reduce turnaround time by 15% by end of 2026.
- Budget cycle closes in June — a convincing PoC could unlock second-half budget.
- Current KPIs: on-time delivery 78% (target 92%), average delay per work order 4.2 days, 8-12 critical incidents per month.

## Data availability

No data extracts available — AeroStruct's security policy prohibits sharing production data, even samples, during the pre-sales phase. Nadia described the structure verbally: work orders have operations with sequence numbers, each operation is assigned to a work center, estimated duration in hours, and optional predecessor relationships. Thomas confirmed the key entities: Aircraft (by tail number), Work Order (linked to an aircraft), Operation (linked to a work order), Work Center / Resource (shared across work orders).

---
