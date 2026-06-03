# FinBot

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
| Dataset | Score | Accuracy |
|---------|-------|----------|
| Excel (structured tables) | 30/30 | **100%** |
| PDF Text (annual reports) | 30/30 | **100%** |
| Concall Transcripts | 21/30 | **70%** |
| Images (chart descriptions) | 8/30 | **26.7%** |
| Cross‑modal (combined) | 23/30 | **76.7%** |
| **Overall (150Q benchmark)** | **112/150** | **74.7%** |

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