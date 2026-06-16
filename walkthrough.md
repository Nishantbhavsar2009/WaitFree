# Walkthrough — WaitFree (ADHD Waiting Mode Task Breaker)

This guide walks you through setting up and running the WaitFree application locally to experience the visual layout, interactive timers, and synthesizer audio cues.

---

## 1. Setup and Startup

1.  **Start the Backend Server**:
    Run the FastAPI server from the project directory:
    ```bash
    .venv/bin/uvicorn main:app --reload --host 127.0.0.1 --port 8000
    ```
2.  **Open the Web Interface**:
    Launch your browser and navigate to:
    ```
    http://127.0.0.1:8000
    ```

---

## 2. Using the Dashboard (Task Decomposer)

1.  **Main Input Field**:
    In the central input form, type a task that you feel frozen on (e.g. `"Draft the final essay"`, `"Clean my study desk"`, `"Pack my clothes for the trip"`).
2.  **Available Time Slider**:
    Adjust the slider to match how much time you have before your next meeting, class, or appointment (e.g., `20 minutes`). This acts as the timebox.
3.  **Decompose Task**:
    Click the **Decompose Task** button. The button will change to "Decomposing Inertia..." and disable input fields. The backend contacts Gemini to generate 3-7 sub-2-minute micro-actions.

---

## 3. Entering the Active Focus Room

Once generated, the UI switches to the **Active Focus Panel** with a dark, neon-teal cyber-theme.

1.  **The Focus Ring**:
    You will see a large circular countdown ring with a digital-style clock showing `02:00` (or the specific seconds allocated to Step 1).
2.  **Step Card**:
    Below the ring, you are presented with exactly *one* physical action:
    *   *Title*: `"Open Google Docs and create a blank file named Essay"`
    *   *Description*: `"Just open the tab and write the title. Don't worry about writing paragraphs yet."`
3.  **Synthesizer Audio Feedback**:
    A welcoming C-major sound sweep will play to reward you for initiating the task and ease your start resistance.

---

## 4. Working Through the Micro-Tasks

1.  **Start the Timer**:
    Click **Start Timer**. The circle stroke will gradually wind down, counting down the seconds. The synthesizer plays a subtle, low-frequency click every 10 seconds to keep your attention anchored.
2.  **Complete the Step**:
    Once you have completed the physical action, click **Complete Step**.
    *   If there are more steps, a clean ascending chime plays, and the Focus Ring transitions to Step 2.
    *   If you finish the final step, a triumphant major arpeggio sound sequence plays, logging the victory and returning you to the dashboard.

---

## 5. Victories & Streak Tracking

After completing or aborting a session:
1.  Your **Streak** pill updates (e.g., `1d` streak).
2.  The **Victories** counter increments.
3.  The **Recent Victories** panel updates with your task, the date/time, and status (e.g., `Success` or `Partial`).
