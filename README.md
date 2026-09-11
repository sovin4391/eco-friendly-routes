# QuestionBot

An AI chatbot with one strange rule: **It must never answer the user; it must only respond with another relevant question.**

## Project Structure

```
QuestionBot/
│
├── frontend/         # React + Vite + Tailwind CSS
├── backend/          # Python + FastAPI
├── .gitignore        # Git ignore rules (protects API keys)
└── README.md         # Project documentation
```

## Phase 0: Initial Setup

Phase 0 sets up the development foundation:
- **Backend**: FastAPI running on `http://127.0.0.1:8000` with a `/health` endpoint.
- **Frontend**: React + Vite + Tailwind CSS running on `http://localhost:5173`.
- **Security**: `.env` is strictly ignored by Git to prevent leaking API keys.

## How to Run the Project

QuestionBot consists of two parts that run side-by-side:

### 1. Start the Backend (FastAPI Server)

Open terminal #1:
```bash
cd backend
.venv\Scripts\activate
uvicorn main:app --reload --port 8000
```
You can verify the backend is healthy by opening `http://127.0.0.1:8000/health` in your browser. It should return:
```json
{"status": "ok"}
```

### 2. Start the Frontend (React + Vite App)

Open terminal #2:
```bash
cd frontend
npm run dev
```
Open `http://localhost:5173` in your browser to view QuestionBot.
