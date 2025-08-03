const API_BASE_URL = 'http://localhost:5000/api';

document.addEventListener('DOMContentLoaded', function() {
    loadHistory();
    
    // Prevent form submission
    const form = document.getElementById('newsForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            e.stopPropagation();
            return false;
        });
    }
    
    // Add click handler to button
    const analyzeBtn = document.getElementById('analyzeBtn');
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            analyzeNews();
            return false;
        });
    }
});

async function analyzeNews() {
    const newsText = document.getElementById('newsText').value.trim();
    
    if (!newsText) {
        alert('Silakan masukkan teks berita terlebih dahulu.');
        return;
    }
    
    const loadingDiv = document.getElementById('loadingDiv');
    const resultDiv = document.getElementById('resultDiv');
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    // Show loading
    loadingDiv.style.display = 'block';
    resultDiv.style.display = 'none';
    analyzeBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: newsText })
        });
        
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        
        const result = await response.json();
        displayResult(result);
        loadHistory(); // Refresh history
        
    } catch (error) {
        console.error('Error:', error);
        displayError('Terjadi kesalahan saat menganalisis berita. Pastikan server backend berjalan.');
    } finally {
        loadingDiv.style.display = 'none';
        analyzeBtn.disabled = false;
    }
}

function displayResult(result) {
    const resultDiv = document.getElementById('resultDiv');
    
    const isReal = result.prediction === 'Real';
    const cardClass = isReal ? 'result-real' : 'result-fake';
    const badgeClass = isReal ? 'badge-real' : 'badge-fake';
    const iconClass = isReal ? 'fas fa-check-circle' : 'fas fa-exclamation-triangle';
    const confidencePercent = (result.confidence * 100).toFixed(1);
    
    resultDiv.innerHTML = `
        <div class="result-card card ${cardClass}">
            <div class="card-body">
                <div class="row align-items-center mb-3">
                    <div class="col-auto">
                        <i class="${iconClass} fa-3x ${isReal ? 'text-success' : 'text-danger'}"></i>
                    </div>
                    <div class="col">
                        <h3 class="mb-1">
                            <span class="badge ${badgeClass} fs-5">${result.prediction === 'Real' ? 'BERITA ASLI' : 'KEMUNGKINAN HOAX'}</span>
                        </h3>
                        <p class="mb-1 text-muted">Tingkat kepercayaan: ${confidencePercent}%</p>
                        <small class="text-muted">
                            <i class="fas fa-cog me-1"></i>Basis keputusan: <strong>${result.decision_basis}</strong>
                            ${result.verification_weight > 0 ? ` (Bobot verifikasi: ${(result.verification_weight * 100).toFixed(0)}%)` : ''}
                        </small>
                    </div>
                </div>
                
                <div class="mb-4">
                    <label class="form-label fw-bold">Tingkat Kepercayaan:</label>
                    <div class="confidence-bar">
                        <div class="confidence-indicator" style="left: ${confidencePercent}%"></div>
                    </div>
                    <div class="d-flex justify-content-between mt-1">
                        <small class="text-danger">Hoax</small>
                        <small class="text-warning">Netral</small>
                        <small class="text-success">Asli</small>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="feature-item">
                            <h6 class="fw-bold mb-2">
                                <i class="fas fa-file-alt me-2"></i>Analisis Teks
                            </h6>
                            <p class="mb-1"><strong>Jumlah kata:</strong> ${result.analysis.word_count}</p>
                            <p class="mb-1"><strong>Sentimen:</strong> ${result.analysis.sentiment}</p>
                            <p class="mb-0"><strong>Indikator mencurigakan:</strong> ${result.analysis.suspicious_indicators}</p>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="feature-item">
                            <h6 class="fw-bold mb-2">
                                <i class="fas fa-shield-alt me-2"></i>Verifikasi Sumber
                            </h6>
                            <p class="mb-1"><strong>Skor sumber terpercaya:</strong> ${(result.trusted_sources_score * 100).toFixed(1)}%</p>
                            <p class="mb-0 text-muted small">Berdasarkan referensi ke sumber berita terpercaya</p>
                        </div>
                    </div>
                </div>
                
                <div class="mt-3">
                    <h6 class="fw-bold mb-2">
                        <i class="fas fa-search me-2"></i>Verifikasi Real-time
                    </h6>
                    ${result.real_time_verification ? `
                        <div class="feature-item">
                            <p class="mb-2"><strong>Status:</strong> ${result.real_time_verification.message}</p>
                            <p class="mb-2"><strong>Kata kunci pencarian:</strong> ${result.real_time_verification.keywords_used.join(', ')}</p>
                            <p class="mb-2"><strong>Skor verifikasi:</strong> ${(result.real_time_verification.verification_score * 100).toFixed(1)}%</p>
                            
                            ${result.real_time_verification.claim_type === 'suspicious_geopolitical_claim' ? `
                                <div class="alert alert-danger mt-3">
                                    <strong><i class="fas fa-exclamation-triangle me-1"></i>PERINGATAN:</strong> 
                                    Klaim ini terdeteksi sebagai potensi misinformasi geopolitik. 
                                    Klaim seperti "Indonesia dijajah/budak negara lain" umumnya merupakan hoax 
                                    yang bertujuan menyebarkan kebencian atau disinformasi.
                                </div>
                            ` : ''}
                            
                            ${result.real_time_verification.trusted_articles.length > 0 ? `
                                <div class="mt-3">
                                    <strong>Artikel dari Sumber Terpercaya:</strong>
                                    ${result.real_time_verification.trusted_articles.map(article => `
                                        <div class="mt-2 p-2 bg-light rounded">
                                            <small class="text-primary fw-bold">${article.source}</small><br>
                                            <a href="${article.link}" target="_blank" class="text-decoration-none">
                                                ${article.title}
                                            </a>
                                        </div>
                                    `).join('')}
                                </div>
                            ` : ''}
                            
                            ${result.real_time_verification.fact_checks.length > 0 ? `
                                <div class="mt-3">
                                    <strong>Fact-Check:</strong>
                                    ${result.real_time_verification.fact_checks.map(check => `
                                        <div class="mt-2 p-2 bg-warning bg-opacity-10 rounded">
                                            <small class="text-warning fw-bold">${check.source}</small><br>
                                            <a href="${check.link}" target="_blank" class="text-decoration-none">
                                                ${check.title}
                                            </a>
                                        </div>
                                    `).join('')}
                                </div>
                            ` : ''}
                        </div>
                    ` : ''}
                </div>
                
                ${result.user_explanation ? `
                <div class="mt-4">
                    <h6 class="fw-bold mb-3">
                        <i class="fas fa-lightbulb me-2"></i>Penjelasan Lengkap
                    </h6>
                    
                    <div class="card border-info border-opacity-25">
                        <div class="card-body">
                            <div class="mb-3">
                                <h6 class="text-info mb-2"><i class="fas fa-info-circle me-1"></i>Ringkasan</h6>
                                <p class="mb-0">${result.user_explanation.summary}</p>
                            </div>
                            
                            ${result.user_explanation.detailed_explanation ? `
                            <div class="mb-3">
                                <h6 class="text-info mb-2"><i class="fas fa-list me-1"></i>Penjelasan Detail</h6>
                                <div class="bg-light p-3 rounded">
                                    <pre class="mb-0" style="white-space: pre-wrap; font-family: inherit;">${result.user_explanation.detailed_explanation}</pre>
                                </div>
                            </div>
                            ` : ''}
                            
                            <div class="mb-3">
                                <h6 class="text-info mb-2"><i class="fas fa-check-circle me-1"></i>Hasil Fact-Check</h6>
                                <div class="alert ${result.prediction === 'Real' ? 'alert-success' : 'alert-warning'} mb-0">
                                    <pre style="white-space: pre-wrap; font-family: inherit; margin: 0;">${result.user_explanation.fact_check_result}</pre>
                                </div>
                            </div>
                            
                            <div class="mb-0">
                                <h6 class="text-info mb-2"><i class="fas fa-thumbs-up me-1"></i>Rekomendasi</h6>
                                <div class="bg-info bg-opacity-10 p-3 rounded">
                                    <p class="mb-0">${result.user_explanation.recommendation}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                ` : ''}
                
                ${result.related_authentic_news && result.related_authentic_news.related_articles.length > 0 ? `
                <div class="mt-4">
                    <h6 class="fw-bold mb-3">
                        <i class="fas fa-newspaper me-2"></i>Berita Terkait dari Sumber Terpercaya
                    </h6>
                    <div class="row">
                        ${result.related_authentic_news.related_articles.map((article, index) => `
                            <div class="col-md-6 mb-3">
                                <div class="card h-100 border-success border-opacity-25">
                                    <div class="card-body">
                                        <div class="d-flex justify-content-between align-items-start mb-2">
                                            <span class="badge bg-success bg-opacity-10 text-success">${article.source}</span>
                                            ${article.relevance_score ? `<small class="text-muted">Relevansi: ${article.relevance_score}</small>` : ''}
                                        </div>
                                        <h6 class="card-title">
                                            <a href="${article.link}" target="_blank" class="text-decoration-none text-dark">
                                                ${article.title}
                                            </a>
                                        </h6>
                                        ${article.excerpt ? `<p class="card-text text-muted small">${article.excerpt}</p>` : ''}
                                        <div class="mt-auto">
                                            <a href="${article.link}" target="_blank" class="btn btn-outline-success btn-sm">
                                                <i class="fas fa-external-link-alt me-1"></i>Baca Selengkapnya
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    <div class="alert alert-success bg-opacity-10 border-success">
                        <small>
                            <i class="fas fa-info-circle me-1"></i>
                            ${result.related_authentic_news.message}. 
                            Kata kunci yang digunakan: <strong>${result.related_authentic_news.keywords_used.join(', ')}</strong>
                        </small>
                    </div>
                </div>
                ` : ''}
                
                <div class="mt-3">
                    <h6 class="fw-bold mb-2">
                        <i class="fas fa-robot me-2"></i>Prediksi Individual Model
                    </h6>
                    <div class="row">
                        ${Object.entries(result.individual_predictions).map(([model, pred]) => `
                            <div class="col-md-4 mb-2">
                                <div class="text-center p-2 bg-light rounded">
                                    <strong>${model.replace('_', ' ').toUpperCase()}</strong><br>
                                    <span class="text-${pred.prediction === 'Real' ? 'success' : 'danger'}">${pred.prediction}</span><br>
                                    <small class="text-muted">${(pred.confidence * 100).toFixed(1)}%</small>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    
                    ${result.ml_prediction !== result.prediction ? `
                        <div class="alert alert-info mt-2">
                            <small><i class="fas fa-info-circle me-1"></i>
                            <strong>OVERRIDE:</strong> Model ML memprediksi <strong>${result.ml_prediction}</strong> (${(result.ml_confidence * 100).toFixed(1)}%), 
                            tetapi berdasarkan <strong>${result.decision_basis.toLowerCase()}</strong>, 
                            keputusan final adalah: <strong>${result.prediction}</strong> (${(result.confidence * 100).toFixed(1)}%)
                            </small>
                        </div>
                    ` : result.verification_weight > 0.5 ? `
                        <div class="alert alert-success mt-2">
                            <small><i class="fas fa-check-circle me-1"></i>
                            <strong>VERIFIKASI KUAT:</strong> Keputusan didukung oleh ${result.decision_basis.toLowerCase()} 
                            dengan bobot ${(result.verification_weight * 100).toFixed(0)}%
                            </small>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
    
    resultDiv.style.display = 'block';
}

function displayError(message) {
    const resultDiv = document.getElementById('resultDiv');
    resultDiv.innerHTML = `
        <div class="alert alert-danger" role="alert">
            <i class="fas fa-exclamation-circle me-2"></i>
            ${message}
        </div>
    `;
    resultDiv.style.display = 'block';
}

async function loadHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/history`);
        
        if (!response.ok) {
            throw new Error('Failed to load history');
        }
        
        const history = await response.json();
        displayHistory(history);
        
    } catch (error) {
        console.error('Error loading history:', error);
        document.getElementById('historyDiv').innerHTML = `
            <p class="text-muted">Tidak dapat memuat riwayat analisis.</p>
        `;
    }
}

function displayHistory(history) {
    const historyDiv = document.getElementById('historyDiv');
    
    if (!history || history.length === 0) {
        historyDiv.innerHTML = '<p class="text-muted">Belum ada riwayat analisis.</p>';
        return;
    }
    
    historyDiv.innerHTML = history.map(item => {
        const isReal = item.prediction === 'Real';
        const badgeClass = isReal ? 'badge-real' : 'badge-fake';
        const date = new Date(item.timestamp).toLocaleDateString('id-ID', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        return `
            <div class="history-item">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <span class="badge ${badgeClass}">${isReal ? 'ASLI' : 'HOAX'}</span>
                    <small class="text-muted">${date}</small>
                </div>
                <p class="mb-1">${item.preview}${item.preview.length >= 100 ? '...' : ''}</p>
                <small class="text-muted">Kepercayaan: ${(item.confidence * 100).toFixed(1)}%</small>
            </div>
        `;
    }).join('');
}