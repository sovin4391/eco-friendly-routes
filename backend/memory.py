import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# In-memory storage in RAM: key is conversation_id, value is conversation dictionary
# No database is used. If the server restarts, this RAM memory resets.
_conversations: Dict[str, Dict[str, Any]] = {}


def get_or_create(conversation_id: Optional[str] = None) -> str:
    """
    Returns an existing conversation_id if valid, or generates a new one.
    """
    if conversation_id and conversation_id in _conversations:
        return conversation_id

    new_id = str(uuid.uuid4())
    _conversations[new_id] = {
        "conversation_id": new_id,
        "messages": [],
        "question_count": 0,
        "depth": 0,
    }
    return new_id


def get(conversation_id: str) -> Dict[str, Any]:
    """
    Retrieves a conversation by ID.
    """
    if conversation_id not in _conversations:
        get_or_create(conversation_id)
    return _conversations[conversation_id]


def add_turn(conversation_id: str, user_text: str, bot_question: str) -> Dict[str, Any]:
    """
    Adds a user message and a bot question to the conversation history,
    and increments the question counter and depth.
    """
    conversation = get(conversation_id)
    now = datetime.now(timezone.utc).isoformat()

    # Append user message
    conversation["messages"].append({
        "id": str(uuid.uuid4()),
        "role": "user",
        "content": user_text,
        "timestamp": now,
    })

    # Append bot question
    conversation["messages"].append({
        "id": str(uuid.uuid4()),
        "role": "bot",
        "content": bot_question,
        "timestamp": now,
    })

    # Update question count and depth
    conversation["question_count"] += 1
    conversation["depth"] = conversation["question_count"]

    return conversation


def reset(conversation_id: str) -> Dict[str, Any]:
    """
    Clears all messages and resets counters for the specified conversation.
    """
    if conversation_id in _conversations:
        _conversations[conversation_id] = {
            "conversation_id": conversation_id,
            "messages": [],
            "question_count": 0,
            "depth": 0,
        }
    else:
        get_or_create(conversation_id)

    return _conversations[conversation_id]