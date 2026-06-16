// Web Audio Synthesizer for High-Craft Audio Feedback
class AudioSynth {
    constructor() {
        this.ctx = null;
    }

    init() {
        if (!this.ctx) {
            this.ctx = new (window.AudioContext || window.webkitAudioContext)();
        }
    }

    // Play a short, clean tick sound
    playTick() {
        this.init();
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        
        osc.frequency.setValueAtTime(800, this.ctx.currentTime);
        gain.gain.setValueAtTime(0.05, this.ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.05);
        
        osc.start();
        osc.stop(this.ctx.currentTime + 0.05);
    }

    // Play an ascending sweep chime for step completion
    playSuccess() {
        this.init();
        const now = this.ctx.currentTime;
        
        // Dynamic notes: C5 then G5
        this.playTone(523.25, 0.1, 0.15); // C5
        setTimeout(() => {
            this.playTone(783.99, 0.1, 0.25); // G5
        }, 120);
    }

    // Play a beautiful, rich major triad arpeggio for session completion
    playVictory() {
        this.init();
        const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
        notes.forEach((freq, index) => {
            setTimeout(() => {
                this.playTone(freq, 0.15, 0.4);
            }, index * 150);
        });
    }

    // Play a warning chime when timer runs out
    playTimerWarning() {
        this.init();
        this.playTone(440, 0.15, 0.2); // A4
        setTimeout(() => {
            this.playTone(440, 0.15, 0.2); // A4
        }, 200);
    }

    playTone(frequency, attack, duration) {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sine';
        osc.connect(gain);
        gain.connect(this.ctx.destination);

        const now = this.ctx.currentTime;
        osc.frequency.setValueAtTime(frequency, now);
        
        // Attack
        gain.gain.setValueAtTime(0, now);
        gain.gain.linearRampToValueAtTime(0.12, now + attack);
        // Release
        gain.gain.exponentialRampToValueAtTime(0.001, now + duration);

        osc.start(now);
        osc.stop(now + duration);
    }
}

// App State
const state = {
    currentSession: null,
    currentStepIdx: 0,
    timerInterval: null,
    timerSeconds: 0,
    totalDurationSeconds: 0,
    timerIsRunning: false,
    synth: new AudioSynth()
};

// SVG Progress Ring Parameters
const CIRCLE_RADIUS = 145;
const CIRCUMFERENCE = 2 * Math.PI * CIRCLE_RADIUS; // ~911.06 px

// DOM Elements
const panelEntry = document.getElementById("panel-entry");
const panelFocus = document.getElementById("panel-focus");
const panelHistory = document.getElementById("panel-history");

const formTaskCreator = document.getElementById("form-task-creator");
const inputTaskName = document.getElementById("input-task-name");
const inputDuration = document.getElementById("input-duration");
const sliderValueDisplay = document.getElementById("slider-value-display");
const btnDecompose = document.getElementById("btn-decompose");

const sessionTaskTitle = document.getElementById("session-task-title");
const timerDisplay = document.getElementById("timer-display");
const timerRingPath = document.getElementById("timer-ring-path");
const currentStepIndexEl = document.getElementById("current-step-index");
const totalStepCountEl = document.getElementById("total-step-count");
const stepTitleEl = document.getElementById("step-title");
const stepExplanationEl = document.getElementById("step-explanation");
const timerToggleText = document.getElementById("timer-toggle-text");
const sessionTotalEst = document.getElementById("session-total-est");

const btnTimerToggle = document.getElementById("btn-timer-toggle");
const btnStepComplete = document.getElementById("btn-step-complete");
const btnAbortSession = document.getElementById("btn-abort-session");

const historyList = document.getElementById("history-list");
const historyCount = document.getElementById("history-count");
const statStreak = document.getElementById("stat-streak");
const statVictories = document.getElementById("stat-victories");

// Initialize Progress Ring Stroke Properties
timerRingPath.style.strokeDasharray = `${CIRCUMFERENCE} ${CIRCUMFERENCE}`;
timerRingPath.style.strokeDashoffset = CIRCUMFERENCE;

// Initialize Available Duration Slider Listeners
inputDuration.addEventListener("input", (e) => {
    sliderValueDisplay.textContent = `${e.target.value} mins`;
});

// Load stats and history on startup
document.addEventListener("DOMContentLoaded", () => {
    loadStats();
    loadHistory();
});

// API Integration: Fetch User Stats
async function loadStats() {
    try {
        const res = await fetch("/api/stats");
        if (res.ok) {
            const data = await res.json();
            statStreak.textContent = `${data.current_streak}d`;
            statVictories.textContent = data.total_micro_tasks_completed;
        }
    } catch (err) {
        console.error("Failed to load user stats:", err);
    }
}

// API Integration: Fetch History Sessions
async function loadHistory() {
    try {
        const res = await fetch("/api/sessions?limit=10");
        if (res.ok) {
            const sessions = await res.json();
            renderHistory(sessions);
        }
    } catch (err) {
        console.error("Failed to load history:", err);
    }
}

// Render Recent Victories panel
function renderHistory(sessions) {
    if (!sessions || sessions.length === 0) {
        historyList.innerHTML = `<p class="empty-state">No victories logged yet. Let's break some starting resistance!</p>`;
        historyCount.textContent = "0 Sessions";
        return;
    }

    historyCount.textContent = `${sessions.length} Session${sessions.length > 1 ? 's' : ''}`;
    historyList.innerHTML = "";
    
    sessions.forEach(session => {
        const dateObj = new Date(session.created_at);
        const formattedDate = dateObj.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
        
        const isCompleted = session.completed;
        const statusClass = isCompleted ? 'status-completed' : 'status-partial';
        const statusLabel = isCompleted ? 'Success' : `${session.completed_steps}/${session.total_steps} steps`;

        const item = document.createElement("div");
        item.className = "history-item";
        item.innerHTML = `
            <div class="history-item-left">
                <span class="history-item-title">${escapeHTML(session.task_name)}</span>
                <div class="history-item-meta">
                    <span>${formattedDate}</span>
                    <span>•</span>
                    <span>${session.duration_minutes ? session.duration_minutes + 'm limit' : 'no limit'}</span>
                </div>
            </div>
            <span class="history-status-pill ${statusClass}">${statusLabel}</span>
        `;
        historyList.appendChild(item);
    });
}

// Helper: Escape HTML to prevent injection
function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
        tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
    );
}

// Form Submission: Create Task Session
formTaskCreator.addEventListener("submit", async (e) => {
    e.preventDefault();
    state.synth.init(); // Initialize audio context on user gesture
    
    const taskName = inputTaskName.value.trim();
    const duration = parseInt(inputDuration.value);
    
    if (!taskName) return;

    // Loading State UI update
    btnDecompose.classList.add("disabled");
    btnDecompose.querySelector(".btn-text").textContent = "Decomposing Inertia...";
    
    try {
        const response = await fetch("/api/sessions", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                task_name: taskName,
                duration_minutes: duration
            })
        });

        if (!response.ok) {
            throw new Error("Failed to decompose task");
        }

        const session = await response.json();
        startFocusSession(session);
    } catch (err) {
        alert("Unable to reach the breakdown generator. Please try again.");
        console.error(err);
    } finally {
        btnDecompose.classList.remove("disabled");
        btnDecompose.querySelector(".btn-text").textContent = "Decompose Task";
    }
});

// Setup and Launch Active Focus Panel
function startFocusSession(session) {
    state.currentSession = session;
    state.currentStepIdx = 0;
    
    // Set static details
    sessionTaskTitle.textContent = session.task_name.toUpperCase();
    totalStepCountEl.textContent = session.steps.length;
    
    // Calculate total session time estimate
    const totalSeconds = session.steps.reduce((acc, step) => acc + step.estimated_seconds, 0);
    sessionTotalEst.textContent = `${Math.ceil(totalSeconds / 60)}m`;

    // Load first step
    loadStep(0);
    
    // Panel Transition animations
    panelEntry.classList.add("hidden");
    panelHistory.classList.add("hidden");
    panelFocus.classList.remove("hidden");
    
    // Play welcoming start chime
    state.synth.playSuccess();
}

// Load a specific step into the Focus Panel
function loadStep(index) {
    state.currentStepIdx = index;
    const step = state.currentSession.steps[index];
    
    currentStepIndexEl.textContent = index + 1;
    stepTitleEl.textContent = step.title;
    stepExplanationEl.textContent = step.explanation;
    
    // Configure timers
    pauseTimer();
    state.timerSeconds = step.estimated_seconds;
    state.totalDurationSeconds = step.estimated_seconds;
    updateTimerDisplay();
    updateProgressRing(1); // Reset ring to 100% full
}

// Update Timer Display Text (MM:SS)
function updateTimerDisplay() {
    const mins = Math.floor(state.timerSeconds / 60);
    const secs = state.timerSeconds % 60;
    timerDisplay.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// Update SVG Progress Ring countdown
function updateProgressRing(percent) {
    // Offset ranges from 0 (completely full) to CIRCUMFERENCE (empty)
    const offset = CIRCUMFERENCE - (percent * CIRCUMFERENCE);
    timerRingPath.style.strokeDashoffset = offset;
}

// Timer controls
function startTimer() {
    if (state.timerIsRunning) return;
    state.timerIsRunning = true;
    timerToggleText.textContent = "Pause Timer";
    
    state.timerInterval = setInterval(() => {
        if (state.timerSeconds > 0) {
            state.timerSeconds--;
            updateTimerDisplay();
            
            const percent = state.timerSeconds / state.totalDurationSeconds;
            updateProgressRing(percent);
            
            // Audio tick for focus every 10 seconds (subtle)
            if (state.timerSeconds % 10 === 0 && state.timerSeconds > 0) {
                state.synth.playTick();
            }
        } else {
            // Timer expired
            clearInterval(state.timerInterval);
            state.timerIsRunning = false;
            timerToggleText.textContent = "Resume Timer";
            state.synth.playTimerWarning();
        }
    }, 1000);
}

function pauseTimer() {
    if (!state.timerIsRunning) return;
    state.timerIsRunning = false;
    clearInterval(state.timerInterval);
    timerToggleText.textContent = "Start Timer";
}

// Toggle Timer Listener
btnTimerToggle.addEventListener("click", () => {
    state.synth.init();
    if (state.timerIsRunning) {
        pauseTimer();
    } else {
        startTimer();
    }
});

// Complete Step Action Listener
btnStepComplete.addEventListener("click", async () => {
    state.synth.init();
    pauseTimer();
    
    const currentStep = state.currentSession.steps[state.currentStepIdx];
    const isLastStep = state.currentStepIdx === state.currentSession.steps.length - 1;
    
    // Disable complete button temporarily
    btnStepComplete.classList.add("disabled");
    
    try {
        // Send completion status to the backend SQLite database
        const res = await fetch(`/api/steps/${currentStep.id}?completed=true`, {
            method: "PUT"
        });

        if (!res.ok) throw new Error("Failed to complete step");

        if (isLastStep) {
            // Completed all steps!
            state.synth.playVictory();
            setTimeout(() => {
                endFocusSession();
            }, 600);
        } else {
            // Load next step
            state.synth.playSuccess();
            loadStep(state.currentStepIdx + 1);
        }
    } catch (err) {
        console.error(err);
        alert("Failed to record task progress. Please verify backend connection.");
    } finally {
        btnStepComplete.classList.remove("disabled");
    }
});

// Abort / Back button logic
btnAbortSession.addEventListener("click", () => {
    if (confirm("Are you sure you want to abort? Your completed steps will still be saved, but the session will remain incomplete.")) {
        endFocusSession();
    }
});

// Return to Dashboard and update lists
function endFocusSession() {
    pauseTimer();
    state.currentSession = null;
    state.currentStepIdx = 0;
    
    // Panel Transition
    panelFocus.classList.add("hidden");
    panelEntry.classList.remove("hidden");
    panelHistory.classList.remove("hidden");
    
    // Reset task form input
    inputTaskName.value = "";
    
    // Reload lists
    loadStats();
    loadHistory();
}
