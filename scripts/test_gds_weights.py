"""
Test GDS longestPath weights on Aura (direct bolt connection).

Graph: START -> A(3d) -> B(5d) -> C(2d)
                                -> D(4d)
Expected: D = 12.0  (critical path)
"""

import os
import sys
import uuid

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI   = os.getenv("NEO4J_URI")
USER  = os.getenv("NEO4J_USER", "neo4j")
PWD   = os.getenv("NEO4J_PASSWORD", "")
LABEL = "GdsTestNode"

TEARDOWN = f"MATCH (n:{LABEL}) DETACH DELETE n"

SETUP = f"""
MERGE (s:{LABEL} {{id: 'START'}})
MERGE (a:{LABEL} {{id: 'A'}})
MERGE (b:{LABEL} {{id: 'B'}})
MERGE (c:{LABEL} {{id: 'C'}})
MERGE (d:{LABEL} {{id: 'D'}})
MERGE (s)-[:TE {{duration: 3.0}}]->(a)
MERGE (a)-[:TE {{duration: 5.0}}]->(b)
MERGE (b)-[:TE {{duration: 2.0}}]->(c)
MERGE (b)-[:TE {{duration: 4.0}}]->(d)
"""

def make_project_query(graph_name: str) -> str:
    return f"""
CYPHER runtime=parallel
MATCH (n:{LABEL})-[r:TE]->(m:{LABEL})
RETURN gds.graph.project(
  '{graph_name}', n, m,
  {{
    relationshipType: type(r),
    relationshipProperties: r {{.duration}}
  }},
  {{ memory: '2GB' }}
) AS result
"""

LONGEST_W = """
CALL gds.dag.longestPath.stream($g, {relationshipWeightProperty: 'duration'})
YIELD targetNode, totalCost
RETURN gds.util.asNode(targetNode).id AS node, totalCost
ORDER BY totalCost DESC
"""

LONGEST_U = """
CALL gds.dag.longestPath.stream($g)
YIELD targetNode, totalCost
RETURN gds.util.asNode(targetNode).id AS node, totalCost
ORDER BY totalCost DESC
"""

DROP = "CALL gds.graph.drop($g, false) YIELD graphName"


def main():
    print(f"Connecting to: {URI}")
    driver = GraphDatabase.driver(URI, auth=(USER, PWD))

    with driver.session() as s:

        print("\n[1] Setting up test data...")
        s.run(TEARDOWN)
        s.run(SETUP)
        print("    OK — START->A(3)->B(5)->C(2) and B->D(4)")

        g = "test_" + uuid.uuid4().hex[:6]
        print(f"\n[2] Projecting graph (name={g}, auto session 2GB)...")
        try:
            res = list(s.run(make_project_query(g)))
            if res:
                r = res[0]["result"]
                print(f"    OK — nodes={r['nodeCount']}  rels={r['relationshipCount']}")
            else:
                print("    WARN: no result returned")
                sys.exit(1)
        except Exception as e:
            print(f"    ERROR => {e}")
            s.run(TEARDOWN)
            driver.close()
            sys.exit(1)

        print("\n[3] longestPath WEIGHTED (expected: D=12.0)...")
        try:
            rows_w = list(s.run(LONGEST_W, {"g": g}))
            rows_u = list(s.run(LONGEST_U, {"g": g}))
            print(f"  {'node':<8}  {'weighted':>10}  {'unweighted':>10}")
            for w, u in zip(rows_w, rows_u):
                print(f"  {w['node']:<8}  {w['totalCost']:>10.2f}  {u['totalCost']:>10.2f}")
            best = max(rows_w, key=lambda x: x["totalCost"]) if rows_w else None
            if best and abs(best["totalCost"] - 12.0) < 0.01 and best["node"] == "D":
                print("\n    ✓ CORRECT — D=12.0, weights working!")
            else:
                print(f"\n    ✗ WRONG — expected D=12.0, got {best['node']}={best['totalCost']}")
        except Exception as e:
            print(f"    ERROR => {e}")

        print("\n[4] Cleanup...")
        try:
            s.run(DROP, {"g": g})
        except Exception:
            pass
        s.run(TEARDOWN)
        print("    done.")

    driver.close()


if __name__ == "__main__":
    main()
