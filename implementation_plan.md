# Implementation Plan - WaitFree (ADHD Waiting Mode Task Breaker)

WaitFree is a web application designed to help people with ADHD overcome "waiting mode" (the feeling of being frozen or unable to start a task before an appointment or event). It solves this by breaking large, ambiguous tasks down into highly visual, step-by-step interactive blocks that take less than 2 minutes each.

---

## 1. Design Direction (Luxury Cyber-Minimalism)
*   **Aesthetic Name**: Luxury Cyber-Minimalism (Dark theme with glowing neon-teal and violet accents, thin clean borders, and premium typography).
*   **DFII Score**: **19 / 15** (Impact: 5, Fit: 5, Feasibility: 5, Performance: 5, Consistency Risk: 1).
*   **Design Rationale**: ADHD brains are highly sensitive to cognitive clutter and visual noise. The interface needs to feel calming yet engaging. High-contrast dark backgrounds minimize eye strain, while sharp typography and clear neon-glowing interactive elements guide attention to exactly one action at a time.
*   **Differentiation Anchor**: A central, circular "Inertia Breaker" focus ring that acts as both a visual progress indicator and a 2-minute focus timer. Completing a micro-task plays a tactile SVG morph animation and a subtle spatial audio chime (generated via the Web Audio API).

---

## 2. Design System Snapshot
*   **Color Palette**:
    ```css
    --bg-dark: #0a0a0c;      /* Deep obsidian void */
    --card-dark: #121216;    /* Dark card background */
    --text-primary: #f3f4f6; /* Off-white main text */
    --text-muted: #8b8ea0;   /* Muted grey metadata */
    --accent-teal: #00f5d4;  /* Glowing teal for progress & focus */
    --accent-violet: #7b2cbf;/* Muted violet for secondary actions */
    --border-subtle: #24252e;/* Thin dark border */
    ```
*   **Typography**:
    *   Display: `Orbitron` or `Outfit` (Expressive modern geometric display for counters and headers)
    *   Body: `Cabinet Grotesk` or standard high-craft sans-serif
*   **Spacing Rhythm**: Base-8 rhythm (`8px`, `16px`, `24px`, `32px`, `64px`). Very generous padding and margin to give elements "breathing room" (controlled negative space).

---

## 3. Project Architecture

### Directory Structure
```
/Users/nishantbhavsar/Projects/WaitFree/
├── requirements.txt
├── main.py                     # FastAPI server
├── api/
│   ├── __init__.py
│   ├── gemini_client.py        # Task subdivision engine using Gemini API
│   ├── db_manager.py           # SQLite manager for tasks, steps, and history
│   └── models.py               # Pydantic schemas
├── static/                     # Frontend served statically
│   ├── index.html              # Core application layout
│   ├── css/
│   │   └── style.css           /* Luxury Cyber-Minimalism Design System */
│   └── js/
│       └── app.js              /* Interactive state, timers, Web Audio, API fetch */
├── tests/
│   └── test_main.py            # Integration tests
├── README.md                   # Project documentation
├── walkthrough.md              # Feature demo walkthrough
└── implementation_plan.md      # This plan
```

---

## 4. Key Features

1.  **AI-Powered Task Subdivision**: User enters a daunting goal (e.g. "Clean my room", "Write a cover letter"). The backend queries Gemini with a specialized system prompt to output a JSON list of sub-2-minute steps.
2.  **Focus Ring & Timer**: Displays exactly *one* micro-task at a time. A circular SVG ring fills up as the 2-minute timer counts down.
3.  **Gamified Interactive Progress**: Sound chimes, particle bursts on step completion, and a satisfying progress tracker showing how close the user is to escaping "waiting mode."
4.  **Local History**: Save completed sessions to SQLite database, displaying daily streaks and completed goals.

---

## 5. Development Steps

### Phase 1: Foundation (Backend & Database)
- Initialize Git repository and Python virtual environment.
- Create `db_manager.py` with tables: `sessions` (id, task, created_at, completed) and `steps` (id, session_id, title, duration, position, completed).
- Implement `gemini_client.py` using Gemini API to decompose a prompt into structured JSON.
- Build the FastAPI server in `main.py` serving static files and exposing `/api/sessions` (POST/GET) and `/api/steps` (PUT).

### Phase 2: Design & Frontend Development
- Create `static/css/style.css` defining the CSS custom properties, responsive typography, and animations.
- Create `static/index.html` with clean semantic HTML5, including sections for Dashboard, Active Focus Mode, and Session History.
- Create `static/js/app.js` containing the state machine, Web Audio synthesizer (for spatial chimes), timer controls, and API integration.

### Phase 3: Integration & Testing
- Write integration tests in `tests/test_main.py` validating task generation, database read/writes, and status updates.
- Test the application end-to-end to ensure the transition from dashboard to active timer is seamless.
- Optimize INP (Interaction to Next Paint) and eliminate visual layout shifts (CLS).

### Phase 4: Documentation & Logging
- Write `README.md` and `walkthrough.md`.
- Commit changes and push to GitHub.
