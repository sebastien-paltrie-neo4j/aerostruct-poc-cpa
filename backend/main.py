import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .models import GanttResponse

logger = logging.getLogger(__name__)
from .neo4j_client import Neo4jClient
from .queries_cypher import calculate_critical_path
from .queries_gds import calculate_critical_path_gds

app = FastAPI(title="CPA / Topological Sort Demo", version="1.0.0")
app.mount("/static", StaticFiles(directory="frontend"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
def shutdown_event():
    Neo4jClient.close()


@app.get("/")
async def root():
    return FileResponse("frontend/index.html")


@app.get("/gantt/baseline", response_model=GanttResponse)
async def get_baseline(
    root: str = Query(..., description="Root wipOrderNo"),
    useGds: bool = Query(False, description="Use GDS backend instead of Cypher"),
):
    calc = calculate_critical_path_gds if useGds else calculate_critical_path
    try:
        result = calc(root)
    except RuntimeError as e:
        if "GDS" in str(e):
            logger.exception("GDS baseline failed: %s", e)
            raise HTTPException(503, str(e)) from e
        raise
    if not result["tasks"]:
        raise HTTPException(404, f"WorkOrder '{root}' not found")
    result["backend"] = "gds" if useGds else "cypher"
    return result


@app.get("/gantt/incident", response_model=GanttResponse)
async def get_incident(
    root: str = Query(...),
    incidentWo: str = Query(...),
    delayDays: float = Query(...),
    useGds: bool = Query(False, description="Use GDS backend instead of Cypher"),
):
    calc = calculate_critical_path_gds if useGds else calculate_critical_path
    try:
        result = calc(root, incidentWo, delayDays)
    except RuntimeError as e:
        if "GDS" in str(e):
            logger.exception("GDS incident failed: %s", e)
            raise HTTPException(503, str(e)) from e
        raise
    if not result["tasks"]:
        raise HTTPException(404, f"WorkOrder '{root}' not found")
    if not any(t["id"] == incidentWo for t in result["tasks"]):
        raise HTTPException(400, f"'{incidentWo}' not found in subgraph")
    result["backend"] = "gds" if useGds else "cypher"
    return result
