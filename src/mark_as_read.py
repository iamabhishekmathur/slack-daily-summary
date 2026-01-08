"""Mark Slack messages as read"""

import logging
import time
from typing import Dict, List, Any
from slack_sdk.errors import SlackApiError
from src.slack_client import SlackClient
from src.config import Config

logger = logging.getLogger(__name__)


class MarkAsReadHandler:
    """Handle marking messages and threads as read in Slack"""

    def __init__(self, slack_client: SlackClient):
        """
        Initialize mark as read handler

        Args:
            slack_client: Configured SlackClient instance
        """
        self.client = slack_client
        self.marked_conversations: List[Dict[str, Any]] = []

    def mark_conversations_read(self, conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Mark all conversations as read

        Args:
            conversations: List of processed conversations

        Returns:
            Dictionary with results: {'success': [...], 'failed': [...]}
        """
        if not conversations:
            logger.info("No conversations to mark as read")
            return {'success': [], 'failed': []}

        logger.info(f"Marking {len(conversations)} conversations as read...")

        success = []
        failed = []

        for conv in conversations:
            channel_id = conv['channel_id']
            channel_name = conv['channel_name']

            try:
                # Find the latest timestamp in the conversation
                latest_ts = self._get_latest_timestamp(conv)

                if latest_ts:
                    result = self._mark_conversation_read(channel_id, latest_ts)
                    if result:
                        success.append({
                            'channel_id': channel_id,
                            'channel_name': channel_name,
                            'timestamp': latest_ts
                        })
                        logger.info(f"  ✓ Marked {channel_name} as read")
                    else:
                        failed.append({
                            'channel_id': channel_id,
                            'channel_name': channel_name,
                            'error': 'Mark operation returned false'
                        })
                else:
                    logger.warning(f"  ⚠ No valid timestamp found for {channel_name}")

            except Exception as e:
                logger.error(f"  ✗ Error marking {channel_name} as read: {e}")
                failed.append({
                    'channel_id': channel_id,
                    'channel_name': channel_name,
                    'error': str(e)
                })

            # Rate limiting delay
            time.sleep(Config.RATE_LIMIT_DELAY)

        logger.info(f"Marked {len(success)} conversations as read, {len(failed)} failed")

        # Store marked conversations for potential undo
        self.marked_conversations = success

        return {
            'success': success,
            'failed': failed
        }

    def _mark_conversation_read(self, channel_id: str, timestamp: str) -> bool:
        """
        Mark a conversation as read up to a timestamp

        Args:
            channel_id: Channel ID
            timestamp: Timestamp to mark read up to

        Returns:
            True if successful, False otherwise
        """
        try:
            # Use the user client to mark as read
            response = self.client.user_client.conversations_mark(
                channel=channel_id,
                ts=timestamp
            )

            return response.get('ok', False)

        except SlackApiError as e:
            error_msg = e.response['error']

            if error_msg == 'not_in_channel':
                logger.warning(f"Not in channel {channel_id}, skipping mark as read")
                return False
            elif error_msg == 'channel_not_found':
                logger.warning(f"Channel {channel_id} not found")
                return False
            else:
                logger.error(f"Slack API error marking {channel_id} as read: {error_msg}")
                raise

    def _get_latest_timestamp(self, conversation: Dict[str, Any]) -> str:
        """
        Get the latest timestamp from a conversation

        Args:
            conversation: Processed conversation dict

        Returns:
            Latest timestamp string or empty string if none found
        """
        timestamps = []

        # Get timestamps from regular messages
        for msg in conversation.get('messages', []):
            timestamps.append(msg['timestamp'])

        # Get timestamps from threads (including parent and replies)
        for thread in conversation.get('threads', []):
            # Parent timestamp
            timestamps.append(thread['parent']['timestamp'])

            # Reply timestamps
            for reply in thread.get('replies', []):
                timestamps.append(reply['timestamp'])

        if not timestamps:
            return ''

        # Return the latest timestamp
        # Timestamps are strings like '1234567890.123456', so string comparison works
        return max(timestamps)

    def get_marked_conversations(self) -> List[Dict[str, Any]]:
        """
        Get list of conversations that were marked as read

        Returns:
            List of marked conversation dicts
        """
        return self.marked_conversations
