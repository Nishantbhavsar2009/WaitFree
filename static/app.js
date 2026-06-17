// WaitFree - Front-End HUD State Controller & Audio Engine

// Web Audio API Synthesizer for Offline Premium SFX
class SynthAudio {
    constructor() {
        this.ctx = null;
        this.profile = "cyberpunk"; // "cyberpunk", "retro", "off"
    }

    init() {
        if (!this.ctx) {
            this.ctx = new (window.AudioContext || window.webkitAudioContext)();
        }
    }

    setProfile(profile) {
        this.profile = profile;
    }

    playTick() {
        if (this.profile === "off") return;
        this.init();
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.connect(gain);
        gain.connect(this.ctx.destination);

        if (this.profile === "cyberpunk") {
            osc.frequency.setValueAtTime(2000, this.ctx.currentTime);
            gain.gain.setValueAtTime(0.02, this.ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + 0.05);
            osc.start();
            osc.stop(this.ctx.currentTime + 0.05);
        } else {
            osc.type = "square";
            osc.frequency.setValueAtTime(800, this.ctx.currentTime);
            gain.gain.setValueAtTime(0.01, this.ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + 0.03);
            osc.start();
            osc.stop(this.ctx.currentTime + 0.03);
        }
    }

    playBeep() {
        if (this.profile === "off") return;
        this.init();
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.connect(gain);
        gain.connect(this.ctx.destination);

        if (this.profile === "cyberpunk") {
            // Cyberpunk minor third alert
            osc.type = "sine";
            osc.frequency.setValueAtTime(880, now);
            gain.gain.setValueAtTime(0.1, now);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.6);
            osc.start(now);
            osc.stop(now + 0.6);

            const osc2 = this.ctx.createOscillator();
            const gain2 = this.ctx.createGain();
            osc2.connect(gain2);
            gain2.connect(this.ctx.destination);
            osc2.type = "sine";
            osc2.frequency.setValueAtTime(1046.5, now + 0.1);
            gain2.gain.setValueAtTime(0.08, now + 0.1);
            gain2.gain.exponentialRampToValueAtTime(0.0001, now + 0.7);
            osc2.start(now + 0.1);
            osc2.stop(now + 0.7);
        } else {
            osc.type = "square";
            osc.frequency.setValueAtTime(440, now);
            gain.gain.setValueAtTime(0.08, now);
            gain.gain.setValueAtTime(0.08, now + 0.15);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.2);
            osc.start(now);
            osc.stop(now + 0.2);
        }
    }

    playSuccess() {
        if (this.profile === "off") return;
        this.init();
        const now = this.ctx.currentTime;
        const notes = this.profile === "cyberpunk" 
            ? [523.25, 659.25, 783.99, 1046.50] // C5 Major chord
            : [261.63, 329.63, 392.00, 523.25];
            
        notes.forEach((freq, idx) => {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            
            osc.type = this.profile === "cyberpunk" ? "sine" : "triangle";
            osc.frequency.setValueAtTime(freq, now + idx * 0.08);
            
            gain.gain.setValueAtTime(0.0, now);
            gain.gain.linearRampToValueAtTime(0.06, now + idx * 0.08 + 0.04);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + idx * 0.08 + 0.5);
            
            osc.start(now + idx * 0.08);
            osc.stop(now + idx * 0.08 + 0.5);
        });
    }

    playClick() {
        if (this.profile === "off") return;
        this.init();
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        
        osc.type = "sine";
        osc.frequency.setValueAtTime(1200, this.ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(600, this.ctx.currentTime + 0.05);
        gain.gain.setValueAtTime(0.05, this.ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + 0.05);
        
        osc.start();
        osc.stop(this.ctx.currentTime + 0.05);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const taskForm = document.getElementById("task-form");
    const taskTitleInput = document.getElementById("task-title");
    const coachingVibeSelect = document.getElementById("coaching-vibe");
    const submitBtn = document.getElementById("submit-btn");
    const streakCount = document.getElementById("streak-count");
    const userRank = document.getElementById("user-rank");
    const userXp = document.getElementById("user-xp");
    const xpProgressBar = document.getElementById("xp-progress-bar");
    const stepsContainer = document.getElementById("steps-container");
    const taskStatus = document.getElementById("task-status");
    const systemLog = document.getElementById("system-log");
    const currentTimeEl = document.getElementById("current-time");
    
    // Pill Selectors
    const pillBtns = document.querySelectorAll(".pill-btn");
    const minutesLeftInput = document.getElementById("minutes-left");
    const customInputContainer = document.querySelector(".custom-input-container");
    const customMinutesInput = document.getElementById("custom-minutes");

    // Timer Elements
    const timerHud = document.getElementById("timer-hud");
    const timerProgress = document.getElementById("timer-progress");
    const timerDigits = document.getElementById("timer-digits");
    const timerPlayPause = document.getElementById("timer-play-pause");
    const timerSkip = document.getElementById("timer-skip");

    // Recent Missions Elements
    const recentMissionsList = document.getElementById("recent-missions-list");

    // Custom Step Creation Elements
    const addSubtaskWrapper = document.getElementById("add-subtask-wrapper");
    const addSubtaskForm = document.getElementById("add-subtask-form");
    const btnAddStepTrigger = document.getElementById("btn-add-step-trigger");
    const btnSaveNewSubtask = document.getElementById("btn-save-new-subtask");
    const btnCancelNewSubtask = document.getElementById("btn-cancel-new-subtask");
    const newSubtaskTitleInput = document.getElementById("new-subtask-title");
    const newSubtaskDurationInput = document.getElementById("new-subtask-duration");

    // Sound profile setup
    const soundProfileSelect = document.getElementById("sound-profile");
    const synthAudio = new SynthAudio();
    synthAudio.setProfile(soundProfileSelect.value);
    
    soundProfileSelect.addEventListener("change", () => {
        synthAudio.setProfile(soundProfileSelect.value);
        synthAudio.playClick();
    });

    // App State
    let activeTask = null;
    let activeSubtaskIndex = -1;
    let timerInterval = null;
    let timerTimeLeft = 0;
    let timerTotalDuration = 0;
    let isTimerRunning = false;

    // 1. Initialize clock in footer
    function updateClock() {
        const now = new Date();
        currentTimeEl.textContent = now.toTimeString().split(' ')[0];
    }
    setInterval(updateClock, 1000);
    updateClock();

    // 2. Fetch statistics and render levels/ranks
    async function loadStats() {
        try {
            const response = await fetch("/api/stats");
            if (response.ok) {
                const stats = await response.json();
                streakCount.textContent = `${stats.streak}D`;
                
                // Gamification feedback
                userRank.textContent = `${stats.rank.replace("_", " ")} (LVL ${stats.level})`;
                
                const currentXP = stats.total_xp;
                const prevLevelXP = stats.prev_level_xp;
                const nextLevelXP = stats.next_level_xp;
                
                if (stats.level >= 5) {
                    xpProgressBar.style.width = "100%";
                    userXp.textContent = `${currentXP} XP (MAX)`;
                } else {
                    const range = nextLevelXP - prevLevelXP;
                    const gained = currentXP - prevLevelXP;
                    const pct = Math.max(0, Math.min(100, Math.round((gained / range) * 100)));
                    xpProgressBar.style.width = `${pct}%`;
                    userXp.textContent = `${currentXP} / ${nextLevelXP} XP`;
                }
            }
        } catch (error) {
            console.error("Error loading stats:", error);
        }
    }
    loadStats();

    // 3. Load Recent Missions
    async function loadRecentMissions() {
        try {
            const response = await fetch("/api/tasks");
            if (response.ok) {
                const tasks = await response.json();
                renderRecentMissions(tasks);
            }
        } catch (err) {
            console.error("Error loading recent missions:", err);
        }
    }
    loadRecentMissions();

    function renderRecentMissions(tasks) {
        recentMissionsList.innerHTML = "";
        
        if (!tasks || tasks.length === 0) {
            recentMissionsList.innerHTML = `<div class="recent-mission-item empty">No previous operations logged.</div>`;
            return;
        }
        
        tasks.slice(0, 5).forEach(task => {
            const total = task.subtasks.length;
            const completed = task.subtasks.filter(s => s.completed).length;
            const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
            
            const item = document.createElement("div");
            item.className = "recent-mission-item";
            item.innerHTML = `
                <span class="recent-mission-title">${task.title}</span>
                <span class="recent-mission-meta">${pct}% SUCCESS</span>
            `;
            
            item.addEventListener("click", () => {
                synthAudio.playClick();
                activeTask = task;
                systemLog.textContent = `SYS_HISTORY: Task loaded: ${task.title}`;
                
                // Show subtask wrapper
                addSubtaskWrapper.classList.remove("hidden");
                
                renderSubtasks();
                
                const firstUncompleted = activeTask.subtasks.findIndex(s => !s.completed);
                if (firstUncompleted !== -1) {
                    setActiveSubtask(firstUncompleted);
                } else {
                    finishTaskFlow();
                }
            });
            
            recentMissionsList.appendChild(item);
        });
    }

    // 4. Handle Pill Selections
    pillBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            pillBtns.forEach(p => {
                p.classList.remove("active");
                p.setAttribute("aria-checked", "false");
            });

            btn.classList.add("active");
            btn.setAttribute("aria-checked", "true");

            if (btn.classList.contains("custom-trigger")) {
                customInputContainer.classList.remove("hidden");
                customMinutesInput.required = true;
                customMinutesInput.focus();
            } else {
                customInputContainer.classList.add("hidden");
                customMinutesInput.required = false;
                minutesLeftInput.value = btn.getAttribute("data-value");
            }
        });
    });

    customMinutesInput.addEventListener("input", () => {
        minutesLeftInput.value = customMinutesInput.value;
    });

    // 5. Form Submission (Break the Freeze)
    taskForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const title = taskTitleInput.value.trim();
        const minutesLeft = parseInt(minutesLeftInput.value);
        const coachingVibe = coachingVibeSelect.value;

        if (!title || isNaN(minutesLeft)) return;

        submitBtn.disabled = true;
        submitBtn.textContent = "[BREAKING FREEZE...]";
        taskStatus.textContent = "DECOMPOSING";
        taskStatus.className = "status-indicator active";
        systemLog.textContent = "SYS_API: Splitting task into micro-actions...";

        try {
            const response = await fetch("/api/tasks", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                    title, 
                    minutes_left: minutesLeft,
                    coaching_vibe: coachingVibe
                })
            });

            if (response.ok) {
                activeTask = await response.json();
                systemLog.textContent = `SYS_API: Breakout sequence mapped. ID: ${activeTask.id}`;
                
                // Show custom subtask trigger area
                addSubtaskWrapper.classList.remove("hidden");
                
                renderSubtasks();
                startSubtaskFlow();
                loadRecentMissions();
            } else {
                const err = await response.json();
                systemLog.textContent = `SYS_ERROR: ${err.detail || "Failed to decompose task"}`;
            }
        } catch (error) {
            console.error(error);
            systemLog.textContent = "SYS_ERROR: Network request failed.";
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = "BREAK THE FREEZE";
        }
    });

    // 6. Render Checklist Steps
    function renderSubtasks() {
        stepsContainer.innerHTML = "";
        
        if (!activeTask || !activeTask.subtasks || activeTask.subtasks.length === 0) {
            stepsContainer.innerHTML = `
                <div class="terminal-placeholder">
                    <p class="blink-line">&gt; SYSTEM COMPLETED. NO STEPS DETECTED.</p>
                </div>
            `;
            return;
        }

        activeTask.subtasks.forEach((subtask, index) => {
            const card = document.createElement("div");
            card.className = `step-card ${subtask.completed ? 'completed' : ''}`;
            if (index === activeSubtaskIndex && !subtask.completed) {
                card.classList.add("active");
            }
            card.setAttribute("data-id", subtask.id);
            card.setAttribute("data-index", index);
            
            const minutes = Math.floor(subtask.duration_seconds / 60);
            const seconds = subtask.duration_seconds % 60;
            const durationStr = `${minutes}m ${seconds > 0 ? seconds + 's' : ''}`;

            card.innerHTML = `
                <div class="step-info">
                    <span class="step-title">${subtask.title}</span>
                    <div class="step-meta">
                        <span>STEP_${(index + 1).toString().padStart(2, '0')}</span>
                        <span>DURATION: ${durationStr}</span>
                    </div>
                </div>
                <div class="step-right-controls">
                    <button class="step-action-btn edit" title="Edit Step">EDIT</button>
                    <button class="step-action-btn delete" title="Delete Step">DEL</button>
                    <div class="checkbox-visual"></div>
                </div>
            `;

            // Prevent event bubbling when clicking inside input or on control buttons
            card.addEventListener("click", (e) => {
                if (e.target.tagName === "INPUT" || e.target.tagName === "BUTTON" || e.target.closest(".step-edit-form") || e.target.closest(".step-action-btn")) {
                    return;
                }
                if (subtask.completed) {
                    toggleSubtask(subtask.id, index);
                } else {
                    setActiveSubtask(index);
                }
            });

            // Specific Checkbox click handler
            const checkbox = card.querySelector(".checkbox-visual");
            checkbox.addEventListener("click", (e) => {
                e.stopPropagation();
                toggleSubtask(subtask.id, index);
            });

            // Edit button handler
            const editBtn = card.querySelector(".step-action-btn.edit");
            editBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                enterEditMode(card, subtask, index);
            });

            // Delete button handler
            const deleteBtn = card.querySelector(".step-action-btn.delete");
            deleteBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                deleteSubtaskItem(subtask.id, index);
            });

            stepsContainer.appendChild(card);
        });

        if (taskStatus.textContent !== "SUCCESS") {
            taskStatus.textContent = "ACTIVE";
            taskStatus.className = "status-indicator active";
        }
    }

    // Inline step editor
    function enterEditMode(card, subtask, index) {
        card.classList.add("editing");
        
        card.innerHTML = `
            <form class="step-edit-form">
                <div class="step-edit-inputs">
                    <input type="text" class="edit-title" value="${subtask.title}" required autocomplete="off">
                    <input type="number" class="edit-duration" value="${subtask.duration_seconds}" min="5" max="600" required>
                </div>
                <div class="step-edit-buttons">
                    <button type="submit" class="btn-sub-action">SAVE</button>
                    <button type="button" class="btn-sub-action cancel">CANCEL</button>
                </div>
            </form>
        `;
        
        const form = card.querySelector(".step-edit-form");
        const cancelBtn = card.querySelector(".cancel");
        
        cancelBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            card.classList.remove("editing");
            renderSubtasks();
        });
        
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const newTitle = card.querySelector(".edit-title").value.trim();
            const newDur = parseInt(card.querySelector(".edit-duration").value);
            
            if (!newTitle || isNaN(newDur)) return;
            
            try {
                const response = await fetch(`/api/subtasks/${subtask.id}/content`, {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ title: newTitle, duration_seconds: newDur })
                });
                
                if (response.ok) {
                    subtask.title = newTitle;
                    subtask.duration_seconds = newDur;
                    systemLog.textContent = `SYS_EDITOR: Step ${index + 1} updated.`;
                    card.classList.remove("editing");
                    
                    if (index === activeSubtaskIndex) {
                        timerTotalDuration = newDur;
                        timerTimeLeft = Math.min(timerTimeLeft, newDur);
                        updateTimerVisuals();
                    }
                    
                    renderSubtasks();
                } else {
                    systemLog.textContent = "SYS_ERROR: Failed to update step content.";
                }
            } catch (err) {
                console.error(err);
                systemLog.textContent = "SYS_ERROR: Update network call failed.";
            }
        });
    }

    // Delete subtask action
    async function deleteSubtaskItem(id, index) {
        if (!confirm("Delete this decomposition step?")) return;
        synthAudio.playClick();
        
        try {
            const response = await fetch(`/api/subtasks/${id}`, {
                method: "DELETE"
            });
            
            if (response.ok) {
                activeTask.subtasks.splice(index, 1);
                systemLog.textContent = `SYS_EDITOR: Step removed.`;
                
                if (index === activeSubtaskIndex) {
                    clearInterval(timerInterval);
                    timerHud.classList.add("hidden");
                    activeSubtaskIndex = -1;
                } else if (index < activeSubtaskIndex) {
                    activeSubtaskIndex--;
                }
                
                renderSubtasks();
                loadStats();
                loadRecentMissions();
                
                if (activeTask.subtasks.length === 0) {
                    finishTaskFlow();
                }
            } else {
                systemLog.textContent = "SYS_ERROR: Failed to delete step.";
            }
        } catch (err) {
            console.error(err);
            systemLog.textContent = "SYS_ERROR: Delete request failed.";
        }
    }

    // 7. Initiate Active Flow (ADHD Focus Timer Engine)
    function startSubtaskFlow() {
        const firstUncompletedIndex = activeTask.subtasks.findIndex(s => !s.completed);
        
        if (firstUncompletedIndex === -1) {
            finishTaskFlow();
            return;
        }

        setActiveSubtask(firstUncompletedIndex);
    }

    function setActiveSubtask(index) {
        activeSubtaskIndex = index;
        const activeSubtask = activeTask.subtasks[index];

        // Setup Timer HUD
        timerTotalDuration = activeSubtask.duration_seconds;
        timerTimeLeft = timerTotalDuration;
        
        timerHud.classList.remove("hidden");
        updateTimerVisuals();
        
        // Highlight active step
        renderSubtasks();
        
        // Start running immediately
        startTimer();
        systemLog.textContent = `SYS_FOCUS: Active Step: "${activeSubtask.title}". Focus now.`;
    }

    // 8. Timer Controller Functions
    function startTimer() {
        if (timerInterval) clearInterval(timerInterval);
        isTimerRunning = true;
        timerPlayPause.textContent = "PAUSE";
        
        timerInterval = setInterval(() => {
            timerTimeLeft--;
            updateTimerVisuals();

            // Sound tick countdown in last 10 seconds
            if (timerTimeLeft <= 10 && timerTimeLeft > 0) {
                synthAudio.playTick();
            }

            if (timerTimeLeft <= 0) {
                clearInterval(timerInterval);
                isTimerRunning = false;
                timerDigits.textContent = "00:00";
                synthAudio.playBeep();
                systemLog.textContent = `SYS_ALERT: Step time expired. Complete step to proceed.`;
            }
        }, 1000);
    }

    function pauseTimer() {
        clearInterval(timerInterval);
        isTimerRunning = false;
        timerPlayPause.textContent = "RESUME";
    }

    function updateTimerVisuals() {
        const mins = Math.floor(timerTimeLeft / 60).toString().padStart(2, '0');
        const secs = (timerTimeLeft % 60).toString().padStart(2, '0');
        timerDigits.textContent = `${mins}:${secs}`;

        const progressFraction = timerTimeLeft / timerTotalDuration;
        const offset = 283 * (1 - progressFraction);
        timerProgress.style.strokeDashoffset = offset;
    }

    timerPlayPause.addEventListener("click", () => {
        synthAudio.playClick();
        if (isTimerRunning) {
            pauseTimer();
        } else {
            startTimer();
        }
    });

    timerSkip.addEventListener("click", () => {
        synthAudio.playClick();
        clearInterval(timerInterval);
        systemLog.textContent = `SYS_TIMER: Step ${activeSubtaskIndex + 1} skipped.`;
        
        const nextIndex = activeSubtaskIndex + 1;
        if (nextIndex < activeTask.subtasks.length) {
            setActiveSubtask(nextIndex);
        } else {
            finishTaskFlow();
        }
    });

    // 9. Toggle Subtask Status
    async function toggleSubtask(id, index) {
        synthAudio.playClick();
        const subtask = activeTask.subtasks[index];
        const newStatus = !subtask.completed;

        try {
            const response = await fetch(`/api/subtasks/${id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ completed: newStatus })
            });

            if (response.ok) {
                subtask.completed = newStatus;
                
                loadStats();
                loadRecentMissions();
                renderSubtasks();

                // If completed the active step, move forward
                if (newStatus && index === activeSubtaskIndex) {
                    clearInterval(timerInterval);
                    const nextUncompletedIndex = activeTask.subtasks.findIndex((s, i) => i > index && !s.completed);
                    
                    if (nextUncompletedIndex !== -1) {
                        setActiveSubtask(nextUncompletedIndex);
                    } else {
                        const anyUncompleted = activeTask.subtasks.findIndex(s => !s.completed);
                        if (anyUncompleted !== -1) {
                            setActiveSubtask(anyUncompleted);
                        } else {
                            finishTaskFlow();
                        }
                    }
                }
            }
        } catch (error) {
            console.error("Error updating subtask status:", error);
        }
    }

    // 10. Inject Custom Step Action UI logic
    btnSaveNewSubtask.addEventListener("click", async () => {
        const title = newSubtaskTitleInput.value.trim();
        const duration = parseInt(newSubtaskDurationInput.value);
        
        if (!title || isNaN(duration)) {
            systemLog.textContent = "SYS_ERROR: Subtask title and duration are required.";
            return;
        }
        
        if (!activeTask) {
            systemLog.textContent = "SYS_ERROR: No active task session.";
            return;
        }
        
        try {
            const response = await fetch(`/api/tasks/${activeTask.id}/subtasks`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title, duration_seconds: duration })
            });
            
            if (response.ok) {
                const res = await response.json();
                activeTask.subtasks.push({
                    id: res.id,
                    task_id: activeTask.id,
                    title,
                    duration_seconds: duration,
                    completed: 0,
                    order_index: activeTask.subtasks.length
                });
                
                systemLog.textContent = `SYS_EDITOR: Step injected.`;
                
                addSubtaskForm.classList.add("hidden");
                btnAddStepTrigger.classList.remove("hidden");
                newSubtaskTitleInput.value = "";
                
                if (taskStatus.textContent === "SUCCESS") {
                    taskStatus.textContent = "ACTIVE";
                    taskStatus.className = "status-indicator active";
                    startSubtaskFlow();
                } else {
                    renderSubtasks();
                }
                loadStats();
                loadRecentMissions();
            } else {
                systemLog.textContent = "SYS_ERROR: Failed to inject step.";
            }
        } catch (err) {
            console.error(err);
            systemLog.textContent = "SYS_ERROR: Inject connection failed.";
        }
    });

    btnAddStepTrigger.addEventListener("click", () => {
        synthAudio.playClick();
        addSubtaskForm.classList.remove("hidden");
        btnAddStepTrigger.classList.add("hidden");
        newSubtaskTitleInput.focus();
    });
    
    btnCancelNewSubtask.addEventListener("click", () => {
        synthAudio.playClick();
        addSubtaskForm.classList.add("hidden");
        btnAddStepTrigger.classList.remove("hidden");
        newSubtaskTitleInput.value = "";
    });

    // 11. Task Flow Complete
    function finishTaskFlow() {
        clearInterval(timerInterval);
        timerHud.classList.add("hidden");
        taskStatus.textContent = "SUCCESS";
        taskStatus.className = "status-indicator success-state";
        systemLog.textContent = "MISSION ACCOMPLISHED: Inertia broken successfully!";
        synthAudio.playSuccess();
        
        stepsContainer.innerHTML = `
            <div class="step-card completed" style="text-align: center; justify-content: center; padding: var(--spacing-lg);">
                <div class="step-info">
                    <span class="logo-icon" style="font-size: 40px; margin-bottom: 12px; display: block;">▲</span>
                    <span class="step-title" style="font-size: 18px; text-decoration: none; font-weight: 800; letter-spacing: 1.5px; color: var(--accent-green);">WAITING_MODE: SHATTERED</span>
                    <p style="font-size: 12px; color: var(--text-dim); margin-top: var(--spacing-xs);">You successfully broke inertia. Keep moving forward!</p>
                </div>
            </div>
        `;
    }
});
