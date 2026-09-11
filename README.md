# QuestionBot (Powered by Google Gemini)

An AI chatbot with one strange rule: **It must never answer the user; it must only respond with another relevant question.**

---

## 1. Setting Up Your Google Gemini API Key

QuestionBot uses Google's official Gemini API (`google-genai` SDK) to dynamically formulate questions using models like `gemini-2.5-flash` available on the free tier.

1. Open `backend/.env` in your editor.
2. Enter your Gemini API key:
   ```env
   GEMINI_API_KEY=AIzaSyYourActualGeminiKeyHere
   GEMINI_MODEL=gemini-2.5-flash
   PORT=8000
   HOST=127.0.0.1
   ```
3. Save the file.

> **Security Note**: `backend/.env` is strictly ignored by Git (via `.gitignore`). Your API key is stored only on the backend and is never exposed to the frontend or GitHub.

---

## 2. How to Run the Project (Two Terminals)

QuestionBot consists of two programs that run side-by-side:

### Terminal 1 — Backend (FastAPI Server)

```bash
cd backend
.\.venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

- Health check: `http://127.0.0.1:8000/health`
- API runs on: `http://127.0.0.1:8000`

### Terminal 2 — Frontend (React + Vite App)

```bash
cd frontend
npm run dev
```

- Web UI: `http://localhost:5173`

---

## 3. How to Test QuestionBot

1. Open `http://localhost:5173` in your browser.
2. Type any question or thought, for example:
   > *"What is the capital of France?"*
3. The bot will **never** answer with *"Paris"*. Instead, it queries Google Gemini with QuestionBot's strict prompt and responds with:
   > *"Why do you need to know the capital of France?"*
4. Notice the **Question Counter** and **Depth Counter** increment with every turn.
5. Click **Reset** in the top right to clear the conversation and restart counters.

---

## 4. Project Structure

```
QuestionBot/
│
├── .gitignore                    # Ensures backend/.env and dependencies are never committed
├── README.md                     # Documentation & setup guide
│
├── backend/
│   ├── .env                      # Local secret keys (IGNORED BY GIT)
│   ├── .env.example              # Public template
│   ├── main.py                   # FastAPI server & endpoints (/health, /chat, /reset)
│   ├── memory.py                 # In-memory conversation store in RAM
│   ├── gemini_client.py          # Google Gemini API client with validation & retry
│   ├── prompts.py                # System prompt and core QuestionBot rules
│   ├── validator.py              # Validates that AI responses are strictly questions
│   └── requirements.txt          # Python packages (FastAPI, google-genai, Uvicorn, etc.)
│
└── frontend/
    ├── index.html                # App root HTML
    ├── package.json              # React dependencies and scripts
    ├── vite.config.js            # Vite configuration
    └── src/
        ├── main.jsx              # React entry point
        ├── index.css             # Tailwind CSS styles
        ├── App.jsx               # Main chat state & interface
        └── components/
            ├── ChatWindow.jsx    # Message history & auto-scroll
            ├── MessageBubble.jsx # User & Bot message styling
            ├── Composer.jsx      # Message input & Send button
            └── Sidebar.jsx       # Header, question counter, depth, reset button
```