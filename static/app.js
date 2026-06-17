// WaitFree - Front-End HUD State Controller

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const taskForm = document.getElementById("task-form");
    const taskTitleInput = document.getElementById("task-title");
    const submitBtn = document.getElementById("submit-btn");
    const streakCount = document.getElementById("streak-count");
    const subtaskCompletedCount = document.getElementById("subtask-completed-count");
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
    const beepSound = document.getElementById("beep-sound");

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

    // 2. Fetch daily statistics
    async function loadStats() {
        try {
            const response = await fetch("/api/stats");
            if (response.ok) {
                const stats = await response.json();
                streakCount.textContent = `${stats.streak}D`;
                subtaskCompletedCount.textContent = stats.completed_subtasks;
            }
        } catch (error) {
            console.error("Error loading stats:", error);
        }
    }
    loadStats();

    // 3. Handle Pill Selections
    pillBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            // Remove active class from all pills
            pillBtns.forEach(p => {
                p.classList.remove("active");
                p.setAttribute("aria-checked", "false");
            });

            // Set current active
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

    // 4. Form Submission (Break the Freeze)
    taskForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const title = taskTitleInput.value.trim();
        const minutesLeft = parseInt(minutesLeftInput.value);

        if (!title || isNaN(minutesLeft)) return;

        // Disable UI and set state to breaking
        submitBtn.disabled = true;
        submitBtn.textContent = "[BREAKING FREEZE...]";
        taskStatus.textContent = "DECOMPOSING";
        taskStatus.className = "status-indicator active";
        systemLog.textContent = "SYS_API: Connecting to task breaker module...";

        try {
            const response = await fetch("/api/tasks", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title, minutes_left: minutesLeft })
            });

            if (response.ok) {
                activeTask = await response.json();
                systemLog.textContent = `SYS_API: Task decomposed successfully. ID: ${activeTask.id}`;
                renderSubtasks();
                startSubtaskFlow();
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

    // 5. Render Checklist Steps
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
                <div class="checkbox-visual"></div>
            `;

            // Step click toggles completion
            card.addEventListener("click", () => {
                toggleSubtask(subtask.id, index);
            });

            stepsContainer.appendChild(card);
        });

        taskStatus.textContent = "ACTIVE";
        taskStatus.className = "status-indicator active";
    }

    // 6. Initiate Active Flow (ADHD Focus Timer Engine)
    function startSubtaskFlow() {
        // Find first uncompleted subtask
        const firstUncompletedIndex = activeTask.subtasks.findIndex(s => !s.completed);
        
        if (firstUncompletedIndex === -1) {
            finishTaskFlow();
            return;
        }

        setActiveSubtask(firstUncompletedIndex);
    }

    function setActiveSubtask(index) {
        // Clear past active state from DOM
        const cards = document.querySelectorAll(".step-card");
        cards.forEach(c => c.classList.remove("active"));

        activeSubtaskIndex = index;
        const activeSubtask = activeTask.subtasks[index];

        // Highlight active card
        const activeCard = document.querySelector(`.step-card[data-index="${index}"]`);
        if (activeCard) {
            activeCard.classList.add("active");
            activeCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }

        // Setup Timer HUD
        timerTotalDuration = activeSubtask.duration_seconds;
        timerTimeLeft = timerTotalDuration;
        
        timerHud.classList.remove("hidden");
        updateTimerVisuals();
        
        // Start running immediately
        startTimer();
        systemLog.textContent = `SYS_FOCUS: Step ${index + 1} started. Focus on this step.`;
    }

    // 7. Timer Controller Functions
    function startTimer() {
        if (timerInterval) clearInterval(timerInterval);
        isTimerRunning = true;
        timerPlayPause.textContent = "PAUSE";
        
        timerInterval = setInterval(() => {
            timerTimeLeft--;
            updateTimerVisuals();

            if (timerTimeLeft <= 0) {
                clearInterval(timerInterval);
                isTimerRunning = false;
                timerDigits.textContent = "00:00";
                beepSound.play().catch(e => console.log("Audio play blocked by browser:", e));
                systemLog.textContent = `SYS_ALERT: Step ${activeSubtaskIndex + 1} time finished. Complete task to advance.`;
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

        // Calculate progress stroke dashoffset (283 is full circle length)
        const progressFraction = timerTimeLeft / timerTotalDuration;
        const offset = 283 * (1 - progressFraction);
        timerProgress.style.strokeDashoffset = offset;
    }

    timerPlayPause.addEventListener("click", () => {
        if (isTimerRunning) {
            pauseTimer();
        } else {
            startTimer();
        }
    });

    timerSkip.addEventListener("click", () => {
        clearInterval(timerInterval);
        systemLog.textContent = `SYS_TIMER: Step ${activeSubtaskIndex + 1} skipped.`;
        
        // Find next step
        const nextIndex = activeSubtaskIndex + 1;
        if (nextIndex < activeTask.subtasks.length) {
            setActiveSubtask(nextIndex);
        } else {
            finishTaskFlow();
        }
    });

    // 8. Toggle Subtask Status (Complete checkmark)
    async function toggleSubtask(id, index) {
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
                
                // Update stats HUD
                loadStats();
                
                // Re-render checklist item status
                const card = document.querySelector(`.step-card[data-id="${id}"]`);
                if (card) {
                    if (newStatus) {
                        card.classList.add("completed");
                    } else {
                        card.classList.remove("completed");
                    }
                }

                // If completed the active step, move forward
                if (newStatus && index === activeSubtaskIndex) {
                    clearInterval(timerInterval);
                    const nextUncompletedIndex = activeTask.subtasks.findIndex((s, i) => i > index && !s.completed);
                    
                    if (nextUncompletedIndex !== -1) {
                        setActiveSubtask(nextUncompletedIndex);
                    } else {
                        // Check if there are any uncompleted steps at all
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
            console.error("Error updating subtask:", error);
        }
    }

    // 9. Task Flow Complete (All Subtasks Checked Off)
    function finishTaskFlow() {
        clearInterval(timerInterval);
        timerHud.classList.add("hidden");
        taskStatus.textContent = "SUCCESS";
        taskStatus.className = "status-indicator success-state";
        systemLog.textContent = "MISSION ACCOMPLISHED: All steps completed! Waiting mode broken.";
        
        // Render completion screen inside container
        stepsContainer.innerHTML = `
            <div class="step-card completed" style="text-align: center; justify-content: center; padding: var(--spacing-lg);">
                <div class="step-info">
                    <span class="logo-icon" style="font-size: 40px; margin-bottom: 12px; display: block;">▲</span>
                    <span class="step-title" style="font-size: 18px; text-decoration: none; font-weight: 800; letter-spacing: 1.5px; color: var(--accent-green);">WAITING_MODE_PARALYSIS: BROKEN</span>
                    <p style="font-size: 12px; color: var(--text-dim); margin-top: var(--spacing-xs);">You have broken inertia and initiated momentum. Keep building!</p>
                </div>
            </div>
        `;
    }
});
