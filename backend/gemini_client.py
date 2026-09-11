import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError

from prompts import SYSTEM_PROMPT, FALLBACK_QUESTION, RETRY_REMINDER
from validator import is_valid_question

# Path to backend/.env
env_path = Path(__file__).resolve().parent / ".env"


def get_api_key() -> str:
    """
    Retrieves the Gemini API key strictly from backend/.env or environment.
    Always reloads backend/.env with override=True so edits are picked up immediately.
    Raises a clean error if missing or placeholder.
    """
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)

    key = os.getenv("GEMINI_API_KEY", "").strip().strip('"\'')

    if not key or key == "your_gemini_api_key_here":
        raise ValueError(
            "Gemini API key is missing. Please add your key to backend/.env (GEMINI_API_KEY=...) to enable AI responses."
        )
    return key


def get_model_name() -> str:
    """
    Returns the configured Gemini model name.
    Defaults to gemini-3.6-flash (current fast, economical, free-tier model).
    """
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
    return os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip().strip('"\'')


def get_client() -> genai.Client:
    """
    Initializes and returns the Google GenAI Client using the key from backend/.env.
    """
    key = get_api_key()
    return genai.Client(api_key=key)


def generate_question(
    history: list[dict],
    user_message: str,
    client: Optional[genai.Client] = None,
) -> str:
    """
    Generates a single relevant question using Google Gemini:
    1. Builds conversation history (user + model turns).
    2. Sends context + strict QuestionBot system instruction to Gemini.
    3. Validates that the response is strictly a single question ending with '?'.
    4. If invalid, retries once with a corrective prompt.
    5. If the second attempt still fails, safely returns FALLBACK_QUESTION.

    Allows passing an optional client instance for unit testing without live API keys.
    """
    if client is None:
        client = get_client()

    model = get_model_name()

    # Build conversation contents for Gemini
    contents: list[types.Content] = []

    # Map previous conversation history turns
    for msg in history:
        role = "user" if msg.get("role") == "user" else "model"
        content_text = msg.get("content", "")
        if content_text:
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=content_text)]
                )
            )

    # Append current user prompt
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_message)]
        )
    )

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.7,
        max_output_tokens=500,
        thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.MINIMAL),
    )

    try:
        # Attempt 1: Standard Generation
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        reply = (response.text or "").strip().strip('"\'`')

        if is_valid_question(reply):
            return reply

        # Attempt 2: Retry once if the first response was not a valid question
        retry_contents = list(contents)
        retry_contents.append(
            types.Content(
                role="model",
                parts=[types.Part.from_text(text=reply)]
            )
        )
        retry_contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=RETRY_REMINDER)]
            )
        )

        retry_response = client.models.generate_content(
            model=model,
            contents=retry_contents,
            config=config,
        )

        retry_reply = (retry_response.text or "").strip().strip('"\'`')

        if is_valid_question(retry_reply):
            return retry_reply

        # Safe fallback if both attempts failed to format as a question
        return FALLBACK_QUESTION

    except APIError as e:
        err_msg = str(e)
        if "401" in err_msg or "403" in err_msg or "API_KEY_INVALID" in err_msg:
            raise ValueError(
                "Authentication failed: The GEMINI_API_KEY in backend/.env is invalid or expired. Please check your key."
            )
        elif "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
            raise RuntimeError(
                "Gemini quota/rate limit reached. Please verify that your Gemini API key has quota available."
            )
        else:
            raise RuntimeError(
                f"Gemini API error ({e.code if hasattr(e, 'code') else 'unknown'}): {e.message if hasattr(e, 'message') else str(e)}"
            )
    except Exception as e:
        raise RuntimeError(f"Could not connect to Gemini service: {str(e)}")