from flask import Flask, render_template, request, jsonify, send_from_directory, abort
from flask_cors import CORS
import os
import sys
import threading
import time
from typing import Dict, Any
import logging

# Add the directory containing uni.py to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import from your enhanced uni.py
from uni import (
    UniversityDocumentProcessor,
    UniversityQueryProcessor,
    AnalysisResponse,
    UNIVERSITY_DOCS_DIR,
    VECTOR_STORE_DIR
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Enable CORS for PDF serving
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
        self.initialize_system()

    def initialize_system(self):
        def init_thread():
            try:
                self.initialization_status = "Loading university documents..."
                documents = self.document_processor.load_all_university_documents()
                self.document_count = len(documents)

                if not documents:
                    self.initialization_status = "No documents found - Web search enabled"
                    logger.warning(f"No documents found in {UNIVERSITY_DOCS_DIR}")
                else:
                    self.initialization_status = f"Processing {len(documents)} document chunks..."

                self.query_processor.initialize_system(documents)
                self.system_ready = True
                self.initialization_status = "System ready!"
                logger.info("CampusQuery system initialized successfully")

            except Exception as e:
                self.initialization_status = f"Initialization failed: {str(e)}"
                logger.error(f"System initialization failed: {e}")

        threading.Thread(target=init_thread, daemon=True).start()

    def get_status(self) -> Dict[str, Any]:
        return {
            "ready": self.system_ready,
            "status": self.initialization_status,
            "document_count": self.document_count,
            "has_documents": self.document_count > 0,
            "web_search_enabled": True
        }

    def process_query(self, query: str) -> Dict[str, Any]:
        if not self.system_ready:
            raise ValueError("System not ready")

        try:
            result = self.query_processor.process_query(query)
            self.last_result = result

            response_data = {
                "answer": result.answer,
                "detailed_answer": result.detailed_answer,
                "justification": result.justification,
                "key_points": result.key_points,
                "document_references": result.document_references,
                "sources": [],
                "applicable_sections": result.applicable_sections,
                "query": query
            }

            for source in result.sources:
                source_data = {
                    "source_id": source.get("source_id", ""),
                    "filename": source.get("filename", "Unknown"),
                    "filepath": source.get("filepath", ""),
                    "content_preview": source.get("content_preview", ""),
                    "content_snippet": source.get("content_snippet", ""),
                    "relevance": source.get("relevance", 0.0),
                    "is_web_result": not source.get("filepath") or "Web Search" in source.get("filename", "")
                }
                response_data["sources"].append(source_data)

            return response_data

        except Exception as e:
            logger.error(f"Query processing error: {e}")
            raise

# Initialize the app
campus_query_app = CampusQueryWebApp()

# Routes
@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/assistant')
def assistant():
    return render_template('index.html')

# Enhanced PDF serving route with proper headers
@app.route('/docs/<path:filename>')
def serve_document(filename):
    try:
        if '..' in filename or filename.startswith('/'):
            logger.warning(f"Blocked potentially malicious file request: {filename}")
            abort(404)
        
        docs_dir = os.path.abspath(UNIVERSITY_DOCS_DIR)
        file_path = os.path.join(docs_dir, filename)
        
        if not os.path.isfile(file_path):
            logger.warning(f"File not found: {file_path}")
            abort(404)
        
        logger.info(f"Serving document: {filename}")
        
        response = send_from_directory(docs_dir, filename, as_attachment=False)
        
        if filename.lower().endswith('.pdf'):
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['Cache-Control'] = 'public, max-age=3600'
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['Access-Control-Allow-Origin'] = '*'
        
        return response
        
    except Exception as e:
        logger.error(f"Error serving document {filename}: {e}")
        abort(404)

# Follow-up question endpoint
@app.route('/api/followup', methods=['POST'])
def api_followup():
    try:
        data = request.get_json()
        if not data or 'selected_text' not in data:
            return jsonify({"error": "No selected text provided"}), 400
        
        selected_text = data['selected_text'].strip()
        context = data.get('context', '')
        document_name = data.get('document_name', '')
        
        if not selected_text:
            return jsonify({"error": "Empty selected text"}), 400
        
        if not campus_query_app.system_ready:
            return jsonify({"error": "System not ready"}), 503
        
        question_prompt = f"""
        Based on this selected text from the university document "{document_name}": 
        
        "{selected_text}"
        
        Context: {context}
        
        Generate a natural, specific follow-up question that would help a student understand this content better. 
        The question should be:
        1. Directly related to the selected text
        2. Practical and useful for students
        3. Clear and specific
        4. Encourage deeper understanding
        
        Respond with just the question, nothing else.
        """
        
        model_client = campus_query_app.query_processor.model_client
        follow_up_question = model_client.generate_content(question_prompt)
        
        return jsonify({
            "question": follow_up_question,
            "selected_text": selected_text,
            "document_name": document_name
        })
        
    except Exception as e:
        logger.error(f"Follow-up question generation error: {e}")
        return jsonify({"error": str(e)}), 500

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

@app.route('/api/rebuild')
def api_rebuild():
    try:
        campus_query_app.system_ready = False
        campus_query_app.initialization_status = "Rebuilding index..."
        campus_query_app.initialize_system()
        return jsonify({"message": "Index rebuild started"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/export')
def api_export():
    if not campus_query_app.last_result:
        return jsonify({"error": "No result to export"}), 400

    try:
        from datetime import datetime
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "query": getattr(campus_query_app.last_result, 'query', ''),
            "answer": campus_query_app.last_result.answer,
            "detailed_answer": campus_query_app.last_result.detailed_answer,
            "justification": campus_query_app.last_result.justification,
            "sources": campus_query_app.last_result.document_references
        }
        return jsonify(export_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    return app.response_class(status=404)

if __name__ == '__main__':
    os.makedirs(UNIVERSITY_DOCS_DIR, exist_ok=True)
    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)

    print("🎓 CampusQuery Web Server Starting...")
    print(f"📁 Documents directory: {UNIVERSITY_DOCS_DIR}")
    print(f"🌐 Server will be available at: http://localhost:5000")
    print(f"📄 PDFs accessible at: http://localhost:5000/docs/filename.pdf")

    app.run(debug=True, host='0.0.0.0', port=5000)
