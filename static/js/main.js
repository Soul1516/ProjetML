// Main Application JavaScript

const API_BASE = '/api';

// State management
let currentUser = null;
let uploadedFiles = [];
let quizData = null;
let currentQuizIndex = 0;
let quizScore = 0;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    setupEventListeners();
});

// Check authentication status
async function checkAuth() {
    try {
        const response = await fetch(`${API_BASE}/user`);
        const data = await response.json();
        
        if (data.success && data.user) {
            currentUser = data.user;
            showApp();
        } else {
            showLogin();
        }
    } catch (error) {
        showLogin();
    }
}

// Setup event listeners
function setupEventListeners() {
    // Login form
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    
    // Logout
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    
    // Image upload
    const imageInput = document.getElementById('image-input');
    imageInput.addEventListener('change', handleImageUpload);
    
    // Drag and drop
    const uploadArea = document.getElementById('upload-area');
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#4C2A85';
    });
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '#d1d5db';
    });
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#d1d5db';
        const files = Array.from(e.dataTransfer.files);
        handleFiles(files);
    });
    
    // Analyze button
    document.getElementById('analyze-btn').addEventListener('click', analyzeImages);
    
    // Patient panel tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    // Education topic selector
    const educationTopic = document.getElementById('education-topic');
    if (educationTopic) {
        educationTopic.addEventListener('change', loadEducationContent);
    }
    
    // Quiz
    document.getElementById('start-quiz-btn').addEventListener('click', startQuiz);
    
    // Motivation
    loadMotivation();
    
    // Calendar
    document.querySelectorAll('.month-btn').forEach(btn => {
        btn.addEventListener('click', () => loadCalendar(btn.dataset.month));
    });
}

// Login handler
async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('login-error');
    
    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentUser = data.user;
            showApp();
        } else {
            errorDiv.textContent = data.error || 'Échec de la connexion';
            errorDiv.classList.add('show');
        }
    } catch (error) {
        errorDiv.textContent = 'Erreur réseau. Veuillez réessayer.';
        errorDiv.classList.add('show');
    }
}

// Logout handler
async function handleLogout() {
    try {
        await fetch(`${API_BASE}/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        currentUser = null;
        showLogin();
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// Show login screen
function showLogin() {
    document.getElementById('login-screen').classList.add('active');
    document.getElementById('app-screen').classList.remove('active');
}

// Show app screen
function showApp() {
    document.getElementById('login-screen').classList.remove('active');
    document.getElementById('app-screen').classList.add('active');
    
    // Update header
    document.getElementById('user-name').textContent = currentUser.name;
    const roleSpan = document.getElementById('user-role');
    roleSpan.textContent = getRoleDisplay(currentUser.role);
    roleSpan.className = `user-role ${currentUser.role}`;
    
    // Show appropriate panel
    if (currentUser.role === 'medical' || currentUser.role === 'admin') {
        document.getElementById('doctor-panel').classList.remove('hidden');
        document.getElementById('patient-panel').classList.add('hidden');
    } else {
        document.getElementById('doctor-panel').classList.add('hidden');
        document.getElementById('patient-panel').classList.remove('hidden');
    }
}

// Get role display text
function getRoleDisplay(role) {
    const roles = {
        'medical': '👨‍⚕️ Médecin',
        'patient': '👤 Patient',
        'admin': '👑 Administrateur'
    };
    return roles[role] || role;
}

// Handle image upload
function handleImageUpload(e) {
    const files = Array.from(e.target.files);
    handleFiles(files);
}

// Handle files (upload or drop)
function handleFiles(files) {
    files.forEach(file => {
        if (file.type.startsWith('image/')) {
            uploadedFiles.push(file);
            displayUploadedImage(file);
        }
    });
    
    updateAnalyzeButton();
}

// Display uploaded image preview
function displayUploadedImage(file) {
    const container = document.getElementById('uploaded-images');
    const reader = new FileReader();
    
    reader.onload = (e) => {
        const div = document.createElement('div');
        div.className = 'uploaded-image-item';
        div.dataset.filename = file.name;
        
        div.innerHTML = `
            <img src="${e.target.result}" alt="${file.name}">
            <button class="remove-btn" onclick="removeImage('${file.name}')">×</button>
        `;
        
        container.appendChild(div);
    };
    
    reader.readAsDataURL(file);
}

// Remove image
function removeImage(filename) {
    uploadedFiles = uploadedFiles.filter(f => f.name !== filename);
    const item = document.querySelector(`[data-filename="${filename}"]`);
    if (item) item.remove();
    updateAnalyzeButton();
}

// Update analyze button state
function updateAnalyzeButton() {
    const btn = document.getElementById('analyze-btn');
    btn.disabled = uploadedFiles.length === 0;
}

// Analyze images
async function analyzeImages() {
    if (uploadedFiles.length === 0) return;
    
    const btn = document.getElementById('analyze-btn');
    btn.disabled = true;
    btn.textContent = 'Analyse en cours...';
    
    const resultsSection = document.getElementById('results-section');
    resultsSection.classList.remove('hidden');
    resultsSection.innerHTML = '<div class="loading"><div class="spinner"></div><p>Analyse des images en cours...</p></div>';
    
    try {
        const formData = new FormData();
        uploadedFiles.forEach(file => {
            formData.append('image', file);
        });
        
        // Add patient info
        const patientForm = document.getElementById('patient-form');
        const formDataObj = new FormData(patientForm);
        formData.append('age', formDataObj.get('age') || '');
        formData.append('gender', formDataObj.get('gender') || '');
        formDataObj.getAll('symptoms').forEach(s => formData.append('symptoms', s));
        formData.append('medical_history', formDataObj.get('medical_history') || '');
        
        let response;
        try {
            response = await fetch(`${API_BASE}/analyze`, {
                method: 'POST',
                credentials: 'include',
                body: formData
            });
        } catch (fetchError) {
            console.error('Fetch error:', fetchError);
            throw new Error(`Network error: ${fetchError.message}. Please ensure the server is running.`);
        }
        
        if (!response.ok) {
            let errorMessage = `HTTP ${response.status}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
            } catch (e) {
                errorMessage = `Server error (${response.status}): ${response.statusText}`;
            }
            throw new Error(errorMessage);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Handle both 'result' (single) and 'results' (multiple)
            if (data.results && data.results.length > 0) {
                displayResults(data.results);
            } else if (data.result) {
                displayResults([data.result]);
            } else {
                throw new Error('No results returned from server');
            }
        } else {
            throw new Error(data.error || 'Analysis failed');
        }
    } catch (error) {
        console.error('Analysis error:', error);
        resultsSection.innerHTML = `<div class="error-message show">Erreur: ${error.message || 'Échec de l\'analyse des images. Veuillez vérifier la console pour plus de détails.'}</div>`;
    } finally {
        btn.disabled = false;
        btn.textContent = '🔍 Analyser les Images';
    }
}

// Display analysis results
function displayResults(results) {
    const container = document.getElementById('results-section');
    
    // Handle multiple results
    if (!Array.isArray(results)) {
        results = [results];
    }
    
    container.innerHTML = results.map((result, idx) => {
        const prediction = result.prediction;
    
    const tumorTypes = {
        'glioma': 'Gliome',
        'meningioma': 'Méningiome',
        'pituitary': 'Tumeur Hypophysaire',
        'notumor': 'Aucune Tumeur Détectée'
    };
    
    const riskColors = {
        'glioma': '#ef4444',
        'meningioma': '#f59e0b',
        'pituitary': '#f59e0b',
        'notumor': '#10b981'
    };
    
        return `
            <div class="card result-item">
                <h3>📊 Résultats de l'Analyse${results.length > 1 ? ` - ${result.filename || `Image ${idx + 1}`}` : ''}</h3>
                
                <div class="result-images">
                    <div class="result-image-container">
                        <img src="${result.images.original}" alt="Original">
                        <p>Image Originale</p>
                    </div>
                    <div class="result-image-container">
                        <img src="${result.images.overlay}" alt="Segmentation">
                        <p>Masque de Segmentation</p>
                    </div>
                </div>
                
                <div class="prediction-metrics">
                    <div class="metric">
                        <div class="metric-label">Type Prédit</div>
                        <div class="metric-value">${tumorTypes[prediction.predicted_stage] || prediction.predicted_stage}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Confiance</div>
                        <div class="metric-value">${(prediction.confidence * 100).toFixed(1)}%</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Niveau de Risque</div>
                        <div class="metric-value" style="color: ${riskColors[prediction.predicted_stage] || '#6b7280'}">
                            ${prediction.risk_level}
                        </div>
                    </div>
                </div>
                
                <div class="prediction-result">
                    <h4>Distribution des Probabilités</h4>
                    <div class="probability-bar">
                        ${Object.entries(prediction.probabilities)
                            .sort((a, b) => b[1] - a[1])
                            .map(([type, prob]) => `
                                <div class="probability-item">
                                    <span class="probability-label">${tumorTypes[type] || type}</span>
                                    <div class="probability-bar-container">
                                        <div class="probability-bar-fill" style="width: ${prob * 100}%"></div>
                                    </div>
                                    <span class="probability-value">${(prob * 100).toFixed(1)}%</span>
                                </div>
                            `).join('')}
                    </div>
                </div>
                
                ${result.recommendations ? `
                    <div class="recommendations">
                        <h4>💡 Recommandations Cliniques</h4>
                        <div class="recommendations-grid">
                            ${result.recommendations.imaging ? `
                                <div class="recommendation-card">
                                    <h5>📋 Imagerie</h5>
                                    <ul>
                                        ${result.recommendations.imaging.map(item => `<li>${item}</li>`).join('')}
                                    </ul>
                                </div>
                            ` : ''}
                            ${result.recommendations.referrals ? `
                                <div class="recommendation-card">
                                    <h5>👥 Spécialistes</h5>
                                    <ul>
                                        ${result.recommendations.referrals.map(item => `<li>${item}</li>`).join('')}
                                    </ul>
                                </div>
                            ` : ''}
                            ${result.recommendations.monitoring ? `
                                <div class="recommendation-card">
                                    <h5>📊 Surveillance</h5>
                                    <ul>
                                        ${result.recommendations.monitoring.map(item => `<li>${item}</li>`).join('')}
                                    </ul>
                                </div>
                            ` : ''}
                            ${result.recommendations.next_steps ? `
                                <div class="recommendation-card">
                                    <h5>➡️ Prochaines Étapes</h5>
                                    <ul>
                                        ${result.recommendations.next_steps.map(item => `<li>${item}</li>`).join('')}
                                    </ul>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');
}

// Patient panel tab switching
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        }
    });
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
        if (content.id === `tab-${tabName}`) {
            content.classList.add('active');
        }
    });
    
    // Load content if needed
    if (tabName === 'education') {
        loadEducationContent();
    } else if (tabName === 'motivation') {
        loadMotivation();
    }
}

// Load education content
async function loadEducationContent() {
    const topic = document.getElementById('education-topic').value;
    const container = document.getElementById('education-content');
    
    try {
        const response = await fetch(`${API_BASE}/patient/education?topic=${topic}`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success && data.content) {
            // Parse markdown-like content and style it beautifully
            const content = data.content.content || '';
            const formattedContent = content
                .replace(/### (.*?)\n/g, '<h3 class="education-section-title">$1</h3>')
                .replace(/\*\*(.*?)\*\*/g, '<strong class="education-bold">$1</strong>')
                .replace(/^- (.*?)$/gm, '<li class="education-list-item">$1</li>')
                .replace(/\n/g, '<br>')
                .replace(/(<li.*?<\/li>)/g, '<ul class="education-list">$1</ul>');
            
            container.innerHTML = `
                <div class="education-card-modern">
                    <div class="education-header-modern">
                        <h2 class="education-title-modern">${data.content.title || 'Contenu Éducatif'}</h2>
                    </div>
                    <div class="education-body-modern">
                        ${formattedContent}
                        ${data.content.resources ? `
                            <div class="education-resources">
                                <h4 class="education-resources-title">📚 Resources</h4>
                                <ul class="education-resources-list">
                                    ${data.content.resources.map(r => `<li>${r}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        } else {
            container.innerHTML = '<div class="education-error">Erreur lors du chargement du contenu. Veuillez réessayer.</div>';
        }
    } catch (error) {
        console.error('Erreur éducation:', error);
        container.innerHTML = '<div class="education-error">Erreur lors du chargement du contenu. Veuillez réessayer.</div>';
    }
}

// Start quiz
async function startQuiz() {
    try {
        const response = await fetch(`${API_BASE}/patient/quiz?num=5`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.success) {
            quizData = data.questions;
            currentQuizIndex = 0;
            quizScore = 0;
            showQuizQuestion();
        }
    } catch (error) {
        console.error('Quiz error:', error);
    }
}

// Show quiz question
function showQuizQuestion() {
    const container = document.getElementById('quiz-content');
    const welcome = document.querySelector('.quiz-welcome');
    
    if (welcome) welcome.classList.add('hidden');
    container.classList.remove('hidden');
    
    if (currentQuizIndex >= quizData.length) {
        showQuizResults();
        return;
    }
    
    const question = quizData[currentQuizIndex];
    
    container.innerHTML = `
        <div class="quiz-question">
            <h3>Question ${currentQuizIndex + 1} sur ${quizData.length}</h3>
            <p style="font-size: 1.1rem; margin: 1rem 0;">${question.question}</p>
            <div class="quiz-options">
                ${question.options.map((option, idx) => `
                    <div class="quiz-option" onclick="selectQuizAnswer(${idx})">
                        ${option}
                    </div>
                `).join('')}
            </div>
            <button id="submit-quiz-answer" class="btn btn-primary" onclick="submitQuizAnswer()" disabled>Soumettre la Réponse</button>
        </div>
    `;
}

let selectedAnswer = null;

function selectQuizAnswer(index) {
    selectedAnswer = index;
    document.querySelectorAll('.quiz-option').forEach((opt, idx) => {
        opt.classList.toggle('selected', idx === index);
    });
    document.getElementById('submit-quiz-answer').disabled = false;
}

async function submitQuizAnswer() {
    if (selectedAnswer === null) return;
    
    const question = quizData[currentQuizIndex];
    const container = document.getElementById('quiz-content');
    const isCorrect = selectedAnswer === question.correct;
    
    if (isCorrect) {
        quizScore++;
        container.innerHTML += `<div style="color: #10b981; margin-top: 1rem; font-weight: 600;">✓ Correct! ${question.explanation}</div>`;
    } else {
        container.innerHTML += `<div style="color: #ef4444; margin-top: 1rem; font-weight: 600;">✗ Incorrect. ${question.explanation}</div>`;
    }
    
    currentQuizIndex++;
    selectedAnswer = null;
    
    const submitBtn = document.getElementById('submit-quiz-answer');
    if (submitBtn) submitBtn.disabled = true;
    
    setTimeout(() => {
        showQuizQuestion();
    }, 2000);
}

function showQuizResults() {
    const container = document.getElementById('quiz-content');
    container.innerHTML = `
        <div style="text-align: center; padding: 2rem;">
            <h3>Quiz Terminé!</h3>
            <p style="font-size: 1.5rem; margin: 1rem 0;">
                Votre score: <strong>${quizScore}/${quizData.length}</strong>
            </p>
            <button class="btn btn-primary" onclick="startQuiz()">Réessayer</button>
        </div>
    `;
}

// Load motivation
async function loadMotivation() {
    try {
        const response = await fetch(`${API_BASE}/patient/motivation`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            const messageEl = document.getElementById('motivation-message');
            const tipEl = document.getElementById('daily-tip');
            
            if (messageEl && data.message) {
                messageEl.textContent = data.message;
            } else if (messageEl) {
                messageEl.textContent = '🌟 Chaque jour est une nouvelle opportunité de prendre soin de votre santé.';
            }
            
            if (tipEl && data.tip) {
                tipEl.textContent = data.tip;
            } else if (tipEl) {
                tipEl.textContent = '💧 Restez hydraté! Buvez au moins 1,5L d\'eau par jour pour une santé cérébrale optimale.';
            }
        } else {
            // Contenu de secours
            document.getElementById('motivation-message').textContent = '🌟 Chaque jour est une nouvelle opportunité de prendre soin de votre santé.';
            document.getElementById('daily-tip').textContent = '💧 Restez hydraté! Buvez au moins 1,5L d\'eau par jour pour une santé cérébrale optimale.';
        }
    } catch (error) {
        console.error('Erreur motivation:', error);
        // Contenu de secours en cas d'erreur
        const messageEl = document.getElementById('motivation-message');
        const tipEl = document.getElementById('daily-tip');
        if (messageEl) messageEl.textContent = '🌟 Chaque jour est une nouvelle opportunité de prendre soin de votre santé.';
        if (tipEl) tipEl.textContent = '💧 Restez hydraté! Buvez au moins 1,5L d\'eau par jour pour une santé cérébrale optimale.';
    }
}

// Load calendar
async function loadCalendar(month) {
    // Update active button
    document.querySelectorAll('.month-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.month === month);
    });
    
    try {
        const response = await fetch(`${API_BASE}/patient/international-days?month=${month}`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        const container = document.getElementById('calendar-content');
        
        if (data.success && Object.keys(data.days).length > 0) {
            container.innerHTML = Object.entries(data.days).map(([day, info]) => `
                <div class="info-card animated-card">
                    <div class="card-badge">${day} ${month.charAt(0).toUpperCase() + month.slice(1)}</div>
                    <h4>${info.name}</h4>
                    <p>${info.description}</p>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p>Aucune journée de sensibilisation pour ce mois.</p>';
        }
    } catch (error) {
        console.error('Calendar error:', error);
    }
}
