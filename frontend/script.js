const API_BASE_URL = 'http://localhost:5000/api';

document.addEventListener('DOMContentLoaded', function() {
    initializeFloatingCursors();
    initializeCursorSelection();
    
    // Landing page navigation
    const startBtn = document.getElementById('startBtn');
    const backBtn = document.getElementById('backBtn');
    const landingPage = document.getElementById('landingPage');
    const mainApp = document.getElementById('mainApp');
    
    startBtn.addEventListener('click', function() {
        landingPage.style.display = 'none';
        mainApp.style.display = 'block';
        // Hide all cursors and selection box when entering main app
        document.body.classList.add('hide-cursors');
        loadHistory();
    });
    
    backBtn.addEventListener('click', function() {
        mainApp.style.display = 'none';
        landingPage.style.display = 'flex';
        // Show cursors and selection box when back to landing
        document.body.classList.remove('hide-cursors');
        // Reset form
        document.getElementById('newsText').value = '';
        document.getElementById('resultSelection').style.display = 'none';
        document.getElementById('detailedResults').style.display = 'none';
    });
    
    // Add click handler to analyze button
    const analyzeBtn = document.getElementById('analyzeBtn');
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            analyzeNews();
        });
    }
});

function initializeFloatingCursors() {
    const clickIcons = document.querySelectorAll('.click-icon');
    clickIcons.forEach((icon, index) => {
        // Smooth cursor movement animation
        function moveCursor() {
            const x = Math.random() * (window.innerWidth - 100);
            const y = Math.random() * (window.innerHeight - 80);
            
            // Add smooth transition
            icon.style.transition = 'all 2s cubic-bezier(0.25, 0.1, 0.25, 1)';
            icon.style.left = x + 'px';
            icon.style.top = y + 'px';
            
            // Schedule next movement
            setTimeout(moveCursor, 3000 + (index * 1500));
        }
        
        // Start initial movement
        setTimeout(moveCursor, 1000 + (index * 1000));
    });
}

function initializeCursorSelection() {
    const selectionBox = document.getElementById('cursorSelectionBox');
    
    // Position selection box initially
    function positionSelectionBox() {
        const x = Math.random() * (window.innerWidth - 270);
        const y = Math.random() * (window.innerHeight - 170);
        selectionBox.style.left = x + 'px';
        selectionBox.style.top = y + 'px';
    }
    
    // Initial position
    positionSelectionBox();
    selectionBox.classList.add('active');
    
    // Move selection box every 4 seconds
    setInterval(() => {
        positionSelectionBox();
    }, 4000);
    
    // Smooth mouse follow effect
    let mouseFollowTimeout;
    document.addEventListener('mousemove', (e) => {
        clearTimeout(mouseFollowTimeout);
        mouseFollowTimeout = setTimeout(() => {
            if (Math.random() < 0.008) { // 0.8% chance to trigger
                selectionBox.style.left = (e.clientX - 125) + 'px';
                selectionBox.style.top = (e.clientY - 75) + 'px';
            }
        }, 100);
    });
    
    // Window resize handler
    window.addEventListener('resize', () => {
        positionSelectionBox();
    });
}

async function analyzeNews() {
    const newsText = document.getElementById('newsText').value.trim();
    
    if (!newsText) {
        alert('Silakan masukkan teks berita terlebih dahulu.');
        return;
    }
    
    const loadingDiv = document.getElementById('loadingDiv');
    const resultSelection = document.getElementById('resultSelection');
    const detailedResults = document.getElementById('detailedResults');
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    // Show loading
    loadingDiv.style.display = 'block';
    resultSelection.style.display = 'none';
    detailedResults.style.display = 'none';
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
        displayResultSelection(result);
        loadHistory(); // Refresh history
        
    } catch (error) {
        console.error('Error:', error);
        displayError('Terjadi kesalahan saat menganalisis berita. Pastikan server backend berjalan.');
    } finally {
        loadingDiv.style.display = 'none';
        analyzeBtn.disabled = false;
    }
}

function displayResultSelection(result) {
    const resultSelection = document.getElementById('resultSelection');
    const detailedResults = document.getElementById('detailedResults');
    
    const isReal = result.prediction === 'Real';
    const confidencePercent = (result.confidence * 100).toFixed(1);
    const hoaxPercent = isReal ? (100 - parseFloat(confidencePercent)).toFixed(1) : confidencePercent;
    const faktaPercent = isReal ? confidencePercent : (100 - parseFloat(confidencePercent)).toFixed(1);
    
    // Update confidence bars and percentages
    setTimeout(() => {
        const hoaxConfidence = document.getElementById('hoaxConfidence');
        const faktaConfidence = document.getElementById('faktaConfidence');
        const hoaxPercentage = document.getElementById('hoaxPercentage');
        const faktaPercentage = document.getElementById('faktaPercentage');
        
        if (hoaxConfidence && faktaConfidence) {
            hoaxConfidence.style.width = hoaxPercent + '%';
            faktaConfidence.style.width = faktaPercent + '%';
            hoaxPercentage.textContent = hoaxPercent + '%';
            faktaPercentage.textContent = faktaPercent + '%';
        }
        
        // Highlight the winning selection
        const hoaxBox = document.getElementById('hoaxBox');
        const faktaBox = document.getElementById('faktaBox');
        
        hoaxBox.classList.remove('selected');
        faktaBox.classList.remove('selected');
        
        if (!isReal) {
            hoaxBox.classList.add('selected');
        } else {
            faktaBox.classList.add('selected');
        }
    }, 500);
    
    // Store result for detailed view
    window.currentResult = result;
    
    // Add click handlers for boxes
    const hoaxBox = document.getElementById('hoaxBox');
    const faktaBox = document.getElementById('faktaBox');
    
    hoaxBox.onclick = () => showDetailedResults(result);
    faktaBox.onclick = () => showDetailedResults(result);
    
    // Show result selection and automatically show detailed results
    resultSelection.style.display = 'block';
    showDetailedResults(result);
}

function showDetailedResults(result) {
    const detailedResults = document.getElementById('detailedResults');
    const resultContent = document.getElementById('resultContent');
    
    const isReal = result.prediction === 'Real';
    const confidencePercent = (result.confidence * 100).toFixed(1);
    
    resultContent.innerHTML = `
        <div class="result-summary">
            <div class="result-badge ${isReal ? 'fakta' : 'hoax'}">
                <i class="${isReal ? 'fas fa-check-circle' : 'fas fa-exclamation-triangle'}"></i>
                <h3>${isReal ? 'FAKTA' : 'HOAX'}</h3>
                <p>Confidence: ${confidencePercent}%</p>
            </div>
        </div>
        
        <div class="analysis-details">
            <div class="detail-section">
                <h5><i class="fas fa-robot"></i> AI Analysis</h5>
                <p><strong>Decision Basis:</strong> ${result.decision_basis}</p>
                <p><strong>Word Count:</strong> ${result.analysis.word_count}</p>
                <p><strong>Sentiment:</strong> ${result.analysis.sentiment}</p>
                <p><strong>Suspicious Indicators:</strong> ${result.analysis.suspicious_indicators}</p>
            </div>
            
            ${result.huggingface_details ? `
            <div class="detail-section">
                <h5><i class="fas fa-brain"></i> Transformer Models</h5>
                <div class="model-results">
                    ${Object.entries(result.huggingface_details.individual_results || {}).map(([model, modelResult]) => `
                        <div class="model-result">
                            <strong>${model}:</strong> 
                            <span class="${modelResult.prediction === 'REAL' ? 'text-success' : 'text-danger'}">
                                ${modelResult.prediction}
                            </span>
                            (${(modelResult.confidence * 100).toFixed(1)}%)
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
            
            ${result.real_time_verification ? `
            <div class="detail-section">
                <h5><i class="fas fa-search"></i> Real-time Verification</h5>
                <p><strong>Status:</strong> ${result.real_time_verification.message}</p>
                <p><strong>Verification Score:</strong> ${(result.real_time_verification.verification_score * 100).toFixed(1)}%</p>
                <p><strong>Keywords Used:</strong> ${result.real_time_verification.keywords_used.join(', ')}</p>
                
                ${result.real_time_verification.trusted_articles.length > 0 ? `
                    <div class="trusted-sources">
                        <h6>Trusted Sources Found:</h6>
                        ${result.real_time_verification.trusted_articles.map(article => `
                            <div class="source-item">
                                <strong>${article.source}:</strong>
                                <a href="${article.link}" target="_blank">${article.title}</a>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
            ` : ''}
        </div>
    `;
    
    detailedResults.style.display = 'block';
    detailedResults.scrollIntoView({ behavior: 'smooth' });
}

function displayError(message) {
    const resultSelection = document.getElementById('resultSelection');
    resultSelection.innerHTML = `
        <div class="error-message">
            <i class="fas fa-exclamation-circle"></i>
            <p>${message}</p>
        </div>
    `;
    resultSelection.style.display = 'block';
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
            <p class="empty-history">Tidak dapat memuat riwayat analisis.</p>
        `;
    }
}

function displayHistory(history) {
    const historyDiv = document.getElementById('historyDiv');
    
    if (!history || history.length === 0) {
        historyDiv.innerHTML = '<p class="empty-history">Belum ada riwayat analisis.</p>';
        return;
    }
    
    historyDiv.innerHTML = history.map(item => {
        const isReal = item.prediction === 'Real';
        const date = new Date(item.timestamp).toLocaleDateString('id-ID', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        return `
            <div class="history-item ${isReal ? '' : 'fake'}">
                <div class="history-header">
                    <span class="history-badge ${isReal ? 'real' : 'fake'}">
                        ${isReal ? 'FAKTA' : 'HOAX'}
                    </span>
                    <small class="history-date">${date}</small>
                </div>
                <p class="history-preview">${item.preview}${item.preview.length >= 100 ? '...' : ''}</p>
                <small class="history-confidence">Confidence: ${(item.confidence * 100).toFixed(1)}%</small>
            </div>
        `;
    }).join('');
}