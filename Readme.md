# CampusQuery — Intelligent Campus Q&A and Document Assistant

> Ask anything about your campus. Get grounded, source-backed answers — not hallucinations.

---

## The Problem

Campus information is fragmented. Exam schedules live in one PDF, fee structures in another, hostel rules somewhere else entirely. Students either waste time digging through documents or get wrong answers from an LLM that confidently makes things up.

CampusQuery solves both problems: a RAG pipeline that retrieves actual campus documents before generating any response, so answers are grounded in what's really there — with the source chunk cited.

---

## What This System Does

A full Retrieval-Augmented Generation (RAG) system built on FastAPI and ChromaDB. You ingest campus documents once. After that, any query — typed or highlighted — gets answered by first retrieving the most relevant document chunks via vector similarity search, then passing that context to an LLM for response generation. If no relevant context is found in the vector store, it falls back to web search rather than hallucinating.

```
User Query
    │
    ▼
Query Embedding  ──▶  ChromaDB Vector Search  ──▶  Top-k Chunks Retrieved
                                                          │
                              Web Search Fallback ◀── No relevant context?
                                                          │
                                                          ▼
                                                  LLM (Gemini) + Context
                                                          │
                                                          ▼
                                              Response + Source References
```

---

## How It Works

### Stage 1 — Document Ingestion

Documents are parsed depending on type:
- **PDFs and DOCX** → extracted via PyMuPDF
- **Scanned/image-based documents** → run through Tesseract OCR before text extraction

Raw extracted text is cleaned and normalised before chunking — whitespace artifacts, header/footer repetitions, and encoding noise are stripped at this stage. Dirty input produces dirty embeddings; this step is not optional.

---

### Stage 2 — Chunking Strategy

Documents are split into overlapping chunks of 300–500 tokens. The overlap is deliberate: if an answer spans a chunk boundary, a purely non-overlapping split would lose it. Overlapping chunks ensure continuity across splits so the retrieval step doesn't miss context that straddles boundaries.

Each chunk stores:
- Source document name
- Page / section reference
- Raw text

---

### Stage 3 — Embedding and Vector Storage

Each chunk is converted into a dense vector embedding that captures semantic meaning rather than surface keywords. This means a query like *"when are fees due"* retrieves chunks containing *"payment deadline"* or *"last date of submission"* — exact word match is not required.

Embeddings are stored in **ChromaDB**, a local persistent vector database. ChromaDB enables fast cosine similarity search over the full document corpus without any external API call at retrieval time.

---

### Stage 4 — Query Processing and Retrieval

When a user submits a query:
1. The query is embedded using the same embedding model used during ingestion — this is important, the vector spaces must match
2. A top-k similarity search runs against ChromaDB
3. The k most relevant chunks are returned with their similarity scores

If no chunk crosses the relevance threshold, the system routes to **web search fallback** rather than generating a response from LLM memory alone. This is the core anti-hallucination mechanism.

---

### Stage 5 — Highlight-to-Query

Users can highlight any passage in a rendered document and trigger a contextual query from that selection. The highlighted text is sent as an enriched query prefix, biasing retrieval toward that document region. This is particularly useful for drilling into specific clauses in policy documents or fee structures without re-reading the whole file.

---

### Stage 6 — Response Generation

Retrieved chunks are assembled into a structured context window and passed to Gemini along with the user query. The LLM generates a response that is grounded in the retrieved text — it cannot invent details not present in the chunks.

Every response includes:
- The generated answer
- Source references: document name, chunk index, and the exact passage used

This makes every answer auditable. If the answer is wrong, you can trace exactly which chunk produced it.

---

### Stage 7 — API Layer

All functionality is exposed through a **FastAPI** backend with modular service separation:

- `ingestion.py` — document parsing, chunking, embedding, storage
- `retrieval.py` — query embedding, vector search, fallback routing
- `llm_pipeline.py` — context assembly, Gemini API call, response formatting

The API is stateless at the request level — each query is self-contained. Session context (for multi-turn conversations) is managed client-side and passed back on each request.

---

## Key Design Decisions

**Why RAG over pure LLM?** Campus documents change — fee structures, exam schedules, regulations. An LLM's training data is stale by definition. RAG retrieves from the live document corpus on every query.

**Why ChromaDB?** Local, persistent, no external API dependency for retrieval. Fast enough for a single-institution corpus. Swappable for Pinecone or Weaviate if scale demands it.

**Why web search fallback instead of refusing?** A refusal is useless. If the document corpus doesn't have the answer, a web search often will. The fallback is clearly indicated in the response so users know the source changed.

**Why overlapping chunks?** Information that spans a paragraph boundary gets lost with hard splits. Overlap is the cheapest way to preserve cross-boundary context without more complex hierarchical chunking.

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| Backend API | FastAPI, Python |
| LLM | Gemini (Google) |
| Orchestration | LangChain |
| Vector Database | ChromaDB |
| Document Parsing | PyMuPDF, python-docx |
| OCR | Tesseract |
| Frontend | Flask, HTML/CSS/JS |

---

## Project Structure

```
├── app.py                      # FastAPI application entry point
├── university.py               # Campus Q&A pipeline
├── insurance_query_system.py   # Domain-specific query variant
├── services/
│   ├── ingestion.py            # Parse → chunk → embed → store
│   ├── retrieval.py            # Query embed → vector search → fallback
│   └── llm_pipeline.py         # Context assembly → Gemini → response
├── utils/
│   ├── text_processing.py      # Cleaning, normalisation, chunking
│   └── ocr.py                  # Tesseract wrapper
├── chroma_db/                  # Persisted vector store
├── university_documents/       # Source document corpus
├── templates/                  # Frontend HTML
├── static/                     # CSS, JS
└── requirements.txt
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

Create a `.env` file:

```
GEMINI_API_KEY=your_api_key_here
```

Run:

```bash
python app.py
```

Access at `http://localhost:5000`

---

## Limitations

- OCR accuracy is bounded by scan quality — low-resolution or skewed scans produce degraded chunks that hurt retrieval
- Retrieval quality is directly tied to embedding model quality — a domain-specific embedding model would outperform a general-purpose one on campus-specific terminology
- Chunk size is fixed; adaptive chunking based on document structure (headings, sections) would improve precision for highly structured documents like rulebooks

---

## License

MIT License. See `LICENSE` for details.
