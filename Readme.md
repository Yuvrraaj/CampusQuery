# CampusQuery - Intelligent Campus Q&A and Document Assistant

> Ask anything about your campus. Get grounded, source-backed answers - not hallucinations.

---

## The Problem

Campus information is fragmented. Exam schedules live in one PDF, fee structures in another, hostel rules somewhere else entirely. Students either waste time digging through documents or get wrong answers from an LLM that confidently makes things up.

CampusQuery solves both: a RAG pipeline that retrieves actual campus documents before generating any response, so every answer is grounded in what's really there - with the exact source chunk cited and openable.

---

## What This System Does

A full Retrieval-Augmented Generation (RAG) system with two interfaces - a **Flask web app** and a **Tkinter desktop GUI**. Drop university documents (PDFs, DOCX, TXT) into the documents folder. The system chunks them, embeds them locally using `sentence-transformers`, stores vectors in ChromaDB, and serves semantic search over them on every query. If no relevant chunk is found, it falls back to web search rather than hallucinating.

```
University Documents (PDF / DOCX / TXT)
           │
           ▼
   Parse  →  Chunk  →  Embed (local, all-MiniLM-L6-v2)  →  ChromaDB
                                                                │
User Query  ──▶  Query Embedding  ──▶  Top-k Vector Search ────┘
                                              │
                           No match? ──▶  Web Search Fallback
                                              │
                                              ▼
                                    Gemini LLM + Retrieved Context
                                              │
                                              ▼
                           Answer + Key Points + Source References
```

---

## How It Works

### Stage 1 - Document Loading and Parsing

`UniversityDocumentProcessor` handles all document types:
- **PDFs** → parsed via both PyPDF2 and PyMuPDF (fitz). PyMuPDF is used when PyPDF2 extraction is incomplete or produces garbled output
- **DOCX** → extracted via python-docx
- **TXT** → read directly

All extracted text is cleaned and normalised before chunking.

---

### Stage 2 - Chunking

Documents are split using LangChain's `RecursiveCharacterTextSplitter`:

```
CHUNK_SIZE    = 1000 tokens  (configurable)
CHUNK_OVERLAP = 200 tokens   (configurable)
```

Overlap is deliberate - answers that span a chunk boundary are preserved rather than silently lost. Each chunk is stored as a LangChain `Document` with source metadata.

---

### Stage 3 - Local Embedding (No API Quotas)

Embeddings are generated using **`sentence-transformers/all-MiniLM-L6-v2`** running entirely locally - no Gemini embedding API, no quotas, no rate limits. This was a deliberate architectural decision: embedding APIs throttle under load; local inference doesn't.

Embedding dimension: **384**

Embeddings and the vector index are cached to disk on first run:
```
university_vector_store/
├── local_embeddings_cache.pkl   # chunk → embedding cache
└── vector_index.pkl             # FAISS/Chroma index
```

On subsequent runs, the cache is loaded directly - startup is near-instant.

---

### Stage 4 - Vector Storage via ChromaDB

Embedded chunks are stored in a local persistent **ChromaDB** instance (`./university_vector_store` and `./chroma_db`). ChromaDB enables fast cosine similarity search over the full document corpus without any external dependency at query time.

---

### Stage 5 - Query Processing

`UniversityQueryProcessor` handles every incoming query:

1. The query is embedded using the same local `all-MiniLM-L6-v2` model
2. Top-k most similar chunks are retrieved from ChromaDB by cosine similarity
3. Each retrieved chunk carries a relevance score - fuzzy membership functions (`very_low`, `low`, `medium`, `high`, `very_high`) classify relevance before the context is assembled
4. If no chunk exceeds the relevance threshold → **web search fallback** is triggered. The answer is still generated, but the source is marked as a web result, not a document chunk

---

### Stage 6 - Response Generation via Gemini

Retrieved chunks are assembled into a structured context window and passed to **Gemini** (Google Generative AI) for response generation. The LLM cannot invent details absent from the retrieved context.

Every response returns:
- `answer` - concise direct answer
- `detailed_answer` - comprehensive explanation (toggleable in both UIs)
- `key_points` - bullet summary
- `justification` - why this answer was retrieved
- `applicable_sections` - relevant document sections
- `document_references` - source names and chunk indices
- `sources` - list of source objects with relevance scores, file paths, and content snippets

---

### Stage 7 - Highlight-to-Query (Follow-up Generation)

Both interfaces support **highlight-to-query**: select any text in a rendered document or response, and the system generates a contextual follow-up question from that selection. The highlighted text is sent as a query prefix, biasing retrieval toward that document region.

In the web interface: `/api/followup` endpoint accepts `selected_text`, `context`, and `document_name`.
In the desktop GUI: text selection in the PDF viewer triggers the same flow through `EnhancedPDFViewer`.

---

## Two Interfaces

### Flask Web App (`app.py`)

A web server exposing the full pipeline over HTTP with a dashboard UI.

Key routes:

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Main dashboard |
| `/assistant` | GET | Chat interface |
| `/api/query` | POST | Submit a query |
| `/api/followup` | POST | Generate follow-up from selected text |
| `/api/status` | GET | System ready status + document count |
| `/api/export` | GET | Export last result as JSON |
| `/api/cache/status` | GET | Embedding cache size and state |
| `/api/cache/clear` | POST | Wipe and rebuild vector store |
| `/api/system/info` | GET | Platform, memory, embedding model info |
| `/api/soft-computing/stats` | GET | Query metrics, fuzzy scoring stats |
| `/docs/<filename>` | GET | Serve university PDFs inline (CORS-safe) |
| `/health` | GET | Health check |

System initialisation runs in a **background thread** on startup - the web server is available immediately while documents are being indexed. `/api/status` reports readiness state so the frontend can gate queries until the system is ready.

---

### Tkinter Desktop GUI (`uni.py`)

A full desktop application for offline or institutional use. Built on Tkinter with a university-themed colour scheme.

Features:
- **Query input panel** with real-time status bar
- **Answer display** with formatted bold/normal text rendering
- **Detailed explanation toggle** - expandable comprehensive analysis panel
- **Source documents tree** - lists all retrieved sources with relevance scores and file type icons (PDF / Word / Web)
- **Enhanced PDF viewer** (`EnhancedPDFViewer`) - opens PDFs inline with:
  - Full text search with prev/next navigation
  - Auto-highlight of the retrieved snippet on open
  - User highlight creation via text selection
  - Highlight-to-query: select text → generate follow-up question
  - Zoom controls and page navigation
- **Export** - save full answer + sources + justification to `.txt`
- **Web search results** displayed inline alongside document results

---

## Key Design Decisions

**Local embeddings over API embeddings** - `all-MiniLM-L6-v2` runs on CPU with no quota. Gemini embedding API would throttle at scale; local inference doesn't. The tradeoff is a slightly lower-quality embedding model, but for campus document retrieval the difference is negligible.

**Disk-cached embeddings** - First run embeds and caches everything. Subsequent runs skip embedding entirely. For institutions re-deploying without document changes, this makes startup near-instant.

**Web search fallback instead of refusal** - A refusal is useless. If the document corpus doesn't have the answer, web search often will. The fallback source is explicitly flagged in the response so users know where the answer came from.

**Fuzzy relevance scoring** - Retrieved chunks are scored not just by raw cosine similarity but through fuzzy membership functions that produce human-readable relevance tiers. This feeds into the `justification` field so users understand *why* a source was returned.

**Two interfaces from one core** - `uni.py` contains `UniversityDocumentProcessor` and `UniversityQueryProcessor` which are imported by both `app.py` (web) and the `main()` Tkinter entrypoint (desktop). The pipeline logic is written once.

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| Web Backend | Flask, Flask-CORS |
| Desktop GUI | Tkinter |
| LLM | Gemini (Google Generative AI) |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` (local) |
| Orchestration | LangChain |
| Vector Database | ChromaDB |
| Document Parsing | PyMuPDF (fitz), PyPDF2, python-docx |
| Language | Python 3.x |

---

## Project Structure

```
├── app.py                        # Flask web server + all API routes
├── uni.py                        # Core pipeline: processor, query engine, desktop GUI
├── university.py                 # Alternate/legacy pipeline variant
├── insurance_query_system.py     # Domain-specific RAG variant (insurance docs)
├── a.py / app2.py                # Experimental builds
├── config.py                     # API keys and configuration constants
├── requirements.txt
│
├── university_documents/         # Drop your PDFs/DOCX/TXT here
├── university_vector_store/      # Auto-generated: embedding cache + vector index
│   ├── local_embeddings_cache.pkl
│   └── vector_index.pkl
├── chroma_db/                    # ChromaDB persistent store
│
├── templates/                    # Flask HTML templates
│   ├── dashboard.html
│   └── index.html
└── static/                       # CSS, JS assets
    ├── css/
    └── js/
```

---

## Quickstart

```bash
git clone https://github.com/Yuvrraaj/CampusQuery.git
cd CampusQuery

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Create `config.py`:

```python
GEMINI_API_KEY = "your_gemini_api_key_here"
API_RATE_LIMIT = 10
MAX_RETRIES = 3
RETRY_BASE_DELAY = 5
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_CONTEXT_DOCS = 5
CACHE_DIR = "./api_cache"
```

Add university documents:
```
university_documents/
├── academic_calendar.pdf
├── fee_structure.pdf
├── hostel_rules.docx
└── ...
```

**Run web app:**
```bash
python app.py
# → http://localhost:5000
```

**Run desktop GUI:**
```bash
python uni.py
```

First run embeds all documents and caches to disk. Subsequent runs load from cache - startup is fast.

---

## API Reference

**POST `/api/query`**
```json
{ "query": "What is the last date to pay semester fees?" }
```
Returns: `answer`, `detailed_answer`, `key_points`, `justification`, `sources[]`, `document_references[]`

**POST `/api/followup`**
```json
{
  "selected_text": "Students must pay fees before 15th January",
  "context": "Fee Structure document",
  "document_name": "fee_structure.pdf"
}
```
Returns: generated follow-up question string

**GET `/api/status`** - System readiness, document count, embedding type

**GET `/api/system/info`** - Platform, memory, embedding model, document list

**GET `/health`** - Lightweight health check

---

## Limitations

- OCR for scanned PDFs is not currently implemented - only text-layer PDFs are parsed. Scanned documents require a Tesseract preprocessing step before ingestion
- Embedding quality is bounded by `all-MiniLM-L6-v2` - a general-purpose model. A domain-fine-tuned embedding model would improve retrieval precision on campus-specific terminology
- Chunk size is fixed globally - adaptive chunking based on document structure (headings, tables) would improve precision for heavily structured documents like rulebooks or schedules

---

## License

MIT License. See `LICENSE` for details.
