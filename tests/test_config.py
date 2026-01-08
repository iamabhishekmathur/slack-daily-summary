"""Tests for configuration module"""

import pytest
import os
from src.config import Config


class TestConfig:
    """Test configuration management"""

    def test_config_validation_missing_tokens(self, monkeypatch):
        """Test that validation fails with missing tokens"""
        # Clear environment variables
        monkeypatch.setenv("SLACK_USER_TOKEN", "")
        monkeypatch.setenv("SLACK_BOT_TOKEN", "")
        monkeypatch.setenv("OPENAI_API_KEY", "")
        monkeypatch.setenv("SLACK_USER_ID", "")

        # Reload config
        Config.SLACK_USER_TOKEN = ""
        Config.SLACK_BOT_TOKEN = ""
        Config.OPENAI_API_KEY = ""
        Config.SLACK_USER_ID = ""

        assert not Config.validate()

    def test_config_validation_invalid_token_format(self, monkeypatch):
        """Test that validation fails with invalid token formats"""
        monkeypatch.setenv("SLACK_USER_TOKEN", "invalid-token")
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-validbot")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-validkey")
        monkeypatch.setenv("SLACK_USER_ID", "U123")

        Config.SLACK_USER_TOKEN = "invalid-token"
        Config.SLACK_BOT_TOKEN = "xoxb-validbot"
        Config.OPENAI_API_KEY = "sk-validkey"
        Config.SLACK_USER_ID = "U123"

        assert not Config.validate()

    def test_config_validation_success(self, monkeypatch):
        """Test that validation succeeds with valid tokens"""
        monkeypatch.setenv("SLACK_USER_TOKEN", "xoxp-valid-user-token")
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-valid-bot-token")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-valid-api-key")
        monkeypatch.setenv("SLACK_USER_ID", "U01234ABCDE")

        Config.SLACK_USER_TOKEN = "xoxp-valid-user-token"
        Config.SLACK_BOT_TOKEN = "xoxb-valid-bot-token"
        Config.OPENAI_API_KEY = "sk-valid-api-key"
        Config.SLACK_USER_ID = "U01234ABCDE"

        assert Config.validate()

    def test_conversation_types_configured(self):
        """Test that conversation types are properly configured"""
        assert "public_channel" in Config.CONVERSATION_TYPES
        assert "private_channel" in Config.CONVERSATION_TYPES
        assert "im" in Config.CONVERSATION_TYPES
        assert "mpim" in Config.CONVERSATION_TYPES

    def test_rate_limits_configured(self):
        """Test that rate limits are configured"""
        assert Config.RATE_LIMIT_DELAY > 0
        assert Config.MAX_RETRIES > 0
        assert Config.BACKOFF_FACTOR > 1
