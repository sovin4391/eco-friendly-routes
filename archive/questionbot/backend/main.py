from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import memory
import gemini_client
from personalities import validate_personality

app = FastAPI(title="QuestionBot API (Phase 3: Personalities & Challenge Mode)", version="0.4.0")

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
    personality: str = "NORMAL"
    is_break_mode: bool = False


class ResetRequest(BaseModel):
    conversation_id: str | None = None


def _serialize_response(
    conversation_id: str,
    conv: dict,
    personality: str = "NORMAL",
    is_break_mode: bool = False,
) -> dict:
    last_reply = None
    for msg in reversed(conv["messages"]):
        if msg["role"] == "bot":
            last_reply = msg["content"]
            break

    depth = conv.get("depth", 0)
    max_depth = conv.get("max_depth", depth)
    depth_title = memory.get_depth_title(depth)
    all_achievements, _ = memory.evaluate_achievements(
        depth,
        conv.get("break_attempts", 0),
        conv.get("unlocked_achievements", [])
    )
    stats = memory.get_stats(conv, current_personality=personality)

    return {
        "conversation_id": conversation_id,
        "reply": last_reply,
        "question": last_reply,
        "question_count": conv["question_count"],
        "depth": depth,
        "max_depth": max_depth,
        "depth_title": depth_title,
        "break_attempts": conv.get("break_attempts", 0),
        "questions_survived": conv.get("questions_survived", 0),
        "personality": personality,
        "is_break_mode": is_break_mode,
        "achievements": all_achievements,
        "new_achievements": conv.get("newly_unlocked", []),
        "stats": stats,
        "messages": conv["messages"],
    }


@app.get("/health")
def health_check():
    """Health check endpoint to verify that the server is alive and functioning."""
    return {"status": "ok"}


@app.post("/chat")
def chat(request: ChatRequest):
    """
    Receives user message, queries Google Gemini with active personality and challenge mode directives,
    validates that the response is strictly a single question, stores the turn in RAM memory,
    and returns the updated state.
    """
    text = request.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    conv_id = memory.get_or_create(request.conversation_id)
    conv = memory.get(conv_id)

    # Validate personality string cleanly (defaults to NORMAL if invalid, never crashes)
    safe_personality = validate_personality(request.personality)

    # Generate question using Gemini client with personality and challenge mode support
    try:
        bot_question = gemini_client.generate_question(
            conv["messages"],
            text,
            personality=safe_personality,
            is_break_mode=request.is_break_mode,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=503, detail=str(re))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="An error occurred while communicating with Google Gemini. Please try again."
        )

    # Record turn in RAM memory with challenge mode tracking
    updated_conv = memory.add_turn(
        conv_id,
        text,
        bot_question,
        personality=safe_personality,
        is_break_mode=request.is_break_mode
    )

    return _serialize_response(
        conv_id,
        updated_conv,
        personality=safe_personality,
        is_break_mode=request.is_break_mode
    )


@app.get("/stats")
def conversation_stats(conversation_id: str | None = None):
    """
    Returns the conversation summary / statistics including the central joke:
    ANSWERS RECEIVED: 0
    """
    conv_id = memory.get_or_create(conversation_id)
    conv = memory.get(conv_id)
    return memory.get_stats(conv)


@app.post("/reset")
def reset_conversation(request: ResetRequest):
    """
    Clears the messages and counters for the conversation in RAM.
    """
    conv_id = memory.get_or_create(request.conversation_id)
    cleared_conv = memory.reset(conv_id)
    return _serialize_response(conv_id, cleared_conv)