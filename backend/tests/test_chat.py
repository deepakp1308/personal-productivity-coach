"""Tests for the chat API."""

import pytest
from backend.storage import db
from backend.api.chat import handle_chat, _route_question


@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    test_db = str(tmp_path / "test_coach.db")
    db.set_db_path(test_db)
    db.init_db()
    db.insert_priority("Advanced Analytics & AI-Powered Insights", "", 0.40, pillar=2)
    db.insert_priority("Platform Intelligence Across MC & QBO", "", 0.35, pillar=3)
    db.insert_priority("Trusted Data Foundation & Quality at Scale", "", 0.25, pillar=1)
    yield


class TestChatRouting:
    def test_time_question_routes(self):
        response = _route_question("What did I spend time on this week?")
        assert "Summary" in response or "activities" in response.lower()

    def test_alignment_question_routes(self):
        response = _route_question("Am I on track for my priorities?")
        assert "Alignment" in response or "alignment" in response

    def test_meeting_question_routes(self):
        response = _route_question("How many meetings do I have?")
        assert "Meeting" in response or "meeting" in response

    def test_priority_question_routes(self):
        response = _route_question("What are my priorities?")
        assert "Priorities" in response or "FY26" in response

    def test_decision_question_routes(self):
        response = _route_question("What decisions did I make?")
        assert "decision" in response.lower()

    def test_open_question_routes(self):
        response = _route_question("What's unresolved?")
        assert "question" in response.lower()

    def test_recommendation_question_routes(self):
        response = _route_question("Give me coaching advice")
        assert "recommendation" in response.lower() or "pipeline" in response.lower()

    def test_unknown_question_gives_help(self):
        response = _route_question("xyzzy foobar gibberish")
        assert "help" in response.lower() or "can help" in response.lower()


class TestHandleChat:
    def test_returns_response_and_session(self):
        result = handle_chat("What are my priorities?")
        assert "response" in result
        assert "context" in result
        assert "session_id" in result["context"]

    def test_saves_to_chat_history(self):
        result = handle_chat("Hello", session_id="test-session-1")
        history = db.get_chat_history("test-session-1")
        assert len(history) == 2  # user + assistant
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_preserves_session_id(self):
        result = handle_chat("Hi", session_id="my-session")
        assert result["context"]["session_id"] == "my-session"

    def test_generates_session_id_if_none(self):
        result = handle_chat("Hi")
        assert result["context"]["session_id"] is not None
        assert len(result["context"]["session_id"]) > 0
