CampusQuery AI – Intelligent Campus Q&A and Document Assistant

CampusQuery AI is a backend-driven information retrieval system designed to answer campus-related queries and extract insights from uploaded documents. It combines OCR, embedding-based retrieval, and LLM-powered response generation to provide accurate, context-aware answers with source references.

The system was built to solve the problem of fragmented campus information and inefficient document search by enabling users to query structured and unstructured data through a unified interface.

System Overview

The system follows a retrieval-augmented generation (RAG) pipeline:

User Query → Embedding → Vector Search → Context Retrieval → LLM Response Generation → Source Referencing

For documents:

Document Upload → Parsing (PDF/DOCX/OCR) → Chunking → Embedding → Vector Storage → Query-based Retrieval

Core Features

Campus Q&A System
The system answers campus-related queries using a retrieval-based approach instead of relying purely on a generative model. Queries are converted into embeddings and matched against stored knowledge to fetch relevant context before generating responses.

Document-Based Question Answering
Users can upload documents (PDF, DOCX, TXT, scanned images). The system extracts text, splits it into chunks, and stores embeddings for semantic retrieval.

Highlight-to-Query Interaction
Users can highlight a portion of a document, which is treated as a query input. The system generates context-aware follow-up questions or explanations based on the selected text.

Source Referencing
Each response includes references to the exact document chunks used during retrieval, ensuring transparency and trust in the output.

Scalable Backend
The backend is designed using FastAPI with modular components for ingestion, retrieval, and response generation, allowing horizontal scaling.

How It Works
Document Ingestion
PDF and DOCX are parsed using PyMuPDF or similar libraries
Scanned documents are processed using Tesseract OCR
Extracted text is cleaned and normalized
Text Chunking
Large documents are split into smaller chunks (typically 300–500 tokens)
Overlapping chunks are used to preserve context
Embedding Generation
Each chunk is converted into a vector representation using embedding models
These vectors capture semantic meaning instead of keyword matching
Vector Storage
Embeddings are stored in a vector database (FAISS or Pinecone)
Enables fast similarity search
Query Processing
User query is converted into an embedding
Top-k similar chunks are retrieved from the vector database
Response Generation
Retrieved context is passed to an LLM
LLM generates a grounded response based only on retrieved content
Source Attribution
The system attaches references to the original chunks used in answering
Tech Stack

Backend
Python
FastAPI

AI/ML
LLM APIs (Gemini / OpenAI)
LangChain (for chaining retrieval and generation)
Hugging Face (optional for embeddings or models)

Document Processing
PyMuPDF
Tesseract OCR
Pandas (for preprocessing where required)

Vector Database
FAISS (local setup)
Pinecone (cloud option)

Frontend
React.js or Streamlit (depending on deployment version)

Deployment
Docker (optional)
Render / AWS / local server

Project Structure (Typical)

backend/

app.py (FastAPI entry point)
routes/ (API endpoints)
services/
ingestion.py
retrieval.py
llm_pipeline.py
utils/
text_processing.py
ocr.py

data/

documents
embeddings

frontend/

React or Streamlit app
Setup Instructions
Clone the repository
Create a virtual environment
python -m venv venv
source venv/bin/activate (Linux/Mac)
venv\Scripts\activate (Windows)
Install dependencies
pip install -r requirements.txt
Set environment variables in .env
GEMINI_API_KEY=your_key
Run the backend
python app.py
Access the application
http://localhost:5000
Usage
Ask campus-related queries directly through the API or UI
Upload documents and query them
Highlight text (UI feature) to trigger contextual queries
Receive responses with source references
Key Design Decisions

Retrieval-Augmented Generation
Instead of relying purely on LLM knowledge, the system retrieves relevant context first, ensuring factual accuracy and reducing hallucinations.

Chunk-Based Processing
Splitting documents into chunks improves retrieval precision and avoids token limits in LLMs.

Embedding-Based Search
Semantic similarity search allows better matching than keyword-based approaches.

OCR Integration
Supports scanned documents, making the system usable for real-world unstructured data.

Performance Considerations
Query latency optimized using vector indexing
Batch embedding used during ingestion
Caching applied for repeated queries
Chunk size tuned for optimal retrieval accuracy
Limitations
OCR accuracy depends on input image quality
Embedding quality affects retrieval relevance
Requires proper chunking strategy for best performance
Future Improvements
Fine-tuned domain-specific embedding models
Better OCR preprocessing for noisy scans
Multi-language support
Role-based access for campus stakeholders
Contribution

Fork the repository
Create a new branch
Commit changes
Push and create a pull request

License

MIT License
