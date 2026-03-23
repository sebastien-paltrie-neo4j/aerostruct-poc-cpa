"""
Test GDS longestPath via GdsSessions (Aura API credentials).
Graph: START -> A(3d) -> B(5d) -> C(2d)
                                -> D(4d)
Expected: D = 12.0
"""

import os
import uuid
from dotenv import load_dotenv
from graphdatascience.session import GdsSessions, AuraAPICredentials, DbmsConnectionInfo, SessionMemory

load_dotenv()

URI            = os.getenv("NEO4J_URI")
USER           = os.getenv("NEO4J_USER", "neo4j")
PWD            = os.getenv("NEO4J_PASSWORD", "")
CLIENT_ID      = os.getenv("AURA_CLIENT_ID")
CLIENT_SECRET  = os.getenv("AURA_CLIENT_SECRET")
PROJECT_ID     = os.getenv("AURA_PROJECT_ID")

LABEL = "GdsTestNode"

# ── GdsSessions connection ────────────────────────────────────────────────────
sessions = GdsSessions(api_credentials=AuraAPICredentials(
    CLIENT_ID,
    CLIENT_SECRET,
    project_id=PROJECT_ID
))
gds = sessions.get_or_create(
    session_name="test-gds-weights",
    memory=SessionMemory.m_2GB,
    db_connection=DbmsConnectionInfo(URI, USER, PWD)
)
print("Session OK")

# ── Data setup ────────────────────────────────────────────────────────────────
gds.run_cypher(f"MATCH (n:{LABEL}) DETACH DELETE n")
gds.run_cypher(f"""
MERGE (s:{LABEL} {{id: 'START'}})
MERGE (a:{LABEL} {{id: 'A'}})
MERGE (b:{LABEL} {{id: 'B'}})
MERGE (c:{LABEL} {{id: 'C'}})
MERGE (d:{LABEL} {{id: 'D'}})
MERGE (s)-[:TE {{duration: 3.0}}]->(a)
MERGE (a)-[:TE {{duration: 5.0}}]->(b)
MERGE (b)-[:TE {{duration: 2.0}}]->(c)
MERGE (b)-[:TE {{duration: 4.0}}]->(d)
""")
print("Setup OK")

# ── Projection ────────────────────────────────────────────────────────────────
g_name = "test_" + uuid.uuid4().hex[:6]
G, _ = gds.graph.project(
    g_name,
    f"""
    MATCH (n:{LABEL})-[r:TE]->(m:{LABEL})
    RETURN gds.graph.project.remote(n, m, {{
        relationshipType: type(r),
        relationshipProperties: r {{.duration}}
    }}) AS p
    """
)
print(f"Projection OK — nodes={G.node_count()}  rels={G.relationship_count()}")

# ── longestPath ───────────────────────────────────────────────────────────────
result = gds.dag.longestPath.stream(G, relationshipWeightProperty="duration")
print(result.sort_values("totalCost", ascending=False).to_string())

best = result.loc[result["totalCost"].idxmax()]
if abs(best["totalCost"] - 12.0) < 0.01:
    print("\n✓ CORRECT — D=12.0, weights working!")
else:
    print(f"\n✗ WRONG — expected D=12.0, got {best['totalCost']}")

# ── Cleanup ───────────────────────────────────────────────────────────────────
G.drop()
gds.run_cypher(f"MATCH (n:{LABEL}) DETACH DELETE n")
gds.close()
