"""Process and enrich Slack messages with metadata"""

import logging
from typing import Dict, List, Any, Optional
from src.slack_client import SlackClient
from src.config import Config

logger = logging.getLogger(__name__)


class MessageProcessor:
    """Process messages: enrich with metadata, group, and prioritize"""

    def __init__(self, slack_client: SlackClient):
        """
        Initialize message processor

        Args:
            slack_client: Configured SlackClient instance
        """
        self.client = slack_client
        self.user_cache: Dict[str, Dict[str, Any]] = {}
        self.team_info: Optional[Dict[str, Any]] = None

    def process_messages(self, raw_messages: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process raw messages: enrich with metadata and organize

        Args:
            raw_messages: Dictionary from MessageFetcher with channel_id -> data

        Returns:
            List of processed conversation groups ready for summarization
        """
        if not raw_messages:
            logger.info("No messages to process")
            return []

        logger.info(f"Processing {len(raw_messages)} conversations...")

        # Get team info for permalinks
        self.team_info = self.client.get_team_info()

        processed = []
        for channel_id, data in raw_messages.items():
            try:
                conversation = self._process_conversation(channel_id, data)
                if conversation:
                    processed.append(conversation)
            except Exception as e:
                logger.error(f"Error processing conversation {channel_id}: {e}")
                continue

        # Prioritize conversations
        prioritized = self._prioritize_conversations(processed)

        logger.info(f"Processed {len(prioritized)} conversations")
        return prioritized

    def _process_conversation(self, channel_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single conversation

        Args:
            channel_id: Channel ID
            data: Conversation data from MessageFetcher

        Returns:
            Processed conversation dict or None if empty
        """
        info = data['info']
        messages = data['messages']
        threads = data['threads']

        # Enrich messages with metadata
        enriched_messages = []
        for msg in messages:
            enriched = self._enrich_message(channel_id, msg)
            if enriched:
                enriched_messages.append(enriched)

        # Enrich threads
        enriched_threads = []
        for thread_ts, thread_data in threads.items():
            enriched_thread = self._enrich_thread(channel_id, thread_data)
            if enriched_thread:
                enriched_threads.append(enriched_thread)

        # Skip if no content after enrichment
        if not enriched_messages and not enriched_threads:
            return None

        return {
            'channel_id': channel_id,
            'channel_name': self._get_conversation_display_name(info),
            'channel_type': self._get_conversation_type(info),
            'is_dm': info.get('is_im', False),
            'is_private': info.get('is_private', False),
            'messages': enriched_messages,
            'threads': enriched_threads,
            'total_count': len(enriched_messages) + len(enriched_threads),
            'channel_link': self._get_channel_link(channel_id)
        }

    def _enrich_message(self, channel_id: str, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Enrich a message with user info and permalink

        Args:
            channel_id: Channel ID
            message: Raw message from Slack

        Returns:
            Enriched message dict or None if should be skipped
        """
        # Skip messages without text
        if not message.get('text'):
            return None

        user_id = message.get('user')
        if not user_id:
            return None

        # Get user info (with caching)
        user = self._get_user_info_cached(user_id)

        # Truncate long messages
        text = message['text']
        if len(text) > Config.MAX_MESSAGE_LENGTH:
            text = text[:Config.MAX_MESSAGE_LENGTH] + "..."

        return {
            'text': text,
            'user_id': user_id,
            'user_name': user.get('real_name', user.get('name', 'Unknown')),
            'timestamp': message['ts'],
            'permalink': self._generate_permalink(channel_id, message['ts']),
            'has_attachments': bool(message.get('files') or message.get('attachments')),
            'reactions': message.get('reactions', [])
        }

    def _enrich_thread(self, channel_id: str, thread_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Enrich a thread with metadata

        Args:
            channel_id: Channel ID
            thread_data: Thread data with parent and replies

        Returns:
            Enriched thread dict
        """
        parent = thread_data['parent']
        replies = thread_data['replies']

        # Enrich parent message
        enriched_parent = self._enrich_message(channel_id, parent)
        if not enriched_parent:
            return None

        # Enrich replies
        enriched_replies = []
        for reply in replies[:Config.MAX_THREAD_REPLIES]:
            enriched_reply = self._enrich_message(channel_id, reply)
            if enriched_reply:
                enriched_replies.append(enriched_reply)

        return {
            'parent': enriched_parent,
            'replies': enriched_replies,
            'reply_count': len(replies),
            'showing_count': len(enriched_replies),
            'thread_link': enriched_parent['permalink']
        }

    def _get_user_info_cached(self, user_id: str) -> Dict[str, Any]:
        """
        Get user info with caching

        Args:
            user_id: User ID

        Returns:
            User info dict
        """
        if user_id not in self.user_cache:
            self.user_cache[user_id] = self.client.get_user_info(user_id)
        return self.user_cache[user_id]

    def _generate_permalink(self, channel_id: str, message_ts: str) -> str:
        """
        Generate Slack permalink for a message

        Args:
            channel_id: Channel ID
            message_ts: Message timestamp

        Returns:
            Slack permalink URL
        """
        # Convert timestamp: 1234567890.123456 -> 1234567890123456
        ts_parts = message_ts.split('.')
        if len(ts_parts) == 2:
            permalink_ts = ts_parts[0] + ts_parts[1]
        else:
            permalink_ts = message_ts.replace('.', '')

        team_domain = self.team_info.get('domain', 'slack') if self.team_info else 'slack'
        return f"https://{team_domain}.slack.com/archives/{channel_id}/p{permalink_ts}"

    def _get_channel_link(self, channel_id: str) -> str:
        """
        Generate link to channel

        Args:
            channel_id: Channel ID

        Returns:
            Slack channel URL
        """
        team_domain = self.team_info.get('domain', 'slack') if self.team_info else 'slack'
        return f"https://{team_domain}.slack.com/archives/{channel_id}"

    def _get_conversation_display_name(self, info: Dict[str, Any]) -> str:
        """
        Get display name for a conversation

        Args:
            info: Conversation info from Slack

        Returns:
            Display name
        """
        if info.get('is_im'):
            user_id = info.get('user')
            if user_id:
                user = self._get_user_info_cached(user_id)
                return f"DM with {user.get('real_name', user.get('name', 'Unknown'))}"
            return "Direct Message"

        elif info.get('is_mpim'):
            name = info.get('name', 'group')
            # Clean up mpim name format (remove mpdm- prefix and timestamps)
            if name.startswith('mpdm-'):
                name = name[5:].split('--')[0]
            return f"Group: {name}"

        else:
            name = info.get('name', info.get('name_normalized', 'unknown'))
            is_private = info.get('is_private', False)
            prefix = "🔒 " if is_private else "#"
            return f"{prefix}{name}"

    def _get_conversation_type(self, info: Dict[str, Any]) -> str:
        """
        Get conversation type

        Args:
            info: Conversation info from Slack

        Returns:
            Type string: 'dm', 'group_dm', 'private_channel', 'public_channel'
        """
        if info.get('is_im'):
            return 'dm'
        elif info.get('is_mpim'):
            return 'group_dm'
        elif info.get('is_private'):
            return 'private_channel'
        else:
            return 'public_channel'

    def _prioritize_conversations(self, conversations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort conversations by priority

        Priority order:
        1. Direct messages
        2. Private channels
        3. Group DMs
        4. Public channels

        Within each category, sort by message count (descending)

        Args:
            conversations: List of processed conversations

        Returns:
            Sorted list of conversations
        """
        priority_order = {
            'dm': 1,
            'private_channel': 2,
            'group_dm': 3,
            'public_channel': 4
        }

        def sort_key(conv):
            priority = priority_order.get(conv['channel_type'], 5)
            count = conv['total_count']
            return (priority, -count)  # Negative count for descending order

        return sorted(conversations, key=sort_key)
