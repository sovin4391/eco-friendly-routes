from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import memory

app = FastAPI(title="QuestionBot API", version="0.1.0")

# CORS setup: allows the React frontend on localhost:5173 to communicate with this backend
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phase 1 uses these canned questions. OpenAI integration will arrive in a future phase.
CANNED_QUESTIONS = [
    "Why do you need to know?",
    "What made you curious about that?",
    "If you already had the answer, what would you do next?",
    "Who first made you wonder about this?",
    "Why does that matter so much to you?",
    "What would change if you never found out?",
    "Why do you define your situation in those terms?",
    "Where does that assumption come from?",
]


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str


class ResetRequest(BaseModel):
    conversation_id: str


def _serialize_response(conversation_id: str, conv: dict) -> dict:
    last_reply = None
    for msg in reversed(conv["messages"]):
        if msg["role"] == "bot":
            last_reply = msg["content"]
            break

    return {
        "conversation_id": conversation_id,
        "reply": last_reply,
        "question_count": conv["question_count"],
        "depth": conv["depth"],
        "messages": conv["messages"],
    }


@app.get("/health")
def health_check():
    """Health check endpoint to verify that the server is alive and functioning."""
    return {"status": "ok"}


@app.post("/chat")
def chat(request: ChatRequest):
    """
    Receives user message, stores it in RAM memory, generates a canned question,
    stores the question in memory, and returns the updated state.
    """
    text = request.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    conv_id = memory.get_or_create(request.conversation_id)
    conv = memory.get(conv_id)

    # Pick next canned question based on question count
    question = CANNED_QUESTIONS[conv["question_count"] % len(CANNED_QUESTIONS)]

    # Record turn in RAM memory
    updated_conv = memory.add_turn(conv_id, text, question)

    return _serialize_response(conv_id, updated_conv)


@app.post("/reset")
def reset_conversation(request: ResetRequest):
    """
    Clears the messages and counters for the conversation in RAM.
    """
    conv_id = memory.get_or_create(request.conversation_id)
    cleared_conv = memory.reset(conv_id)
    return _serialize_response(conv_id, cleared_conv)