# 🏗️ CPA Workshop — Build a PoC from Brief to Demo

> Build a Critical Path Analysis PoC from the AeroStruct client brief to a working demo, applying SE Augmented AI practices throughout.
>
> Each phase produces an MD artifact in `notes/` that serves as input to the next.

---

## ⚙️ Prerequisites

- ✅ Day 0 completed (§0 — Getting Ready)
- ✅ Workshop repo cloned and dependencies installed
- ✅ Neo4j instance running (AuraDB Free) with MCP connected in Cursor

---

## 📦 What's provided

> 🔗 **Workshop repo**: [github.com/neo4j-field/se-ai-workshop-cpa](https://github.com/neo4j-field/se-ai-workshop-cpa) **⚠️ DOES NOT EXIST YET**

| File | Purpose |
|------|---------|
| `brief/aerostruct.md` | Client meeting notes — your only input |
| `backend/requirements.txt` | Python dependencies, pinned |
| `backend/main.py` | Empty FastAPI entrypoint |
| `frontend/index.html` | Frappe Gantt CDN linked, empty shell |
| `.cursor/mcp.json` | Template — replace with your credentials |
| `data/seed-dataset.cypher` | Pre-built dataset (use only if skipping Phase 4) |
| `notes/` | Your workspace for MD artifacts |

## 🚫 What's NOT provided

- ❌ No data model — you design it
- ❌ No Cypher queries — you write them
- ❌ No endpoint logic — you build it
- ❌ No front-end code — you code it
- ❌ No Pydantic schemas — you define them

---

## 🎯 Success path
```
Phase 1 ──→ Phase 2 ──→ Phase 3 ──→ Phase 5 ──→ Phase 7
Understand    Frame        Model       Code         Demo
the problem   the PoC      & validate  (1 endpoint) (mini demo)
                             │
                             ├──→ Phase 4 ········→ Phase 5 (with your own data)
                             │    Generate data      
                             │    [STRETCH]          
                             │
                             └──→ Phase 5 ········→ Phase 6
                                  + delay sim        AWS deploy
                                  + resource view    [BONUS]
                                  [STRETCH]
```

Tu as raison. Voici mon estimation révisée — je tiens compte du fait que les SEs sont tech-oriented mais découvrent le workflow AI-augmented, et qu'il y a un temps de "prise en main" au début qui diminue ensuite :

| Phase | Goal | Status | Time |
|-------|------|--------|------|
| 1 — Understand the problem | Domain analysis + provenance tags | 🟢 **Core** | ~30 min |
| 2 — Frame the PoC | Hypothesis, business questions, non-goals | 🟢 **Core** | ~20 min |
| 3 — Data model | Graph schema + proof-point query patterns | 🟢 **Core** | ~40 min |
| 4 — Synthetic data | Generate your own dataset | 🟡 Stretch | ~45 min |
| 5 — Code (critical path) | One endpoint + Gantt visualization | 🟢 **Core** | ~60 min |
| 5 — Code (delay sim) | What-if simulation endpoint | 🟡 Stretch | ~30 min |
| 5 — Code (resource contention) | Resource contention view | 🔵 Bonus | ~30 min |
| 6 — AWS deploy | Containerize and deploy | 🔵 Bonus | ~30 min |
| 7 — Demo | Demo script + dry run | 🟢 **Core** | ~20 min |

**Core path** = Phases 1 → 2 → 3 → 5 (one endpoint) → 7 (mini demo). Get here first.
**Stretch** = generate your own data (Phase 4) · delay simulation endpoint · resource contention view
**Bonus** = AWS deployment (Phase 6)

**Estimated duration**

| Path | Time |
|------|------|
| 🟢 Core | ~3h |
| 🟢 + 🟡 Stretch | ~4h |
| 🟢 + 🟡 + 🔵 Full | ~5h |




---

## 👥 Working mode

**Pairs recommended** if team size allows: one SE drives in Cursor, the other cross-validates on Gemini/ChatGPT. Swap roles between phases.

If working solo: use one LLM to produce, another to challenge — don't do both in the same conversation.

---
---

## Phase 1 — Understand the client problem
*Guide ref: §5.1*

> 🎯 **Goal**: understand what the client actually needs — not what the brief literally says.

**📋 Exercise**
- Load `brief/aerostruct.md` into a Reasoning-tier LLM
- Ramp up on the domain — what does the client need and why?
- Apply **provenance discipline**: classify every element (verified fact / client assumption / model inference / open question)
- Separate signal from noise: core problem vs. context vs. out of scope
- **Cross-validate** your analysis with a second LLM

**📄 Output**: `notes/01-domain-analysis.md`

**⚠️ Biases to watch**: sycophancy · client over-trust · framing

**💬 What would you say to the client now?**
How would you summarize back to Jean-Marc what you understood, and what you'd need to clarify?

<details>
<summary>💡 Hint 1</summary>

Not everything in the brief is a problem to solve. Some things are context, some are constraints, some are distractions. Who stated the actual pain?
</details>

<details>
<summary>💡 Hint 2</summary>

Nadia and Jean-Marc describe the same problem from different angles. Thomas raises technical context that matters but isn't the core need. The KPIs are verified; the estimates are not.
</details>

<details>
<summary>💡 Hint 3 — last resort</summary>

The core problem is cross-work-order dependency visibility and delay impact analysis. The analytics dashboard question, the data quality issue, and the budget timeline are context to acknowledge but not to solve in the PoC.
</details>

---

## Phase 2 — Frame the PoC
*Guide ref: §5.2*

> 🎯 **Goal**: define what the PoC must prove — and what it must NOT try to do.

**📋 Exercise**
- Define: hypothesis, success criteria, non-goals
- Formulate the **business questions** the PoC must answer (natural language, client perspective)
- Scope ruthlessly — what's in, what's out, what's post-PoC
- **Cross-validate** with a second LLM

**📄 Output**: `notes/02-poc-brief.md`

**⚠️ Biases to watch**: framing · false precision

**💬 What would you say to the client now?**
How would you pitch this PoC scope to Nadia and Thomas in one paragraph?

<details>
<summary>💡 Hint 1</summary>

Think from Nadia's chair. What would she need to see to stop using Excel?
</details>

<details>
<summary>💡 Hint 2</summary>

You need at least 3 business questions. One about the current state, one about simulating change, one about shared constraints.
</details>

<details>
<summary>💡 Hint 3 — last resort</summary>

Example hypothesis: "Neo4j's graph traversal can compute the critical path across work orders and simulate delay impact in seconds, replacing a 3-4 day manual process." Non-goals: SAP replacement, data quality remediation, production-grade UI.
</details>

---

## Phase 3 — Build and validate the data model
*Guide ref: §6.1*

> 🎯 **Goal**: create a graph model that can answer every business question from Phase 2.

**📋 Exercise**
- Describe the domain → generate an ontology using MCP Data Modeling
- **Validate**: translate each business question from Phase 2 into a traversal pattern. If a question can't be answered → the model is incomplete, iterate.
- **Cross-validate** with a second LLM

**📄 Output**: `notes/03-data-model.md` — schema + proof-point query patterns

**⚠️ Biases to watch**: schema literalism · mode collapse

**💬 What would you say to the client now?**
How would you walk Thomas through this model and explain why it enables what SAP can't do today?

<details>
<summary>💡 Hint 1</summary>

Start from what Nadia described — what are the things she manipulates daily? What connects them?
</details>

<details>
<summary>💡 Hint 2</summary>

You need 4 node types. Think: what flies, what's planned, what's executed, what's shared.
</details>

<details>
<summary>💡 Hint 3 — last resort</summary>

Aircraft, WorkOrder, Operation, Resource. The cross-work-order `PRECEDES` relationship is what makes CPA possible — and what SAP doesn't have.
</details>

---

## Phase 4 — Generate synthetic data — STRETCH
*Guide ref: §6.2*

> ⏭️ **Short on time?** Skip this phase — load the provided seed dataset and go straight to Phase 5:
> ```bash
> cat data/seed-dataset.cypher | cypher-shell -u neo4j -p <password> -a <your-aura-uri>
> ```
> Or load it via MCP in Cursor: *"Execute the content of data/seed-dataset.cypher on my Neo4j instance."*
>
> Come back to this phase async to practice synthetic data generation.

> 🎯 **Goal**: build a realistic dataset from the verbal description only — no client data available.

**📋 Exercise**
- Generate data from the validated schema — use the brief's clues to calibrate volume and realism
- Execute and validate via MCP: run proof-point queries from Phase 3
- **Cross-validate** the generation logic with a second LLM

**📄 Output**: populated Neo4j instance + `data/generate.cypher`

**⚠️ Biases to watch**: distribution blindness

<details>
<summary>💡 Hint 1</summary>

The brief gives you all the numbers you need. Re-read what Jean-Marc and Thomas said about volumes.
</details>

<details>
<summary>💡 Hint 2</summary>

~10 work orders, 2-3 aircraft, 100-150 operations, 2-3 shared resources. Reflect the "60% properly maintained" in your data.
</details>

<details>
<summary>💡 Hint 3 — last resort</summary>

Create deliberate bottlenecks — one dense critical path, one over-scheduled shared resource. Without bottlenecks, your CPA demo shows nothing interesting.
</details>

---

## Phase 5 — Code the application
*Guide ref: §7.1, §7.2*

> 🎯 **Goal**: a working app — critical path visible on a Gantt chart, end to end.

**Stack is decided**: Python + FastAPI + Pydantic / Vanilla HTML + Frappe Gantt via CDN. No framework, no build step. PoC, not production.

> 📦 **The repo provides your starting point**: `backend/main.py` (empty FastAPI entrypoint, dependencies pinned in `requirements.txt`) and `frontend/index.html` (Frappe Gantt CDN linked, empty shell). You write the logic, not the boilerplate.

**🎯 In-session target**

| | Endpoint | Status |
|---|----------|--------|
| 🟢 | Critical path → Gantt visualization | **Do this first** |
| 🟡 | Delay simulation (what-if) | Stretch |
| 🔵 | Resource contention | Bonus |

**📋 Exercise**
- Design endpoints that serve the proof points from Phase 3
- Cypher queries validated via MCP first, then hardened in code
- Front-end: Frappe Gantt renders the schedule, critical path highlighted
- Cross-validate plans before coding
- Git commit before every major agent intervention

**📄 Output**: working local app

**⚠️ Biases to watch**: over-engineering · confirmation/commitment

**💬 What would you say to the client now?**
You have a working prototype. How would you frame a 30-minute demo invitation to Jean-Marc and Nadia?

<details>
<summary>💡 Hint 1</summary>

Start with one endpoint — the critical path. Get it working end to end (Cypher → FastAPI → Gantt) before adding anything else.
</details>

<details>
<summary>💡 Hint 2</summary>

You need 2-3 endpoints max. One for critical path, one for delay simulation. Frappe Gantt takes a simple JSON array of tasks with dependencies.
</details>

<details>
<summary>💡 Hint 3 — last resort</summary>

The critical path is a longest-path traversal through `PRECEDES` relationships, weighted by duration. Frappe Gantt's `custom_class` property lets you highlight critical path bars with CSS.
</details>

---

## Phase 6 — Deploy on AWS — BONUS

> Only if Phase 5 works locally. Containerize and deploy.

<details>
<summary>💡 Hint 1</summary>

One Dockerfile, both back-end and front-end.
</details>

<details>
<summary>💡 Hint 2</summary>

FastAPI can serve the static HTML too — no separate web server needed.
</details>

<details>
<summary>💡 Hint 3 — last resort</summary>

Externalize Neo4j connection string as environment variables. AWS App Runner takes a Docker image directly.
</details>

---

## Phase 7 — Prepare and run the demo
*Guide ref: §7.3*

> 🎯 **Goal**: deliver a convincing demo to the AeroStruct team.

**📋 Exercise**
- Snapshot the known-good dataset
- Prepare fallback queries for each proof point
- Generate demo narrative from your PoC brief
- Dry run: LLM plays the skeptical client — what questions would they ask?

**📄 Output**: `notes/07-demo-script.md` + known-good dataset

**💬 What would you say to the client now?**
This is it — deliver the demo.

<details>
<summary>💡 Hint 1</summary>

The storyline follows Nadia's day: something breaks → she needs impact → she runs what-if → she decides.
</details>

<details>
<summary>💡 Hint 2</summary>

For each proof point, have a known-good result AND a simpler fallback. Pre-capture screenshots.
</details>

<details>
<summary>💡 Hint 3 — last resort</summary>

Ask the LLM to play Nadia. She'll ask: "What if two operations slip?", "Can I see by resource?", "How fresh is this data?" — prepare answers.
</details>