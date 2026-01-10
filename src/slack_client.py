"""Slack API client with rate limiting and error handling"""

import time
import logging
from typing import List, Dict, Any, Optional
from functools import wraps
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from src.config import Config

logger = logging.getLogger(__name__)


def rate_limited(func):
    """Decorator to add rate limiting to Slack API calls"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        time.sleep(Config.RATE_LIMIT_DELAY)
        return func(*args, **kwargs)
    return wrapper


def retry_on_rate_limit(func):
    """Decorator to retry on rate limit errors with exponential backoff"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        retries = 0
        backoff = 1

        while retries < Config.MAX_RETRIES:
            try:
                return func(*args, **kwargs)
            except SlackApiError as e:
                if e.response['error'] == 'rate_limited':
                    retry_after = int(e.response.get('headers', {}).get('Retry-After', backoff))
                    logger.warning(f"Rate limited. Waiting {retry_after}s before retry {retries + 1}/{Config.MAX_RETRIES}")
                    time.sleep(retry_after)
                    retries += 1
                    backoff *= Config.BACKOFF_FACTOR
                else:
                    raise
        raise Exception(f"Max retries ({Config.MAX_RETRIES}) exceeded for rate limiting")

    return wrapper


class SlackClient:
    """Wrapper around Slack SDK with rate limiting and pagination support"""

    def __init__(self, user_token: str, bot_token: str):
        """
        Initialize Slack clients

        Args:
            user_token: User OAuth token (xoxp-...) for reading messages
            bot_token: Bot OAuth token (xoxb-...) for sending messages
        """
        self.user_client = WebClient(token=user_token)
        self.bot_client = WebClient(token=bot_token)
        logger.info("Slack clients initialized")

    @rate_limited
    @retry_on_rate_limit
    def get_conversations_list(self, types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get all conversations (channels, DMs, etc.) with pagination

        Args:
            types: List of conversation types (e.g., ['public_channel', 'private_channel', 'im', 'mpim'])

        Returns:
            List of conversation objects
        """
        if types is None:
            types = Config.CONVERSATION_TYPES

        types_str = ",".join(types)
        conversations = []
        cursor = None

        logger.info(f"Fetching conversations of types: {types_str}")

        while True:
            try:
                response = self.user_client.conversations_list(
                    types=types_str,
                    exclude_archived=True,
                    limit=200,
                    cursor=cursor
                )

                conversations.extend(response['channels'])

                # Check if there are more pages
                cursor = response.get('response_metadata', {}).get('next_cursor')
                if not cursor:
                    break

                logger.debug(f"Fetched {len(conversations)} conversations so far, continuing pagination...")

            except SlackApiError as e:
                logger.error(f"Error fetching conversations: {e.response['error']}")
                raise

        logger.info(f"Fetched {len(conversations)} total conversations")
        return conversations

    @rate_limited
    @retry_on_rate_limit
    def get_conversation_history(
        self,
        channel_id: str,
        oldest: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history with pagination

        Args:
            channel_id: Channel ID
            oldest: Only messages after this timestamp
            limit: Maximum number of messages to fetch

        Returns:
            List of message objects
        """
        messages = []
        cursor = None
        fetched_count = 0

        while fetched_count < limit:
            try:
                params = {
                    'channel': channel_id,
                    'limit': min(200, limit - fetched_count),
                    'cursor': cursor
                }
                if oldest:
                    params['oldest'] = oldest

                response = self.user_client.conversations_history(**params)
                batch = response['messages']
                messages.extend(batch)
                fetched_count += len(batch)

                # Check if there are more pages
                cursor = response.get('response_metadata', {}).get('next_cursor')
                if not cursor or not batch:
                    break

            except SlackApiError as e:
                logger.error(f"Error fetching history for channel {channel_id}: {e.response['error']}")
                raise

        logger.debug(f"Fetched {len(messages)} messages from channel {channel_id}")
        return messages

    @rate_limited
    @retry_on_rate_limit
    def get_thread_replies(
        self,
        channel_id: str,
        thread_ts: str,
        oldest: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get replies to a thread

        Args:
            channel_id: Channel ID
            thread_ts: Thread timestamp
            oldest: Only fetch replies after this timestamp

        Returns:
            List of reply message objects
        """
        try:
            params = {
                'channel': channel_id,
                'ts': thread_ts,
                'limit': Config.MAX_THREAD_REPLIES
            }
            if oldest:
                params['oldest'] = oldest

            response = self.user_client.conversations_replies(**params)

            # First message is the parent, rest are replies
            messages = response['messages']
            replies = messages[1:] if len(messages) > 1 else []

            logger.debug(f"Fetched {len(replies)} replies from thread {thread_ts}")
            return replies

        except SlackApiError as e:
            logger.error(f"Error fetching thread replies: {e.response['error']}")
            raise

    @rate_limited
    @retry_on_rate_limit
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information

        Args:
            user_id: User ID

        Returns:
            User info object
        """
        try:
            response = self.user_client.users_info(user=user_id)
            return response['user']
        except SlackApiError as e:
            logger.warning(f"Error fetching user info for {user_id}: {e.response['error']}")
            return {'id': user_id, 'name': 'Unknown User', 'real_name': 'Unknown User'}

    @rate_limited
    @retry_on_rate_limit
    def get_conversation_info(self, channel_id: str) -> Dict[str, Any]:
        """
        Get conversation/channel information

        Args:
            channel_id: Channel ID

        Returns:
            Conversation info object
        """
        try:
            response = self.user_client.conversations_info(channel=channel_id)
            return response['channel']
        except SlackApiError as e:
            logger.warning(f"Error fetching conversation info for {channel_id}: {e.response['error']}")
            return {'id': channel_id, 'name': 'Unknown Channel'}

    @rate_limited
    @retry_on_rate_limit
    def send_dm(self, user_id: str, blocks: List[Dict[str, Any]], text: str = "") -> Dict[str, Any]:
        """
        Send a DM to a user using bot token

        Args:
            user_id: User ID to send DM to
            blocks: Slack Block Kit blocks
            text: Fallback text

        Returns:
            Response from Slack API
        """
        try:
            # Open DM channel with user
            im_response = self.bot_client.conversations_open(users=user_id)
            channel_id = im_response['channel']['id']

            # Send message
            response = self.bot_client.chat_postMessage(
                channel=channel_id,
                blocks=blocks,
                text=text
            )

            logger.info(f"Sent DM to user {user_id}")
            return response

        except SlackApiError as e:
            logger.error(f"Error sending DM: {e.response['error']}")
            raise

    @rate_limited
    @retry_on_rate_limit
    def update_message(
        self,
        channel_id: str,
        message_ts: str,
        blocks: List[Dict[str, Any]],
        text: str = ""
    ) -> Dict[str, Any]:
        """
        Update an existing message

        Args:
            channel_id: Channel ID
            message_ts: Message timestamp
            blocks: New Slack Block Kit blocks
            text: Fallback text

        Returns:
            Response from Slack API
        """
        try:
            response = self.bot_client.chat_update(
                channel=channel_id,
                ts=message_ts,
                blocks=blocks,
                text=text
            )
            logger.debug(f"Updated message {message_ts} in channel {channel_id}")
            return response

        except SlackApiError as e:
            logger.error(f"Error updating message: {e.response['error']}")
            raise

    def get_team_info(self) -> Dict[str, Any]:
        """
        Get team/workspace information

        Returns:
            Team info including domain
        """
        try:
            response = self.user_client.team_info()
            return response['team']
        except SlackApiError as e:
            logger.error(f"Error fetching team info: {e.response['error']}")
            return {'domain': 'slack', 'id': 'unknown'}
