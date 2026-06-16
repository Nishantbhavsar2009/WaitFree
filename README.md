# WaitFree — ADHD Waiting Mode Task Breaker

WaitFree is a full-stack, single-page web application designed specifically to help users overcome **ADHD Waiting Mode** and **Start Resistance** (Task Inertia). It solves cognitive freezing by breaking large, ambiguous goals into a series of highly specific, physical sub-2-minute steps.

---

## 🚀 Key Features

*   **Generative Task Decomposer**: Leverages the Gemini API to break down large user queries into 3-7 sequential, physical micro-actions, each taking less than 120 seconds.
*   **Active Focus Room**: Displays exactly *one* micro-task at a time to minimize cognitive overload, accompanied by a visual SVG progress timer.
*   **Web Audio Synthesizer**: Generates clean, responsive spatial chimes and focus clicks directly in the browser (no external static assets needed).
*   **SQLite Local History**: Logs completed tasks, daily streaks, and step status locally in a lightweight database.
*   **Luxury Cyber-Minimalism Design**: Features a dark, premium aesthetic using Orbitron and Outfit fonts, noise textures, and clean CSS-only animations.

---

## 🛠️ Tech Stack

*   **Backend**: Python, FastAPI, Pydantic v2
*   **Database**: SQLite (built-in relational cache)
*   **AI Engine**: Google Generative AI SDK (`gemini-1.5-flash`)
*   **Frontend**: Vanilla HTML5, CSS3, Javascript ES6
*   **Testing**: pytest, starlette TestClient

---

## 📁 Project Structure

```
WaitFree/
├── requirements.txt            # Package dependencies
├── main.py                     # FastAPI entry point
├── waitfree.db                 # SQLite database file (auto-generated)
├── api/
│   ├── models.py               # Pydantic validation schemas
│   ├── db_manager.py           # SQLite interactions & stats manager
│   └── gemini_client.py        # Task decomposition using Gemini
├── static/                     # Static assets served by FastAPI
│   ├── index.html              # Core SPA interface
│   ├── css/
│   │   └── style.css           # Luxury Cyber-Minimalist styling
│   └── js/
│       └── app.js              # State machine & Audio synthesizer
├── tests/
│   └── test_main.py            # Pytest integration tests
└── README.md                   # This overview
```

---

## ⚡ Quick Start

### 1. Requirements
Ensure you have Python 3.11+ installed. Clone or copy the folder:
```bash
cd /Users/nishantbhavsar/Projects/WaitFree
```

### 2. Install Dependencies
Initialize the virtual environment and install packages:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
*(Or use `uv venv && uv pip install -r requirements.txt` for 10x faster installation)*

### 3. Set Up API Key
Ensure your `.env` file contains your Gemini API key:
```env
GEMINI_API_KEY=your-api-key-here
```

### 4. Run the Application
Start the server:
```bash
uvicorn main:app --reload
```
Open your browser and navigate to **[http://127.0.0.1:8000](http://127.0.0.1:8000)**.
