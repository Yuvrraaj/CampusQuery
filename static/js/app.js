class CampusQueryApp {
    constructor() {
        this.currentQuery = '';
        this.currentResult = null;
        this.detailVisible = false;
        this.systemStatus = { ready: false, has_documents: false };
        this.selectedText = '';
        this.currentPdfUrl = '';
        this.currentDocumentName = '';
        
        // PDF.js variables
        this.pdfDoc = null;
        this.pageNum = 1;
        this.scale = 1.0;
        this.pageRendering = false;
        this.pageNumPending = null;
        
        this.init();
    }

    $(sel) { return document.querySelector(sel); }
    $all(sel) { return Array.from(document.querySelectorAll(sel)); }

    init() {
        this.bindNav();
        this.bindCompose();
        this.bindModal();
        this.bindActions();
        this.checkStatus();
        this.initializePDFJS();
        this.addStyles();
        this.toast('Welcome to Enhanced CampusQuery with Accurate Highlighting!', 'success');
    }

    // Initialize PDF.js with proper worker
    initializePDFJS() {
        if (typeof pdfjsLib === 'undefined') {
            this.loadPDFJS();
        } else {
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.worker.min.js';
        }
    }

    loadPDFJS() {
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.min.js';
        script.onload = () => {
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.worker.min.js';
        };
        document.head.appendChild(script);
    }

    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            /* Enhanced PDF viewer styles */
            .pdf-viewer-container {
                position: relative;
                background: #f5f5f5;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                overflow: auto;
                max-height: 700px;
            }
            
            .pdf-page-container {
                position: relative;
                margin: 20px auto;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
                background: white;
                display: flex;
                justify-content: center;
            }
            
            .pdf-canvas {
                display: block;
            }
            
            .pdf-text-layer {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                color: transparent;
                user-select: text;
                -webkit-user-select: text;
                -moz-user-select: text;
                -ms-user-select: text;
                pointer-events: auto;
                line-height: 1.0;
            }
            
            .pdf-text-layer > span {
                position: absolute;
                white-space: pre;
                cursor: text;
                transform-origin: 0% 0%;
            }
            
            /* Enhanced selection highlighting */
            .pdf-text-layer ::selection {
                background: rgba(255, 255, 0, 0.8) !important;
                color: #000 !important;
            }
            
            .pdf-text-layer ::-moz-selection {
                background: rgba(255, 255, 0, 0.8) !important;
                color: #000 !important;
            }
            
            /* PDF controls styling */
            .pdf-controls {
                display: flex;
                gap: 8px;
                align-items: center;
                flex-wrap: wrap;
                padding: 12px;
                background: linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(34, 211, 238, 0.1));
                border-radius: 8px 8px 0 0;
                border-bottom: 1px solid var(--border);
            }
            
            .pdf-btn {
                padding: 8px 12px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 600;
                font-size: 12px;
                transition: all 0.2s ease;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            
            .pdf-btn-primary { 
                background: linear-gradient(135deg, var(--primary), var(--primary-2)); 
                color: white; 
            }
            .pdf-btn-success { 
                background: var(--success); 
                color: white; 
            }
            .pdf-btn-secondary { 
                background: var(--info); 
                color: white; 
            }
            
            .pdf-btn:hover { 
                transform: translateY(-2px); 
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            }
            
            .pdf-info {
                padding: 8px 12px;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
                color: var(--primary);
                border: 1px solid var(--border);
            }
            
            /* Selection display styling */
            .selection-display {
                background: linear-gradient(135deg, rgba(255, 235, 59, 0.2), rgba(255, 193, 7, 0.1));
                border: 2px solid #ffc107;
                border-radius: 12px;
                padding: 16px;
                margin: 16px 0;
                box-shadow: 0 4px 12px rgba(255, 193, 7, 0.2);
            }
            
            .selection-text {
                background: rgba(255, 241, 118, 0.7);
                color: #000;
                padding: 10px 12px;
                border-radius: 8px;
                font-family: 'Segoe UI', monospace;
                font-weight: 500;
                line-height: 1.5;
                max-height: 120px;
                overflow-y: auto;
                border: 1px solid rgba(255, 193, 7, 0.4);
                margin: 8px 0;
            }
            
            /* Highlight search terms */
            mark {
                background: rgba(255, 241, 118, 0.8);
                color: #000;
                padding: 2px 4px;
                border-radius: 3px;
                font-weight: 600;
            }
        `;
        document.head.appendChild(style);
    }

    /* Navigation */
    bindNav() {
        const items = this.$all('.nav-item');
        items.forEach(btn => btn.addEventListener('click', () => {
            items.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const target = btn.dataset.section;
            this.$all('.section').forEach(s => s.classList.remove('active'));
            const targetSection = this.$('#section-' + target);
            if (targetSection) targetSection.classList.add('active');
            const sectionTitle = this.$('#sectionTitle');
            if (sectionTitle) sectionTitle.textContent = btn.textContent.trim();
            
            if (target === 'index') {
                this.updateIndexSection();
            }
        }));
    }

    /* Compose area */
    bindCompose() {
        const askBtn = this.$('#askButton');
        const input = this.$('#queryInput');
        const samples = this.$('#sampleQuestions');

        if (samples) {
            samples.addEventListener('click', (e) => {
                if (e.target.classList.contains('chip')) {
                    input.value = e.target.dataset.query || e.target.textContent;
                    input.focus();
                    this.resizeTextarea(input);
                }
            });
        }

        if (input) {
            input.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.key === 'Enter') { 
                    e.preventDefault();
                    this.processQuery(); 
                }
            });
            
            input.addEventListener('input', () => {
                this.resizeTextarea(input);
            });
        }

        if (askBtn) {
            askBtn.addEventListener('click', () => this.processQuery());
        }
    }

    resizeTextarea(textarea) {
        if (!textarea) return;
        textarea.style.height = 'auto';
        const maxHeight = 300;
        const scrollHeight = Math.min(maxHeight, textarea.scrollHeight);
        textarea.style.height = scrollHeight + 'px';
    }

    /* Modal */
    bindModal() {
        const close = this.$('#modalClose');
        const modal = this.$('#snippetModal');
        
        if (close && modal) {
            close.addEventListener('click', () => {
                modal.classList.add('hidden');
                this.cleanupModal();
            });
        }
        
        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal && !modal.classList.contains('hidden')) {
                modal.classList.add('hidden');
                this.cleanupModal();
            }
        });
        
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.add('hidden');
                    this.cleanupModal();
                }
            });
        }
    }

    cleanupModal() {
        this.selectedText = '';
        this.pdfDoc = null;
        this.currentPdfUrl = '';
        this.currentDocumentName = '';
    }

    /* Actions */
    bindActions() {
        const clear = this.$('#clearButton');
        const detail = this.$('#detailToggle');
        const exportBtn = this.$('#exportButton');
        const copyAns = this.$('#copyAnswerBtn');
        const rebuild = this.$('#rebuildButton');

        if (clear) clear.addEventListener('click', () => this.clearQuery());
        if (detail) detail.addEventListener('click', () => this.toggleDetailedExplanation());
        if (exportBtn) exportBtn.addEventListener('click', () => this.exportAnswer());
        if (copyAns) copyAns.addEventListener('click', () => this.copyAnswer());
        if (rebuild) rebuild.addEventListener('click', () => this.rebuildIndex());
    }

    /* Status check */
    async checkStatus() {
        const dot = this.$('#statusDot');
        const text = this.$('#statusText');
        const sub = this.$('#statusSubtext');
        const askButton = this.$('#askButton');

        try {
            const res = await fetch('/api/status');
            if (!res.ok) throw new Error('HTTP ' + res.status);
            const data = await res.json();
            
            this.systemStatus = data;

            if (data.ready) {
                if (dot) dot.style.background = 'var(--success)';
                if (text) text.textContent = 'Ready';
                
                if (data.has_documents) {
                    if (sub) sub.textContent = `${data.document_count} documents loaded - Ask away!`;
                } else {
                    if (sub) sub.textContent = 'Web search enabled - Ask anything!';
                }
                
                if (askButton) askButton.disabled = false;
                const detailToggle = this.$('#detailToggle');
                const exportButton = this.$('#exportButton');
                if (detailToggle) detailToggle.disabled = false;
                if (exportButton) exportButton.disabled = false;
                return;
            } else {
                if (dot) dot.style.background = 'var(--warning)';
                if (text) text.textContent = 'Loading…';
                if (sub) sub.textContent = data.status || 'Initializing…';
                if (askButton) askButton.disabled = true;
                setTimeout(() => this.checkStatus(), 1500);
            }

        } catch (e) {
            if (dot) dot.style.background = 'var(--danger)';
            if (text) text.textContent = 'Error';
            if (sub) sub.textContent = 'Connection failed - retrying...';
            setTimeout(() => this.checkStatus(), 2500);
        }
    }

    updateIndexSection() {
        const statusText = this.$('#indexStatusText');
        const stats = this.$('#documentStats');
        const docCount = this.$('#docCount');
        const webStatus = this.$('#webSearchStatus');

        if (this.systemStatus.ready) {
            if (statusText) statusText.textContent = 'Ready ✅';
            if (stats) stats.classList.remove('hidden');
            if (docCount) docCount.textContent = this.systemStatus.document_count || 0;
            if (webStatus) webStatus.textContent = this.systemStatus.web_search_enabled ? 'Enabled ✅' : 'Disabled ❌';
        } else {
            if (statusText) statusText.textContent = this.systemStatus.status || 'Loading...';
            if (stats) stats.classList.add('hidden');
        }
    }

    /* UX helpers */
    showLoading(msg = 'Working…') {
        const overlay = this.$('#loadingOverlay');
        const loadingText = this.$('.loading-text');
        if (loadingText) loadingText.textContent = msg;
        if (overlay) overlay.classList.remove('hidden');
    }

    hideLoading() { 
        const overlay = this.$('#loadingOverlay');
        if (overlay) overlay.classList.add('hidden'); 
    }

    toast(message, type = 'success', timeout = 3000) {
        const wrap = this.$('#toasts');
        if (!wrap) return;
        
        const node = document.createElement('div');
        node.className = 'toast ' + (type || '');
        
        const icons = {
            success: '✅',
            error: '❌',
            warn: '⚠️',
            info: '💡'
        };
        
        node.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <span>${icons[type] || '📢'}</span>
                <span>${message}</span>
            </div>
        `;
        wrap.appendChild(node);
        
        node.addEventListener('click', () => node.remove());
        
        setTimeout(() => {
            if (node.parentNode) {
                node.style.opacity = '0';
                node.style.transform = 'translateX(100%)';
                setTimeout(() => node.remove(), 300);
            }
        }, timeout);
    }

    showAlert(message, type = 'warn') { 
        this.toast(message, type); 
    }

    formatText(text = '') {
        let t = (text || '').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        t = t.replace(/\n/g, '<br>'); 
        t = t.replace(/^- (.+)$/gm, '<li>$1</li>');
        t = t.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
        return t; 
    }

    stripHTML(html = '') { 
        const tmp = document.createElement('div'); 
        tmp.innerHTML = html; 
        return tmp.textContent || tmp.innerText || ''; 
    }

    /* Core actions */
    clearQuery() {
        const input = this.$('#queryInput');
        if (input) {
            input.value = '';
            this.resizeTextarea(input);
        }
        this.hideResults();
        this.toast('Query cleared', 'success');
    }

    hideResults() {
        const resultsSection = this.$('#resultsSection');
        const detailCard = this.$('#detailCard');
        const docsCard = this.$('#docsCard');
        
        if (resultsSection) resultsSection.classList.add('hidden');
        if (detailCard) detailCard.classList.add('hidden');
        if (docsCard) docsCard.classList.add('hidden');
        
        this.detailVisible = false;
        
        const detailBtn = this.$('#detailToggle');
        if (detailBtn) {
            detailBtn.innerHTML = '<span>📖</span> Details';
        }
    }

    async processQuery() {
        const input = this.$('#queryInput');
        const q = input ? (input.value || '').trim() : '';
        if (!q) {
            this.showAlert('Please enter a question.', 'warn');
            return;
        }

        this.currentQuery = q;
        this.showLoading('Processing your query…');
        const askBtn = this.$('#askButton');
        const originalText = askBtn ? askBtn.innerHTML : '';
        if (askBtn) {
            askBtn.disabled = true;
            askBtn.innerHTML = '<span>🔄</span> Processing…';
        }

        try {
            const startTime = Date.now();
            const res = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: q })
            });
            
            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.error || 'Query failed');
            }

            const processingTime = ((Date.now() - startTime) / 1000).toFixed(1);
            this.currentResult = data;
            this.displayResults(data);
            
            if (data.answer.includes('🌐 **Information from Web Search:**')) {
                this.toast(`Web search completed in ${processingTime}s`, 'info');
            } else {
                this.toast(`Document search completed in ${processingTime}s`, 'success');
            }

        } catch (err) {
            this.showAlert('Error: ' + err.message, 'error');
        } finally {
            this.hideLoading();
            if (askBtn) {
                askBtn.disabled = false;
                askBtn.innerHTML = originalText;
            }
        }
    }

    displayResults(data) {
        const resCard = this.$('#resultsSection');
        if (resCard) resCard.classList.remove('hidden');
        
        const answerContent = this.$('#answerContent');
        if (answerContent) {
            answerContent.innerHTML = this.formatText(data.answer || 'No answer available.');
            
            if (data.answer.includes('🌐 **Information from Web Search:**')) {
                answerContent.insertAdjacentHTML('afterbegin', 
                    '<div class="answer-source-indicator">🌐 Web Search Result</div>'
                );
            } else if (data.sources && data.sources.length > 0) {
                answerContent.insertAdjacentHTML('afterbegin', 
                    '<div class="answer-source-indicator">📄 Document-based Answer</div>'
                );
            }
        }

        const container = this.$('#documentsContainer');
        const docsCard = this.$('#docsCard');
        if (container) container.innerHTML = '';

        if (data.sources && data.sources.length && container && docsCard) {
            docsCard.classList.remove('hidden');
            data.sources.forEach((s, idx) => {
                const el = document.createElement('div');
                el.className = 'doc-card';
                
                if (s.is_web_result) {
                    el.setAttribute('data-web', 'true');
                }
                
                const icon = s.is_web_result ? '🌐' : '📄';
                const type = s.is_web_result ? 'Web Result' : 'PDF Document';
                const relevancePercent = Math.round(s.relevance * 100);
                
                el.innerHTML = `
                    <div class="doc-name">${icon} ${s.filename}</div>
                    <div class="doc-preview">${s.content_preview}</div>
                    <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px;">
                        <div class="badge ${s.is_web_result ? 'web-result' : 'document-result'}">
                            ${relevancePercent}% relevant
                        </div>
                        <div class="badge">${type}</div>
                        ${!s.is_web_result ? '<div class="badge" style="background: rgba(255, 193, 7, 0.2); color: #ff8f00; border-color: rgba(255, 193, 7, 0.3);">🖍️ Click to Highlight</div>' : ''}
                    </div>
                `;

                if (!s.is_web_result) {
                    el.addEventListener('click', () => this.openAccuratePDFViewer(s));
                    el.style.cursor = 'pointer';
                    el.title = 'Click to open PDF with accurate text highlighting';
                } else {
                    el.addEventListener('click', () => this.showWebResult(s));
                    el.style.cursor = 'pointer';
                    el.title = 'Click to view web result';
                }
                
                container.appendChild(el);
            });
        }

        if (resCard) {
            resCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    /* MAIN FEATURE: Accurate PDF Viewer with Pixel-Perfect Text Highlighting */
    openAccuratePDFViewer(source) {
        const modal = this.$('#snippetModal');
        const title = this.$('#modalTitle');
        const subtitle = this.$('#modalSubtitle');
        const message = this.$('#modalMessage');

        if (!modal || !title || !subtitle || !message) {
            this.showAlert('Modal elements not found', 'error');
            return;
        }

        title.textContent = `📄 ${source.filename} - PDF Highlighter`;
        subtitle.textContent = 'Accurate text highlighting and navigation';
        
        this.currentDocumentName = source.filename;
        this.currentPdfUrl = `/docs/${source.filename}`;

        message.innerHTML = `
            <div class="pdf-viewer-container">
                <div class="pdf-controls">
                    <button id="openInTabBtn" class="pdf-btn pdf-btn-primary">🔗 Open in New Tab</button>
                    <button id="downloadPDFBtn" class="pdf-btn pdf-btn-success">💾 Download</button>
                    <button id="prevPageBtn" class="pdf-btn pdf-btn-secondary">◀ Prev</button>
                    <span id="pageInfoDisplay" class="pdf-info">Page 1 of 1</span>
                    <button id="nextPageBtn" class="pdf-btn pdf-btn-secondary">Next ▶</button>
                    <button id="zoomOutBtn" class="pdf-btn pdf-btn-secondary">🔍-</button>
                    <span id="zoomLevelDisplay" class="pdf-info">100%</span>
                    <button id="zoomInBtn" class="pdf-btn pdf-btn-secondary">🔍+</button>
                </div>

                <div id="pdfDisplayContainer" style="text-align: center; background: #f8f9fa; padding: 20px; min-height: 400px; border-radius: 0 0 8px 8px;">
                    <div id="loadingMessage" style="padding: 60px; color: #666; font-size: 16px;">
                        📄 Loading PDF with accurate text layer...<br>
                        <div style="margin-top: 10px; font-size: 14px; opacity: 0.7;">Please wait while we prepare the interactive PDF viewer</div>
                    </div>
                </div>
            </div>

            <div id="textSelectionDisplay" class="selection-display" style="display: none;">
                <div style="font-weight: bold; margin-bottom: 12px; color: #ff8f00; display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1.2em;">🖍️</span>
                    Selected Text:
                </div>
                <div id="selectedTextBox" class="selection-text"></div>
                <div style="display: flex; gap: 12px; margin-top: 14px; flex-wrap: wrap;">
                    <button id="generateQuestionBtn" class="pdf-btn pdf-btn-primary" style="padding: 10px 16px;">
                        🤔 Generate Follow-up Question
                    </button>
                    <button id="clearSelectionBtn" class="pdf-btn pdf-btn-secondary" style="padding: 10px 16px;">
                        ✖️ Clear Selection
                    </button>
                </div>
            </div>

            <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.05)); border-radius: 12px; padding: 16px; margin-top: 16px; border-left: 4px solid var(--success);">
                <div style="font-weight: 600; color: var(--success); margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">
                    <span>🎯</span>
                    How to Use:
                </div>
                <div style="font-size: 0.9em; line-height: 1.7; color: #374151;">
                    • <strong>Navigate:</strong> Use Prev/Next buttons to browse through all pages<br>
                    • <strong>Zoom:</strong> Zoom in/out for better text readability<br>
                    • <strong>Highlight:</strong> Click and drag to select text with pixel-perfect accuracy<br>
                    • <strong>Question:</strong> Generate intelligent follow-up questions from selected text<br>
                    • <strong>Access:</strong> Open in new tab or download PDF directly
                </div>
            </div>
        `;

        // Set up event handlers
        setTimeout(() => {
            this.setupPDFEventHandlers();
            this.initializeAccuratePDFViewer();
        }, 100);

        modal.classList.remove('hidden');
    }

    setupPDFEventHandlers() {
        const openTabBtn = document.getElementById('openInTabBtn');
        const downloadBtn = document.getElementById('downloadPDFBtn');
        const generateBtn = document.getElementById('generateQuestionBtn');
        const clearBtn = document.getElementById('clearSelectionBtn');

        if (openTabBtn) {
            openTabBtn.onclick = () => {
                window.open(this.currentPdfUrl, '_blank');
                this.toast('PDF opened in new tab', 'success');
            };
        }

        if (downloadBtn) {
            downloadBtn.onclick = () => {
                const a = document.createElement('a');
                a.href = this.currentPdfUrl;
                a.download = this.currentDocumentName;
                a.click();
                this.toast('Download started', 'success');
            };
        }

        if (generateBtn) {
            generateBtn.onclick = () => this.generateFollowUpFromPDF();
        }

        if (clearBtn) {
            clearBtn.onclick = () => this.clearPDFSelection();
        }
    }

    async initializeAccuratePDFViewer() {
        try {
            if (typeof pdfjsLib === 'undefined') {
                await this.loadPDFJSPromise();
            }

            const loadingTask = pdfjsLib.getDocument(this.currentPdfUrl);
            this.pdfDoc = await loadingTask.promise;
            
            const loadingMessage = document.getElementById('loadingMessage');
            if (loadingMessage) {
                loadingMessage.style.display = 'none';
            }
            
            this.pageNum = 1;
            this.scale = 1.0;
            
            await this.renderPageAccurately(this.pageNum);
            this.bindPDFNavigationControls();
            
            this.toast('PDF loaded successfully with accurate highlighting!', 'success');
            
        } catch (error) {
            console.error('Error loading PDF:', error);
            this.showAlert('Failed to load PDF: ' + error.message, 'error');
            
            const loadingMessage = document.getElementById('loadingMessage');
            if (loadingMessage) {
                loadingMessage.innerHTML = `
                    <div style="color: #dc3545;">
                        ❌ Failed to load PDF<br>
                        <div style="font-size: 14px; margin-top: 8px;">${error.message}</div>
                        <button onclick="window.open('${this.currentPdfUrl}', '_blank')" style="margin-top: 12px; padding: 8px 16px; background: var(--primary); color: white; border: none; border-radius: 6px; cursor: pointer;">
                            🔗 Try opening in new tab
                        </button>
                    </div>
                `;
            }
        }
    }

    loadPDFJSPromise() {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.min.js';
            script.onload = () => {
                pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.worker.min.js';
                resolve();
            };
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    async renderPageAccurately(num) {
        if (this.pageRendering) {
            this.pageNumPending = num;
            return;
        }
        
        this.pageRendering = true;
        
        try {
            const page = await this.pdfDoc.getPage(num);
            const viewport = page.getViewport({ scale: this.scale });
            
            const container = document.getElementById('pdfDisplayContainer');
            if (!container) {
                this.pageRendering = false;
                return;
            }
            
            container.innerHTML = `
                <div class="pdf-page-container" style="width: ${viewport.width}px; height: ${viewport.height}px;">
                    <canvas class="pdf-canvas" width="${viewport.width}" height="${viewport.height}"></canvas>
                    <div class="pdf-text-layer"></div>
                </div>
            `;
            
            const canvas = container.querySelector('.pdf-canvas');
            const ctx = canvas.getContext('2d');
            const textLayerDiv = container.querySelector('.pdf-text-layer');
            
            // Render PDF page
            const renderContext = {
                canvasContext: ctx,
                viewport: viewport
            };
            
            await page.render(renderContext).promise;
            
            // Render text layer using PDF.js built-in method for pixel-perfect accuracy
            const textContent = await page.getTextContent();
            
            // Clear existing text layer
            while (textLayerDiv.firstChild) {
                textLayerDiv.removeChild(textLayerDiv.firstChild);
            }
            
            // Use PDF.js renderTextLayer for accurate positioning
            pdfjsLib.renderTextLayer({
                textContent: textContent,
                container: textLayerDiv,
                viewport: viewport,
                textDivs: [],
                enhanceTextSelection: true
            });
            
            // Add selection handler
            this.addAccurateSelectionHandler(textLayerDiv);
            
            this.pageRendering = false;
            
            if (this.pageNumPending !== null) {
                this.renderPageAccurately(this.pageNumPending);
                this.pageNumPending = null;
            }
            
            // Update UI
            const pageInfo = document.getElementById('pageInfoDisplay');
            if (pageInfo) {
                pageInfo.textContent = `Page ${num} of ${this.pdfDoc.numPages}`;
            }
            
        } catch (error) {
            console.error('Error rendering page:', error);
            this.pageRendering = false;
            this.showAlert('Error rendering PDF page: ' + error.message, 'error');
        }
    }

    addAccurateSelectionHandler(textLayerDiv) {
        let selectionTimeout;
        
        const handleSelection = () => {
            clearTimeout(selectionTimeout);
            selectionTimeout = setTimeout(() => {
                const selection = window.getSelection();
                const selectedText = selection.toString().trim();
                
                if (selectedText.length > 5) {
                    this.selectedText = selectedText;
                    
                    const selectionDisplay = document.getElementById('textSelectionDisplay');
                    const selectedTextBox = document.getElementById('selectedTextBox');
                    
                    if (selectedTextBox && selectionDisplay) {
                        selectedTextBox.textContent = selectedText;
                        selectionDisplay.style.display = 'block';
                        selectionDisplay.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }
                    
                    this.toast(`Selected ${selectedText.length} characters. Use buttons below to generate questions.`, 'success');
                } else {
                    this.clearPDFSelection();
                }
            }, 250);
        };
        
        textLayerDiv.addEventListener('mouseup', handleSelection);
        textLayerDiv.addEventListener('touchend', handleSelection);
    }

    bindPDFNavigationControls() {
        const prevBtn = document.getElementById('prevPageBtn');
        const nextBtn = document.getElementById('nextPageBtn');
        const zoomInBtn = document.getElementById('zoomInBtn');
        const zoomOutBtn = document.getElementById('zoomOutBtn');
        
        if (prevBtn) {
            prevBtn.onclick = () => {
                if (this.pageNum <= 1) {
                    this.toast('Already on first page', 'info');
                    return;
                }
                this.pageNum--;
                this.renderPageAccurately(this.pageNum);
                this.clearPDFSelection();
            };
        }
        
        if (nextBtn) {
            nextBtn.onclick = () => {
                if (this.pageNum >= this.pdfDoc.numPages) {
                    this.toast('Already on last page', 'info');
                    return;
                }
                this.pageNum++;
                this.renderPageAccurately(this.pageNum);
                this.clearPDFSelection();
            };
        }
        
        if (zoomInBtn) {
            zoomInBtn.onclick = () => {
                this.scale = Math.min(this.scale + 0.25, 3.0);
                this.renderPageAccurately(this.pageNum);
                const zoomDisplay = document.getElementById('zoomLevelDisplay');
                if (zoomDisplay) {
                    zoomDisplay.textContent = Math.round(this.scale * 100) + '%';
                }
                this.clearPDFSelection();
                this.toast(`Zoomed to ${Math.round(this.scale * 100)}%`, 'info');
            };
        }
        
        if (zoomOutBtn) {
            zoomOutBtn.onclick = () => {
                this.scale = Math.max(this.scale - 0.25, 0.5);
                this.renderPageAccurately(this.pageNum);
                const zoomDisplay = document.getElementById('zoomLevelDisplay');
                if (zoomDisplay) {
                    zoomDisplay.textContent = Math.round(this.scale * 100) + '%';
                }
                this.clearPDFSelection();
                this.toast(`Zoomed to ${Math.round(this.scale * 100)}%`, 'info');
            };
        }
    }

    async generateFollowUpFromPDF() {
        if (!this.selectedText) {
            this.showAlert('Please select some text first by clicking and dragging on the PDF', 'warn');
            return;
        }
        
        try {
            this.showLoading('Generating intelligent follow-up question from selected text...');
            
            const response = await fetch('/api/followup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    selected_text: this.selectedText,
                    context: `Selected from PDF: ${this.currentDocumentName}, Page ${this.pageNum}`,
                    document_name: this.currentDocumentName
                })
            });
            
            const data = await response.json();
            if (!response.ok) throw new Error(data.error);
            
            this.hideLoading();
            
            // Set the generated question in the main query input
            const queryInput = this.$('#queryInput');
            if (queryInput) {
                queryInput.value = data.question;
                this.resizeTextarea(queryInput);
            }
            
            // Close modal and focus on query
            const modal = this.$('#snippetModal');
            if (modal) modal.classList.add('hidden');
            this.cleanupModal();
            
            this.toast('Follow-up question generated from highlighted PDF text!', 'success');
            
            // Auto-submit option
            if (confirm('Would you like to automatically search for the answer to this follow-up question?')) {
                this.processQuery();
            }
            
        } catch (err) {
            this.hideLoading();
            this.showAlert('Failed to generate follow-up question: ' + err.message, 'error');
        }
    }

    clearPDFSelection() {
        this.selectedText = '';
        const selectionDisplay = document.getElementById('textSelectionDisplay');
        if (selectionDisplay) {
            selectionDisplay.style.display = 'none';
        }
        
        if (window.getSelection) {
            window.getSelection().removeAllRanges();
        }
        
        this.toast('Selection cleared', 'info');
    }

    /* Web Results */
    showWebResult(source) {
        const modal = this.$('#snippetModal');
        const title = this.$('#modalTitle');
        const subtitle = this.$('#modalSubtitle');
        const message = this.$('#modalMessage');

        if (!modal || !title || !subtitle || !message) return;

        title.textContent = `🌐 ${source.filename}`;
        subtitle.textContent = 'Web search result';
        
        message.innerHTML = `
            <div style="margin-bottom: 1.5rem; padding: 1rem; background: rgba(34, 211, 238, 0.1); border-radius: 12px; border-left: 4px solid var(--primary-2);">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    <span style="font-size: 1.2em;">🌐</span>
                    <strong>Web Search Result:</strong> ${source.filename}
                </div>
                <div style="font-size: 0.9em; color: var(--muted);">
                    Relevance: ${Math.round(source.relevance * 100)}% | Source: Internet
                </div>
            </div>
            
            <div style="padding: 1.25rem; background: rgba(34, 211, 238, 0.05); border-radius: 12px; border-left: 4px solid var(--primary-2); line-height: 1.7;">
                <div style="font-weight: 600; margin-bottom: 1rem; color: var(--primary-2);">🔍 Web Search Content:</div>
                <div>${this.highlightSearchTerms(source.content_snippet || 'No content available', this.currentQuery)}</div>
            </div>
            
            <div style="color: var(--muted); font-size: 0.9rem; margin-top: 1.5rem; padding: 1rem; background: rgba(245, 158, 11, 0.1); border-radius: 8px; border-left: 4px solid var(--warning);">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                    <span>💡</span>
                    <strong style="color: var(--warning);">Web Search Information</strong>
                </div>
                This information was retrieved through web search as it wasn't available in local university documents.
            </div>
        `;

        modal.classList.remove('hidden');
    }

    highlightSearchTerms(content, query) {
        if (!content || !query) return content;
        
        const terms = query.toLowerCase().split(/\s+/).filter(term => term.length > 2);
        let highlightedContent = content;
        
        terms.forEach(term => {
            const regex = new RegExp(`(${term})`, 'gi');
            highlightedContent = highlightedContent.replace(regex, '<mark>$1</mark>');
        });
        
        return highlightedContent;
    }

    /* Additional Methods */
    toggleDetailedExplanation() {
        if (!this.currentResult) return;

        const card = this.$('#detailCard');
        const btn = this.$('#detailToggle');

        if (!card || !btn) return;

        if (this.detailVisible) {
            card.classList.add('hidden');
            btn.innerHTML = '<span>📖</span> Details';
            this.detailVisible = false;
        } else {
            card.classList.remove('hidden');
            const detailContent = this.$('#detailContent');
            if (detailContent) {
                detailContent.innerHTML = this.formatText(this.currentResult.detailed_answer);
            }
            btn.innerHTML = '<span>📖</span> Hide Details';
            this.detailVisible = true;
            setTimeout(() => card.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
        }
    }

    async exportAnswer() {
        if (!this.currentResult) {
            this.showAlert('No answer to export', 'warn');
            return;
        }

        try {
            const res = await fetch('/api/export');
            const data = await res.json();
            if (!res.ok) throw new Error(data.error);

            const content = `CampusQuery Enhanced - Exported Answer
${'='.repeat(60)}
Generated: ${new Date(data.timestamp).toLocaleString()}

QUESTION:
${this.currentQuery}

ANSWER:
${this.stripHTML(this.currentResult.answer)}

DETAILED EXPLANATION:
${this.stripHTML(this.currentResult.detailed_answer)}

SOURCES:
${data.sources.map(source => `- ${source}`).join('\n')}

JUSTIFICATION:
${this.currentResult.justification}
${'='.repeat(60)}
Generated by CampusQuery Enhanced - University Information Assistant
`;

            const blob = new Blob([content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `campusquery_answer_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
            a.click();
            URL.revokeObjectURL(url);

            this.toast('Answer exported successfully!', 'success');
        } catch (err) {
            this.showAlert('Export failed: ' + err.message, 'error');
        }
    }

    copyAnswer() {
        if (!this.currentResult) {
            this.showAlert('No answer to copy', 'warn');
            return;
        }

        const text = this.stripHTML(this.currentResult.answer);
        navigator.clipboard.writeText(text).then(() => {
            this.toast('Answer copied to clipboard!', 'success');
        }).catch(() => {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            this.toast('Answer copied to clipboard!', 'success');
        });
    }

    async rebuildIndex() {
        if (!confirm('Are you sure you want to rebuild the document index? This may take a few minutes.')) return;
        
        this.showLoading('Rebuilding document index...');
        
        try {
            const res = await fetch('/api/rebuild');
            const data = await res.json();
            if (!res.ok) throw new Error(data.error);
            
            this.toast('Index rebuild started - system will be ready shortly', 'info', 5000);
            this.systemStatus.ready = false;
            setTimeout(() => this.checkStatus(), 3000);
            
        } catch (err) {
            this.showAlert('Rebuild failed: ' + err.message, 'error');
        } finally {
            this.hideLoading();
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const app = new CampusQueryApp();
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            const queryInput = document.querySelector('#queryInput');
            if (document.activeElement === queryInput) {
                e.preventDefault();
                app.processQuery();
            }
        }
    });
    
    // Connection monitoring
    window.addEventListener('online', () => {
        app.toast('Connection restored', 'success');
    });
    
    window.addEventListener('offline', () => {
        app.toast('Connection lost - some features may not work', 'warn');
    });
    
    // Error handling for uncaught errors
    window.addEventListener('error', (e) => {
        console.error('Uncaught error:', e.error);
        app.showAlert('An unexpected error occurred', 'error');
    });
    
    console.log('🎓 CampusQuery Enhanced with Pixel-Perfect PDF Highlighting initialized successfully');
});
