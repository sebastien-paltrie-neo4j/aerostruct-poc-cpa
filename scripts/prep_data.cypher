// =============================================================================
// Data preparation script for the Tri Topo Gantt demo
// Run once in Neo4j Browser before starting the application
// =============================================================================

// -----------------------------------------------------------------------------
// 1. Convert ISO date strings to DateTime properties
//    (preserves original gantt_start / gantt_end string fields)
// -----------------------------------------------------------------------------

MATCH (w:WorkOrder)
WHERE w.gantt_start IS NOT NULL
SET w.gantt_start_dt = datetime(w.gantt_start);

MATCH (w:WorkOrder)
WHERE w.gantt_end IS NOT NULL
SET w.gantt_end_dt = datetime(w.gantt_end);

// -----------------------------------------------------------------------------
// 2. Compute duration_days_computed from start/end dates
//    Rounded to nearest 0.25-day increment, minimum 0.25
// -----------------------------------------------------------------------------

MATCH (w:WorkOrder)
WHERE w.gantt_start_dt IS NOT NULL AND w.gantt_end_dt IS NOT NULL
WITH w, round(duration.inSeconds(w.gantt_start_dt, w.gantt_end_dt).seconds / 86400.0 / 0.25) * 0.25 AS dur
SET w.duration_days_computed = CASE WHEN dur < 0.25 THEN 0.25 ELSE dur END;

// -----------------------------------------------------------------------------
// 3. Copy duration onto PRECEDES_WO relationships (= source node duration)
//    Required by GDS longestPath on Aura (relationshipProperties: r {.duration})
// -----------------------------------------------------------------------------

MATCH (n:WorkOrder)
SET n.duration = CASE WHEN coalesce(n.duration_days_computed, 0.0) < 0.75 
                      THEN 0.75 
                      ELSE coalesce(n.duration_days_computed, 0.0) END
WITH n
MATCH (n)-[r:PRECEDES_WO]->()
SET r.duration = n.duration;

// -----------------------------------------------------------------------------
// 4. Validation: find WorkOrders missing a duration
// -----------------------------------------------------------------------------

MATCH (w:WorkOrder)
WHERE w.duration_days_computed IS NULL
RETURN w.wipOrderNo AS missingDuration, 
       "WARNING: This WorkOrder has no duration_days_computed" AS warning;

// -----------------------------------------------------------------------------
// 5. Graph statistics (informational)
// -----------------------------------------------------------------------------

MATCH (w:WorkOrder)
OPTIONAL MATCH (w)-[r:PRECEDES_WO]->()
RETURN count(DISTINCT w) AS totalWorkOrders,
       count(r) AS totalRelationships,
       avg(w.duration_days_computed) AS avgDuration,
       min(w.duration_days_computed) AS minDuration,
       max(w.duration_days_computed) AS maxDuration;
