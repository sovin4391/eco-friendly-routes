import re


def is_valid_question(text: str) -> bool:
    """
    Validates whether the AI-generated response is strictly a single question.

    Criteria:
    1. Must be non-empty.
    2. Must end with a question mark (?).
    3. Must not include preceding explanatory or factual sentences
       (e.g., "Paris is the capital of France. Why do you need to know?").
    4. Must have meaningful length (> 2 characters).
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

    # Disallow preceding declarative sentences before the question mark.
    # E.g. "The answer is 42. What else do you want to know?" -> Invalid
    preceding_text = cleaned[:-1]  # everything before the final ?
    declarative_parts = [p.strip() for p in preceding_text.split(".") if p.strip()]
    if len(declarative_parts) > 1:
        return False

    # Check for newline-separated paragraphs/sentences
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    if len(lines) > 1:
        return False

    return True