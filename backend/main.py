"""Workshop starter: FastAPI shell only. Add your routes and Neo4j logic per course instructions."""

import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

app = FastAPI(title="CPA Workshop", version="0.1.0")
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
