# FinBot Project State

This document provides a comprehensive overview of the current state, architecture, and implementation details of the FinBot system, a multimodal Retrieval-Augmented Generation (RAG) based financial intelligence platform built for Chartered Accountants.

---

## 1. Overall Project Purpose and Architecture

**Purpose**: FinBot is designed to allow Chartered Accountants to interact via natural language with a company's financial corpus. It answers complex financial queries, calculates ratios, analyzes multi-year trends, and summarizes narratives from various document modalities (Excel, PDF, Images, Earnings Calls).

**Architecture Overview**:
The system is divided into a **Next.js frontend** and a **FastAPI backend**. The core intelligence layer uses a multi-agent RAG architecture:
1. **Router Agent**: Classifies queries by intent (Calculation vs. Narrative) and routes them to specific data modalities (Excel, PDF, Concall, Images) using a hybrid LLM/Keyword approach.
2. **Clarifier Agent**: Decomposes complex user queries into focused sub-queries to optimize vector retrieval.
3. **Calculation Agent**: Intercepts calculation queries (e.g., ratios, margins, growth) and computes them using specific formulas and raw data retrieved from Excel chunks.
4. **RAG Synthesizer**: Ingests the top retrieved chunks, calculation traces, and sub-queries to formulate a comprehensive response using GPT-4.1-mini.

---

## 2. Frontend Architecture and Features

**Tech Stack**: Next.js 16.2.6, React 19, Tailwind CSS v4, TypeScript, Recharts, React Markdown.

**Core Components** (`frontend/app/components`):
- **`FinbotDashboard.tsx`**: Main entry point that orchestrates the UI layout.
- **`ChatWindow.tsx` & `InputBar.tsx`**: The core conversational interface where users submit queries and receive AI responses with markdown and LaTeX (math) support.
- **`KPICards.tsx`**: Dynamic, real-time metric cards displaying 4-year trend charts that can be switched by metric and year.
- **`Sidebar.tsx` & `CompanyCard.tsx`**: Navigation layer and company context switcher. Displays live stock prices.
- **`CorpusStatus.tsx` & `UploadModal.tsx`**: UI to manage data ingestion, file uploads, and indexing status.
- **`SessionsRail.tsx`**: Manages the display of past chat sessions and history.
- **`ReportConfigModal.tsx`**: Configuration interface for Custom Report Generation.

---

## 3. Backend Architecture and API Endpoints

**Tech Stack**: FastAPI, Uvicorn, Pydantic, Loguru.

**Core API Routes** (`backend/app/api/routes/`):
- **`/api/v1/companies`**: Manages the active company registry (`companies.json`), fetches KPI data, and company context.
- **`/api/v1/upload`**: Handles multimodal document ingestion (Excel, PDF, audio transcripts). Triggers background chunking and embedding processes.
- **`/api/v1/query`**: The primary endpoint for executing RAG queries. It orchestrates the router, calculation agent, and RAG synthesis pipelines.
- **`/api/v1/sessions`**: Manages the creation, retrieval, and updates of chat histories using SQLite (`sessions.db`).

---

## 4. Session Management and Chat History System

Session management is handled via a SQLite database (`sessions.db`). The `sessions.py` route and `sessions_db.py` logic provide CRUD operations for conversation histories.
- Each session is tied to a specific `company_slug`.
- Chat context and agent traces (citations, calculation steps) are persisted so users can seamlessly resume previous analyses.
- The UI surfaces these through the `SessionsRail` component.

---

## 5. Multimodal Ingestion Pipeline

The backend supports ingestion across four distinct modalities:
1. **Excel Data**: Extracted via `excel_processor.py`. Parses structured financial tables (P&L, Balance Sheet, Cash Flow) into text chunks enriched with `year` and `sheet` metadata.
2. **PDF Documents**: Handled by `pdf_processor.py`. Extracts text from Annual Reports, identifying narrative sections like MD&A and Director's Reports.
3. **Images / Charts**: When `ENABLE_IMAGE_EMBEDDING=true` is set, image pages from PDFs are described using a Vision model (GPT-4o) to create searchable text captions.
4. **Concall / Audio**: Audio transcripts are processed via `ingest_concall.py` to extract management commentary, analyst Q&A, and forward-looking guidance.

---

## 6. Agent Architecture

1. **Router Agent** (`router_agent.py`): Uses an LLM to evaluate the user's question against routing rules (e.g., "H1/quarterly" -> concall, "chart/visuals" -> images). Falls back to a robust keyword heuristic system if the LLM fails.
2. **Calculation Agent** (`calculation_agent.py`): Bypasses standard text generation for math questions. Identifies formulas (e.g., "debt to equity", "EBITDA margin"), retrieves the exact raw metrics from Excel chunks, evaluates the mathematical expression safely using AST, and returns a synthetic "calc context" to the final prompt. Can compute "risk flags" based on predefined thresholds.
3. **Clarifier Agent** (`clarifier_agent.py`): Breaks down complex questions ("Compare revenue and profit growth") into distinct queries to prevent single-vector retrieval bias.
4. **RAG Agent** (`rag.py`): Enforces an input guardrail to block non-financial queries, retrieves multi-source contexts, dynamically balances chunk budgets, and calls the generation LLM.
5. **Report Generation / Builder**: Orchestrates multi-query reports utilizing the underlying RAG pipeline based on configurations passed through `ReportConfigModal.tsx`.

---

## 7. RAG Pipeline and Retrieval Flow

1. **Input Guardrail**: Checks if the query is a valid financial/company question.
2. **Routing**: Identifies `source_types` (excel, pdf, images, concall) and `year`.
3. **Calculation Check**: If it's a known metric ratio/growth, the calculation agent pre-computes the answer and formats it as a high-confidence context chunk.
4. **Decomposition**: Clarifier splits the query into sub-queries.
5. **Embedding & Retrieval**: Sub-queries are embedded and queried against the routed ChromaDB collections.
6. **Budgeting & Ranking**: A `MIN_BUDGET_PER_SOURCE` ensures that dominant sources (like Excel) don't crowd out narrative sources (like Concalls). Chunks are ranked by score and capped (`TOP_K_CHUNKS`).
7. **Synthesis**: GPT-4.1-mini generates the final answer and structured citations based *only* on the provided chunks.

---

## 8. ChromaDB Collections and Data Organization

**Storage Structure**: Vector databases are isolated per company under `chroma_store/{company_slug}/`.
**Collections**:
- `{company_slug}_excel`: Structured numerical data.
- `{company_slug}_pdf_text`: Annual report text and narratives.
- `{company_slug}_images`: Captioned charts, tables, and infographics.
- `{company_slug}_concalls`: Earnings call transcripts.

Metadata is extensively used for filtering (e.g., `year`, `sheet`, `page`, `chunk_type`).

---

## 9. Embedding Models and LLMs Used

- **Generation LLM**: OpenAI GPT-4.1-mini. Chosen for high reasoning capability and fast generation speed.
- **Vision LLM**: OpenAI GPT-4o. Used during ingestion to describe image pages and charts.
- **Embedding Model**: `BAAI/bge-large-en-v1.5`. Runs locally (CPU or GPU) to generate high-quality dense vector representations.
- **Fallback Configurations**: Code contains placeholders for Ollama (`llama3.1:8b`), though OpenAI is the active default.

---

## 10. Evaluation Framework and Benchmark Results

**Evaluation Tooling**: RAGAS metrics are utilized for measuring context relevance, correctness, and faithfulness.
**Current Benchmark (V2.2 - 77 Questions)**:
- **Routing Accuracy**: 92.2%
- **Citation Accuracy**: 94.8%
- **Answer Correctness**: 59.7% (Up from 48.1% initially)
- **RAGAS Faithfulness**: 0.63
- **RAGAS Answer Relevancy**: 0.70

*Note: The bottleneck has been identified as retrieval (chunking quality of PDFs/MD&A tables), not the LLM generation capabilities.*

---

## 11. Docker Architecture

The stack is fully containerized using `docker-compose.yml`.
- **`backend`**: FastAPI app running on port 8000. Mounts local volumes for `chroma_store`, `data`, `logs`, and `sessions.db`. Uses HuggingFace cache volume for embedding models.
- **`frontend`**: Next.js app running on port 3000. Depends on the backend container.
- **Monitoring Containers**: Prometheus, Grafana, Loki, and Promtail (detailed below).
All services communicate over an internal `finbot-network` bridge.

---

## 12. Monitoring Stack

A complete observability stack is defined in `docker-compose.yml` and `monitoring/`:
- **Prometheus** (Port 9090): Scrapes backend metrics (e.g., `chroma_query_latency_seconds`, `openai_call_latency`, `openai_call_count`).
- **Loki** (Port 3100): Centralized log aggregation.
- **Promtail**: Tails the FastAPI JSON logs (`logs/finbot.json`) and ships them to Loki.
- **Grafana** (Port 3001): Visualizes Prometheus metrics and Loki logs via pre-provisioned dashboards.

---

## 13. CI/CD Pipeline and Testing Strategy

- **CI/CD**: Managed via GitHub Actions (`.github/workflows/ci.yml`). Verified by the CI/CD badge in the README.
- **Testing**: A dedicated `tests/` directory contains evaluation scripts, the 77-question benchmark suite, and RAGAS metric validation scripts. Includes automated evaluation pipelines that generate artifacts like `phase_a_baseline_results.md` and `generation_failure_analysis.md`.

---

## 14. Security and Secrets Management

- **Environment Variables**: Managed locally via `.env` files.
- **Secrets Management**: Configuration indicates the use of `.env` for secure secrets injection (e.g., `OPENAI_API_KEY`) in production environments, preventing hardcoded credentials in the repository.

---

## 15. Current Supported Features

- Direct financial lookups across up to 10 years of data.
- Complex ratio and margin calculations via a dedicated deterministic calculation agent.
- Narrative summarization from Annual Reports and Concalls.
- Cross-modal reasoning (e.g., matching a Concall statement with an Excel financial figure).
- Real-time stock price display and interactive 4-year KPI charting.
- Input guardrails preventing non-financial prompt injections.

---

## 16. Known Limitations and Bottlenecks

- **Image Accuracy**: Highly dependent on the quality of the GPT-4o description generated during the ingestion phase.
- **MD&A Table Extraction**: Complex ratio tables within PDF MD&A sections are not perfectly retrieved as structured data due to current chunking limitations.
- **Concall Routing**: The router occasionally misses highly specific quarterly questions.
- **Cross-Year Scope**: Calculations requiring cross-year data depend entirely on the retrieval of all relevant years in a single context window.

---

## 17. Technical Achievements

- **Excel Budget Fix**: Addressed retrieval truncation limits by bypassing standard `top_k` for Excel multi-year queries, significantly increasing data accuracy.
- **Calculation Agent Isolation**: Successfully prevents the LLM from hallucinating math by strictly using AST evaluation on retrieved numerical values.
- **Dynamic Chunk Budgeting**: Implemented a `MIN_BUDGET_PER_SOURCE` to ensure multi-source queries maintain context diversity.

---

## 18. Deployment Architecture

Deployments are designed to be environment-agnostic via Docker. The standard setup involves running `docker-compose up -d`, which spins up the Next.js reverse-proxied frontend, the FastAPI ASGI server, and the entire monitoring telemetry stack in tandem.

---

## 19. File and Folder Structure Overview

```text
FinBot/
├── backend/
│   ├── app/
│   │   ├── api/routes/   # FastAPI Endpoints (companies, upload, query, sessions)
│   │   ├── core/         # Agents (Router, Calc, Clarifier, RAG), Embedder, Chunkers
│   │   ├── db/           # ChromaDB Wrappers, SQLite Session Manager
│   │   └── models/       # Pydantic Schemas
│   ├── chroma_store/     # Persistent Vector DB storage per company
│   ├── data/             # Raw uploaded corpus files
│   ├── logs/             # JSON logs for Promtail
│   ├── companies.json    # Registry of loaded companies and KPI data
│   ├── config.py         # Environment and app configuration
│   └── main.py           # FastAPI Application Entry
├── frontend/
│   ├── app/
│   │   ├── components/   # React/Next.js UI Components (Chat, Sidebar, KPIs)
│   │   └── page.tsx      # Main application view
│   ├── lib/              # API Client utilities
│   └── package.json      # Dependencies and scripts
├── monitoring/
│   ├── grafana/          # Dashboards and provisioning configs
│   ├── loki/             # Loki configuration
│   ├── prometheus/       # Prometheus scrape configurations
│   └── promtail/         # Promtail scraping rules
├── tests/                # Benchmark suites and RAGAS evaluations
├── docker-compose.yml    # Full stack container definition
└── README.md             # Project documentation and benchmark reports
```

---

## 20. Future Improvements

- **Layout-Aware PDF Chunking**: Upgrade PDF chunking strategies to better parse structured MD&A tables and retain column/row relationships.
- **Expanded Calculation Registry**: Add more complex intrinsic valuation models (e.g., DCF components) to the `calculation_agent.py` hardcoded formulas.
- **Multi-Company Testing**: Scale evaluation to ensure the system handles concurrent queries across different companies without data bleeding.
- **Report Generation Agent**: Fully implement the automated deep-dive report generator (currently mapped in the UI).
