from flask import Flask, render_template, request, jsonify, send_from_directory, abort
from flask_cors import CORS
import os
import sys
import threading
import time
from typing import Dict, Any
import logging
import config  # Ensure you have a config.py with GEMINI_API_KEY defined

# Add the directory containing uni.py to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import from your enhanced uni.py (now with FREE local embeddings!)
from uni import (
    UniversityDocumentProcessor,
    UniversityQueryProcessor,
    AnalysisResponse,
    UNIVERSITY_DOCS_DIR,
    VECTOR_STORE_DIR
)

app = Flask(__name__)
app.config['SECRET_KEY'] = config.GEMINI_API_KEY

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
        self.initialization_status = "Starting with FREE local embeddings..."
        self.document_count = 0
        self.last_result = None
        self.initialize_system()

    def initialize_system(self):
        def init_thread():
            try:
                self.initialization_status = "📥 Loading university documents..."
                logger.info("Starting document loading...")
                
                documents = self.document_processor.load_all_university_documents()
                self.document_count = len(documents)
                
                logger.info(f"Loaded {self.document_count} document chunks")

                if not documents:
                    self.initialization_status = "⚠️ No documents found - Web search enabled"
                    logger.warning(f"No documents found in {UNIVERSITY_DOCS_DIR}")
                    # Still initialize system for web search
                    self.query_processor.initialize_system([])
                    self.system_ready = True
                else:
                    self.initialization_status = f"⚡ Processing {len(documents)} chunks with FREE embeddings..."
                    logger.info(f"Initializing vector store with {len(documents)} documents")
                    
                    # Initialize with local embeddings (no quota issues!)
                    self.query_processor.initialize_system(documents)
                    
                    self.system_ready = True
                    self.initialization_status = "✅ System ready! (Using FREE local embeddings - No quotas!)"
                    logger.info("🎉 CampusQuery initialized successfully with local embeddings")

            except Exception as e:
                self.initialization_status = f"❌ Initialization failed: {str(e)}"
                logger.error(f"System initialization failed: {e}")
                import traceback
                logger.error(traceback.format_exc())

        threading.Thread(target=init_thread, daemon=True).start()

    def get_status(self) -> Dict[str, Any]:
        return {
            "ready": self.system_ready,
            "status": self.initialization_status,
            "document_count": self.document_count,
            "has_documents": self.document_count > 0,
            "web_search_enabled": True,
            "embedding_type": "local_free"  # NEW: Indicate we're using free embeddings
        }

    def process_query(self, query: str) -> Dict[str, Any]:
        if not self.system_ready:
            raise ValueError("System not ready")

        try:
            logger.info(f"Processing query: {query}")
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

            logger.info(f"Query processed successfully: {len(response_data['sources'])} sources found")
            return response_data

        except Exception as e:
            logger.error(f"Query processing error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

# Initialize the app
campus_query_app = CampusQueryWebApp()

# Routes
@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/assistant')
def assistant():
    """Assistant interface page"""
    return render_template('index.html')

# Enhanced PDF serving route with proper headers
@app.route('/docs/<path:filename>')
def serve_document(filename):
    """Serve PDF documents with proper CORS headers"""
    try:
        # Security: Prevent directory traversal
        if '..' in filename or filename.startswith('/'):
            logger.warning(f"Blocked potentially malicious file request: {filename}")
            abort(404)
        
        docs_dir = os.path.abspath(UNIVERSITY_DOCS_DIR)
        file_path = os.path.join(docs_dir, filename)
        
        # Check if file exists
        if not os.path.isfile(file_path):
            logger.warning(f"File not found: {file_path}")
            abort(404)
        
        logger.info(f"Serving document: {filename}")
        
        response = send_from_directory(docs_dir, filename, as_attachment=False)
        
        # Set proper headers for PDF viewing
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
    """Generate follow-up question based on selected text"""
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
        
        # Create prompt for follow-up question generation
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
        
        # Use Gemini for text generation (not embeddings - those are local now!)
        model_client = campus_query_app.query_processor.model_client
        follow_up_question = model_client.generate_content(question_prompt)
        
        logger.info(f"Generated follow-up question for document: {document_name}")
        
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
    """Get system status"""
    status = campus_query_app.get_status()
    logger.debug(f"Status requested: {status}")
    return jsonify(status)

@app.route('/api/query', methods=['POST'])
def api_query():
    """Process a user query"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "No query provided"}), 400

        query = data['query'].strip()
        if not query:
            return jsonify({"error": "Empty query"}), 400

        if not campus_query_app.system_ready:
            return jsonify({
                "error": "System not ready",
                "status": campus_query_app.initialization_status
            }), 503

        result = campus_query_app.process_query(query)
        return jsonify(result)

    except Exception as e:
        logger.error(f"API query error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/rebuild')
def api_rebuild():
    """Rebuild the vector store index"""
    try:
        logger.info("Rebuild requested")
        campus_query_app.system_ready = False
        campus_query_app.initialization_status = "Rebuilding index with local embeddings..."
        campus_query_app.initialize_system()
        return jsonify({
            "message": "Index rebuild started",
            "status": "rebuilding"
        })
    except Exception as e:
        logger.error(f"Rebuild error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/export')
def api_export():
    """Export the last query result"""
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
            "sources": campus_query_app.last_result.document_references,
            "embedding_type": "local_free"  # Indicate free embeddings used
        }
        return jsonify(export_data)
    except Exception as e:
        logger.error(f"Export error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/cache/status')
def api_cache_status():
    """Get cache statistics (NEW endpoint)"""
    try:
        cache_dir = VECTOR_STORE_DIR
        cache_file = os.path.join(cache_dir, "local_embeddings_cache.pkl")
        index_file = os.path.join(cache_dir, "vector_index.pkl")
        
        cache_info = {
            "cache_exists": os.path.exists(cache_file),
            "index_exists": os.path.exists(index_file),
            "cache_size": 0,
            "index_size": 0
        }
        
        if cache_info["cache_exists"]:
            cache_info["cache_size"] = os.path.getsize(cache_file)
        
        if cache_info["index_exists"]:
            cache_info["index_size"] = os.path.getsize(index_file)
        
        return jsonify(cache_info)
    except Exception as e:
        logger.error(f"Cache status error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/cache/clear', methods=['POST'])
def api_cache_clear():
    """Clear the embedding cache (NEW endpoint)"""
    try:
        import shutil
        
        if os.path.exists(VECTOR_STORE_DIR):
            shutil.rmtree(VECTOR_STORE_DIR)
            os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
            
            logger.info("Cache cleared successfully")
            return jsonify({
                "message": "Cache cleared successfully",
                "status": "success"
            })
        else:
            return jsonify({
                "message": "No cache to clear",
                "status": "success"
            })
            
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/system/info')
def api_system_info():
    """Get system information (NEW endpoint)"""
    try:
        import platform
        import psutil
        
        # Get document statistics
        doc_files = []
        if os.path.exists(UNIVERSITY_DOCS_DIR):
            doc_files = [f for f in os.listdir(UNIVERSITY_DOCS_DIR) 
                        if os.path.isfile(os.path.join(UNIVERSITY_DOCS_DIR, f))]
        
        system_info = {
            "python_version": platform.python_version(),
            "platform": platform.system(),
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "documents_directory": UNIVERSITY_DOCS_DIR,
            "vector_store_directory": VECTOR_STORE_DIR,
            "document_files": len(doc_files),
            "document_list": doc_files[:10],  # First 10 files
            "embedding_type": "sentence-transformers (local)",
            "embedding_model": "all-MiniLM-L6-v2",
            "embedding_dimension": 384,
            "quota_free": True
        }
        
        return jsonify(system_info)
    except Exception as e:
        logger.error(f"System info error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    """Favicon handler"""
    return app.response_class(status=404)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "system_ready": campus_query_app.system_ready,
        "initialization_status": campus_query_app.initialization_status,
        "document_count": campus_query_app.document_count,
        "embedding_type": "local_free"
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

@app.route('/api/soft-computing/stats')
def api_soft_computing_stats():
    """Get soft computing system statistics"""
    try:
        if not campus_query_app.system_ready:
            return jsonify({"error": "System not ready"}), 503
        
        stats = campus_query_app.query_processor.metrics.get_query_statistics()
        
        return jsonify({
            'soft_computing_enabled': True,
            'techniques': [
                'Neural Networks (Transformer Embeddings)',
                'Fuzzy Logic (Relevance Scoring)',
                'Classification (Query Intent)',
                'Clustering (Document Organization)'
            ],
            'statistics': stats,
            'embedding_model': 'all-MiniLM-L6-v2',
            'fuzzy_membership_functions': ['very_low', 'low', 'medium', 'high', 'very_high']
        })
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(UNIVERSITY_DOCS_DIR, exist_ok=True)
    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)

    print("\n" + "="*70)
    print("🎓 CampusQuery Web Server Starting...")
    print("="*70)
    print(f"✅ Using FREE local embeddings (sentence-transformers)")
    print(f"✅ No API quotas - Unlimited embeddings!")
    print(f"✅ Automatic caching for instant performance")
    print(f"📁 Documents directory: {UNIVERSITY_DOCS_DIR}")
    print(f"💾 Vector store directory: {VECTOR_STORE_DIR}")
    print(f"🌐 Server will be available at: http://localhost:5000")
    print(f"📄 PDFs accessible at: http://localhost:5000/docs/filename.pdf")
    print(f"🏥 Health check: http://localhost:5000/health")
    print("="*70 + "\n")

    # Check for existing documents
    if os.path.exists(UNIVERSITY_DOCS_DIR):
        doc_files = [f for f in os.listdir(UNIVERSITY_DOCS_DIR) 
                    if os.path.isfile(os.path.join(UNIVERSITY_DOCS_DIR, f))]
        if doc_files:
            print(f"📚 Found {len(doc_files)} document(s) to process:")
            for f in doc_files[:5]:  # Show first 5
                print(f"   - {f}")
            if len(doc_files) > 5:
                print(f"   ... and {len(doc_files) - 5} more")
            print()
        else:
            print("⚠️  No documents found!")
            print(f"   Add PDF, DOCX, or TXT files to: {os.path.abspath(UNIVERSITY_DOCS_DIR)}")
            print()

    # Check for existing cache
    cache_file = os.path.join(VECTOR_STORE_DIR, "local_embeddings_cache.pkl")
    index_file = os.path.join(VECTOR_STORE_DIR, "vector_index.pkl")
    
    if os.path.exists(cache_file) or os.path.exists(index_file):
        print("💾 Found existing cache - will load quickly!")
        if os.path.exists(cache_file):
            cache_size = os.path.getsize(cache_file) / 1024 / 1024
            print(f"   Embeddings cache: {cache_size:.2f} MB")
        if os.path.exists(index_file):
            index_size = os.path.getsize(index_file) / 1024 / 1024
            print(f"   Vector index: {index_size:.2f} MB")
        print()
    else:
        print("🆕 First run - will create embeddings cache")
        print("   (This takes a few minutes, then it's instant!)")
        print()

    print("🚀 Starting Flask server...")
    print("="*70 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)