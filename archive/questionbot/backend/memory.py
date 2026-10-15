import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# In-memory storage in RAM: key is conversation_id, value is conversation dictionary
_conversations: Dict[str, Dict[str, Any]] = {}

ACHIEVEMENTS_SPEC = [
    {
        "id": "FIRST_QUESTION",
        "title": "FIRST QUESTION",
        "description": "Your first step into questioning.",
        "icon": "🌱",
    },
    {
        "id": "FIVE_DEEP",
        "title": "FIVE DEEP",
        "description": "Five levels. Zero answers.",
        "icon": "🧭",
    },
    {
        "id": "EXISTENTIAL_CRISIS",
        "title": "EXISTENTIAL CRISIS",
        "description": "Reached depth 10.",
        "icon": "💀",
    },
    {
        "id": "BOT_BREAKER",
        "title": "BOT BREAKER",
        "description": "Attempted to force QuestionBot to answer.",
        "icon": "⚔️",
    },
    {
        "id": "QUESTION_ADDICT",
        "title": "QUESTION ADDICT",
        "description": "Reached depth 15.",
        "icon": "🌀",
    },
]


def get_depth_title(depth: int) -> str:
    """
    Returns the progression title based on conversation depth:
    Depth 0: UNINITIATED
    Depth 1-2: CURIOUS
    Depth 3-4: INTERROGATOR
    Depth 5-7: QUESTION ADDICT
    Depth 8-9: PHILOSOPHER
    Depth 10+: EXISTENTIAL CRISIS
    """
    if depth <= 0:
        return "UNINITIATED"
    if depth in (1, 2):
        return "CURIOUS"
    if depth in (3, 4):
        return "INTERROGATOR"
    if 5 <= depth <= 7:
        return "QUESTION ADDICT"
    if 8 <= depth <= 9:
        return "PHILOSOPHER"
    return "EXISTENTIAL CRISIS"


def evaluate_achievements(depth: int, break_attempts: int, currently_unlocked: List[str]) -> tuple[List[dict], List[dict]]:
    """
    Evaluates achievement unlock criteria and returns:
    (all_achievements_with_status, newly_unlocked_achievements)
    """
    unlocked_set = set(currently_unlocked)
    newly_unlocked = []

    checks = {
        "FIRST_QUESTION": depth >= 1,
        "FIVE_DEEP": depth >= 5,
        "EXISTENTIAL_CRISIS": depth >= 10,
        "BOT_BREAKER": break_attempts >= 1,
        "QUESTION_ADDICT": depth >= 15,
    }

    for ach in ACHIEVEMENTS_SPEC:
        ach_id = ach["id"]
        is_met = checks.get(ach_id, False)
        if is_met and ach_id not in unlocked_set:
            unlocked_set.add(ach_id)
            newly_unlocked.append(ach)

    all_achievements = []
    for ach in ACHIEVEMENTS_SPEC:
        all_achievements.append({
            **ach,
            "unlocked": ach["id"] in unlocked_set,
        })

    return all_achievements, newly_unlocked


def get_stats(conversation: Dict[str, Any], current_personality: str = "NORMAL") -> Dict[str, Any]:
    """
    Generates the conversation summary / session results with the central joke:
    ANSWERS RECEIVED: 0
    """
    depth = conversation.get("depth", 0)
    max_depth = conversation.get("max_depth", depth)

    if depth < 5:
        verdict = "You barely scratched the surface."
    elif depth <= 9:
        verdict = "You're getting suspiciously deep."
    else:
        verdict = "You have reached the Question Zone."

    # Count user messages vs bot questions
    user_msgs = sum(1 for m in conversation.get("messages", []) if m.get("role") == "user")
    bot_msgs = sum(1 for m in conversation.get("messages", []) if m.get("role") == "bot")

    return {
        "questions_asked": user_msgs,
        "questions_returned": bot_msgs,
        "answers_received": 0,  # Central joke: QuestionBot NEVER answers
        "max_depth": max_depth,
        "depth_title": get_depth_title(depth),
        "personality_used": current_personality,
        "personalities_used": conversation.get("personalities_used", [current_personality]),
        "break_attempts": conversation.get("break_attempts", 0),
        "questions_survived": conversation.get("questions_survived", 0),
        "depth_message": verdict,
    }


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
        "max_depth": 0,
        "break_attempts": 0,
        "questions_survived": 0,
        "unlocked_achievements": [],
        "personalities_used": [],
        "newly_unlocked": [],
    }
    return new_id


def get(conversation_id: str) -> Dict[str, Any]:
    """
    Retrieves a conversation by ID.
    """
    if conversation_id not in _conversations:
        get_or_create(conversation_id)
    return _conversations[conversation_id]


def add_turn(
    conversation_id: str,
    user_text: str,
    bot_question: str,
    personality: str = "NORMAL",
    is_break_mode: bool = False,
) -> Dict[str, Any]:
    """
    Adds a user message and a bot question to the conversation history,
    increments question count and depth, updates break mode challenge counters,
    tracks max depth and personalities used, and evaluates achievement unlocks.
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

    # Update standard counters
    conversation["question_count"] += 1
    conversation["depth"] = conversation["question_count"]
    conversation["max_depth"] = max(conversation.get("max_depth", 0), conversation["depth"])

    # Track personalities used
    used_list = conversation.get("personalities_used", [])
    if personality not in used_list:
        used_list.append(personality)
    conversation["personalities_used"] = used_list

    # Update challenge mode counters if active
    if is_break_mode:
        conversation["break_attempts"] = conversation.get("break_attempts", 0) + 1
        conversation["questions_survived"] = conversation.get("questions_survived", 0) + 1

    # Evaluate achievements
    all_ach, newly_unlocked = evaluate_achievements(
        conversation["depth"],
        conversation.get("break_attempts", 0),
        conversation.get("unlocked_achievements", [])
    )
    conversation["unlocked_achievements"] = [a["id"] for a in all_ach if a["unlocked"]]
    conversation["newly_unlocked"] = newly_unlocked

    return conversation


def reset(conversation_id: str) -> Dict[str, Any]:
    """
    Clears all messages and resets all counters, achievements, and stats for the conversation.
    """
    if conversation_id in _conversations:
        _conversations[conversation_id] = {
            "conversation_id": conversation_id,
            "messages": [],
            "question_count": 0,
            "depth": 0,
            "max_depth": 0,
            "break_attempts": 0,
            "questions_survived": 0,
            "unlocked_achievements": [],
            "personalities_used": [],
            "newly_unlocked": [],
        }
    else:
        get_or_create(conversation_id)

    return _conversations[conversation_id]