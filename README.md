# CPA Workshop — starter

Minimal **FastAPI + Neo4j + Frappe Gantt (CDN)** skeleton. Workshop steps and brief are in the **course materials**, not here.

## Stack

- `backend/` — FastAPI entry (`main.py`), Neo4j helper (`neo4j_client.py`), empty `models.py` for **your** Pydantic schemas. No business routes yet.
- `frontend/` — Frappe CDN in `index.html`; you add markup and JS.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Set `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD` in `.env`.

## Run

From the repo root:

```bash
uvicorn backend.main:app --reload
```

→ http://localhost:8000
