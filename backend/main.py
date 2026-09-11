from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import memory
import gemini_client

app = FastAPI(title="QuestionBot API (Gemini Edition)", version="0.3.0")

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
    Receives user message, queries Google Gemini with conversation history and strict QuestionBot prompt,
    validates that the response is strictly a single question, stores the turn in RAM memory,
    and returns the updated state.
    """
    text = request.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    conv_id = memory.get_or_create(request.conversation_id)
    conv = memory.get(conv_id)

    # Generate question using Gemini client with retry and validation
    try:
        bot_question = gemini_client.generate_question(conv["messages"], text)
    except ValueError as ve:
        # Cleanly informs user about missing or invalid GEMINI_API_KEY without raw crash
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        # Handles rate limits, quota, or network connectivity issues cleanly
        raise HTTPException(status_code=503, detail=str(re))
    except Exception as e:
        # Catch-all protecting internal stack trace / secrets
        raise HTTPException(
            status_code=500,
            detail="An error occurred while communicating with Google Gemini. Please try again."
        )

    # Record turn in RAM memory
    updated_conv = memory.add_turn(conv_id, text, bot_question)

    return _serialize_response(conv_id, updated_conv)


@app.post("/reset")
def reset_conversation(request: ResetRequest):
    """
    Clears the messages and counters for the conversation in RAM.
    """
    conv_id = memory.get_or_create(request.conversation_id)
    cleared_conv = memory.reset(conv_id)
    return _serialize_response(conv_id, cleared_conv)