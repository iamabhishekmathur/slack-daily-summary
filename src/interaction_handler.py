"""Handle Slack button interactions (simplified for MVP)"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class InteractionHandler:
    """
    Handle Slack button interactions

    Note: This is a simplified implementation for MVP.
    Buttons will open Slack deep links instead of automated undo.
    For full automation, would need webhook server (future enhancement).
    """

    def __init__(self):
        """Initialize interaction handler"""
        logger.info("Interaction handler initialized (simplified mode)")

    def create_keep_unread_button(self, channel_id: str, channel_name: str) -> Dict[str, Any]:
        """
        Create a "Keep Unread" button that opens the conversation in Slack

        Args:
            channel_id: Channel ID
            channel_name: Channel name for display

        Returns:
            Slack button element dict
        """
        # Create a button that opens the channel in Slack
        # This allows user to manually interact with messages to keep them unread
        return {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "Keep Unread",
                "emoji": True
            },
            "url": f"slack://channel?team={{TEAM_ID}}&id={channel_id}",
            "action_id": f"keep_unread_{channel_id}"
        }

    def create_view_messages_button(self, channel_link: str) -> Dict[str, Any]:
        """
        Create a "View Messages" button

        Args:
            channel_link: Full URL to channel

        Returns:
            Slack button element dict
        """
        return {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "View Messages",
                "emoji": True
            },
            "url": channel_link,
            "action_id": "view_messages"
        }

    def create_button_actions(
        self,
        channel_id: str,
        channel_name: str,
        channel_link: str
    ) -> Dict[str, Any]:
        """
        Create action block with both buttons

        Args:
            channel_id: Channel ID
            channel_name: Channel name
            channel_link: Link to channel

        Returns:
            Slack actions block
        """
        return {
            "type": "actions",
            "elements": [
                self.create_view_messages_button(channel_link),
                # Note: Keep Unread button removed for MVP since it requires webhook
                # User can use "View Messages" to access the channel
            ]
        }

    def create_instructions_text(self) -> str:
        """
        Create instructions text for the summary message

        Returns:
            Markdown formatted instructions
        """
        return """💡 *Note:* All messages have been marked as read. To keep a conversation unread, click "View Messages" and interact with it in Slack."""


def format_summary_blocks(
    conversations: List[Dict[str, Any]],
    interaction_handler: InteractionHandler,
    date_str: str
) -> List[Dict[str, Any]]:
    """
    Format conversations as Slack Block Kit blocks

    Args:
        conversations: List of processed conversations with summaries
        interaction_handler: InteractionHandler instance
        date_str: Date string for header

    Returns:
        List of Slack Block Kit blocks
    """
    blocks = []

    # Header
    blocks.append({
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": f"📬 Daily Slack Summary - {date_str}",
            "emoji": True
        }
    })

    # Instructions
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": interaction_handler.create_instructions_text()
        }
    })

    blocks.append({"type": "divider"})

    # Add each conversation
    for conv in conversations:
        # Channel name section
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{conv['channel_name']}* ({conv['total_count']} messages)"
            }
        })

        # Summary
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": conv['summary']
            }
        })

        # Buttons
        blocks.append(interaction_handler.create_button_actions(
            conv['channel_id'],
            conv['channel_name'],
            conv['channel_link']
        ))

        blocks.append({"type": "divider"})

    # Footer
    total_conversations = len(conversations)
    total_messages = sum(c['total_count'] for c in conversations)

    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"📊 Total: {total_messages} messages across {total_conversations} conversations"
            }
        ]
    })

    return blocks


def format_no_unreads_blocks(date_str: str) -> List[Dict[str, Any]]:
    """
    Format blocks for when there are no unread messages

    Args:
        date_str: Date string

    Returns:
        List of Slack Block Kit blocks
    """
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📬 Daily Slack Summary - {date_str}",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "✨ *All caught up!* You have no unread messages."
            }
        }
    ]


def format_error_blocks(error_message: str, date_str: str) -> List[Dict[str, Any]]:
    """
    Format blocks for error notification

    Args:
        error_message: Error description
        date_str: Date string

    Returns:
        List of Slack Block Kit blocks
    """
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"⚠️ Summary Error - {date_str}",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Error generating summary:*\n```{error_message}```"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Check GitHub Actions logs for details."
                }
            ]
        }
    ]
