"""Fetch unread messages from Slack"""

import logging
from typing import Dict, List, Any, Optional
from src.slack_client import SlackClient
from src.config import Config

logger = logging.getLogger(__name__)


class MessageFetcher:
    """Fetches unread messages from Slack across all conversation types"""

    def __init__(self, slack_client: SlackClient):
        """
        Initialize message fetcher

        Args:
            slack_client: Configured SlackClient instance
        """
        self.client = slack_client

    def fetch_all_unread_messages(self) -> Dict[str, Any]:
        """
        Fetch all unread messages from all conversations

        Returns:
            Dictionary mapping channel_id to conversation data:
            {
                'channel_id': {
                    'info': {...channel metadata...},
                    'messages': [...unread messages...],
                    'threads': {
                        'thread_ts': [...replies...]
                    }
                }
            }
        """
        logger.info("Starting to fetch unread messages...")

        # Get all conversations
        conversations = self.client.get_conversations_list()
        logger.info(f"Found {len(conversations)} total conversations")

        # Filter to conversations with unreads
        unread_conversations = self._get_unread_conversations(conversations)
        logger.info(f"Found {len(unread_conversations)} conversations with unread messages")

        if not unread_conversations:
            logger.info("No unread messages found")
            return {}

        # Fetch messages from each conversation with unreads
        all_unreads = {}
        for conversation in unread_conversations:
            channel_id = conversation['id']
            channel_name = self._get_conversation_name(conversation)

            logger.info(f"Fetching unreads from: {channel_name} ({channel_id})")

            try:
                unread_data = self._fetch_conversation_unreads(conversation)
                if unread_data['messages'] or unread_data['threads']:
                    all_unreads[channel_id] = unread_data
                    msg_count = len(unread_data['messages'])
                    thread_count = len(unread_data['threads'])
                    logger.info(f"  Found {msg_count} messages and {thread_count} threads")
            except Exception as e:
                logger.error(f"Error fetching unreads from {channel_name}: {e}")
                continue

        logger.info(f"Completed fetching unreads from {len(all_unreads)} conversations")
        return all_unreads

    def _get_unread_conversations(self, conversations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter conversations to those with unread messages

        Args:
            conversations: List of conversation objects from Slack

        Returns:
            List of conversations with unread messages
        """
        unread = []

        for convo in conversations:
            # Check unread count
            unread_count = convo.get('unread_count_display', 0)

            # Also check if there are unread messages based on last_read
            has_unread = (
                unread_count > 0 or
                (convo.get('last_read') and convo.get('latest') and
                 convo['last_read'] < convo['latest'].get('ts', '0'))
            )

            if has_unread:
                unread.append(convo)

        return unread

    def _fetch_conversation_unreads(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch unread messages and threads from a specific conversation

        Args:
            conversation: Conversation object from Slack

        Returns:
            Dictionary with conversation info, messages, and threads
        """
        channel_id = conversation['id']
        last_read = conversation.get('last_read', '0')

        # Fetch messages after last_read timestamp
        messages = self.client.get_conversation_history(
            channel_id=channel_id,
            oldest=last_read,
            limit=Config.MAX_MESSAGES_PER_CHANNEL
        )

        # Separate regular messages from thread parents
        regular_messages = []
        thread_parents = []

        for msg in messages:
            # Skip bot messages and system messages
            if msg.get('subtype') in ['bot_message', 'channel_join', 'channel_leave']:
                continue

            # Check if it's a thread parent with unread replies
            if msg.get('reply_count', 0) > 0:
                thread_parents.append(msg)
            else:
                # Only include if not a thread reply (thread replies have thread_ts != ts)
                if not msg.get('thread_ts') or msg.get('thread_ts') == msg.get('ts'):
                    regular_messages.append(msg)

        # Fetch thread replies
        threads = {}
        for parent in thread_parents:
            thread_ts = parent['ts']
            try:
                replies = self.client.get_thread_replies(
                    channel_id=channel_id,
                    thread_ts=thread_ts,
                    oldest=last_read
                )
                if replies:
                    threads[thread_ts] = {
                        'parent': parent,
                        'replies': replies
                    }
            except Exception as e:
                logger.warning(f"Error fetching thread {thread_ts}: {e}")
                continue

        return {
            'info': conversation,
            'messages': regular_messages,
            'threads': threads
        }

    def _get_conversation_name(self, conversation: Dict[str, Any]) -> str:
        """
        Get a human-readable name for a conversation

        Args:
            conversation: Conversation object from Slack

        Returns:
            Conversation name or description
        """
        if conversation.get('is_im'):
            # Direct message - get user name
            user_id = conversation.get('user')
            if user_id:
                try:
                    user = self.client.get_user_info(user_id)
                    return f"DM with {user.get('real_name', user.get('name', 'Unknown'))}"
                except Exception:
                    return f"DM (ID: {conversation['id']})"
            return "Direct Message"

        elif conversation.get('is_mpim'):
            # Multi-person DM
            name = conversation.get('name', 'Group DM')
            return f"Group: {name}"

        else:
            # Channel (public or private)
            is_private = conversation.get('is_private', False)
            name = conversation.get('name', conversation.get('name_normalized', 'Unknown'))
            prefix = "🔒" if is_private else "#"
            return f"{prefix}{name}"
