#!/usr/bin/env python3
"""
CPA Workshop — Seed Dataset Generator

Generates a Cypher script for the AeroStruct CPA workshop.
Ontology: Aircraft, WorkOrder, Operation + PRECEDES (within and cross-WO)

Usage:
    python generate_seed_dataset.py > seed-dataset.cypher
    python generate_seed_dataset.py --seed 42 --output seed-dataset.cypher
"""

import argparse
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Optional


# --- Domain config ---

OPERATION_NAMES = [
    "Panel Drilling", "Skin Riveting", "Frame Assembly", "Spar Machining",
    "Sealant Application", "NDI Inspection", "Autoclave Curing", "Surface Treatment",
    "Bracket Installation", "Wire Harness Routing", "Hydraulic Line Fitting",
    "Composite Layup", "Fastener Installation", "Edge Trimming", "Shimming",
    "Pressure Test", "Paint Preparation", "Final Inspection", "Documentation Review",
    "Torque Verification", "Alignment Check", "Gap Measurement", "Bonding Prep",
    "Primer Application", "Quality Gate"
]

AIRCRAFT_PROGRAMS = ["Narrow-Body", "Wide-Body", "Regional"]

# Duration constants (hours) — operations last between half a day and 6 days, in half-day steps
DURATION_MIN = 4
DURATION_MAX = 48
DURATION_STEP = 4
DURATION_CHOICES = list(range(DURATION_MIN, DURATION_MAX + DURATION_STEP, DURATION_STEP))


@dataclass
class Aircraft:
    tail_number: str
    program: str
    delivery_date: str  # ISO date


@dataclass
class WorkOrder:
    wo_number: str
    aircraft_tail: str
    status: str  # New, Started, Completed


@dataclass
class Operation:
    op_id: str
    wo_number: str
    name: str
    sequence_number: int
    estimated_duration: float  # hours
    status: str  # New, InProgress, Completed


# --- DAG generation (inspired by existing script, simplified) ---

def generate_intra_wo_dag(
    rng: random.Random,
    op_ids: List[str],
) -> List[Tuple[str, str]]:
    """
    Generate a non-linear DAG within a single work order.
    Returns list of (from_op_id, to_op_id) — from PRECEDES to.
    ~60% explicit dependencies, ~40% just sequential (matching Thomas's "60% maintained").
    """
    n = len(op_ids)
    if n <= 2:
        return [(op_ids[0], op_ids[1])] if n == 2 else []

    edges: List[Tuple[str, str]] = []

    # Split into layers
    roots_end = min(2, n)
    mid_end = min(n - 2, max(roots_end + 1, int(n * 0.7)))

    roots = list(range(0, roots_end))
    mid = list(range(roots_end, mid_end))
    final = list(range(mid_end, n))

    # Mid-layer ops depend on 1-2 roots
    for i in mid:
        k = min(len(roots), rng.randint(1, 2))
        preds = rng.sample(roots, k)
        for p in preds:
            edges.append((op_ids[p], op_ids[i]))

        # Some mid ops also depend on earlier mid ops (~40% chance)
        earlier_mid = [m for m in mid if m < i]
        if earlier_mid and rng.random() < 0.4:
            p = rng.choice(earlier_mid)
            edges.append((op_ids[p], op_ids[i]))

    # Final ops depend on 2-4 mid/root ops (convergence)
    all_prior = roots + mid
    for i in final:
        k = min(len(all_prior), rng.randint(2, 4))
        preds = rng.sample(all_prior, k)
        for p in preds:
            edges.append((op_ids[p], op_ids[i]))

    # Deduplicate
    return list(dict.fromkeys(edges))


def generate_cross_wo_edges(
    rng: random.Random,
    wo_ops: dict,  # wo_number -> list of op_ids
    same_aircraft_wos: List[str],
    cross_wo_ratio: float = 0.15
) -> List[Tuple[str, str, str]]:
    """
    Generate cross-WO PRECEDES edges for work orders on the same aircraft.
    Returns list of (from_op_id, to_op_id, type).
    These are the edges that make CPA across work orders possible.
    """
    edges = []
    if len(same_aircraft_wos) < 2:
        return edges

    for i, wo1 in enumerate(same_aircraft_wos):
        for wo2 in same_aircraft_wos[i + 1:]:
            ops1 = wo_ops[wo1]
            ops2 = wo_ops[wo2]

            # Pick a few operations from WO1 that WO2 operations depend on
            n_cross = max(1, int(len(ops1) * cross_wo_ratio))
            # Source: late-ish operations in WO1 (not roots)
            source_pool = ops1[len(ops1) // 2:]
            # Target: early-ish operations in WO2 (not final)
            target_pool = ops2[:len(ops2) // 2]

            if source_pool and target_pool:
                for _ in range(n_cross):
                    src = rng.choice(source_pool)
                    tgt = rng.choice(target_pool)
                    edges.append((src, tgt, "explicit"))

    return edges


# --- Main generator ---

def generate_dataset(
    seed: int = 42,
    n_aircraft: int = 3,
    wo_per_aircraft: int = 4,
    ops_per_wo_range: Tuple[int, int] = (10, 18),
) -> str:
    rng = random.Random(seed)
    lines: List[str] = []

    lines.append("// =============================================")
    lines.append("// CPA Workshop — Seed Dataset")
    lines.append("// AeroStruct S.A. — Critical Path Analysis")
    lines.append("// =============================================")
    lines.append("// Ontology: Aircraft, WorkOrder, Operation")
    lines.append("// Relationships: FOR, PART_OF, PRECEDES")
    lines.append("// =============================================")
    lines.append("")

    # --- Constraints ---
    lines.append("// --- Constraints ---")
    lines.append("CREATE CONSTRAINT aircraft_tail IF NOT EXISTS FOR (a:Aircraft) REQUIRE a.tailNumber IS UNIQUE;")
    lines.append("CREATE CONSTRAINT wo_number IF NOT EXISTS FOR (w:WorkOrder) REQUIRE w.woNumber IS UNIQUE;")
    lines.append("CREATE CONSTRAINT op_id IF NOT EXISTS FOR (o:Operation) REQUIRE o.opId IS UNIQUE;")
    lines.append("")

    # --- Aircraft ---
    aircraft_list: List[Aircraft] = []
    delivery_offsets = [30, 60, 90]  # days from "now" — tight, medium, comfortable

    lines.append("// --- Aircraft ---")
    for i in range(n_aircraft):
        tail = f"AF-{i + 1:03d}"
        program = AIRCRAFT_PROGRAMS[i % len(AIRCRAFT_PROGRAMS)]
        # Delivery date as a relative concept (days from now)
        delivery_days = delivery_offsets[i % len(delivery_offsets)]
        delivery = f"2026-{4 + delivery_days // 30:02d}-{15 + (delivery_days % 30) % 28:02d}"
        ac = Aircraft(tail, program, delivery)
        aircraft_list.append(ac)
        lines.append(
            f'MERGE (a:Aircraft {{tailNumber: "{ac.tail_number}"}}) '
            f'SET a.program = "{ac.program}", a.deliveryDate = date("{ac.delivery_date}");'
        )
    lines.append("")

    # --- Work Orders & Operations ---
    all_wo_ops: dict = {}  # wo_number -> [op_ids]
    aircraft_wos: dict = {}  # tail -> [wo_numbers]
    all_intra_edges: List[Tuple[str, str, str]] = []  # (from, to, type)
    op_counter = 1

    lines.append("// --- Work Orders, Operations, and intra-WO PRECEDES ---")

    for ac in aircraft_list:
        aircraft_wos[ac.tail_number] = []

        for wo_idx in range(wo_per_aircraft):
            wo_number = f"WO-{ac.tail_number}-{wo_idx + 1:02d}"
            aircraft_wos[ac.tail_number].append(wo_number)

            # Status distribution: mostly active
            if wo_idx == 0:
                wo_status = "Started"
            elif wo_idx == wo_per_aircraft - 1:
                wo_status = "New"
            else:
                wo_status = rng.choice(["Started", "Started", "New"])

            lines.append(f"")
            lines.append(f"// Work Order: {wo_number} ({wo_status}) for {ac.tail_number}")
            lines.append(
                f'MERGE (wo:WorkOrder {{woNumber: "{wo_number}"}}) '
                f'SET wo.status = "{wo_status}";'
            )
            lines.append(
                f'MATCH (a:Aircraft {{tailNumber: "{ac.tail_number}"}}), '
                f'(wo:WorkOrder {{woNumber: "{wo_number}"}}) '
                f'MERGE (wo)-[:FOR]->(a);'
            )

            # Operations
            n_ops = rng.randint(*ops_per_wo_range)
            op_ids = []
            available_names = rng.sample(OPERATION_NAMES, min(n_ops, len(OPERATION_NAMES)))
            if n_ops > len(available_names):
                available_names += [f"Operation-{j}" for j in range(n_ops - len(available_names))]

            for op_idx in range(n_ops):
                op_id = f"OP-{op_counter:04d}"
                op_counter += 1
                op_ids.append(op_id)

                name = available_names[op_idx]
                seq = (op_idx + 1) * 10
                duration = rng.choice(DURATION_CHOICES)

                # Status consistent with WO
                if wo_status == "Completed":
                    op_status = "Completed"
                elif wo_status == "Started":
                    if op_idx < n_ops * 0.4:
                        op_status = "Completed"
                    elif op_idx < n_ops * 0.5:
                        op_status = "InProgress"
                    else:
                        op_status = "New"
                else:
                    op_status = "New"

                lines.append(
                    f'MERGE (op:Operation {{opId: "{op_id}"}}) '
                    f'SET op.name = "{name}", op.sequenceNumber = {seq}, '
                    f'op.estimatedDuration = {duration}, op.status = "{op_status}";'
                )
                lines.append(
                    f'MATCH (wo:WorkOrder {{woNumber: "{wo_number}"}}), '
                    f'(op:Operation {{opId: "{op_id}"}}) '
                    f'MERGE (op)-[:PART_OF]->(wo);'
                )

            all_wo_ops[wo_number] = op_ids

            # Intra-WO PRECEDES (DAG)
            intra_edges = generate_intra_wo_dag(rng, op_ids)

            # Mark ~60% as explicit, ~40% as default (Thomas's data quality)
            for src, tgt in intra_edges:
                edge_type = "explicit" if rng.random() < 0.6 else "default"
                all_intra_edges.append((src, tgt, edge_type))

    lines.append("")

    # --- PRECEDES relationships (intra-WO) ---
    lines.append("// --- PRECEDES relationships (intra-WO) ---")
    for src, tgt, edge_type in all_intra_edges:
        lines.append(
            f'MATCH (a:Operation {{opId: "{src}"}}), (b:Operation {{opId: "{tgt}"}}) '
            f'MERGE (a)-[:PRECEDES {{type: "{edge_type}"}}]->(b);'
        )
    lines.append("")

    # --- Cross-WO PRECEDES (the critical piece) ---
    lines.append("// --- PRECEDES relationships (cross-WO) ---")
    lines.append("// These cross-WO dependencies are what makes CPA possible")
    lines.append("// and what SAP cannot do today.")

    cross_edges = []
    for ac in aircraft_list:
        wos = aircraft_wos[ac.tail_number]
        ac_cross = generate_cross_wo_edges(rng, all_wo_ops, wos, cross_wo_ratio=0.12)
        cross_edges.extend(ac_cross)

    for src, tgt, edge_type in cross_edges:
        lines.append(
            f'MATCH (a:Operation {{opId: "{src}"}}), (b:Operation {{opId: "{tgt}"}}) '
            f'MERGE (a)-[:PRECEDES {{type: "{edge_type}"}}]->(b);'
        )
    lines.append("")

    # --- Intentional bottleneck for demo ---
    lines.append("// --- Intentional bottleneck ---")
    lines.append("// OP-0042 is on the critical path of AF-001 with a long duration.")
    lines.append("// The what-if demo: 'if OP-0042 slips by 3 days, what happens?'")

    # Make OP-0042 a long operation if it exists
    if op_counter > 42:
        lines.append(
            'MATCH (op:Operation {opId: "OP-0042"}) '
            'SET op.estimatedDuration = 72.0, op.name = "Autoclave Curing (Critical)";'
        )
    lines.append("")

    # --- Summary ---
    total_ops = op_counter - 1
    total_intra = len(all_intra_edges)
    total_cross = len(cross_edges)
    lines.append(f"// --- Summary ---")
    lines.append(f"// Aircraft: {n_aircraft}")
    lines.append(f"// Work Orders: {n_aircraft * wo_per_aircraft}")
    lines.append(f"// Operations: {total_ops}")
    lines.append(f"// PRECEDES (intra-WO): {total_intra}")
    lines.append(f"// PRECEDES (cross-WO): {total_cross}")
    lines.append(f"// Total PRECEDES: {total_intra + total_cross}")
    lines.append(f"// Explicit vs default: ~60% / ~40%")

    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description="Generate CPA Workshop seed dataset as Cypher")
    p.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    p.add_argument("--output", type=str, default=None, help="Output file (default: stdout)")
    args = p.parse_args()

    cypher = generate_dataset(seed=args.seed)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(cypher)
        print(f"Written to {args.output}")
    else:
        print(cypher)


if __name__ == "__main__":
    main()