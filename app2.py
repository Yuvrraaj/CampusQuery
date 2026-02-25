from flask import Flask, render_template, request, jsonify, send_from_directory, abort, redirect
from flask_cors import CORS
import os
import sys
import threading
import time
from typing import Dict, Any, List  # Added List import
import logging

# Add the directory containing a.py to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import from your enhanced a.py
from a import (
    UniversityDocumentProcessor,
    UniversityQueryProcessor,
    AnalysisResponse,
    UNIVERSITY_DOCS_DIR,
    PROCESSED_DOCS_FILE
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Enable CORS
CORS(app, resources={
    r"/docs/*": {"origins": "*"},
    r"/api/*": {"origins": "*"},
    r"/static/*": {"origins": "*"}
})

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CampusQueryWebApp:
    def __init__(self):
        self.document_processor = UniversityDocumentProcessor()
        self.query_processor = UniversityQueryProcessor()
        self.system_ready = False
        self.initialization_status = "Starting..."
        self.document_count = 0
        self.last_result = None
        self.last_query = None
        self.initialize_system()
    
    def initialize_system(self):
        def init_thread():
            try:
                self.initialization_status = "Loading university documents (offline)..."
                
                # Use the correct method name from a.py
                documents = self.document_processor.load_and_process_documents()
                self.document_count = len(documents)
                
                if not documents:
                    self.initialization_status = "No documents found"
                    logger.warning(f"No documents found in {UNIVERSITY_DOCS_DIR}")
                    self.system_ready = True  # Still mark as ready for testing
                else:
                    self.initialization_status = f"Initializing search system with {len(documents)} chunks (NO API calls)..."
                    self.query_processor.initialize_system(documents)
                    self.system_ready = True
                    self.initialization_status = "System ready! All indexing done offline."
                
                logger.info("CampusQuery system initialized successfully with ZERO API calls for indexing")
                
            except Exception as e:
                self.initialization_status = f"Initialization failed: {str(e)}"
                logger.error(f"System initialization failed: {e}")
                import traceback
                traceback.print_exc()
        
        threading.Thread(target=init_thread, daemon=True).start()
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "ready": self.system_ready,
            "status": self.initialization_status,
            "document_count": self.document_count,
            "has_documents": self.document_count > 0
        }
    
    def process_query(self, query: str) -> Dict[str, Any]:
        if not self.system_ready:
            raise ValueError("System not ready")
        
        try:
            result = self.query_processor.process_query(query)
            self.last_result = result
            self.last_query = query
            
            # Prepare response data with enhanced sources
            response_data = {
                "answer": result.answer,
                "detailed_answer": "",  # Empty - generated on demand
                "justification": result.justification,
                "key_points": result.key_points,
                "document_references": result.document_references,
                "sources": [],
                "applicable_sections": result.applicable_sections,
                "query": query,
                "confidence_score": result.confidence_score,
                "follow_up_suggestions": self._generate_follow_up_suggestions(query, result)
            }
            
            for source in result.sources:
                source_data = {
                    "source_id": source.get("source_id", ""),
                    "filename": source.get("filename", "Unknown"),
                    "filepath": source.get("filepath", ""),
                    "content_preview": source.get("content_preview", ""),
                    "content_snippet": source.get("content_snippet", ""),
                    "relevance": source.get("relevance", 0.0),
                    "chunk_info": source.get("chunk_info", ""),
                    "keywords": source.get("keywords", [])
                }
                response_data["sources"].append(source_data)
            
            return response_data
            
        except Exception as e:
            logger.error(f"Query processing error: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _generate_follow_up_suggestions(self, query: str, result: AnalysisResponse) -> List[str]:
        """Generate intelligent follow-up question suggestions"""
        suggestions = []
        query_lower = query.lower()
        
        # Define follow-up mappings
        follow_up_map = {
            'facilities': [
                "What are the library facilities at VIT-AP?",
                "Tell me about the hostel facilities",
                "What sports facilities are available?",
                "What are the laboratory facilities?"
            ],
            'campus': [
                "What is the campus size?",
                "How many buildings are there on campus?",
                "What facilities are available on campus?",
                "Tell me about campus life at VIT-AP"
            ],
            'programs': [
                "What are the admission requirements for these programs?",
                "What is the fee structure for these programs?",
                "What are the career opportunities after these programs?",
                "What is the curriculum for specific programs?"
            ],
            'admission': [
                "What documents are required for admission?",
                "What is the admission process timeline?",
                "What are the eligibility criteria?",
                "Are there any entrance exams required?"
            ],
            'fees': [
                "What scholarships are available?",
                "What is the payment schedule?",
                "Are there any additional fees?",
                "What are the hostel fees?"
            ],
            'scholarship': [
                "What are the eligibility criteria for scholarships?",
                "How to apply for scholarships?",
                "What documents are needed for scholarships?",
                "When is the scholarship application deadline?"
            ],
            'hostel': [
                "What are the hostel rules and regulations?",
                "What facilities are provided in hostels?",
                "What is the hostel fee structure?",
                "How to book a hostel room?"
            ],
            'course': [
                "What are the course requirements?",
                "How many credits is this course?",
                "Who teaches this course?",
                "What are the prerequisites?"
            ]
        }
        
        # Find relevant suggestions based on query
        for key, suggestions_list in follow_up_map.items():
            if key in query_lower:
                suggestions.extend(suggestions_list[:2])  # Add up to 2 suggestions per category
        
        # Add general suggestions if no specific ones found
        if not suggestions:
            suggestions = [
                "What are the admission requirements?",
                "Tell me about the campus facilities",
                "What programs does VIT-AP offer?",
                "What scholarships are available?"
            ]
        
        return suggestions[:3]  # Return max 3 suggestions
    
    def generate_detailed_explanation(self, query: str = None) -> str:
        """Generate detailed explanation on demand"""
        if not self.system_ready or not self.last_result:
            raise ValueError("No query result available")
        
        query_to_use = query or self.last_query
        if not query_to_use:
            raise ValueError("No query available")
        
        # Find relevant docs for context
        relevant_docs = self.query_processor.search_relevant_content(query_to_use, k=5)
        
        context = "\n\n".join([
            f"Document: {doc.metadata.get('filename', 'Unknown')}\nContent: {doc.content[:1000]}..."
            for doc in relevant_docs[:5]
        ])
        
        return self.query_processor.generate_detailed_explanation(query_to_use, context)

# Initialize the app
campus_query_app = CampusQueryWebApp()

# Routes
@app.route('/')
def dashboard():
    """Dashboard page"""
    return render_template('dashboard.html') if os.path.exists('templates/dashboard.html') else redirect('/assistant')

@app.route('/assistant')
def assistant():
    """Main assistant interface"""
    return render_template('index.html') if os.path.exists('templates/index.html') else enhanced_interface()

def enhanced_interface():
    """Enhanced web interface with follow-up questions and document highlighting"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎓 VIT-AP University Assistant</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', system-ui, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container { 
                max-width: 1200px; 
                margin: 0 auto; 
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #1e3a8a 0%, #7c3aed 100%);
                color: white;
                padding: 2rem;
                text-align: center;
            }
            .header h1 { font-size: 2rem; margin-bottom: 0.5rem; }
            .header p { opacity: 0.9; }
            .content { padding: 2rem; }
            .status-box { 
                background: #f0f9ff; 
                padding: 1rem; 
                border-radius: 10px; 
                margin-bottom: 1.5rem;
                border-left: 4px solid #0ea5e9;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .status-icon { 
                width: 12px; 
                height: 12px; 
                border-radius: 50%; 
                background: #ef4444; 
            }
            .status-icon.ready { background: #10b981; }
            textarea { 
                width: 100%; 
                height: 120px; 
                padding: 1rem; 
                border: 2px solid #e5e7eb; 
                border-radius: 10px; 
                font-family: inherit;
                font-size: 16px;
                resize: vertical;
                outline: none;
                transition: border-color 0.3s;
            }
            textarea:focus { border-color: #3b82f6; }
            .button-group { 
                display: flex; 
                gap: 10px; 
                margin-top: 1rem; 
                flex-wrap: wrap;
            }
            button { 
                background: #3b82f6; 
                color: white; 
                padding: 12px 24px; 
                border: none; 
                border-radius: 8px; 
                cursor: pointer; 
                font-size: 16px;
                font-weight: 600;
                transition: all 0.3s;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            button:hover { background: #2563eb; transform: translateY(-2px); }
            button:disabled { background: #9ca3af; cursor: not-allowed; transform: none; }
            .btn-secondary { background: #6b7280; }
            .btn-secondary:hover { background: #4b5563; }
            .result-box { 
                margin-top: 2rem;
                padding: 1.5rem; 
                background: #f8fafc; 
                border-radius: 10px; 
                border-left: 4px solid #3b82f6; 
                display: none;
            }
            .result-box h3 { color: #1e40af; margin-bottom: 1rem; }
            .answer { line-height: 1.6; margin-bottom: 1rem; }
            .answer strong { color: #1e40af; }
            .meta-info { 
                margin-top: 1rem; 
                padding-top: 1rem; 
                border-top: 1px solid #e5e7eb;
                font-size: 14px;
                color: #6b7280;
                display: flex;
                gap: 2rem;
                flex-wrap: wrap;
            }
            .loading { 
                display: inline-flex;
                align-items: center;
                gap: 8px;
            }
            .spinner { 
                width: 16px; 
                height: 16px; 
                border: 2px solid #ffffff30; 
                border-top: 2px solid #fff; 
                border-radius: 50%; 
                animation: spin 1s linear infinite; 
            }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            .sample-questions {
                margin-top: 1.5rem;
            }
            .sample-questions h3 {
                color: #374151;
                margin-bottom: 1rem;
            }
            .sample-btn {
                display: block;
                width: 100%;
                text-align: left;
                background: #f3f4f6;
                color: #374151;
                padding: 10px 15px;
                margin: 5px 0;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
            }
            .sample-btn:hover {
                background: #e5e7eb;
                border-color: #9ca3af;
            }
            
            /* Enhanced Features */
            .follow-up-questions {
                margin-top: 1rem;
                padding: 1rem;
                background: #ecfdf5;
                border-radius: 8px;
                border-left: 4px solid #10b981;
            }
            .follow-up-questions h4 {
                color: #065f46;
                margin-bottom: 0.5rem;
                font-size: 14px;
                font-weight: 600;
            }
            .follow-up-btn {
                display: inline-block;
                background: #10b981;
                color: white;
                padding: 6px 12px;
                margin: 3px;
                border-radius: 16px;
                font-size: 12px;
                text-decoration: none;
                cursor: pointer;
                border: none;
            }
            .follow-up-btn:hover {
                background: #059669;
            }
            
            .sources-section {
                margin-top: 1.5rem;
                padding: 1rem;
                background: #fefce8;
                border-radius: 8px;
                border-left: 4px solid #eab308;
            }
            .sources-section h4 {
                color: #92400e;
                margin-bottom: 1rem;
                font-size: 16px;
            }
            .source-item {
                background: white;
                padding: 1rem;
                margin: 0.5rem 0;
                border-radius: 6px;
                border: 1px solid #e5e7eb;
                cursor: pointer;
                transition: all 0.3s;
            }
            .source-item:hover {
                border-color: #3b82f6;
                transform: translateX(5px);
            }
            .source-filename {
                font-weight: 600;
                color: #1e40af;
                margin-bottom: 0.5rem;
            }
            .source-preview {
                font-size: 14px;
                color: #6b7280;
                line-height: 1.4;
            }
            .source-meta {
                font-size: 12px;
                color: #9ca3af;
                margin-top: 0.5rem;
                display: flex;
                justify-content: space-between;
            }
            
            .detailed-explanation {
                margin-top: 1rem;
                display: none;
            }
            .detailed-content {
                background: #f8fafc;
                padding: 1.5rem;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
                line-height: 1.6;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎓 VIT-AP University Assistant</h1>
                <p>Enhanced with intelligent search and follow-up questions</p>
            </div>
            
            <div class="content">
                <div class="status-box" id="statusBox">
                    <div class="status-icon" id="statusIcon"></div>
                    <div>
                        <strong>System Status:</strong> <span id="statusText">Loading system...</span>
                        <br><small id="statusDetails">Please wait while we initialize the document index</small>
                    </div>
                </div>
                
                <textarea id="query" placeholder="Ask your question about VIT-AP University here...\\n\\nExample: What are the campus facilities available at VIT-AP University?"></textarea>
                
                <div class="button-group">
                    <button id="askBtn" onclick="askQuestion()" disabled>
                        <span>💬</span> Get Answer
                    </button>
                    <button class="btn-secondary" onclick="clearQuery()">
                        <span>🗑️</span> Clear
                    </button>
                    <button class="btn-secondary" onclick="rebuildIndex()">
                        <span>🔄</span> Rebuild Index
                    </button>
                </div>
                
                <div class="sample-questions">
                    <h3>💡 Sample Questions:</h3>
                    <button class="sample-btn" onclick="setQuery(this.textContent)">What are the campus facilities available at VIT-AP University?</button>
                    <button class="sample-btn" onclick="setQuery(this.textContent)">What programs does VIT-AP University offer?</button>
                    <button class="sample-btn" onclick="setQuery(this.textContent)">What are the admission requirements for VIT-AP?</button>
                    <button class="sample-btn" onclick="setQuery(this.textContent)">What is the fee structure at VIT-AP University?</button>
                    <button class="sample-btn" onclick="setQuery(this.textContent)">What scholarships are available at VIT-AP?</button>
                    <button class="sample-btn" onclick="setQuery(this.textContent)">Tell me about the hostel facilities at VIT-AP</button>
                </div>
                
                <div id="result" class="result-box"></div>
            </div>
        </div>
        
        <script>
            let systemReady = false;
            let currentResult = null;
            
            function checkStatus() {
                fetch('/api/status')
                    .then(response => response.json())
                    .then(data => {
                        const statusIcon = document.getElementById('statusIcon');
                        const statusText = document.getElementById('statusText');
                        const statusDetails = document.getElementById('statusDetails');
                        const askBtn = document.getElementById('askBtn');
                        
                        statusText.textContent = data.status;
                        statusDetails.textContent = `Documents loaded: ${data.document_count}`;
                        systemReady = data.ready;
                        
                        if (systemReady) {
                            statusIcon.classList.add('ready');
                            askBtn.disabled = false;
                        } else {
                            statusIcon.classList.remove('ready');
                            askBtn.disabled = true;
                            setTimeout(checkStatus, 2000);
                        }
                    })
                    .catch(error => {
                        document.getElementById('statusText').textContent = 'Error checking system';
                        setTimeout(checkStatus, 5000);
                    });
            }
            
            function setQuery(text) {
                document.getElementById('query').value = text;
            }
            
            function askQuestion() {
                if (!systemReady) {
                    alert('⚠️ System not ready yet. Please wait...');
                    return;
                }
                
                const query = document.getElementById('query').value.trim();
                if (!query) {
                    alert('📝 Please enter a question.');
                    return;
                }
                
                const askBtn = document.getElementById('askBtn');
                const resultBox = document.getElementById('result');
                
                // Show loading state
                askBtn.innerHTML = '<div class="loading"><div class="spinner"></div>Processing...</div>';
                askBtn.disabled = true;
                resultBox.innerHTML = '<div class="loading"><div class="spinner"></div>Searching through university documents...</div>';
                resultBox.style.display = 'block';
                
                fetch('/api/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query })
                })
                .then(response => response.json())
                .then(data => {
                    currentResult = data;
                    if (data.error) {
                        resultBox.innerHTML = `
                            <h3>❌ Error</h3>
                            <p style="color: #dc2626;">${data.error}</p>
                        `;
                    } else {
                        displayResults(data);
                    }
                })
                .catch(error => {
                    resultBox.innerHTML = `
                        <h3>❌ Error</h3>
                        <p style="color: #dc2626;">Failed to process query. Please try again.</p>
                    `;
                })
                .finally(() => {
                    askBtn.innerHTML = '<span>💬</span> Get Answer';
                    askBtn.disabled = false;
                });
            }
            
            function displayResults(data) {
                const resultBox = document.getElementById('result');
                const answer = data.answer.replace(/\\n/g, '<br>').replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
                
                let html = `
                    <h3>💡 Answer</h3>
                    <div class="answer">${answer}</div>
                    
                    <div class="meta-info">
                        <span><strong>Confidence:</strong> ${(data.confidence_score * 100).toFixed(1)}%</span>
                        <span><strong>Sources:</strong> ${data.sources.length} documents</span>
                        <span><strong>References:</strong> ${data.document_references.join(', ')}</span>
                    </div>
                `;
                
                // Add follow-up questions
                if (data.follow_up_suggestions && data.follow_up_suggestions.length > 0) {
                    html += `
                        <div class="follow-up-questions">
                            <h4>🔍 Related Questions You Might Ask:</h4>
                    `;
                    data.follow_up_suggestions.forEach(suggestion => {
                        html += `<button class="follow-up-btn" onclick="setQuery('${suggestion}'); askQuestion();">${suggestion}</button>`;
                    });
                    html += '</div>';
                }
                
                // Add detailed explanation button
                html += `
                    <div style="margin-top: 1rem;">
                        <button class="btn-secondary" onclick="toggleDetailedExplanation()">
                            <span>📖</span> Show Detailed Explanation
                        </button>
                    </div>
                    
                    <div class="detailed-explanation" id="detailedExplanation">
                        <div class="detailed-content" id="detailedContent">
                            Loading detailed explanation...
                        </div>
                    </div>
                `;
                
                // Add sources section
                if (data.sources && data.sources.length > 0) {
                    html += `
                        <div class="sources-section">
                            <h4>📚 Reference Documents</h4>
                    `;
                    data.sources.forEach((source, index) => {
                        const keywords = source.keywords ? source.keywords.join(', ') : '';
                        html += `
                            <div class="source-item" onclick="viewDocumentHighlight('${source.filename}', \`${source.content_snippet}\`)">
                                <div class="source-filename">📄 ${source.filename}</div>
                                <div class="source-preview">${source.content_preview}</div>
                                <div class="source-meta">
                                    <span>${source.chunk_info}</span>
                                    <span>Relevance: ${(source.relevance * 100).toFixed(0)}%</span>
                                </div>
                                ${keywords ? `<div style="font-size: 11px; color: #9ca3af; margin-top: 0.25rem;">Keywords: ${keywords}</div>` : ''}
                            </div>
                        `;
                    });
                    html += '</div>';
                }
                
                resultBox.innerHTML = html;
            }
            
            function toggleDetailedExplanation() {
                const detailedDiv = document.getElementById('detailedExplanation');
                const detailedContent = document.getElementById('detailedContent');
                
                if (detailedDiv.style.display === 'none' || !detailedDiv.style.display) {
                    detailedDiv.style.display = 'block';
                    
                    // Fetch detailed explanation
                    fetch('/api/detailed-explanation', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query: currentResult.query })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.detailed_answer) {
                            detailedContent.innerHTML = data.detailed_answer.replace(/\\n/g, '<br>').replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
                        } else {
                            detailedContent.innerHTML = 'Error loading detailed explanation.';
                        }
                    })
                    .catch(error => {
                        detailedContent.innerHTML = 'Error loading detailed explanation.';
                    });
                } else {
                    detailedDiv.style.display = 'none';
                }
            }
            
            function viewDocumentHighlight(filename, snippet) {
                // Enhanced document highlighting
                const url = `/docs/${encodeURIComponent(filename)}`;
                
                // Show modal with highlighted content instead of alert
                const modal = document.createElement('div');
                modal.style.cssText = `
                    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                    background: rgba(0,0,0,0.8); display: flex; align-items: center;
                    justify-content: center; z-index: 1000;
                `;
                modal.innerHTML = `
                    <div style="background: white; padding: 2rem; border-radius: 10px; max-width: 80%; max-height: 80%; overflow-y: auto;">
                        <h3 style="color: #1e40af; margin-bottom: 1rem;">📄 ${filename}</h3>
                        <div style="background: #f8fafc; padding: 1rem; border-radius: 6px; line-height: 1.6; margin-bottom: 1rem;">
                            <strong>Relevant excerpt:</strong><br><br>
                            "${snippet}"
                        </div>
                        <div style="display: flex; gap: 10px; justify-content: flex-end;">
                            <button onclick="window.open('${url}', '_blank')" style="background: #3b82f6; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer;">
                                Open Full Document
                            </button>
                            <button onclick="this.closest('div').remove()" style="background: #6b7280; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer;">
                                Close
                            </button>
                        </div>
                    </div>
                `;
                
                // Click outside to close
                modal.addEventListener('click', function(e) {
                    if (e.target === modal) {
                        modal.remove();
                    }
                });
                
                document.body.appendChild(modal);
            }
            
            function clearQuery() {
                document.getElementById('query').value = '';
                document.getElementById('result').style.display = 'none';
                currentResult = null;
            }
            
            function rebuildIndex() {
                if (!confirm('🔄 This will rebuild the document index.\\nThis may take a few minutes. Continue?')) {
                    return;
                }
                
                fetch('/api/rebuild', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    alert('✅ ' + (data.message || data.error));
                    if (data.message) {
                        systemReady = false;
                        document.getElementById('askBtn').disabled = true;
                        checkStatus();
                    }
                })
                .catch(error => {
                    alert('❌ Failed to rebuild index');
                });
            }
            
            // Start status checking
            checkStatus();
            
            // Allow Ctrl+Enter to submit
            document.getElementById('query').addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && e.ctrlKey) {
                    askQuestion();
                }
            });
        </script>
    </body>
    </html>
    '''

@app.route('/docs/<filename>')
def serve_document(filename):
    try:
        if '..' in filename or filename.startswith('/'):
            abort(404)
        
        docs_dir = os.path.abspath(UNIVERSITY_DOCS_DIR)
        file_path = os.path.join(docs_dir, filename)
        
        if not os.path.isfile(file_path):
            abort(404)
        
        logger.info(f"Serving document: {filename}")
        response = send_from_directory(docs_dir, filename, as_attachment=False)
        
        if filename.lower().endswith('.pdf'):
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
            response.headers['Access-Control-Allow-Origin'] = '*'
        
        return response
        
    except Exception as e:
        logger.error(f"Error serving document {filename}: {e}")
        abort(404)

@app.route('/api/status')
def api_status():
    return jsonify(campus_query_app.get_status())

@app.route('/api/query', methods=['POST'])
def api_query():
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "No query provided"}), 400
        
        query = data['query'].strip()
        if not query:
            return jsonify({"error": "Empty query"}), 400
        
        if not campus_query_app.system_ready:
            return jsonify({"error": "System not ready"}), 503
        
        result = campus_query_app.process_query(query)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"API query error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/detailed-explanation', methods=['POST'])
def api_detailed_explanation():
    try:
        data = request.get_json()
        query = data.get('query') if data else None
        
        if not campus_query_app.system_ready:
            return jsonify({"error": "System not ready"}), 503
        
        detailed_answer = campus_query_app.generate_detailed_explanation(query)
        
        return jsonify({
            "detailed_answer": detailed_answer,
            "query": query or campus_query_app.last_query
        })
        
    except Exception as e:
        logger.error(f"Detailed explanation error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/rebuild', methods=['POST'])
def api_rebuild():
    try:
        campus_query_app.system_ready = False
        campus_query_app.initialization_status = "Rebuilding index offline..."
        
        # Delete cached processed documents to force rebuild
        if os.path.exists(PROCESSED_DOCS_FILE):
            os.remove(PROCESSED_DOCS_FILE)
            logger.info("Deleted processed documents cache")
        
        campus_query_app.initialize_system()
        return jsonify({"message": "Index rebuild started (offline processing)"})
        
    except Exception as e:
        logger.error(f"Rebuild error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    return app.response_class(status=404)

if __name__ == '__main__':
    # Ensure required directories exist
    os.makedirs(UNIVERSITY_DOCS_DIR, exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    print("🎓 Enhanced CampusQuery Web Server Starting...")
    print(f"📁 Documents directory: {UNIVERSITY_DOCS_DIR}")
    print(f"🌐 Server will be available at: http://localhost:5000")
    print(f"📄 PDFs accessible at: http://localhost:5000/docs/filename.pdf")
    print("💡 Enhanced with better search and follow-up questions!")
    
    # Check if documents exist
    if os.path.exists(UNIVERSITY_DOCS_DIR):
        doc_files = [f for f in os.listdir(UNIVERSITY_DOCS_DIR) if f.endswith(('.pdf', '.docx', '.txt'))]
        print(f"📚 Found {len(doc_files)} document files")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
