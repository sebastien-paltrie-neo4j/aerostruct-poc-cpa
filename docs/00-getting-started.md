# §0 — Getting Ready (Day 0)

> Prerequisite checklist. Complete this to be operational with the SE Augmented AI approach. Everything here is done once — not per PoC.

---

## 0.1 — Request access

*Allow lead time for IT approval.*

| Tool | How | Required? |
|------|-----|-----------|
| Cursor | IT Service Portal → Licenses & Software Access Requests | **Required** |
| Gemini | Already available (Google Workspace) | **Required** |
| ChatGPT | IT Service Portal → Licenses & Software Access Requests | Optional |
| Claude Desktop | IT Service Portal → Licenses & Software Access Requests | Optional |
| Claude Code | Managed by Field — check `#ai-devtools` | Not a prerequisite |

Minimum: **Cursor + Gemini**. Optional tools are for SEs who prefer a different LLM for cross-validation. What matters: at least one LLM outside Cursor.

---

## 0.2 — Install & configure

### Cursor

- Sign in with your **neo4j account**
- Enable **Privacy Mode** (default when working with client data)
- Credit budget: Auto = daily driver, Sonnet 4.6 = advanced, Opus = last resort (details in §4)

### Neo4j MCP server

- Install: `brew install neo4j-mcp`
- Verify: `neo4j-mcp --version`
- Will be configured per project (see §0.3)

### Cross-validation LLM

- Verify Gemini access (or ChatGPT/Claude if that's your preference)
- Habit to adopt: one dedicated conversation per PoC, never mix contexts

---

## 0.3 — Set up your first project

Create a scratch project to validate your setup:

```bash
mkdir poc-sandbox && cd poc-sandbox
```

Connect to any Neo4j instance you have available (AuraDB Free, local, existing demo). Create `.cursor/mcp.json` at the project root:

```json
{
  "mcpServers": {
    "neo4j": {
      "command": "neo4j-mcp",
      "env": {
        "NEO4J_URI": "neo4j+s://your-instance.databases.neo4j.io",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "your-password",
        "NEO4J_DATABASE": "neo4j",
        "NEO4J_READ_ONLY": "true"
      }
    }
  }
}
```

- Replace credentials with your own instance
- `NEO4J_READ_ONLY=true` is the safe default for exploration
- Verify in Cursor: **Settings → Tools & Integrations → MCP tools** — neo4j should show as connected
- Ref: [neo4j.com/docs/mcp/current/installation](https://neo4j.com/docs/mcp/current/installation/)

---

## 0.4 — Smoke test (15 min)

Three checks that validate the full toolchain:

1. **MCP works** — In Cursor Agent mode, ask: *"List all node labels and relationship types in my Neo4j instance."* Expect a schema response.
2. **Cross-validation works** — Ask the same Cypher question in Cursor and in Gemini (or your chosen LLM). Note the differences.
3. **MD reflex works** — Save both outputs in a `notes/day0-smoke-test.md` file.

All three pass → you're operational for any PoC.
