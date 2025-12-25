// Simple Test Dashboard - Fixed Results Display
class Dashboard {
    constructor() {
        this.tests = [];
        this.results = [];
        this.suite = 'all';
        this.running = false;
        this.baseURL = window.location.origin;
        this.init();
    }

    init() {
        document.getElementById('runAllBtn').onclick = () => this.runAll();
        document.getElementById('refreshBtn').onclick = () => this.loadTests();
        document.getElementById('clearBtn').onclick = () => this.clear();
        document.getElementById('closeResults').onclick = () => this.hideResults();
        document.getElementById('viewResultsBtn').onclick = () => this.toggleResults();
        this.loadTests();
        setInterval(() => { if (this.running) this.checkStatus(); }, 2000);
    }

    async loadTests() {
        const grid = document.getElementById('testsGrid');
        grid.innerHTML = '<div class="loading"><div class="spinner-large"></div><p>Loading...</p></div>';
        const btn = document.getElementById('refreshBtn');
        btn.disabled = true;
        try {
            const res = await fetch(`${this.baseURL}/api/test-cases`);
            const data = await res.json();
            this.tests = data.test_cases || [];
            this.render();
            this.updateStats();
            this.createTabs(data.suites || {});
            this.toast('Loaded ' + this.tests.length + ' tests', 'success');
        } catch (e) {
            this.toast('Failed to load tests', 'error');
            grid.innerHTML = '<div class="loading"><p>Error: ' + e.message + '</p><button class="btn btn-primary" onclick="dashboard.loadTests()">Retry</button></div>';
        } finally {
            btn.disabled = false;
        }
    }

    createTabs(suites) {
        const tabs = document.getElementById('tabs');
        const all = ['all', ...Object.keys(suites).filter(s => suites[s] > 0)];
        tabs.innerHTML = all.map(s => {
            const count = s === 'all' ? this.tests.length : suites[s] || 0;
            return `<button class="tab ${s === this.suite ? 'active' : ''}" onclick="dashboard.filter('${s}')">${s === 'all' ? 'All' : s} (${count})</button>`;
        }).join('');
    }

    filter(suite) {
        this.suite = suite;
        document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.textContent.includes(suite === 'all' ? 'All' : suite)));
        this.render();
    }

    render() {
        const grid = document.getElementById('testsGrid');
        let filtered = this.suite === 'all' ? this.tests : this.tests.filter(t => t.suite === this.suite);
        if (filtered.length === 0) {
            grid.innerHTML = '<div class="loading"><p>No tests in this suite</p></div>';
            return;
        }
        grid.innerHTML = filtered.map(t => this.renderCard(t)).join('');
        grid.querySelectorAll('.run-test').forEach(btn => {
            btn.onclick = () => {
                try {
                    const test = JSON.parse(btn.dataset.test);
                    this.runTest(test);
                } catch (e) {
                    this.toast('Error parsing test', 'error');
                }
            };
        });
        grid.querySelectorAll('.run-suite').forEach(btn => {
            btn.onclick = () => this.runSuite(btn.dataset.suite);
        });
    }

    renderCard(test) {
        const r = this.getResult(test.method);
        const s = r ? r.status : 'pending';
        const m = r ? r.message : '';
        const d = r ? r.duration : null;
        const icon = s === 'pass' ? 'check-circle' : s === 'fail' ? 'times-circle' : s === 'error' ? 'exclamation-triangle' : s === 'running' ? 'spinner fa-spin' : 'clock';
        return `<div class="test-card ${s}">
            <div class="test-header">
                <div><div class="test-title">${this.escape(test.name)}</div><div class="test-suite">${this.escape(test.suite)}</div></div>
                <span class="test-status ${s}"><i class="fas fa-${icon}"></i> ${s.toUpperCase()}</span>
            </div>
            <div class="test-message">${this.escape(m || 'Not executed')}</div>
            <div class="test-footer">
                <div>${d ? d.toFixed(2) + 's' : 'Not run'}</div>
                <div class="test-actions">
                    <button class="btn-icon run-test" data-test='${JSON.stringify(test).replace(/'/g, "&#39;")}' ${this.running ? 'disabled' : ''}><i class="fas fa-play"></i></button>
                    <button class="btn-icon run-suite" data-suite="${this.escape(test.suite)}" ${this.running ? 'disabled' : ''}><i class="fas fa-layer-group"></i></button>
                </div>
            </div>
        </div>`;
    }

    getResult(method) {
        return this.results.find(r => r.test_name && r.test_name.toLowerCase().includes(method.toLowerCase()));
    }

    async runTest(test) {
        if (this.running) { this.toast('Tests running, wait...', 'warning'); return; }
        this.running = true;
        this.showStatus('Running: ' + test.name);
        this.disable(true);
        try {
            const res = await fetch(`${this.baseURL}/api/run-test`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({suite: test.suite, name: test.name, method: test.method})
            });
            const data = await res.json();
            if (res.ok) {
                this.toast('Test started', 'success');
                this.startPolling();
            } else {
                throw new Error(data.error || 'Failed');
            }
        } catch (e) {
            this.toast('Error: ' + e.message, 'error');
            this.running = false;
            this.hideStatus();
            this.disable(false);
        }
    }

    async runSuite(suite) {
        if (this.running) { this.toast('Tests running, wait...', 'warning'); return; }
        if (!confirm('Run all tests in ' + suite + '?')) return;
        this.running = true;
        this.showStatus('Running ' + suite + '...');
        this.disable(true);
        try {
            const res = await fetch(`${this.baseURL}/api/run-suite`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({suite: suite})
            });
            const data = await res.json();
            if (res.ok) {
                this.toast('Suite started', 'success');
                this.startPolling();
            } else {
                throw new Error(data.error || 'Failed');
            }
        } catch (e) {
            this.toast('Error: ' + e.message, 'error');
            this.running = false;
            this.hideStatus();
            this.disable(false);
        }
    }

    async runAll() {
        if (this.running) { 
            this.toast('Tests are already running. Please wait...', 'warning'); 
            return; 
        }
        if (this.tests.length === 0) { 
            this.toast('No tests available. Please refresh first.', 'warning'); 
            return; 
        }
        if (!confirm(`Run all ${this.tests.length} tests? This may take several minutes.`)) {
            return;
        }
        
        this.running = true;
        this.showStatus('Running all tests... This may take a while.');
        this.disable(true);
        this.results = []; // Clear previous results
        
        try {
            const res = await fetch(`${this.baseURL}/api/run-all`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            });
            
            if (!res.ok) {
                const errorData = await res.json().catch(() => ({}));
                throw new Error(errorData.error || `Server error: ${res.status}`);
            }
            
            const data = await res.json();
            console.log('Run all response:', data);
            this.toast('All tests started successfully', 'success');
            this.startPolling();
        } catch (e) {
            console.error('Run all error:', e);
            this.toast('Error: ' + e.message, 'error');
            this.running = false;
            this.hideStatus();
            this.disable(false);
        }
    }

    startPolling() {
        if (this.interval) clearInterval(this.interval);
        this.interval = setInterval(() => this.checkStatus(), 2000);
    }

    async checkStatus() {
        try {
            const res = await fetch(`${this.baseURL}/api/test-status`);
            if (!res.ok) return;
            const data = await res.json();
            this.running = data.running || false;
            
            if (data.current_test) this.showStatus('Running: ' + data.current_test);
            
            // IMPORTANT: Always get ALL results from server
            if (data.results && Array.isArray(data.results)) {
                if (data.results.length > 0) {
                    // Store ALL results - don't merge, replace completely
                    this.results = [...data.results];
                    this.render();
                    this.updateStats();
                    // Always show all results
                    this.showResults(this.results);
                    console.log('Results updated:', this.results.length, 'tests');
                } else {
                    // Empty results
                    this.results = [];
                    this.updateStats();
                }
            }
            
            if (!this.running) {
                if (this.interval) { clearInterval(this.interval); this.interval = null; }
                this.hideStatus();
                this.disable(false);
                if (data.results && data.results.length > 0) {
                    const p = data.results.filter(r => r.status === 'pass').length;
                    const f = data.results.filter(r => r.status === 'fail').length;
                    const e = data.results.filter(r => r.status === 'error').length;
                    this.toast(`Done: ${p} passed, ${f} failed, ${e} errors`, f > 0 || e > 0 ? 'error' : 'success');
                }
            }
        } catch (e) {
            console.error('Status error:', e);
        }
    }

    showStatus(text) {
        document.getElementById('statusBar').style.display = 'flex';
        document.getElementById('statusText').textContent = text;
    }

    hideStatus() {
        document.getElementById('statusBar').style.display = 'none';
    }

    disable(disable) {
        ['runAllBtn', 'refreshBtn', 'clearBtn'].forEach(id => {
            document.getElementById(id).disabled = disable;
        });
    }

    showResults(results) {
        const section = document.getElementById('results');
        const content = document.getElementById('resultsContent');
        const summary = document.getElementById('resultsSummary');
        
        // Debug: Check if elements exist
        if (!section) {
            console.error('Results section not found!');
            return;
        }
        if (!content) {
            console.error('Results content not found!');
            return;
        }
        
        // Always show results section when we have results
        if (results && results.length > 0) {
            section.style.display = 'block';
            section.style.visibility = 'visible';
            
            const viewBtn = document.getElementById('viewResultsBtn');
            if (viewBtn) viewBtn.style.display = 'inline-flex';
            
            const total = results.length;
            const passed = results.filter(r => r.status === 'pass').length;
            const failed = results.filter(r => r.status === 'fail').length;
            const errors = results.filter(r => r.status === 'error').length;
            
            // Show summary
            if (summary) {
                summary.innerHTML = `
                    <div class="summary-item total">
                        <div class="summary-label">Total Tests</div>
                        <div class="summary-value">${total}</div>
                    </div>
                    <div class="summary-item pass">
                        <div class="summary-label">Passed</div>
                        <div class="summary-value">${passed}</div>
                    </div>
                    <div class="summary-item fail">
                        <div class="summary-label">Failed</div>
                        <div class="summary-value">${failed}</div>
                    </div>
                    <div class="summary-item error">
                        <div class="summary-label">Errors</div>
                        <div class="summary-value">${errors}</div>
                    </div>
                `;
            }
            
            // Show all results
            content.innerHTML = results.map(r => {
                const d = r.duration ? r.duration.toFixed(2) + 's' : 'N/A';
                const t = r.timestamp ? new Date(r.timestamp).toLocaleString() : '';
                const icon = r.status === 'pass' ? 'check-circle' : r.status === 'fail' ? 'times-circle' : 'exclamation-triangle';
                const statusColor = r.status === 'pass' ? '#10b981' : r.status === 'fail' ? '#ef4444' : '#f59e0b';
                
                return `<div class="result-item ${r.status}" data-status="${r.status}">
                    <div class="result-header-row">
                        <div class="result-name">
                            <i class="fas fa-${icon}" style="color: ${statusColor}; margin-right: 8px;"></i>
                            ${this.escape(r.test_name || 'Unknown Test')}
                        </div>
                        <span class="result-status-badge ${r.status}">${r.status.toUpperCase()}</span>
                    </div>
                    <div class="result-meta">
                        <div class="result-meta-item">
                            <i class="fas fa-clock"></i>
                            <span>Duration: ${d}</span>
                        </div>
                        <div class="result-meta-item">
                            <i class="fas fa-calendar"></i>
                            <span>${t}</span>
                        </div>
                    </div>
                    <div class="result-message">
                        <strong>Result:</strong> ${this.escape(r.message || 'No message available')}
                    </div>
                </div>`;
            }).join('');
            
            // Setup filter buttons
            this.setupFilters();
            
            // Scroll to results after a short delay
            setTimeout(() => {
                section.scrollIntoView({behavior: 'smooth', block: 'start'});
            }, 200);
        } else {
            // No results yet
            if (summary) summary.innerHTML = '';
            content.innerHTML = '<div class="loading"><p>No results available yet. Run tests to see results.</p></div>';
        }
    }
    
    setupFilters() {
        document.querySelectorAll('.btn-filter').forEach(btn => {
            btn.onclick = () => {
                document.querySelectorAll('.btn-filter').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const filter = btn.dataset.filter;
                document.querySelectorAll('.result-item').forEach(item => {
                    item.classList.toggle('hidden', filter !== 'all' && item.dataset.status !== filter);
                });
            };
        });
    }

    hideResults() {
        const s = document.getElementById('results');
        if (s) s.style.display = 'none';
    }
    
    toggleResults() {
        const s = document.getElementById('results');
        if (s) s.style.display = s.style.display === 'none' ? 'block' : 'none';
    }

    clear() {
        if (!confirm('Clear all results?')) return;
        this.results = [];
        this.render();
        this.updateStats();
        this.hideResults();
        const btn = document.getElementById('viewResultsBtn');
        if (btn) btn.style.display = 'none';
        this.toast('Results cleared', 'success');
    }

    updateStats() {
        document.getElementById('totalTests').textContent = this.tests.length;
        document.getElementById('passedTests').textContent = this.results.filter(r => r.status === 'pass').length;
        document.getElementById('failedTests').textContent = this.results.filter(r => r.status === 'fail').length;
        document.getElementById('errorTests').textContent = this.results.filter(r => r.status === 'error').length;
    }

    toast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = 'toast ' + type;
        toast.innerHTML = '<i class="fas fa-' + (type === 'success' ? 'check' : type === 'error' ? 'times' : 'exclamation') + '"></i> ' + this.escape(message);
        container.appendChild(toast);
        setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 3000);
    }

    escape(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

let dashboard;
window.onload = () => { dashboard = new Dashboard(); window.dashboard = dashboard; };
