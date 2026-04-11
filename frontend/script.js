// Song Genie Frontend JavaScript
class SongGenieGame {
    constructor() {
        this.session_id = null;
        this.currentType = null;
        this.questionCount = 0;
        this.init();
    }

    init() {
        this.setupThemeToggle();
        this.loadTheme();
        this.startGame();
    }

    // Theme management
    setupThemeToggle() {
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        console.log('Theme switched to:', newTheme);
    }

    loadTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        console.log('Theme loaded:', savedTheme);
    }

    // Game management
    async startGame() {
        this.resetUI();
        this.showLoading();
        
        try {
            console.log('Making request to /start...');
            const res = await fetch("/start", {
                method: "GET",
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            });
            
            console.log('Response status:', res.status);
            console.log('Response ok:', res.ok);
            
            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            
            const data = await res.json();
            console.log('Response data:', data);
            
            this.session_id = data.session_id;
            this.updateSessionId(data.session_id);
            this.handleResponse(data);
        } catch (error) {
            console.error('Failed to start game:', error);
            console.error('Error details:', error.message);
            this.showError('Failed to start game. Please try again.');
        }
    }

    async sendAnswer(answer) {
        this.disableAnswerButtons();
        this.showLoading();

        try {
            const res = await fetch("/answer", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: this.session_id,
                    answer: answer
                })
            });

            const data = await res.json();
            this.handleResponse(data);
        } catch (error) {
            console.error('Failed to send answer:', error);
            this.showError('Failed to send answer. Please try again.');
            this.enableAnswerButtons();
        }
    }

    handleResponse(data) {
        this.hideLoading();
        
        // Check if response has a question (initial response)
        if (data.question) {
            this.showQuestion(data);
        } else if (data.type === "guess") {
            this.showGuess(data);
        } else if (data.type === "learn") {
            this.showLearning(data);
        } else {
            // Handle case where backend returns "learn" without explicit type
            // This happens when AI can't find the song
            this.showLearning(data);
        }
    }

    showQuestion(data) {
        console.log('showQuestion called with data:', data);
        
        // Update question text
        const questionElement = document.getElementById('question-text');
        if (questionElement) {
            questionElement.textContent = data.question.text;
            console.log('Question text updated to:', data.question.text);
        } else {
            console.error('question-text element not found!');
        }
        
        // Increment count after showing question
        this.questionCount++;
        this.updateProgress();
        this.updateQuestionNumber();
        
        // Show question section, hide others
        const answersSection = document.getElementById('answers-section');
        if (answersSection) {
            answersSection.style.display = 'block';
            console.log('Answers section shown');
        }
        
        document.getElementById('result-section').style.display = 'none';
        document.getElementById('learning-section').style.display = 'none';
        
        // Enable answer buttons
        this.enableAnswerButtons();
    }

    showGuess(data) {
        // Hide question section
        document.getElementById('answers-section').style.display = 'none';
        
        // Show result section
        const resultSection = document.getElementById('result-section');
        resultSection.style.display = 'block';
        
        // Update result content
        document.getElementById('result-title').textContent = 
            `I'm guessing: ${data.song_name || `Song ID ${data.song_id}`} (confidence ${(data.confidence * 100).toFixed(1)}%)`;
        
        // Update confidence bar
        const confidencePercent = data.confidence * 100;
        document.getElementById('confidence-fill').style.width = `${confidencePercent}%`;
        document.getElementById('confidence-text').textContent = `Confidence: ${confidencePercent.toFixed(1)}%`;
        
        // Show top candidates if available
        if (data.top_candidates && data.top_candidates.length > 0) {
            this.showTopCandidates(data.top_candidates);
        }
        
        // Hide top candidates section if no candidates
        const candidatesSection = document.getElementById('top-candidates');
        if (!data.top_candidates || data.top_candidates.length === 0) {
            candidatesSection.style.display = 'none';
        }
    }

    showLearning(data) {
        // Hide question section
        document.getElementById('answers-section').style.display = 'none';
        
        // Show learning section
        document.getElementById('learning-section').style.display = 'block';
        
        // Hide top candidates
        document.getElementById('top-candidates').style.display = 'none';
        
        // Show closest matches if available
        if (data.top_candidates && data.top_candidates.length > 0) {
            this.showClosestMatches(data.top_candidates);
        }
        
        // You could show inferred features here if needed
        if (data.inferred_features) {
            console.log('Inferred features:', data.inferred_features);
        }
    }

    showClosestMatches(candidates) {
        const matchesContainer = document.getElementById('closest-matches');
        matchesContainer.innerHTML = '';
        
        candidates.slice(0, 3).forEach((candidate, index) => {
            const matchDiv = document.createElement('div');
            matchDiv.className = 'match-item';
            matchDiv.innerHTML = `
                <span class="match-name">${candidate.name || `Song ${candidate.id}`}</span>
                <span class="match-confidence">${(candidate.confidence * 100).toFixed(1)}%</span>
            `;
            matchesContainer.appendChild(matchDiv);
        });
    }

    confirmCorrect() {
        console.log('User confirmed: AI was correct');
        alert('Great! Thanks for confirming I was right!');
        setTimeout(() => {
            if (game) {
                game.startGame();
            }
        }, 1500);
    }

    confirmIncorrect() {
        console.log('User confirmed: AI was incorrect');
        const userSongInput = document.getElementById('user-song-input');
        const confirmationSection = document.querySelector('.confirmation-section');
        
        // Hide confirmation buttons and show song input
        confirmationSection.style.display = 'none';
        userSongInput.style.display = 'block';
        userSongInput.focus();
    }

    submitUserSong() {
        const userSongInput = document.getElementById('user-song-input');
        const songName = userSongInput.value.trim();
        
        if (!songName) {
            alert('Please enter the song name and artist');
            return;
        }
        
        console.log('User submitted song:', songName);
        alert('Thank you for your feedback! This will help me improve.');
        
        // Clear input and restart game
        userSongInput.value = '';
        setTimeout(() => {
            if (game) {
                game.startGame();
            }
        }, 2000);
    }

    showTopCandidates(candidates) {
        const candidatesList = document.getElementById('candidates-list');
        const candidatesSection = document.getElementById('top-candidates');
        
        candidatesList.innerHTML = '';
        
        candidates.slice(0, 5).forEach((candidate, index) => {
            const candidateDiv = document.createElement('div');
            candidateDiv.className = 'candidate';
            candidateDiv.innerHTML = `
                <span class="candidate-name">${candidate.name || `Song ${candidate.id}`}</span>
                <span class="candidate-confidence">${(candidate.confidence * 100).toFixed(1)}%</span>
            `;
            candidatesList.appendChild(candidateDiv);
        });
        
        candidatesSection.style.display = 'block';
    }

    // UI helper methods
    resetUI() {
        this.questionCount = 0;
        this.updateProgress();
        this.updateQuestionNumber();
        document.getElementById('answers-section').style.display = 'none';
        document.getElementById('result-section').style.display = 'none';
        document.getElementById('learning-section').style.display = 'none';
        document.getElementById('top-candidates').style.display = 'none';
        document.getElementById('question-text').textContent = 'Think of a song, and I\'ll try to guess it...';
    }

    updateProgress() {
        const progressFill = document.getElementById('progress-fill');
        const maxQuestions = 20; // Estimate max questions
        const progress = Math.min((this.questionCount / maxQuestions) * 100, 100);
        progressFill.style.width = `${progress}%`;
    }

    updateQuestionNumber() {
        document.getElementById('current-question').textContent = this.questionCount + 1;
        document.getElementById('question-counter').textContent = `Question ${this.questionCount + 1}`;
    }

    updateSessionId(sessionId) {
        document.getElementById('session-id').textContent = sessionId.substring(0, 8) + '...';
    }

    updateQuestionsCount() {
        document.getElementById('questions-count').textContent = this.questionCount;
    }

    enableAnswerButtons() {
        const buttons = document.querySelectorAll('.answer-btn');
        buttons.forEach(btn => btn.disabled = false);
        this.updateQuestionsCount();
    }

    disableAnswerButtons() {
        const buttons = document.querySelectorAll('.answer-btn');
        buttons.forEach(btn => btn.disabled = true);
    }

    showLoading() {
        const questionCard = document.querySelector('.question-card');
        if (questionCard) {
            questionCard.classList.add('loading');
        }
    }

    hideLoading() {
        const questionCard = document.querySelector('.question-card');
        if (questionCard) {
            questionCard.classList.remove('loading');
        }
    }

    showError(message) {
        // You could implement a toast notification here
        console.error(message);
        // For now, just update the question text
        document.getElementById('question-text').textContent = message;
    }
}

// Global functions for onclick handlers
let game;

function sendAnswer(answer) {
    if (game) {
        game.sendAnswer(answer);
    }
}

function startGame() {
    if (game) {
        game.startGame();
    }
}

function submitFeedback() {
    const feedbackInput = document.getElementById('song-feedback');
    const feedback = feedbackInput.value.trim();
    
    if (!feedback) {
        alert('Please enter the song name and artist');
        return;
    }
    
    // Send feedback to backend (you can implement this endpoint)
    console.log('Feedback submitted:', feedback);
    
    // Clear input and show confirmation
    feedbackInput.value = '';
    alert('Thank you for your feedback! This will help me improve.');
    
    // Optionally restart game
    setTimeout(() => {
        if (game) {
            game.startGame();
        }
    }, 2000);
}

// Initialize the game when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    game = new SongGenieGame();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && game && !game.session_id) {
        // Restart game if page becomes visible and no session exists
        game.startGame();
    }
});

// Add keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (!game || !game.session_id) return;
    
    // Only handle keys when answer buttons are enabled
    const answerButtons = document.querySelectorAll('.answer-btn');
    const areButtonsEnabled = Array.from(answerButtons).some(btn => !btn.disabled);
    
    if (!areButtonsEnabled) return;
    
    switch(e.key.toLowerCase()) {
        case 'y':
        case '1':
            game.sendAnswer('yes');
            break;
        case 'n':
        case '2':
            game.sendAnswer('no');
            break;
        case 'u':
        case '3':
        case ' ':
            game.sendAnswer('unsure');
            break;
        case 'r':
            if (e.ctrlKey || e.metaKey) {
                e.preventDefault();
                game.startGame();
            }
            break;
    }
});

// Add smooth scrolling
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});