# FinBot

![CI/CD Pipeline](https://github.com/gaurangpatil97/FinBot-AI/actions/workflows/ci.yml/badge.svg)

## Project Overview
FinBot is a multimodal Retrieval‑Augmented Generation (RAG) based financial intelligence system built for Chartered Accountants. It enables natural‑language querying of a company's financial information across:
- Excel worksheets (historical KPIs, balance‑sheet tables, etc.)
- Annual Report PDFs (textual sections, tables, footnotes)
- Earnings‑call transcripts (audio‑to‑text)
- Visual chart images (caption generation via vision model)

## Tech Stack
| Layer | Technologies |
|-------|----------------|
| **Frontend** | Next.js, Tailwind CSS, TypeScript |
| **Backend** | FastAPI, Uvicorn |
| **LLM (text)** | GPT‑4.1‑mini via OpenAI |
| **Vision** | GPT‑4o (image descriptions) |
| **Embeddings** | `BAAI/bge-large-en-v1.5` (GPU accelerated) |
| **Vector DB** | ChromaDB |
| **Router** | LLM‑based router with keyword‑fallback logic |

## Current Status & Roadmap
**Phase A (Complete):** Evaluation infrastructure, retrieval baseline, and generation prompt engineering are stable. The core pipeline is validated against the 77-question benchmark.
**Next Steps (Weekend Goals):**
- Report Generation Agent
- Sessions / Chat History
- Second Company testing (scaling beyond Craftsman Automation)

## Supported Query Types
- Direct financial lookups (revenue, profit, EBITDA for any year)
- Ratio calculations (Debt/Equity, EBITDA margin, ROE, Interest Coverage, Cash Conversion)
- Multi-year trend analysis across all available years
- Cross-metric comparisons (e.g. receivables growth vs revenue growth)
- Annual report narrative questions (strategy, MD&A, risk factors, chairman message)
- Management commentary from earnings call transcripts
- Visual chart data from annual report image pages

## Architecture
```
User Query
   │
   ▼
LLM Router ──► Clarifier Agent ──► Decompose into sub‑queries
   │                                      │
   ▼                                      ▼
ChromaDB Collections (Excel, PDF, Images, Concall)
   │                                      │
   ▼                                      ▼
Embedding Retrieval (semantic search)     │
   │                                      │
   └──────────────► GPT‑4.1‑mini ◄───────┘
                │
                ▼
          Response + Citations
```

## Key Features
- **Multi‑source RAG**: Handles Excel, PDF, image, and concall collections
- **Clarifier Agent**: Decomposes complex multi-metric queries into focused sub‑queries for better retrieval
- **Calculation Agent**: Executes formula‑based calculations using a registry of standard financial ratios plus LLM-derived custom formulas
- **Dynamic KPI Cards**: Real‑time metric cards with 4-year trend charts, switchable by metric and year
- **Per‑Company Isolation**: Each company's vector store lives in its own Chroma collection under a company slug
- **Live Stock Price**: Real‑time price fetched from Yahoo Finance for contextual sidebar display

## Project Structure
```
FinBot/
├─ backend/
│   ├─ main.py                  # FastAPI entry point
│   ├─ config.py                # All settings and constants
│   ├─ companies.json           # Active company registry
│   ├─ .env                     # Environment variables
│   ├─ app/
│   │   ├─ api/routes/          # API endpoints
│   │   ├─ core/                # RAG, router, clarifier, calc agent, embedder
│   │   ├─ db/                  # ChromaDB vector store wrappers
│   │   └─ models/              # Pydantic schemas
│   ├─ chroma_store/            # Per-company ChromaDB collections
│   ├─ data/uploads/            # Raw uploaded files per company
│   └─ requirements.txt
├─ frontend/
│   ├─ app/
│   │   ├─ components/          # UI components (KPI cards, charts, sidebar)
│   │   └─ page.tsx             # Main dashboard
│   ├─ lib/                     # API helpers
│   └─ package.json
├─ tests/
│   ├─ questions/               # Benchmark question sets
│   └─ results/                 # Benchmark results
└─ README.md
```

## Setup & Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/gaurangpatil97/Financial-AI-Assisstant.git
   cd FinBot
   ```

2. **Backend**
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

3. **Frontend**
   ```bash
   cd ../frontend
   npm install
   ```

4. **Environment variables** — create a `.env` file at the project root with:
   ```dotenv
   OPENAI_API_KEY=your-openai-key
   TMP_DIR=D:\FinBot\backend\tmp_images
   ENABLE_IMAGE_EMBEDDING=false
   ```

5. **(Optional) GPU** — ensure PyTorch detects your CUDA GPU for faster embedding generation with `BAAI/bge-large-en-v1.5`

## Running the System

**Start backend** (from `backend/` folder):
```bash
python main.py
```

**Start frontend** (from `frontend/` folder):
```bash
npm run dev
```

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

## Data Ingestion
1. Click **Upload Dataset** in the sidebar UI
2. Upload Excel financials, Annual Report PDFs, and earnings call transcripts for a company
3. Click **Generate Embeddings** — the backend will:
   - Extract text from PDFs using `pdfplumber`
   - Describe image pages using GPT-4o (if `ENABLE_IMAGE_EMBEDDING=true`)
   - Generate embeddings using `BAAI/bge-large-en-v1.5`
   - Store vectors in company-specific ChromaDB collections
4. Once ingestion completes the system is ready to answer queries

## Benchmark Results

### V1 — Initial Benchmark (150Q, May 2026)

First benchmark run using 150 questions across 5 sections against Craftsman Automation Ltd.

| Section | Score | Accuracy |
|---------|-------|----------|
| Excel (structured tables) | 30/30 | **100%** |
| PDF Text (annual reports) | 30/30 | **100%** |
| Concall Transcripts | 21/30 | **70%** |
| Images (chart descriptions) | 8/30 | **26.7%** |
| Cross-modal (combined) | 23/30 | **76.7%** |
| **Overall** | **112/150** | **74.7%** |

> ⚠️ V1 scores for Excel and PDF were later found to be inflated due to loose citation matching in the evaluation script. These numbers were not fully trusted.

---

### V2 — Validated Benchmark (77Q, June 2026)

A fresh 77-question benchmark was built from scratch with CA-level forensic questions across all 4 source types plus cross-source questions. Questions were generated independently from the test set to avoid benchmark leakage.

#### Auto-Scored Metrics
| Metric | Score |
|--------|-------|
| Routing Accuracy | 72.7% (56/77) |
| Citation Accuracy | 63.6% (49/77) |
| Answer Correctness | 48.1% raw → **54.5% validated** |
| Answer Relevancy (RAGAS) | 67.4% |
| Context Precision (RAGAS) | 30.9% |
| Avg Latency | 15.36s |

#### Per Section Breakdown
| Section | Routing | Answer Correctness |
|---------|---------|-------------------|
| Excel | 67% | **93%** |
| Cross-source | 73% | **60%** |
| Images | 75% | **44%** |
| PDF Text | 81% | **25%** |
| Concall | 67% | **20%** |

#### Failure Analysis
A full audit of all 40 failures was conducted to separate system quality from evaluation pipeline quality.

| Failure Type | Count | % | Implication |
|---|---|---|---|
| Retrieval failure | 19 | 48% | Router correct, chunks didn't contain answer |
| Routing failure | 14 | 35% | Wrong source selected upstream |
| Scoring failure | 5 | 12% | Evaluator marked correct answers as wrong |
| Generation failure | 2 | 5% | Had right context but wrong answer |

**Key finding:** 83% of failures originated upstream in routing and retrieval. Only 5% were generation failures — meaning the LLM produces correct answers when supplied with relevant context. The language model and prompt engineering are not the bottleneck.

**Validated accuracy:** After correcting 5 evaluator scoring errors, true answer correctness is **54.5%** not 48.1%.

#### Post-Fix Improvements (June 2026)
After targeted fixes to the router and calculation agent:
- Routing accuracy improved for H1/H2/quarterly questions → concall
- Routing accuracy improved for MD&A narrative questions → pdf
- Calculation agent no longer intercepts narrative explanation questions
- 4 previously failing questions now answered correctly

---

### V2.1 — RAGAS Fully Resolved (June 13, 2026)

Note that all 4 RAGAS metrics now return real values (zero NaN rows out of 77) for the first time, after fixing: (a) the V2 schema column-naming mismatch for `ragas==0.3.1`, and (b) rate-limit-induced NaN poisoning of aggregate averages.

**Scores:**
- Faithfulness: 0.6714
- Answer Relevancy: 0.6624
- Context Precision: 0.3303
- Context Recall: 0.2481

*Note explicitly: these scores were computed on data from the eval run before the Excel limit=20 fix, and a rerun with the Excel fix is expected to follow shortly with updated numbers.*

**Excel Limit=20 Fix:**
The `query_collection_all()` chunks now bypass the `top_chunks` limit in `rag.py`. This fixes an Excel multi-year retrieval bug where it was dropping ~10/30 chunks, which caused the Excel answer accuracy to regress from 93% to 73%. The upcoming rerun is expected to show an impact from this fix.

---


### V2.2 — Generation Prompt Improvements (June 13, 2026)

This run incorporates significant fixes to retrieval budgeting and generation prompting, establishing a strong baseline.

#### Auto-Scored Metrics
- **Routing Accuracy:** 72.7% → **92.2%** (lenient)
- **Citation Accuracy:** 63.6% → **94.8%**
- **Answer Correctness:** 49.4% → 57.1% → **59.7%** (following two rounds of generic prompt fixes, no hardcoding)

#### RAGAS Metrics
All 4 RAGAS metrics are now reliably non-NaN:
- **Faithfulness:** 0.63
- **Answer Relevancy:** 0.70
- **Context Precision:** 0.37
- **Context Recall:** 0.30

#### Per Section Breakdown
- **Excel:** 73%
- **Cross-source:** 67%
- **Images:** Improved (Q59-62 routing fix successfully recovered MD&A table questions)
- **Concall & PDF Text:** Improved significantly from the prompt instruction fixes.

#### Key Fixes Implemented
- **Excel limit=20 truncation bug fixed:** `excel_all_chunks` now bypasses generic retrieval limits, ensuring all 10 years of data are provided.
- **Per-source retrieval budgets:** Fixed the issue where a high volume of Excel chunks was evicting relevant concall chunks.
- **PDF top-k reduction:** Reduced from 20 to 8 chunks to minimize noise.
- **Images routing fix:** Resolved an over-triggering issue that misrouted image tables to the PDF collection.
- **Generation Prompt Guardrails:** Added 5 generic instructions to prevent hallucination, enforce strict metric extraction, clarify multi-part questions, and demand explicit reasoning.

#### Known Issues / Next Steps
- **Q16, Q18:** Genuine retrieval gaps (specific figures simply absent from current chunks).
- **Q32, Q40, Q44:** MD&A ratio tables are not retrievable as structured data. This is a chunking/retrieval issue requiring future layout-aware extraction improvements.

### What the Numbers Mean

*Note: The assessments below are based on the V2.0 baseline. The V2.2 updates significantly improved routing, citation, and generation metrics, confirming that retrieval (chunking) remains the primary bottleneck for further improvements.*

| Component | Assessment |
|-----------|------------|
| Excel retrieval | Production-ready (93%) |
| LLM generation quality | Strong — only 2/40 generation failures |
| Routing | Good — fixable with prompt improvements |
| Retrieval (chunking) | Primary bottleneck — quarterly data not in annual chunks |
| Embeddings | Working correctly — Excel 93% proves embedding stack quality |

**Future optimization priority:** Retrieval quality and chunking strategy, not LLM or prompt engineering.

## Sample Queries
```
"What was the revenue growth from FY23 to FY25?"
"Compare employee costs as a percentage of revenue across FY22 to FY25"
"Does receivables growth outpace revenue growth over FY2019-FY2025?"
"What is the company-within-company operational framework mentioned in the FY22 annual report?"
"Calculate the Beneish M-Score DSRI component for FY2025"
"Free cash flow vs dividend payout — did the company pay dividends in years with negative FCF?"
```

## Known Limitations
- Image accuracy depends on GPT-4o description quality during ingestion
- Concall routing misses some quarterly-specific questions
- Cross-year calculations require all relevant data to be embedded
- Currently tested on Craftsman Automation Ltd only — multi-company testing in progress

## Demo Company
**Craftsman Automation Ltd** (NSE: CRAFTSMAN) — pre‑loaded sample data demonstrates end‑to‑end query handling across all modalities.

---
*FinBot is a research prototype built for CA-level financial analysis. Contributions and feedback are welcome.*