"""GDS Critical Path — APOC subgraph → project → longestPath → drop."""

import time
import uuid
from datetime import date, timedelta
from math import ceil, floor

from .neo4j_client import Neo4jClient


GDS_PROJECT = """
    // 1. Build subgraph from root (APOC)
    MATCH (root:WorkOrder {wipOrderNo: $root})
    CALL apoc.path.subgraphAll(root, {relationshipFilter: 'PRECEDES_WO>', maxLevel: 100})
    YIELD nodes, relationships

    // 2. GDS projection: one edge per relationship, weight = duration (+ incident delay if applicable)
    CALL {
        WITH relationships
        UNWIND relationships AS rel
        WITH startNode(rel) AS src, endNode(rel) AS tgt,
             rel.duration + CASE WHEN startNode(rel).wipOrderNo = $incidentWo THEN $delay ELSE 0.0 END AS dur
        RETURN gds.graph.project($g, src, tgt, {
            relationshipType: 'PRECEDES_WO',
            relationshipProperties: { duration: dur }
        }) AS proj
    }
    RETURN proj.nodeCount AS n
"""

GDS_LONGEST_PATH = """
    // 1. Longest path from root (one row per target node, cost = sum of durations)
    CALL gds.dag.longestPath.stream($g, {relationshipWeightProperty: 'duration'})
    YIELD targetNode, totalCost, nodeIds
    WITH gds.util.asNode(targetNode) AS n, totalCost, nodeIds

    // 2. Dependencies (predecessors) and path as wipOrderNo list
    OPTIONAL MATCH (pred:WorkOrder)-[:PRECEDES_WO]->(n)
    RETURN n.wipOrderNo AS wip,
           n.duration AS duration,
           totalCost,
           collect(DISTINCT pred.wipOrderNo) AS deps,
           [x IN nodeIds | gds.util.asNode(x).wipOrderNo] AS path
"""

DROP = "CALL gds.graph.drop($g, false)"


def calculate_critical_path_gds(
    root: str,
    incident_wo: str = None,
    delay_days: float = 0,
    start_date: str = None,
) -> dict:
    start_date = start_date or (date.today() + timedelta(days=1)).isoformat()
    delay = float(delay_days or 0)
    inc = incident_wo or ""
    empty = {
        "tasks": [],
        "criticalPath": [],
        "totalDuration": 0,
        "sink": None,
        "incidentWo": incident_wo,
        "delayDays": delay,
    }
    g = "cpa_" + uuid.uuid4().hex[:8]
    t0 = time.perf_counter()

    project_results = Neo4jClient.run(GDS_PROJECT, {"root": root, "g": g, "incidentWo": inc, "delay": delay})
    if not project_results or project_results[0]["n"] == 0:
        return empty

    try:
        rows = Neo4jClient.run(GDS_LONGEST_PATH, {"g": g})
        if not rows:
            return empty

        best = max(rows, key=lambda r: r["totalCost"])
        critical = set(best["path"])
        ref = date.fromisoformat(start_date)

        def duration(r):
            d = r["duration"] or 0.75
            return d + delay if (inc and r["wip"] == inc and delay > 0) else d

        tasks = []
        for r in sorted(rows, key=lambda r: r["totalCost"]):
            d = duration(r)
            start_day = ceil(r["totalCost"])
            end_day = floor(r["totalCost"] + d)
            tasks.append({
                "id": r["wip"],
                "name": r["wip"],
                "start": str(ref + timedelta(days=start_day)),
                "end": str(ref + timedelta(days=end_day)),
                "dependencies": ",".join(r["deps"]),
                "isCritical": r["wip"] in critical,
                "isIncident": bool(inc and r["wip"] == inc),
                "duration_days": d,
            })

        sink_dur = duration(best)
        print(f"[GDS] {time.perf_counter() - t0:.3f}s", flush=True)
        return {
            "tasks": tasks,
            "criticalPath": best["path"],
            "totalDuration": float(best["totalCost"] + sink_dur),
            "sink": best["wip"],
            "incidentWo": incident_wo,
            "delayDays": delay,
        }
    finally:
        try:
            Neo4jClient.run(DROP, {"g": g})
        except Exception:
            pass
