import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

import memory
from memory import get_depth_title, evaluate_achievements, get_stats
from main import app


class TestQuestionBotPhase4Mocked(unittest.TestCase):

    def setUp(self):
        memory._conversations.clear()
        self.client = TestClient(app)

    # -------------------------------------------------------------
    # 1. Depth Progression Titles Test
    # -------------------------------------------------------------
    def test_depth_progression_titles(self):
        self.assertEqual(get_depth_title(0), "UNINITIATED")
        self.assertEqual(get_depth_title(1), "CURIOUS")
        self.assertEqual(get_depth_title(2), "CURIOUS")
        self.assertEqual(get_depth_title(3), "INTERROGATOR")
        self.assertEqual(get_depth_title(4), "INTERROGATOR")
        self.assertEqual(get_depth_title(5), "QUESTION ADDICT")
        self.assertEqual(get_depth_title(6), "QUESTION ADDICT")
        self.assertEqual(get_depth_title(7), "QUESTION ADDICT")
        self.assertEqual(get_depth_title(8), "PHILOSOPHER")
        self.assertEqual(get_depth_title(9), "PHILOSOPHER")
        self.assertEqual(get_depth_title(10), "EXISTENTIAL CRISIS")
        self.assertEqual(get_depth_title(15), "EXISTENTIAL CRISIS")
        self.assertEqual(get_depth_title(50), "EXISTENTIAL CRISIS")

    # -------------------------------------------------------------
    # 2. Achievement System Unlock Tests
    # -------------------------------------------------------------
    def test_achievements_evaluation(self):
        # Initial depth 0, 0 attempts -> 0 unlocked
        all_ach, newly = evaluate_achievements(0, 0, [])
        unlocked_ids = [a["id"] for a in all_ach if a["unlocked"]]
        self.assertEqual(unlocked_ids, [])
        self.assertEqual(newly, [])

        # Depth 1 -> FIRST_QUESTION unlocks
        all_ach, newly = evaluate_achievements(1, 0, [])
        unlocked_ids = [a["id"] for a in all_ach if a["unlocked"]]
        self.assertEqual(unlocked_ids, ["FIRST_QUESTION"])
        self.assertEqual(len(newly), 1)
        self.assertEqual(newly[0]["id"], "FIRST_QUESTION")

        # Break attempt 1 -> BOT_BREAKER unlocks
        all_ach, newly = evaluate_achievements(1, 1, ["FIRST_QUESTION"])
        unlocked_ids = [a["id"] for a in all_ach if a["unlocked"]]
        self.assertIn("BOT_BREAKER", unlocked_ids)
        self.assertIn("FIRST_QUESTION", unlocked_ids)
        self.assertEqual(len(newly), 1)
        self.assertEqual(newly[0]["id"], "BOT_BREAKER")

        # Depth 5 -> FIVE_DEEP unlocks
        all_ach, newly = evaluate_achievements(5, 1, ["FIRST_QUESTION", "BOT_BREAKER"])
        unlocked_ids = [a["id"] for a in all_ach if a["unlocked"]]
        self.assertIn("FIVE_DEEP", unlocked_ids)

        # Depth 10 -> EXISTENTIAL_CRISIS unlocks
        all_ach, newly = evaluate_achievements(10, 1, ["FIRST_QUESTION", "BOT_BREAKER", "FIVE_DEEP"])
        unlocked_ids = [a["id"] for a in all_ach if a["unlocked"]]
        self.assertIn("EXISTENTIAL_CRISIS", unlocked_ids)

        # Depth 15 -> QUESTION_ADDICT unlocks
        all_ach, newly = evaluate_achievements(15, 1, ["FIRST_QUESTION", "BOT_BREAKER", "FIVE_DEEP", "EXISTENTIAL_CRISIS"])
        unlocked_ids = [a["id"] for a in all_ach if a["unlocked"]]
        self.assertIn("QUESTION_ADDICT", unlocked_ids)
        self.assertEqual(len(unlocked_ids), 5)

    # -------------------------------------------------------------
    # 3. Conversation Stats / Summary Tests
    # -------------------------------------------------------------
    def test_conversation_stats_summary(self):
        conv_id = memory.get_or_create(None)
        memory.add_turn(conv_id, "User Q1", "Bot Q1?", personality="SARCASTIC", is_break_mode=False)
        memory.add_turn(conv_id, "User Q2", "Bot Q2?", personality="PHILOSOPHICAL", is_break_mode=True)

        conv = memory.get(conv_id)
        stats = get_stats(conv, current_personality="PHILOSOPHICAL")

        self.assertEqual(stats["questions_asked"], 2)
        self.assertEqual(stats["questions_returned"], 2)
        self.assertEqual(stats["answers_received"], 0)  # The central joke: strictly 0!
        self.assertEqual(stats["max_depth"], 2)
        self.assertEqual(stats["break_attempts"], 1)
        self.assertEqual(stats["questions_survived"], 1)
        self.assertIn("SARCASTIC", stats["personalities_used"])
        self.assertIn("PHILOSOPHICAL", stats["personalities_used"])
        self.assertEqual(stats["depth_message"], "You barely scratched the surface.")

    def test_depth_verdict_messages(self):
        # < 5
        conv = {"depth": 3, "max_depth": 3, "messages": [], "break_attempts": 0, "questions_survived": 0}
        self.assertEqual(get_stats(conv)["depth_message"], "You barely scratched the surface.")

        # 5-9
        conv = {"depth": 7, "max_depth": 7, "messages": [], "break_attempts": 0, "questions_survived": 0}
        self.assertEqual(get_stats(conv)["depth_message"], "You're getting suspiciously deep.")

        # 10+
        conv = {"depth": 11, "max_depth": 11, "messages": [], "break_attempts": 0, "questions_survived": 0}
        self.assertEqual(get_stats(conv)["depth_message"], "You have reached the Question Zone.")

    # -------------------------------------------------------------
    # 4. API Endpoints Return Phase 4 Fields
    # -------------------------------------------------------------
    @patch("gemini_client.generate_question")
    def test_chat_returns_phase4_fields(self, mock_gemini):
        mock_gemini.return_value = "What makes you curious?"

        res = self.client.post("/chat", json={
            "message": "First message",
            "personality": "CHAOTIC",
            "is_break_mode": True,
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("depth_title", data)
        self.assertEqual(data["depth_title"], "CURIOUS")
        self.assertIn("max_depth", data)
        self.assertEqual(data["max_depth"], 1)
        self.assertIn("achievements", data)
        self.assertEqual(len(data["achievements"]), 5)

        # Check unlocked achievements in response
        unlocked = [a for a in data["achievements"] if a["unlocked"]]
        unlocked_ids = [a["id"] for a in unlocked]
        self.assertIn("FIRST_QUESTION", unlocked_ids)
        self.assertIn("BOT_BREAKER", unlocked_ids)

        # Check stats object
        self.assertIn("stats", data)
        self.assertEqual(data["stats"]["answers_received"], 0)
        self.assertEqual(data["stats"]["questions_asked"], 1)
        self.assertEqual(data["stats"]["questions_returned"], 1)

    def test_stats_endpoint(self):
        conv_id = memory.get_or_create(None)
        memory.add_turn(conv_id, "Hello", "Why hello?", is_break_mode=False)

        res = self.client.get(f"/stats?conversation_id={conv_id}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["answers_received"], 0)
        self.assertEqual(data["questions_asked"], 1)
        self.assertEqual(data["questions_returned"], 1)
        self.assertEqual(data["depth_title"], "CURIOUS")


if __name__ == "__main__":
    unittest.main()
