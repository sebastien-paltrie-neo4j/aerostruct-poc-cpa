# Tri Topo Gantt Demo

Topological sort demo with incident simulation on Neo4j: two side-by-side Gantt charts (baseline vs incident) with critical path highlighting. Two backends available: **Cypher** (full Cypher) or **GDS** (APOC subgraph → project → longestPath → drop).

## Prerequisites

- Python 3.10+
- Neo4j 5.x with **APOC** (for the Cypher backend)
- For the GDS backend: Neo4j with **GDS** (plugin or Aura)

## Setup

1. **Create and activate a virtual environment**

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure Neo4j**

```bash
cp .env.example .env
```

Edit `.env`:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

4. **Load test data** (optional)

Import your WorkOrders and `PRECEDES_WO` relationships into Neo4j.

5. **Prepare data** (required)

Run `scripts/prep_data.cypher` in Neo4j Browser to compute:
- `gantt_start_dt` / `gantt_end_dt` (DateTime)
- `duration_days_computed`
- `duration` on nodes and relationships (required for GDS)

## Running the App

```bash
uvicorn backend.main:app --reload
```

The application is available at http://localhost:8000

## Usage

1. Enter a **root WorkOrder** (e.g. `25005598260` or `25005646425`)
2. Optional: select **GDS** to use the GDS backend instead of Cypher
3. Click **Load Baseline** → Gantt with critical path highlighted
4. Select an **incident WO** from the dropdown, enter a **delay (days)**, then click **Simulate** → Incident Gantt with delta

**Bar colours:**
- **Red**: Critical (on the critical path)
- **Purple**: Critical + Incident (incident WO is on the critical path)
- **Orange**: Incident (not Critical) (incident WO is off the critical path)

## Project Structure

```
backend/
  main.py           # FastAPI + routes /gantt/baseline, /gantt/incident
  models.py         # Pydantic (GanttResponse)
  neo4j_client.py   # Neo4j connection + run()
  queries_cypher.py # Critical path — full Cypher
  queries_gds.py    # Critical path — GDS (project → longestPath → drop)

frontend/
  index.html        # Gantt page
  app.js            # Baseline/incident loading, Frappe Gantt rendering
  styles.css        # Styles + bar colours

scripts/
  prep_data.cypher  # Data preparation (durations, etc.)
```

## API

- `GET /gantt/baseline?root=<wipOrderNo>&useGds=false` — Baseline (Cypher by default, GDS if `useGds=true`)
- `GET /gantt/incident?root=<wipOrderNo>&incidentWo=<wipOrderNo>&delayDays=<float>&useGds=false` — Incident simulation

Response: `tasks`, `criticalPath`, `totalDuration`, `sink`, `incidentWo`, `delayDays`, `backend` (`"cypher"` or `"gds"`).

## GDS Backend

With the **GDS** toggle, each request:
1. Builds the subgraph from the root (APOC `subgraphAll`)
2. Projects it into memory with `gds.graph.project` (weight = duration + incident delay if applicable)
3. Runs `gds.dag.longestPath.stream`
4. Drops the projected graph

No persistent session or "Init GDS" button: everything is computed on the fly per request.

## Neo4j Data Model

**Nodes** `:WorkOrder`:
- `wipOrderNo` — identifier
- `gantt_start`, `gantt_end` — dates (ISO string)
- `gantt_start_dt`, `gantt_end_dt` — DateTime (set by prep_data)
- `duration_days_computed`, `duration` — duration in days (set by prep_data)

**Relationships**: `(:WorkOrder)-[:PRECEDES_WO]->(:WorkOrder)` with `duration` property (set by prep_data).
