# CampusQuery AI – Intelligent Campus Q&A and Document Assistant

CampusQuery AI is a backend-driven information retrieval system designed to answer campus-related queries and extract insights from uploaded documents. It combines OCR, embedding-based retrieval, and LLM-powered response generation to provide accurate, context-aware answers with source references.

The system solves the problem of fragmented campus information and inefficient document search by enabling users to query structured and unstructured data through a unified interface.

---

## System Overview

The system follows a Retrieval-Augmented Generation (RAG) pipeline:
User Query → Embedding → Vector Search → Context Retrieval → LLM → Response + Sources


For document ingestion:


Document Upload → Parsing → Chunking → Embedding → Vector Storage → Retrieval

---

## Core Features

### Campus Q&A System
Answers campus-related queries using embedding-based retrieval instead of relying purely on LLM memory.

### Document-Based Question Answering
Supports PDF, DOCX, TXT, and scanned documents. Extracts and indexes content for semantic search.

### Highlight-to-Query Interaction
Allows users to highlight text in a document and generate context-aware follow-up queries.

### Source Referencing
Each response includes references to the exact document chunks used during retrieval.

### Scalable Backend
Built using FastAPI with modular services for ingestion, retrieval, and response generation.

---

## How It Works

### 1. Document Ingestion
- PDFs and DOCX parsed using PyMuPDF
- Scanned files processed using Tesseract OCR
- Extracted text is cleaned and normalized

### 2. Text Chunking
- Documents split into chunks (300–500 tokens)
- Overlapping chunks preserve context

### 3. Embedding Generation
- Each chunk converted into vector embeddings
- Captures semantic meaning instead of keywords

### 4. Vector Storage
- Stored in FAISS (local) or Pinecone (cloud)
- Enables fast similarity search

### 5. Query Processing
- User query converted into embedding
- Top-k relevant chunks retrieved

### 6. Response Generation
- Retrieved context passed to LLM
- LLM generates grounded response

### 7. Source Attribution
- Response includes references to source chunks

---

## Tech Stack

### Backend
- Python
- FastAPI

### AI/ML
- LLM APIs (Gemini / OpenAI)
- LangChain
- Hugging Face (optional)

### Document Processing
- PyMuPDF
- Tesseract OCR
- Pandas

### Vector Database
- FAISS
- Pinecone

### Frontend
- React.js / Streamlit

### Deployment
- Docker (optional)
- Render / AWS / Local

---

## Project Structure
backend/
│── app.py
│── routes/
│── services/
│ ├── ingestion.py
│ ├── retrieval.py
│ ├── llm_pipeline.py
│── utils/
│ ├── text_processing.py
│ ├── ocr.py

data/
│── documents/
│── embeddings/

frontend/
│── (React or Streamlit app)

---

## Setup Instructions

### 1. Clone Repository
git clone <repo-url>
cd CampusQuery-AI

### 2. Create Virtual Environment

python -m venv venv


Activate:
Linux / Mac

source venv/bin/activate

Windows

venv\Scripts\activate


### 3. Install Dependencies

pip install -r requirements.txt


### 4. Configure Environment Variables
Create a `.env` file:

GEMINI_API_KEY=your_api_key


### 5. Run Application

python app.py


### 6. Access

http://localhost:5000


---

## Usage

- Ask campus-related queries through UI or API
- Upload documents and query them
- Highlight text to generate contextual queries
- Get answers with source references

---

## Key Design Decisions

- Retrieval-Augmented Generation to reduce hallucination
- Chunk-based document processing for better accuracy
- Embedding-based semantic search instead of keyword matching
- OCR integration for real-world document handling

---

## Performance Considerations

- Vector indexing for fast retrieval
- Batch embedding during ingestion
- Caching for repeated queries
- Optimized chunk size for retrieval accuracy

---

## Limitations

- OCR accuracy depends on image quality
- Retrieval depends on embedding quality
- Poor chunking can reduce accuracy

---

## Future Improvements

- Fine-tuned domain-specific embeddings
- Improved OCR preprocessing
- Multi-language support
- Role-based access control

---

## Contribution


git checkout -b feature-name
git commit -m "Add feature"
git push origin feature-name


Create a Pull Request.

---

## License

MIT License
