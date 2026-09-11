import re


def is_valid_question(text: str) -> bool:
    """
    Strictly validates whether the AI-generated response is a single question.

    Criteria:
    1. Must be a non-empty string.
    2. Must end with a question mark (?).
    3. Must contain exactly ONE question mark (rejects multiple questions).
    4. Must not include preceding declarative/factual sentences or answers
       (e.g., "Paris is the capital. Why do you ask?").
    5. Must not include newline-separated explanations or paragraphs.
    6. Must have meaningful length (> 2 characters).
    """
    if not text or not isinstance(text, str):
        return False

    cleaned = text.strip().strip('"\'`')
    if not cleaned:
        return False

    # Must end with a question mark
    if not cleaned.endswith("?"):
        return False

    # Must be longer than just a question mark
    if len(cleaned) < 3:
        return False

    # Must contain exactly ONE question mark (rejects multiple questions)
    if cleaned.count("?") > 1:
        return False

    # Disallow preceding declarative sentences ending with periods before the question mark.
    # E.g. "Paris is the capital of France. Why do you need to know?" -> Invalid
    preceding_text = cleaned[:-1].strip()  # text before final ?
    declarative_parts = [p.strip() for p in preceding_text.split(".") if p.strip()]
    if len(declarative_parts) > 1:
        return False

    # Check for newline-separated paragraphs or statements
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    if len(lines) > 1:
        return False

    # Disallow exclamation marks, colons, or semicolons before the question (e.g. "Hello! Why do you ask?", "Here is my reply: why?")
    if any(ch in preceding_text for ch in ("!", ":", ";")):
        return False

    return True