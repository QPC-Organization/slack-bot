"""
Pytest coverage for /kr mentor prompt and follow-up flows.
"""

import os
import sys
from unittest.mock import Mock, MagicMock

import pytest

# Ensure repo paths are available for absolute imports
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_PATH = os.path.join(REPO_ROOT, "src")

for path in (REPO_ROOT, SRC_PATH):
    if path not in sys.path:
        sys.path.insert(0, path)

# Provide mocked utils module for src imports that require it
mock_utils = MagicMock()
mock_utils.logger = MagicMock()
mock_utils.error_handler = MagicMock()
mock_utils.input_validator = MagicMock()
mock_utils.input_validator.validate_user_id = MagicMock(return_value=True)
mock_utils.safe_executor = MagicMock()
mock_utils.safe_executor.execute = lambda func, name, user_id, **kwargs: func(**kwargs)
sys.modules["utils"] = mock_utils


class ImmediateThread:
    """Helper thread replacement that executes immediately during tests."""

    def __init__(self, target=None, args=(), kwargs=None):
        self._target = target
        self._args = args
        self._kwargs = kwargs or {}
        self.daemon = False

    def start(self):
        if self._target:
            self._target(*self._args, **self._kwargs)


@pytest.fixture
def mentor_yes_payload():
    return {
        "user": {"id": "U123"},
        "actions": [
            {"action_id": "mentor_yes", "value": "mentor_yes_kr_U123"}
        ],
        "channel": {"id": "C123"},
        "message": {"ts": "167890.123"},
    }


@pytest.fixture
def mentor_no_payload():
    return {
        "user": {"id": "U123"},
        "actions": [
            {"action_id": "mentor_no", "value": "mentor_no_kr_U123"}
        ],
        "channel": {"id": "C123"},
        "message": {"ts": "167890.123"},
    }


def test_kr_command_triggers_mentor_prompt(monkeypatch, mock_slack_client):
    """Ensure /kr command prompts mentor confirmation with parsed sprint/search data."""
    import src.commands as commands

    monkeypatch.setattr(commands.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(commands.time, "sleep", lambda *_: None)

    bot = Mock()
    bot.client = mock_slack_client
    bot.send_mentor_check = Mock(return_value=True)
    bot.pending_kr_search = {}
    bot.pending_kr_sprint = {}
    mock_slack_client.users_info.return_value = {
        "user": {"real_name": "Test User"}
    }

    result = commands._handle_kr_command(
        bot=bot,
        user_id="U123",
        text="5 engagement",
        channel_id="C123",
    )

    assert result is True
    bot.send_mentor_check.assert_called_once_with(
        user_id="U123",
        standup_ts=None,
        user_name="Test User",
        request_type="kr",
        channel="U123",
        search_term="engagement",
        sprint_number=5,
    )


def test_handle_mentor_response_success(monkeypatch, mentor_yes_payload):
    """KR lookup continues once mentor confirmation is received."""
    from src.events import handle_mentor_response

    bot = Mock()
    bot.get_user_name.return_value = "Test User"
    bot.pending_kr_search = {"U123": "engagement"}
    bot.pending_kr_sprint = {"U123": 5}
    bot.coda = Mock()
    bot.coda.search_kr_table.return_value = [
        {
            "c-yQ1M6UqTSj": "Increase Engagement",
            "c-efR-vVo_3w": "Owner A",
            "c-cC29Yow8Gr": "In Progress",
            "c-P_mQJLObL0": "Reach 40% DAU",
            "link": "https://example.com/kr",
        }
    ]
    bot.send_dm = Mock()
    bot.update_message = Mock()

    response = handle_mentor_response(bot, mentor_yes_payload)

    assert response == {"response_action": "clear"}
    bot.coda.search_kr_table.assert_called_once_with("engagement")

    # Ensure user receives search in-progress info and the KR results
    sent_messages = [" ".join(call.args[1].split()) for call in bot.send_dm.call_args_list]
    assert any("Give me one moment" in msg for msg in sent_messages)
    assert any("Increase Engagement" in msg for msg in sent_messages)

    assert "U123" not in bot.pending_kr_search
    assert "U123" not in bot.pending_kr_sprint


def test_handle_mentor_response_not_contacted(monkeypatch, mentor_no_payload):
    """Mentor 'no' response updates the prompt with instructional text."""
    from src.events import handle_mentor_response

    bot = Mock()
    bot.get_user_name.return_value = "Test User"
    bot.pending_kr_search = {"U123": "engagement"}
    bot.pending_kr_sprint = {"U123": 5}
    bot.coda = Mock()
    bot.send_dm = Mock()
    bot.update_message = Mock()

    response = handle_mentor_response(bot, mentor_no_payload)

    assert response == {"response_action": "clear"}
    bot.coda.search_kr_table.assert_not_called()
    bot.update_message.assert_called_once()
    update_kwargs = bot.update_message.call_args.kwargs
    assert "mentor" in update_kwargs.get("text", "").lower()

