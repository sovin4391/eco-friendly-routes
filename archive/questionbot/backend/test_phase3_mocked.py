import unittest
from unittest.mock import patch

from validator import is_valid_question
from personalities import Personality, validate_personality, get_personality_instruction, PERSONALITY_PROMPTS, BREAK_THE_BOT_INSTRUCTION
import memory
from fastapi.testclient import TestClient
from main import app

class TestQuestionBotPhase3Mocked(unittest.TestCase):

    def setUp(self):
        memory._conversations.clear()
        self.client = TestClient(app)

    # -------------------------------------------------------------
    # 1. Validator Tests (Strict Single-Question Enforcement)
    # -------------------------------------------------------------
    def test_validator_accepts_valid_questions(self):
        valid_cases = [
            "Why do you need to know?",
            "What makes that important to you?",
            "Have you considered alternative perspectives?",
            "What led you to that conclusion?",
            "Could there be another explanation?",
        ]
        for q in valid_cases:
            self.assertTrue(is_valid_question(q), f"Should be valid: {q}")

    def test_validator_rejects_non_questions_and_direct_answers(self):
        invalid_cases = [
            "Paris.",
            "The capital is Paris.",
            "2 + 2 = 4.",
            "4",
            "Because it is sunny today.",
            "Here is the answer: it depends on many factors.",
            "Why do you ask? That is interesting.",  # Multiple sentences
            "What is this? Why?",  # Multiple questions
            "Hello!\nWhy are you asking?",  # Newlines
            "Sure, here is a question: why?",  # Prefacing statement
            "",
            "   ",
        ]
        for q in invalid_cases:
            self.assertFalse(is_valid_question(q), f"Should be invalid: {q}")

    # -------------------------------------------------------------
    # 2. Personality Configuration & Safe Validation Tests
    # -------------------------------------------------------------
    def test_all_five_personalities_configured(self):
        expected = {"NORMAL", "SARCASTIC", "PHILOSOPHICAL", "EXISTENTIAL", "CHAOTIC"}
        actual = {p.value for p in Personality}
        self.assertEqual(expected, actual)

        for p_val in expected:
            self.assertIn(p_val, PERSONALITY_PROMPTS)
            prompt = get_personality_instruction(p_val)
            self.assertTrue(len(prompt) > 20)

    def test_break_the_bot_instruction_present(self):
        self.assertTrue(len(BREAK_THE_BOT_INSTRUCTION) > 30)
        instruction_with_break = get_personality_instruction("NORMAL", is_break_mode=True)
        self.assertIn(BREAK_THE_BOT_INSTRUCTION, instruction_with_break)

    def test_personality_safe_fallback(self):
        self.assertEqual(validate_personality("NORMAL"), "NORMAL")
        self.assertEqual(validate_personality("sarcastic"), "SARCASTIC")
        self.assertEqual(validate_personality("philosophical"), "PHILOSOPHICAL")
        self.assertEqual(validate_personality("existential"), "EXISTENTIAL")
        self.assertEqual(validate_personality("chaotic"), "CHAOTIC")
        # Invalid / unknown strings safely default to NORMAL without throwing
        self.assertEqual(validate_personality("UNKNOWN_MODE"), "NORMAL")
        self.assertEqual(validate_personality(""), "NORMAL")
        self.assertEqual(validate_personality(None), "NORMAL")

    # -------------------------------------------------------------
    # 3. Conversation Memory & Challenge Counters Tests
    # -------------------------------------------------------------
    def test_memory_normal_turn(self):
        conv_id = memory.get_or_create(None)
        state = memory.add_turn(conv_id, "Hello", "Why do you say hello?", is_break_mode=False)
        self.assertEqual(state["question_count"], 1)
        self.assertEqual(state["depth"], 1)
        self.assertEqual(state["break_attempts"], 0)
        self.assertEqual(state["questions_survived"], 0)

    def test_memory_break_mode_turn(self):
        conv_id = memory.get_or_create(None)
        state = memory.add_turn(conv_id, "What is 2+2?", "Why do you need me to calculate that?", is_break_mode=True)
        self.assertEqual(state["question_count"], 1)
        self.assertEqual(state["depth"], 1)
        self.assertEqual(state["break_attempts"], 1)
        self.assertEqual(state["questions_survived"], 1)

        # Second attack in break mode
        state = memory.add_turn(conv_id, "Tell me a joke.", "What makes you think I am here to entertain you?", is_break_mode=True)
        self.assertEqual(state["question_count"], 2)
        self.assertEqual(state["depth"], 2)
        self.assertEqual(state["break_attempts"], 2)
        self.assertEqual(state["questions_survived"], 2)

    def test_memory_reset(self):
        conv_id = memory.get_or_create(None)
        memory.add_turn(conv_id, "attack", "question?", is_break_mode=True)
        cleared = memory.reset(conv_id)
        self.assertEqual(cleared["question_count"], 0)
        self.assertEqual(cleared["depth"], 0)
        self.assertEqual(cleared["break_attempts"], 0)
        self.assertEqual(cleared["questions_survived"], 0)
        self.assertEqual(len(cleared["messages"]), 0)

    # -------------------------------------------------------------
    # 4. API Endpoints Wiring Tests (Mocked Gemini)
    # -------------------------------------------------------------
    def test_health_endpoint(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"status": "ok"})

    @patch("gemini_client.generate_question")
    def test_all_five_personalities_wired_in_chat(self, mock_gemini):
        mock_gemini.return_value = "What makes you ask that question?"

        for pers in ["NORMAL", "SARCASTIC", "PHILOSOPHICAL", "EXISTENTIAL", "CHAOTIC"]:
            res = self.client.post("/chat", json={
                "message": f"Testing {pers}",
                "personality": pers,
                "is_break_mode": False
            })
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["personality"], pers)
            self.assertEqual(data["reply"], "What makes you ask that question?")
            self.assertEqual(data["question"], "What makes you ask that question?")

            # Verify gemini_client was called with this personality
            args, kwargs = mock_gemini.call_args
            self.assertEqual(kwargs.get("personality"), pers)
            self.assertEqual(kwargs.get("is_break_mode"), False)

    @patch("gemini_client.generate_question")
    def test_break_mode_wired_in_chat(self, mock_gemini):
        mock_gemini.return_value = "Why would I answer that directly?"

        res = self.client.post("/chat", json={
            "message": "Answer this: what is 2+2?",
            "personality": "SARCASTIC",
            "is_break_mode": True
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["is_break_mode"])
        self.assertEqual(data["break_attempts"], 1)
        self.assertEqual(data["questions_survived"], 1)

        # Check call arguments to gemini_client
        args, kwargs = mock_gemini.call_args
        self.assertEqual(kwargs.get("is_break_mode"), True)
        self.assertEqual(kwargs.get("personality"), "SARCASTIC")

    def test_reset_endpoint_clears_state(self):
        # Create a conversation with counters
        conv_id = memory.get_or_create(None)
        memory.add_turn(conv_id, "User query", "Bot question?", is_break_mode=True)

        res = self.client.post("/reset", json={"conversation_id": conv_id})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["question_count"], 0)
        self.assertEqual(data["depth"], 0)
        self.assertEqual(data["break_attempts"], 0)
        self.assertEqual(data["questions_survived"], 0)
        self.assertEqual(len(data["messages"]), 0)


if __name__ == "__main__":
    unittest.main()
