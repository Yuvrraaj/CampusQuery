# CampusQuery AI – Intelligent Campus Q&A and Document Assistant

CampusQuery AI is an **AI-powered Q&A and document intelligence platform** designed to provide **instant answers to campus-related queries** and enable **document-based question answering** with **source-referenced responses**.  
Originally deployed at **VIT-AP University**, this platform is accessible to users **from anywhere** and integrates advanced **LLM-based search, embeddings, and OCR-powered document parsing** to make information retrieval seamless.

---

##  Features

- **Campus-Focused Q&A System:**  
  Instantly answer any VIT-AP-related question using a fine-tuned **LLM** with embedded knowledge.

- **Highlight-to-Query Interaction:**  
  Highlight any section of a document to **auto-generate follow-up questions** and dive deeper into context.

- **Document Upload and Retrieval:**  
  Upload PDFs, DOCX, TXT, or scanned documents and get **accurate, citation-based answers**.

- **Source Referencing:**  
  Every response includes references to the **relevant source content** for reliability.

- **Scalable Backend:**  
  Designed with **FastAPI, LangChain, and vector databases** to ensure fast, scalable query resolution.

- **User-Friendly Web Interface:**  
  Accessible platform with a **responsive frontend** for students, faculty, and staff.

---

## 🛠 Tech Stack

- **Languages & Frameworks:** Python, FastAPI, HTML/CSS, JavaScript
- **AI/ML:** OpenAI GPT models, LangChain, Hugging Face Transformers
- **Document Processing:** PyMuPDF, Tesseract OCR, Pandas
- **Vector Search:** FAISS / Pinecone
- **Frontend:** React.js (or Streamlit for rapid prototyping)
- **Deployment:** Docker, Render/Heroku/AWS (optional)

---

🔧 Installation & Setup
1. Clone the Repository
git clone https://github.com/YOUR_USERNAME/CampusQuery-AI.git
cd CampusQuery-AI

2. Create Virtual Environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

3. Install Dependencies
pip install -r requirements.txt

4. Set Up Environment Variables

Create a .env file with your keys:

GEMINI_API_KEY=your_gemini_key

5. Run app.py file.


Access the app at http://localhost:5000.

📘 Usage

Ask campus-related questions directly through the chatbot.

Upload any supported document and ask targeted questions.

Highlight document text to auto-generate context-aware follow-up questions.

Get answers with citations for trust and clarity.

🔥 Key Highlights

Supports multiple document formats (PDF, DOCX, TXT, Scanned Images)

Fast, citation-driven responses for document queries

Scalable architecture using FastAPI and vector search

Tested with 40+ students and faculty at VIT-AP

🤝 Contribution

Contributions are welcome! Here’s how to get started:

Fork this repository

Create a new branch: git checkout -b feature-name

Commit changes: git commit -m 'Added new feature'

Push to the branch: git push origin feature-name

Create a Pull Request

🛡️ License

This project is licensed under the MIT License. See LICENSE for details.

