# 🌿 Agentic Analytics ESG

> ⚠️ **DEMO PROJECT — NOT FOR PRODUCTION USE**
>
> This repository is an exploratory prototype built to evaluate the feasibility of applying agentic AI to ESG data analysis and sustainability reporting workflows, synthetic-data based. It is not production-ready, has not been security-audited, and should not be deployed in any live environment or used with sensitive corporate data without significant further development.

## Example of use
### Chatbot
<img width="1933" height="1304" alt="Captura de pantalla 2026-03-01 a las 17 43 23" src="https://github.com/user-attachments/assets/81108e00-a000-4c04-a501-a858edd61de4" />



### Report

<img width="816" height="1143" alt="Captura de pantalla 2026-03-01 a las 17 47 00" src="https://github.com/user-attachments/assets/fe04328c-4df1-4733-a76f-a912f95400b5" />
<img width="821" height="1027" alt="Captura de pantalla 2026-03-01 a las 17 47 13" src="https://github.com/user-attachments/assets/e85dd07e-dbbb-4ba8-9e4f-7a4ceb2f6ae0" />

---

> 🤖 **A note on development methodology**
>
> This project was built through a combination of **hands-on coding and AI-assisted development** using Claude as a collaborator. The distinction between what was done by the author and what was supported by AI is worth being explicit about.
>
> **What the author did:**
> - Identified the business problem and defined the scope of the solution
> - Designed the overall product concept and user experience
> - Planned the two-agent architecture and defined the responsibility boundary between agents
> - Specified every feature: the agentic query loop, the structured KPI extraction, the dual-format report pipeline, and the carbon footprint measurement layer
> - Applied an MVP mindset throughout — consciously deciding what *not* to build, avoiding over-engineering, and keeping the stack as simple as the problem allowed
> - Directed all development decisions, reviewed every output, and validated the system against real data
> - Brought the sustainability domain expertise that shaped how data is interpreted, what metrics matter, and how results should be communicated
>
> **Where Claude helped:**
> - Implementing functions and patterns the author was unfamiliar with (Jinja2 templating, xhtml2pdf rendering)
> - Introducing packages and libraries that the author had not previously worked with, significantly accelerating the build
> - Making the implementation more efficient and idiomatic than it would have been otherwise
> - Debugging environment and dependency issues across Python versions and package conflicts
>
> This is not a project where AI wrote everything and a human watched. It is a project where a **Data Scientist and Sustainability Specialist** used AI as a highly capable technical collaborator — the same way a senior professional might work with a specialist contractor — while retaining full ownership of the product vision, the architectural decisions, and the domain reasoning.
>
> The core competence demonstrated here is not code. It is knowing what to build, why to build it, and how to scope it so that it solves a real problem without unnecessary complexity.

---

## Overview

Agentic Analytics ESG is a two-agent system that turns raw environmental data stored in a DuckDB database into natural-language analysis and structured PDF sustainability reports — entirely through conversational AI.

It was designed by a **Data Scientist and Sustainability Specialist** with the following philosophy: *the most valuable skill is not writing code, it is understanding what a business actually needs and knowing when a simple solution is better than a sophisticated one.*

This prototype demonstrates that a non-engineering profile can reason about agentic system design, define tool boundaries, specify data contracts between agents, and deliver a working end-to-end product — without writing a single line of code manually.

---

## Architecture

```
User
 │
 ├─── Tab 1: Chat ──────► Analyst Agent
 │                              │
 │                         DuckDB (local)
 │                         Claude Opus (API)
 │                              │
 │                         Natural-language answer
 │
 └─── Tab 2: Report ────► Analyst Agent ──► Reporter Agent ──► PDF + HTML
                               │                   │
                          KPI extraction      Jinja2 template
                          (structured JSON)   xhtml2pdf renderer
```

The system consists of two agents with clearly separated responsibilities:

**Analyst Agent** (`analyst_agent.py`) — owns all data access. Uses Claude's native tool use to query DuckDB iteratively, following a chain-of-thought reasoning loop until it has enough evidence to answer the user's question or produce a structured JSON of KPIs.

**Reporter Agent** (`reporter_agent.py`) — owns all presentation. Receives the structured KPI dict, renders an HTML template via Jinja2, and produces both a browser-quality HTML file and a PDF report.

This division is intentional: adding a third agent to "interpret" results was considered and rejected. A new agent is only justified when it has access to a meaningfully different set of resources or performs a qualitatively different task.

---

## Features

- 💬 **Natural-language ESG chat** — ask questions about electricity consumption, water usage, waste, and renewable self-generation in plain language
- 📊 **Structured KPI extraction** — the agent autonomously queries the database, aggregates data across years, and produces a validated JSON with trends and interpretations
- 📄 **Dual-format report generation** — one click produces both a browser HTML (full CSS design) and a PDF (xhtml2pdf compatible layout)
- 🌱 **Carbon footprint measurement** — every query is measured using token-based API emission estimation (methodology: Anthropic energy efficiency data × US East grid carbon intensity), broken down by phase: chat, KPI extraction, and PDF generation
- 🔒 **Read-only database access** — all DuckDB connections are opened in `read_only=True` mode as a safety measure

---

## Stack

| Layer | Technology |
|---|---|
| LLM | Claude Opus (`claude-opus-4-6`) via Anthropic API |
| Agentic loop | Native tool use (no LangChain, no LlamaIndex) |
| Database | DuckDB loaded from Excel via pandas |
| Templating | Jinja2 |
| PDF rendering | xhtml2pdf |
| Interface | Streamlit |
| Carbon tracking | Token-based estimation (CodeCarbon removed due to macOS `powermetrics` permission requirements) |

No vector databases, no RAG, no embeddings. Complexity was deliberately kept to the minimum required to solve the problem.

---

## Project Structure

```
test_2/
├── python code/
│   ├── analyst_agent.py      # Agent 1 — DuckDB + Claude tool use
│   ├── reporter_agent.py     # Agent 2 — Jinja2 + PDF rendering
│   ├── carbon_tracker.py     # Token-based CO₂ estimation
│   ├── load_data.py          # Excel → DuckDB loader
│   └── check_db.py           # Database verification utility
├── plantilla_informes/
│   ├── informe_browser.html  # Full CSS template for browser
│   └── informe_pdf.html      # xhtml2pdf-compatible template
├── data/
│   └── esg_database.duckdb   # Local database (not committed)
├── excel_file/
│   └── environment_data.xlsx # Source data (not committed)
├── reports/                  # Generated reports output directory
├── app.py                    # Streamlit interface
└── requirements.txt
```

---

## Getting Started

```bash
# 1. Install dependencies
pip install anthropic duckdb pandas openpyxl jinja2 xhtml2pdf streamlit

# 2. Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# 3. Load data from Excel into DuckDB
python "python code/load_data.py"

# 4. Verify the database
python "python code/check_db.py"

# 5. Launch the app
/path/to/your/python -m streamlit run app.py
```

---

## Carbon Footprint Methodology

The emission estimate shown in the interface is calculated as follows:

```
kWh = (input_tokens / 1000) × 0.00017 + (output_tokens / 1000) × 0.00043
g CO₂ = kWh × 385
```

Where:
- `0.00017 kWh / 1k tokens` — estimated energy per input token (Anthropic efficiency data)
- `0.00043 kWh / 1k tokens` — estimated energy per output token
- `385 g CO₂ / kWh` — US East (Virginia) grid carbon intensity, where Anthropic's primary inference infrastructure is located

This is an approximation. It does not account for cooling overhead, network transmission, or Anthropic's renewable energy procurement, all of which would reduce the real-world figure.

---

## Limitations of this Prototype

- The system prompts include hardcoded column names derived from a specific Excel file. A production version would discover schema dynamically.
- There is no conversation memory between sessions. Each chat starts fresh.
- The PDF renderer (xhtml2pdf) has limited CSS support, resulting in a simplified layout compared to the browser version.
- No authentication or access control of any kind.
- Error handling is functional but not production-grade.
- The carbon estimate covers API calls only; local compute is not measured (CodeCarbon was removed due to macOS hardware permission requirements).

---

## Roadmap & Next Steps

The following section outlines the evolution path from this prototype towards a production-grade agentic sustainability intelligence system.

### Near-term (v2)

**Predictive consumption modelling**
Add a machine learning tool — likely a lightweight time-series model (Prophet or XGBoost) trained on historical kWh and water data — exposed as a tool callable by the Analyst Agent. This would allow the agent to answer questions such as *"what is our expected electricity consumption in Q3 based on current trends?"* without any change to the user interface.

**Anomaly detection alerts via Telegram**
Implement a scheduled agent that runs nightly, queries the database for statistical anomalies (e.g., consumption spikes above 2σ), and sends a structured alert to a Telegram channel via Bot API. This transforms the system from reactive (answer questions) to proactive (surface insights automatically).

**Dynamic schema discovery**
Replace hardcoded column names in the system prompt with a startup routine that reads the live schema and injects it at runtime. This makes the agent portable across different Excel structures without code changes.

### Medium-term (v3)

**Multi-tenant data isolation**
Add a company/site layer to the database schema and enforce row-level filtering in all queries based on the authenticated user. Required before any shared deployment.

**Persistent conversation memory**
Implement a lightweight conversation store (SQLite or Redis) so the agent retains context across sessions — e.g., remembering that a user is always interested in the Madrid site, or that a previous anomaly was already investigated.

**Structured output validation**
Add Pydantic models for KPI JSON validation between agents. Currently the JSON schema is enforced only via prompt instructions. A formal contract between agents reduces fragility significantly.

**OpenAI-compatible tool exposure**
Package the Analyst Agent as an OpenAI-compatible function tool, making it callable from ChatGPT's custom GPT interface or any MCP-compatible client. This allows non-technical sustainability teams to query the data directly from tools they already use.

### Advanced agentic engineering (v4+)

**Orchestrator–subagent architecture**
Introduce a top-level Orchestrator Agent that decomposes complex multi-step requests (e.g., *"compare our 2023 and 2024 ESG performance and draft the board summary section of the annual report"*) into subtasks delegated to specialised subagents: Analyst, Forecaster, Writer, and Reviewer. Each subagent has a narrowly scoped tool set, reducing hallucination surface area.

**Human-in-the-loop checkpoints**
For high-stakes outputs (board reports, regulatory filings), add explicit approval gates where the agent pauses, presents its reasoning and data sources, and waits for human confirmation before proceeding. This is standard practice in responsible agentic deployments.

**Guardrails and output evaluation**
Implement an LLM-as-judge evaluation layer that scores each agent output on factual grounding, completeness, and regulatory alignment (GRI, ESRS, TCFD) before it reaches the user. Low-confidence outputs are flagged rather than silently presented.

**Retrieval-augmented regulatory context**
Add a vector store containing the relevant sections of GRI Standards, the European Sustainability Reporting Standards (ESRS), and TCFD recommendations. The Analyst Agent can retrieve and cite the applicable standard when interpreting a KPI, making reports audit-ready.

**Automated data ingestion pipeline**
Replace the manual Excel upload with a scheduled pipeline that pulls invoices and consumption data directly from supplier APIs (energy, water, waste management) and updates the DuckDB database nightly — closing the loop from raw data to insight with no manual intervention.

---

## Author

Designed and directed by a **Data Scientist and Sustainability Specialist** whose focus is on translating environmental and operational challenges into scalable, maintainable data products. Technical implementation via AI-assisted development (vibe coding with Claude).

The core competence demonstrated here is not code — it is product thinking: knowing which problem to solve, how to decompose it into agents with clear responsibilities, what to measure, and when to stop adding complexity.

---

*This project is a personal prototype and is not affiliated with or endorsed by any employer or client.*
