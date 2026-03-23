"""Cypher queries: topological sort + critical path (full Cypher)."""

from datetime import date, timedelta
from .neo4j_client import Neo4jClient


QUERY = """
MATCH (root:WorkOrder {wipOrderNo: $root})
CALL apoc.path.subgraphAll(root, {relationshipFilter: "PRECEDES_WO>", maxLevel: 100})
YIELD nodes, relationships
WITH nodes, relationships, root, $incidentWo AS incidentWo, $delayDays AS delayDays, date($startDate) AS refDate

// Duration map with incident delay applied
WITH nodes, relationships, root, incidentWo, delayDays, refDate,
     apoc.map.fromPairs([n IN nodes | [n.wipOrderNo,
         n.duration + CASE WHEN n.wipOrderNo = incidentWo THEN delayDays ELSE 0 END
     ]]) AS durMap

// Critical path: longest path from root to any sink
MATCH criticalPath = (root)-[:PRECEDES_WO*0..]->(sink)
WHERE ALL(n IN nodes(criticalPath) WHERE n IN nodes)
  AND NOT EXISTS { MATCH (sink)-[:PRECEDES_WO]->(x) WHERE x IN nodes }
WITH nodes, relationships, root, incidentWo, refDate, durMap, criticalPath,
     reduce(d = 0.0, n IN nodes(criticalPath) | d + durMap[n.wipOrderNo]) AS pathDuration
ORDER BY pathDuration DESC
LIMIT 1

WITH nodes, relationships, root, incidentWo, refDate, durMap,
     [n IN nodes(criticalPath) | n.wipOrderNo] AS criticalIds,
     pathDuration AS totalDuration,
     last(nodes(criticalPath)).wipOrderNo AS sink

// Forward pass: earliest start day for each node
UNWIND nodes AS node
MATCH path = (root)-[:PRECEDES_WO*0..]->(node) WHERE ALL(n IN nodes(path) WHERE n IN nodes)
WITH nodes, relationships, incidentWo, refDate, durMap, criticalIds, totalDuration, sink, node,
     max(reduce(d = 0.0, i IN range(0, size(nodes(path))-2) | d + durMap[nodes(path)[i].wipOrderNo])) AS startDay

WITH relationships, incidentWo, refDate, criticalIds, totalDuration, sink,
     collect({id: node.wipOrderNo, node: node, startDay: startDay,
              endDay: startDay + durMap[node.wipOrderNo], duration: durMap[node.wipOrderNo]}) AS tasks

RETURN [t IN tasks | {
    id: t.id, name: t.id,
    start: toString(refDate + duration({days: toInteger(ceil(coalesce(t.startDay, 0)))})),
    end:   toString(refDate + duration({days: toInteger(floor(t.endDay))})),
    dependencies: apoc.text.join([r IN relationships WHERE endNode(r) = t.node | startNode(r).wipOrderNo], ','),
    isCritical:   t.id IN criticalIds,
    isIncident:   coalesce(t.id = incidentWo, false),
    duration_days: t.duration
}] AS tasks, criticalIds AS criticalPath, totalDuration, sink
"""


def calculate_critical_path(root: str, incident_wo: str = None, delay_days: float = 0, start_date: str = None) -> dict:
    if start_date is None:
        start_date = (date.today() + timedelta(days=1)).isoformat()
    results = Neo4jClient.run(QUERY, {
        "root":       root,
        "incidentWo": incident_wo,
        "delayDays":  delay_days,
        "startDate":  start_date,
    })
    if not results:
        return {"tasks": [], "criticalPath": [], "totalDuration": 0, "sink": None, "incidentWo": incident_wo, "delayDays": delay_days}
    return {**results[0], "incidentWo": incident_wo, "delayDays": delay_days}
