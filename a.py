# a.py
from flask import Flask, render_template_string, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
import threading
import time
from typing import Dict, Any
import logging
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from university_system import get_ultra_premium_system, initialize_ultra_premium_system, config

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vit-ap-assistant-2025-ultra-secure'
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024

CORS(app, resources={r"/*": {"origins": "*"}})

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

class CampusQueryApp:
    def __init__(self):
        self.system = None
        self.system_ready = False
        self.initialization_status = "Starting system..."
        self.document_count = 0
        self.query_count = 0
        self.successful_queries = 0
        self.init_lock = threading.Lock()
        
        self.initialize_system()
    
    def initialize_system(self):
        def init_thread():
            try:
                with self.init_lock:
                    self.initialization_status = "Loading documents..."
                    logger.info("Starting system initialization")
                    
                    success = initialize_ultra_premium_system(config.FORCE_REBUILD)
                    
                    if success:
                        self.system = get_ultra_premium_system()
                        self.document_count = len(self.system.documents)
                        self.system_ready = True
                        self.initialization_status = f"Ready! {self.document_count} documents loaded"
                        logger.info(f"✓ System initialized with {self.document_count} documents")
                    else:
                        self.initialization_status = "Initialization failed"
                        logger.error("System initialization failed")
                        
            except Exception as e:
                self.initialization_status = f"Error: {str(e)}"
                logger.error(f"Initialization error: {e}")
                logger.error(traceback.format_exc())
        
        threading.Thread(target=init_thread, daemon=True).start()
    
    def get_status(self) -> Dict[str, Any]:
        with self.init_lock:
            actual_doc_count = self.document_count
            if self.system and hasattr(self.system, 'documents'):
                actual_doc_count = len(self.system.documents)
            
            return {
                "ready": self.system_ready and actual_doc_count > 0,
                "status": self.initialization_status,
                "document_count": actual_doc_count,
                "query_count": self.query_count,
                "successful_queries": self.successful_queries,
                "success_rate": (self.successful_queries / max(self.query_count, 1)) * 100
            }
    
    def process_query(self, query: str) -> Dict[str, Any]:
        if not self.system_ready or not self.system:
            raise ValueError("System not ready. Please wait for initialization to complete.")
        
        start_time = time.time()
        
        try:
            result = self.system.process_query_ultra_premium(query)
            self.query_count += 1
            self.successful_queries += 1
            
            response_time = time.time() - start_time
            
            response_data = {
                "answer": result.answer,
                "justification": result.justification,
                "key_points": result.key_points,
                "document_references": result.document_references,
                "sources": result.sources,
                "applicable_sections": result.applicable_sections,
                "query": query,
                "confidence_score": result.confidence_score,
                "quality_score": result.quality_score,
                "follow_up_questions": result.follow_up_questions,
                "processing_time": response_time
            }
            
            logger.info(f"✓ Query processed: '{query[:50]}...' ({response_time:.2f}s)")
            return response_data
            
        except Exception as e:
            self.query_count += 1
            logger.error(f"Query processing error: {e}")
            logger.error(traceback.format_exc())
            raise

campus_app = CampusQueryApp()

# Complete working HTML
COMPLETE_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VIT-AP University Assistant</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container { max-width: 1400px; margin: 0 auto; }
        
        .header {
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .header h1 {
            color: #2563eb;
            font-size: 2.5rem;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .header-subtitle { color: #6b7280; font-size: 1.1rem; }
        
        .status-box {
            background: #f0f9ff;
            padding: 20px;
            border-radius: 12px;
            border-left: 5px solid #2563eb;
            margin-top: 20px;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #dc2626;
            margin-right: 10px;
            animation: pulse 2s infinite;
        }
        
        .status-indicator.ready {
            background: #16a34a;
            animation: none;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .panel {
            background: white;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .panel h3 {
            color: #1f2937;
            margin-bottom: 20px;
            font-size: 1.5rem;
        }
        
        .query-input {
            width: 100%;
            min-height: 150px;
            padding: 15px;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            font-size: 16px;
            resize: vertical;
            font-family: inherit;
            transition: border-color 0.3s;
        }
        
        .query-input:focus {
            outline: none;
            border-color: #2563eb;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }
        
        .btn {
            background: #2563eb;
            color: white;
            padding: 14px 28px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 15px;
            margin-right: 10px;
            transition: all 0.3s;
        }
        
        .btn:hover:not(:disabled) {
            background: #1e40af;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(37, 99, 235, 0.3);
        }
        
        .btn:disabled {
            background: #9ca3af;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-secondary {
            background: #6b7280;
        }
        
        .btn-secondary:hover {
            background: #4b5563;
        }
        
        .sample-btn {
            display: block;
            width: 100%;
            text-align: left;
            background: #f9fafb;
            color: #374151;
            padding: 15px;
            margin: 10px 0;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }
        
        .sample-btn:hover {
            background: #2563eb;
            color: white;
            border-color: #2563eb;
            transform: translateX(8px);
        }
        
        .result-container {
            background: white;
            border-radius: 16px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            display: none;
            animation: slideIn 0.5s ease-out;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .result-header {
            border-bottom: 3px solid #e5e7eb;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .result-title {
            color: #2563eb;
            font-size: 2rem;
            margin-bottom: 15px;
        }
        
        .metrics {
            display: flex;
            gap: 30px;
            flex-wrap: wrap;
        }
        
        .metric {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #6b7280;
            font-size: 14px;
        }
        
        .metric strong {
            color: #1f2937;
        }
        
        .answer-content {
            line-height: 1.9;
            color: #374151;
            margin-bottom: 30px;
            white-space: pre-wrap;
            font-size: 1.1rem;
        }
        
        .key-points {
            background: #eff6ff;
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 30px;
        }
        
        .key-points h3 {
            color: #1e40af;
            margin-bottom: 15px;
        }
        
        .key-points ul {
            list-style: none;
        }
        
        .key-points li {
            padding: 10px 0;
            padding-left: 30px;
            position: relative;
            color: #374151;
        }
        
        .key-points li:before {
            content: "✓";
            position: absolute;
            left: 0;
            color: #2563eb;
            font-weight: bold;
            font-size: 1.2rem;
        }
        
        .sources-section {
            background: #f9fafb;
            padding: 30px;
            border-radius: 12px;
            margin-top: 30px;
        }
        
        .sources-section h3 {
            color: #1f2937;
            margin-bottom: 20px;
        }
        
        .source-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin: 15px 0;
            border-left: 5px solid #2563eb;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }
        
        .source-card:hover {
            transform: translateX(5px);
        }
        
        .source-card-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 15px;
        }
        
        .source-filename {
            font-weight: bold;
            color: #1f2937;
            font-size: 1.1rem;
        }
        
        .view-pdf-btn {
            background: #2563eb;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            transition: background 0.3s;
        }
        
        .view-pdf-btn:hover {
            background: #1e40af;
        }
        
        .citation-box {
            background: #fef3c7;
            border: 2px solid #fbbf24;
            border-radius: 8px;
            padding: 15px;
            margin-top: 10px;
            font-size: 14px;
            color: #92400e;
        }
        
        .citation-label {
            font-weight: bold;
            color: #78350f;
            margin-bottom: 5px;
        }
        
        .followup-section {
            margin-top: 30px;
        }
        
        .followup-section h3 {
            color: #1f2937;
            margin-bottom: 15px;
        }
        
        .followup-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }
        
        .followup-btn {
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            border: 2px solid #bfdbfe;
            color: #1e40af;
            padding: 15px;
            border-radius: 10px;
            cursor: pointer;
            text-align: left;
            transition: all 0.3s;
            font-size: 14px;
        }
        
        .followup-btn:hover {
            background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
            border-color: #2563eb;
            transform: scale(1.02);
        }
        
        .loading {
            text-align: center;
            padding: 60px;
            color: #6b7280;
        }
        
        .spinner {
            border: 4px solid #f3f4f6;
            border-top: 4px solid #2563eb;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .error-box {
            background: #fee2e2;
            border-left: 5px solid #dc2626;
            padding: 20px;
            border-radius: 10px;
            color: #991b1b;
        }
        
        .error-box strong {
            display: block;
            margin-bottom: 10px;
            font-size: 1.1rem;
        }
        
        .modal {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            padding: 20px;
            animation: fadeIn 0.3s;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .modal-content {
            background: white;
            border-radius: 16px;
            max-width: 1200px;
            max-height: 90vh;
            margin: auto;
            display: flex;
            flex-direction: column;
            position: relative;
            top: 50%;
            transform: translateY(-50%);
        }
        
        .modal-header {
            padding: 25px;
            border-bottom: 2px solid #e5e7eb;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .modal-title {
            font-size: 1.5rem;
            color: #1f2937;
            font-weight: bold;
        }
        
        .close-btn {
            background: none;
            border: none;
            font-size: 2rem;
            color: #6b7280;
            cursor: pointer;
            padding: 0;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            transition: all 0.3s;
        }
        
        .close-btn:hover {
            background: #f3f4f6;
            color: #1f2937;
        }
        
        .modal-body {
            padding: 25px;
            overflow-y: auto;
            flex: 1;
        }
        
        .highlight-box {
            background: #fef3c7;
            border: 3px solid #fbbf24;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .highlight-box h4 {
            color: #78350f;
            margin-bottom: 10px;
        }
        
        .pdf-preview {
            background: #f3f4f6;
            padding: 40px;
            border-radius: 10px;
            text-align: center;
            min-height: 300px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        
        .pdf-icon {
            width: 80px;
            height: 80px;
            margin-bottom: 20px;
            color: #6b7280;
        }
        
        .open-pdf-btn {
            background: #2563eb;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 20px;
            text-decoration: none;
            display: inline-block;
            transition: background 0.3s;
        }
        
        .open-pdf-btn:hover {
            background: #1e40af;
        }
        
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            
            .metrics {
                flex-direction: column;
                gap: 15px;
            }
            
            .followup-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <span style="font-size: 2.5rem;">🎓</span>
                VIT-AP University Assistant
            </h1>
            <p class="header-subtitle">Ultra-Premium AI-Powered Information System with Source Citations</p>
            
            <div class="status-box">
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    <span class="status-indicator" id="statusIndicator"></span>
                    <span id="statusText" style="font-weight: 600; font-size: 1.1rem;">Initializing system...</span>
                </div>
                <div class="metrics">
                    <div class="metric">
                        <span>📄</span>
                        <span>Documents: <strong id="docCount">0</strong></span>
                    </div>
                    <div class="metric">
                        <span>💬</span>
                        <span>Queries: <strong id="queryCount">0</strong></span>
                    </div>
                    <div class="metric">
                        <span>📈</span>
                        <span>Success Rate: <strong id="successRate">0%</strong></span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="panel">
                <h3>🔍 Ask Your Question</h3>
                
                <textarea 
                    id="queryInput" 
                    class="query-input" 
                    placeholder="Ask anything about VIT-AP University...

Examples:
- What are the admission requirements?
- What programs are offered at VIT-AP?
- What is the fee structure?
- What facilities are available on campus?
- Tell me about hostel accommodation
- What scholarships are available?"
                ></textarea>
                
                <button id="askBtn" class="btn" onclick="processQuery()" disabled>
                    Ask Question
                </button>
                <button class="btn btn-secondary" onclick="clearQuery()">
                    Clear
                </button>
            </div>
            
            <div class="panel">
                <h3>📚 Sample Questions</h3>
                <button class="sample-btn" onclick="askSampleQuestion(this.textContent.trim())">What are the admission requirements for VIT-AP?</button>
                <button class="sample-btn" onclick="askSampleQuestion(this.textContent.trim())">What undergraduate programs are offered?</button>
                <button class="sample-btn" onclick="askSampleQuestion(this.textContent.trim())">What is the fee structure for B.Tech programs?</button>
                <button class="sample-btn" onclick="askSampleQuestion(this.textContent.trim())">What facilities are available on campus?</button>
                <button class="sample-btn" onclick="askSampleQuestion(this.textContent.trim())">Tell me about hostel facilities and accommodation</button>
                <button class="sample-btn" onclick="askSampleQuestion(this.textContent.trim())">What scholarship opportunities are available?</button>
            </div>
        </div>
        
        <div id="resultContainer" class="result-container"></div>
    </div>
    
    <div id="pdfModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title" id="modalTitle">Document Viewer</h2>
                <button class="close-btn" onclick="closePDFModal()">×</button>
            </div>
            <div class="modal-body" id="modalBody">
                </div>
        </div>
    </div>
    
    <script>
        let systemReady = false;
        let statusCheckCount = 0;
        let statusCheckInterval = null;
        
        // Check system status
        function checkStatus() {
            console.log('[Status Check]', statusCheckCount);
            
            fetch('/api/status')
                .then(r => {
                    if (!r.ok) throw new Error(`HTTP ${r.status}`);
                    return r.json();
                })
                .then(data => {
                    console.log('[Status Response]', data);
                    
                    document.getElementById('statusText').textContent = data.status;
                    document.getElementById('docCount').textContent = data.document_count || 0;
                    document.getElementById('queryCount').textContent = data.query_count || 0;
                    document.getElementById('successRate').textContent = (data.success_rate || 0).toFixed(1) + '%';
                    
                    const indicator = document.getElementById('statusIndicator');
                    const askBtn = document.getElementById('askBtn');
                    
                    // Check if ready
                    if (data.ready && data.document_count > 0) {
                        systemReady = true;
                        indicator.classList.add('ready');
                        askBtn.disabled = false;
                        console.log('✓ SYSTEM READY - Button enabled!');
                        
                        // Stop checking
                        if (statusCheckInterval) {
                            clearInterval(statusCheckInterval);
                            statusCheckInterval = null;
                        }
                    } else {
                        systemReady = false;
                        indicator.classList.remove('ready');
                        askBtn.disabled = true;
                        console.log('System not ready, will retry...');
                    }
                })
                .catch(error => {
                    console.error('[Status Error]', error);
                });
        }
        
        function askSampleQuestion(text) {
            document.getElementById('queryInput').value = text;
            processQuery();
        }
        
        function clearQuery() {
            document.getElementById('queryInput').value = '';
            const result = document.getElementById('resultContainer');
            if (result) result.style.display = 'none';
        }
        
        function processQuery() {
            if (!systemReady) {
                alert('⏳ System is still initializing. Please wait a moment...');
                return;
            }
            
            const query = document.getElementById('queryInput').value.trim();
            if (!query) {
                alert('Please enter a question');
                return;
            }
            
            const askBtn = document.getElementById('askBtn');
            const resultContainer = document.getElementById('resultContainer');
            
            askBtn.disabled = true;
            askBtn.textContent = 'Processing...';
            
            resultContainer.innerHTML = '<div class="loading"><div class="spinner"></div><p style="font-size: 1.2rem;">Analyzing your question with AI...</p></div>';
            resultContainer.style.display = 'block';
            
            // Scroll to results
            resultContainer.scrollIntoView({ behavior: 'smooth' });
            
            console.log('[Query] Sending:', query);
            
            fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query })
            })
            .then(r => {
                if (!r.ok) throw new Error(`HTTP ${r.status}`);
                return r.json();
            })
            .then(data => {
                console.log('[Answer] Received');
                if (data.error) {
                    showError(data.error);
                } else {
                    displayResults(data);
                }
                checkStatus(); // Refresh status
            })
            .catch(error => {
                console.error('[Query Error]', error);
                showError('Network error: ' + error.message);
            })
            .finally(() => {
                askBtn.disabled = !systemReady;
                askBtn.textContent = 'Ask Question';
            });
        }
        
        function displayResults(data) {
            let html = `
                <div class="result-header">
                    <h2 class="result-title">Answer</h2>
                    <div class="metrics">
                        <div class="metric">
                            <span style="color: #16a34a;">✓</span>
                            <span>Confidence: <strong>${(data.confidence_score * 100).toFixed(1)}%</strong></span>
                        </div>
                        <div class="metric">
                            <span style="color: #2563eb;">📊</span>
                            <span>Quality: <strong>${(data.quality_score * 100).toFixed(1)}%</strong></span>
                        </div>
                        <div class="metric">
                            <span style="color: #7c3aed;">⏱️</span>
                            <span>Time: <strong>${data.processing_time.toFixed(2)}s</strong></span>
                        </div>
                    </div>
                </div>

                <div class="answer-content">${escapeHtml(data.answer).replace(/\n/g, '<br>')}</div>
            `;

            if (data.key_points && data.key_points.length > 0) {
                html += '<div class="key-points"><h3>📌 Key Points</h3><ul>';
                data.key_points.forEach(point => {
                    html += `<li>${escapeHtml(point)}</li>`;
                });
                html += '</ul></div>';
            }

            if (data.sources && data.sources.length > 0) {
                html += '<div class="sources-section">';
                html += `<h3>📄 Sources & Citations (${data.sources.length})</h3>`;
                data.sources.forEach((source, i) => {
                    const sourceJSON = JSON.stringify(source).replace(/'/g, '&#39;');
                    html += `
                        <div class="source-card">
                            <div class="source-card-header">
                                <div class="source-filename">${escapeHtml(source.filename)}</div>
                                <button class="view-pdf-btn" onclick='openPDFViewer(${sourceJSON})'>
                                    🔍 View PDF
                                </button>
                            </div>
                            <div style="color: #6b7280; font-size: 14px; margin-bottom: 10px;">
                                Relevance: <strong style="color: #2563eb;">${(source.relevance_score * 100).toFixed(0)}%</strong>
                                ${source.page_number ? ` | Page: ${source.page_number}` : ''}
                            </div>
                            <div class="citation-box">
                                <div class="citation-label">📌 Citation from document:</div>
                                <div>${escapeHtml(source.content_preview.substring(0, 400))}...</div>
                            </div>
                        </div>
                    `;
                });
                html += '</div>';
            }

            if (data.follow_up_questions && data.follow_up_questions.length > 0) {
                html += '<div class="followup-section">';
                html += '<h3>💡 Related Questions</h3>';
                html += '<div class="followup-grid">';
                data.follow_up_questions.forEach(q => {
                    const escaped = escapeHtml(q).replace(/'/g, '&#39;');
                    html += `<button class="followup-btn" onclick="document.getElementById('queryInput').value='${escaped}'; processQuery();">${escapeHtml(q)}</button>`;
                });
                html += '</div></div>';
            }

            document.getElementById('resultContainer').innerHTML = html;
        }
        
        function showError(error) {
            document.getElementById('resultContainer').innerHTML = `
                <div class="error-box">
                    <strong>❌ Error</strong>
                    <div>${escapeHtml(error)}</div>
                </div>
            `;
        }
        
        function openPDFViewer(source) {
            document.getElementById('modalTitle').textContent = source.filename;
            document.getElementById('modalBody').innerHTML = `
                <div class="highlight-box">
                    <h4>📌 Highlighted Citation:</h4>
                    <p>${escapeHtml(source.content_preview)}</p>
                </div>
                <div class="pdf-preview">
                    <svg class="pdf-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <p style="color: #6b7280; font-size: 1.1rem;">PDF Document: <strong>${escapeHtml(source.filename)}</strong></p>
                    <p style="color: #9ca3af; margin-top: 10px;">The citation above shows the exact text used for this answer</p>
                    <a href="/docs/${encodeURIComponent(source.filename)}" target="_blank" class="open-pdf-btn">
                        📄 Open Full PDF in New Tab
                    </a>
                </div>
            `;
            document.getElementById('pdfModal').style.display = 'block';
        }
        
        function closePDFModal() {
            document.getElementById('pdfModal').style.display = 'none';
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Close modal on outside click
        window.onclick = function(event) {
            const modal = document.getElementById('pdfModal');
            if (event.target === modal) {
                closePDFModal();
            }
        }
        
        // Keyboard shortcuts
        document.getElementById('queryInput').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                processQuery();
            }
        });
        
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closePDFModal();
            }
        });
        
        // Initialize - check status immediately and repeatedly
        console.log('=== VIT-AP Assistant Interface Loaded ===');
        checkStatus();
        
        // Set up interval to check every 2 seconds until ready
        statusCheckInterval = setInterval(function() {
            if (!systemReady) {
                statusCheckCount++;
                checkStatus();
                if (statusCheckCount > 60) {
                    clearInterval(statusCheckInterval);
                    console.error('Status check timeout');
                }
            }
        }, 2000);
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(COMPLETE_HTML)

@app.route('/api/status')
def api_status():
    try:
        status = campus_app.get_status()
        logger.info(f"Status request: ready={status['ready']}, docs={status['document_count']}")
        return jsonify(status)
    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({
            "ready": False, 
            "status": f"Error: {str(e)}", 
            "document_count": 0,
            "query_count": 0,
            "successful_queries": 0,
            "success_rate": 0
        }), 500

@app.route('/api/query', methods=['POST'])
def api_query():
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "No query provided"}), 400
        
        query = data['query'].strip()
        if not query:
            return jsonify({"error": "Empty query"}), 400
        
        if not campus_app.system_ready:
            return jsonify({"error": "System is still initializing. Please wait..."}), 503
        
        result = campus_app.process_query(query)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Query API error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/docs/<path:filename>')
def serve_document(filename):
    try:
        if '..' in filename or filename.startswith('/'):
            return "Invalid filename", 404
        
        docs_dir = os.path.abspath(config.UNIVERSITY_DOCS_DIR)
        file_path = os.path.join(docs_dir, filename)
        
        if not os.path.isfile(file_path) or not file_path.startswith(docs_dir):
            return "File not found", 404
        
        return send_from_directory(docs_dir, filename)
    except Exception as e:
        logger.error(f"Document serve error: {e}")
        return "Error serving document", 404

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    os.makedirs(config.UNIVERSITY_DOCS_DIR, exist_ok=True)
    os.makedirs('./persistent_data', exist_ok=True)
    
    print("=" * 80)
    print("🎓 VIT-AP UNIVERSITY ASSISTANT - ULTRA-PREMIUM SYSTEM")
    print("=" * 80)
    print(f"📁 Documents Directory: {config.UNIVERSITY_DOCS_DIR}")
    print(f"🌐 Server URL: http://localhost:5000")
    print(f"🔑 API Keys Configured: {len(config.GEMINI_API_KEYS)}")
    print("=" * 80)
    
    if os.path.exists(config.UNIVERSITY_DOCS_DIR):
        files = [f for f in os.listdir(config.UNIVERSITY_DOCS_DIR) 
                if f.endswith(('.pdf', '.docx', '.txt'))]
        print(f"📚 Found {len(files)} documents")
        if files:
            print(f"📄 Sample files: {', '.join(files[:3])}")
            if len(files) > 3:
                print(f"   ... and {len(files) - 3} more")
    
    print("=" * 80)
    print("🚀 Starting Flask server...")
    print("💡 Open http://localhost:5000 in your browser")
    print("   Wait 5-10 seconds for system initialization")
    print("   Watch for 'System Ready!' status before asking questions")
    print("=" * 80)
    
    app.run(
        debug=False,
        host='0.0.0.0',
        port=5000,
        threaded=True,
        use_reloader=False
    )