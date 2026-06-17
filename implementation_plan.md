# WaitFree (ADHD Waiting Mode Task Breaker) — Implementation Plan

WaitFree is an immersive, high-craft web application designed to help people with ADHD overcome "waiting mode" paralysis. It takes a task the user is frozen on and dynamically breaks it down into sub-2-minute interactive steps, matching their available time before an upcoming appointment or event.

## 1. Design Direction Summary (AAS Frontend Design Skill)

*   **Aesthetic Direction:** *Cyberpunk Utilitarianism / Retro-Futurist Terminal*
*   **DFII Score:** **17 / 15**
    *   *Aesthetic Impact:* 4.5/5 (Immersive dark layout, glassmorphic card overlays, glow states, glowing amber indicators)
    *   *Context Fit:* 4.5/5 (High-contrast, terminal-like design signals "mission-critical focus mode," reducing ambient distraction)
    *   *Implementation Feasibility:* 4.5/5 (Clean single-page app architecture using CSS grid/flexbox and vanilla JS)
    *   *Performance Safety:* 4.5/5 (Pure CSS animations, zero heavyweight frameworks)
    *   *Consistency Risk:* 1/5 (A single interactive viewport dashboard)
*   **Typography:**
    *   Display: *Outfit* (Google Fonts) — modern, geometric, crisp sans-serif.
    *   Body/Terminal: *JetBrains Mono* (Google Fonts) — technical, high readability, monospace for numbers, steps, and statuses.
*   **Color Palette (CSS Variables):**
    *   `--bg-main`: `oklch(14.5% 0.015 285)` (Ultra-dark slate base)
    *   `--bg-card`: `oklch(20% 0.02 285 / 0.7)` (Translucent glass panel)
    *   `--accent-amber`: `oklch(76% 0.18 55)` (Vibrant warning amber for timers, focus buttons, and active states)
    *   `--accent-dim`: `oklch(45% 0.1 55)` (Muted amber for inactive outlines)
    *   `--text-bright`: `oklch(97% 0.01 285)` (High contrast off-white)
    *   `--text-dim`: `oklch(65% 0.01 285)` (Slate-grey subtext)
*   **Motion Philosophy:**
    *   Sparse but high-impact. A pulse/glow effect on the active step, and a typewriter sequence when steps are broken down.
*   **Differentiation Anchor:**
    *   "Mission Control" HUD: A central retro-style analog timer ring and interactive grid cards that step the user through the task like a space flight pre-check list, completely avoiding generic SaaS dashboard patterns.

---

## 2. Form CRO Optimization (AAS Form CRO Skill)

*   **Form Health & Friction Index:** **95 / 100**
    *   *Bottlenecks Avoided:* No sign-up wall, no email input required to start, no multi-page wizard.
    *   *Input Fields:*
        1.  `What task are you frozen on?` (Single text line with immediate validation)
        2.  `When is your next event/appointment?` (Clean radio selector pills: `In 15m`, `In 30m`, `In 1h`, `In 2h`, `Custom`)
    *   *CTA Button Copy:* `[BREAK THE FREEZE]` (Amber glowing button, changes to `[BREAKING...]` and disables during task breakdown generation)

---

## 3. Core Tech Stack

*   **Backend:** Python with FastAPI. Fast, type-safe REST endpoint.
*   **Database:** SQLite (SQLAlchemy or raw SQLite) for storing tasks, generated steps, and daily stats (to showcase streaks and completions).
*   **AI Integration:** Optional integration with Gemini API (using the standard SDK) to generate smart sub-tasks, with a local regex/fallback task breaker if API key is not configured.
*   **Frontend:** Vanilla HTML5, Vanilla CSS3 (CSS Variables, Grid, OKLCH colors), Vanilla JS.

---

## 4. File Layout

```text
WaitFree/
│
├── main.py                 # FastAPI backend & database routing
├── database.py             # SQLite setup, models, and CRUD helper
├── requirements.txt        # python dependencies
├── test_main.py            # Automated tests using pytest
│
├── static/                 # Frontend asset folder
│   ├── index.html          # Main HTML structure (semantic layout)
│   ├── style.css           # Custom CSS variables, glassmorphic HUD layout
│   └── app.js              # State engine, timer logic, API client
│
├── README.md               # Setup and project description
└── walkthrough.md          # Implementation walkthrough & testing log
```

---

## 5. Build Checklist

- [ ] **Phase 1: Project Initialization**
  - Create directory and configuration files.
  - Setup virtual environment and dependencies.
- [ ] **Phase 2: Database and API Backend**
  - Implement SQLite models for `Task` and `SubTask`.
  - Create API routes: `POST /api/tasks` (to parse and break task), `GET /api/tasks/{id}`, `PATCH /api/subtasks/{id}` (toggle done).
  - Implement task breaker logic: a deterministic fallback and a generative prompt utilizing Gemini.
- [ ] **Phase 3: Immersive Frontend Development**
  - Create `index.html` with semantic sections (`<header>`, `<main>`, `<footer>`).
  - Implement CSS styles matching *Cyberpunk Utilitarianism* styling tokens.
  - Implement `app.js` clientside state controller (timer loops, event listeners, active subtask view).
- [ ] **Phase 4: Testing & Verification**
  - Write tests for backend routes.
  - Run app locally to verify visual rendering and complete workflow.
- [ ] **Phase 5: Git & GitHub Publish**
  - Initialize git repo, commit, and push to GitHub.
- [ ] **Phase 6: Iterative Improvements**
  - Expand analytics dashboard, streak trackers, audio focus pings, or task editability.
