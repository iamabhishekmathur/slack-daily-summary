"""Configuration management for Slack summarizer"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class Config:
    """Configuration class for Slack summarizer"""

    # Slack credentials
    SLACK_USER_TOKEN: str = os.getenv("SLACK_USER_TOKEN", "")
    SLACK_BOT_TOKEN: str = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_USER_ID: str = os.getenv("SLACK_USER_ID", "")
    SLACK_SIGNING_SECRET: Optional[str] = os.getenv("SLACK_SIGNING_SECRET")

    # OpenAI credentials
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Timezone configuration
    TIMEZONE: str = "America/New_York"  # EST/EDT

    # Rate limiting
    RATE_LIMIT_DELAY: float = 1.0  # seconds between API calls
    MAX_RETRIES: int = 3
    BACKOFF_FACTOR: float = 2.0  # exponential backoff multiplier

    # Message limits
    MAX_MESSAGES_PER_CHANNEL: int = 50
    MAX_THREAD_REPLIES: int = 10
    MAX_MESSAGE_LENGTH: int = 500  # characters per message for AI summary

    # OpenAI limits
    MAX_TOKENS_INPUT: int = 2000
    MAX_TOKENS_OUTPUT: int = 500

    # Conversation types to fetch
    CONVERSATION_TYPES: list = ["public_channel", "private_channel", "mpim", "im"]

    # Mark as read behavior
    # Set SKIP_MARK_AS_READ=true to keep messages unread after summarizing
    SKIP_MARK_AS_READ: bool = os.getenv("SKIP_MARK_AS_READ", "false").lower() == "true"

    @classmethod
    def validate(cls) -> bool:
        """Validate that all required configuration is present"""
        missing = []

        if not cls.SLACK_USER_TOKEN:
            missing.append("SLACK_USER_TOKEN")
        if not cls.SLACK_BOT_TOKEN:
            missing.append("SLACK_BOT_TOKEN")
        if not cls.SLACK_USER_ID:
            missing.append("SLACK_USER_ID")
        if not cls.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")

        if missing:
            logger.error(f"Missing required configuration: {', '.join(missing)}")
            return False

        # Validate token formats
        if not cls.SLACK_USER_TOKEN.startswith("xoxp-"):
            logger.error("SLACK_USER_TOKEN must start with 'xoxp-'")
            return False

        if not cls.SLACK_BOT_TOKEN.startswith("xoxb-"):
            logger.error("SLACK_BOT_TOKEN must start with 'xoxb-'")
            return False

        if not cls.OPENAI_API_KEY.startswith("sk-"):
            logger.error("OPENAI_API_KEY must start with 'sk-'")
            return False

        logger.info("Configuration validated successfully")
        return True

    @classmethod
    def get_log_level(cls) -> int:
        """Get log level from environment"""
        level = os.getenv("LOG_LEVEL", "INFO").upper()
        return getattr(logging, level, logging.INFO)


# Set log level from config
logging.getLogger().setLevel(Config.get_log_level())
