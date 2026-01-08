"""Main orchestration for Slack unread messages summarizer"""

import sys
import logging
from datetime import datetime
import pytz
from src.config import Config, logger
from src.slack_client import SlackClient
from src.message_fetcher import MessageFetcher
from src.message_processor import MessageProcessor
from src.summarizer import Summarizer
from src.mark_as_read import MarkAsReadHandler
from src.interaction_handler import (
    InteractionHandler,
    format_summary_blocks,
    format_no_unreads_blocks,
    format_error_blocks
)


def get_current_date_string() -> str:
    """
    Get current date in EST/EDT timezone

    Returns:
        Formatted date string
    """
    tz = pytz.timezone(Config.TIMEZONE)
    now = datetime.now(tz)
    return now.strftime("%A, %B %d, %Y")


def send_error_notification(slack_client: SlackClient, error_message: str):
    """
    Send error notification to user

    Args:
        slack_client: Configured SlackClient
        error_message: Error description
    """
    try:
        date_str = get_current_date_string()
        blocks = format_error_blocks(error_message, date_str)

        slack_client.send_dm(
            user_id=Config.SLACK_USER_ID,
            blocks=blocks,
            text=f"Error generating daily summary: {error_message}"
        )
        logger.info("Sent error notification to user")
    except Exception as e:
        logger.error(f"Failed to send error notification: {e}")


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Slack Daily Unread Messages Summarizer")
    logger.info("=" * 60)

    try:
        # 1. Validate configuration
        logger.info("Step 1: Validating configuration...")
        if not Config.validate():
            raise Exception("Configuration validation failed")

        # 2. Initialize clients
        logger.info("Step 2: Initializing Slack clients...")
        slack_client = SlackClient(
            user_token=Config.SLACK_USER_TOKEN,
            bot_token=Config.SLACK_BOT_TOKEN
        )

        logger.info("Step 3: Initializing components...")
        fetcher = MessageFetcher(slack_client)
        processor = MessageProcessor(slack_client)
        summarizer = Summarizer(Config.OPENAI_API_KEY, Config.OPENAI_MODEL)
        mark_as_read_handler = MarkAsReadHandler(slack_client)
        interaction_handler = InteractionHandler()

        # 3. Fetch unread messages
        logger.info("Step 4: Fetching unread messages...")
        raw_messages = fetcher.fetch_all_unread_messages()

        if not raw_messages:
            logger.info("No unread messages found. Sending 'all caught up' message...")
            date_str = get_current_date_string()
            blocks = format_no_unreads_blocks(date_str)

            slack_client.send_dm(
                user_id=Config.SLACK_USER_ID,
                blocks=blocks,
                text="All caught up! No unread messages."
            )

            logger.info("✓ Summary sent successfully")
            logger.info("=" * 60)
            return 0

        # 4. Process and enrich messages
        logger.info("Step 5: Processing messages...")
        processed_conversations = processor.process_messages(raw_messages)

        if not processed_conversations:
            logger.info("No conversations after processing. Sending 'all caught up' message...")
            date_str = get_current_date_string()
            blocks = format_no_unreads_blocks(date_str)

            slack_client.send_dm(
                user_id=Config.SLACK_USER_ID,
                blocks=blocks,
                text="All caught up! No unread messages."
            )

            logger.info("✓ Summary sent successfully")
            logger.info("=" * 60)
            return 0

        # 5. Generate AI summaries
        logger.info("Step 6: Generating AI summaries...")
        summarized_conversations = summarizer.summarize_conversations(processed_conversations)

        # 6. Mark messages as read
        logger.info("Step 7: Marking messages as read...")
        mark_results = mark_as_read_handler.mark_conversations_read(summarized_conversations)

        if mark_results['failed']:
            logger.warning(f"Failed to mark {len(mark_results['failed'])} conversations as read")
            for failed in mark_results['failed']:
                logger.warning(f"  - {failed['channel_name']}: {failed['error']}")

        # 7. Format and send summary
        logger.info("Step 8: Sending summary DM...")
        date_str = get_current_date_string()
        blocks = format_summary_blocks(
            summarized_conversations,
            interaction_handler,
            date_str
        )

        # Calculate totals for fallback text
        total_messages = sum(c['total_count'] for c in summarized_conversations)
        total_conversations = len(summarized_conversations)

        response = slack_client.send_dm(
            user_id=Config.SLACK_USER_ID,
            blocks=blocks,
            text=f"Daily Summary: {total_messages} messages across {total_conversations} conversations"
        )

        logger.info("✓ Summary sent successfully")
        logger.info(f"  Message timestamp: {response['ts']}")
        logger.info(f"  Total conversations: {total_conversations}")
        logger.info(f"  Total messages: {total_messages}")
        logger.info("=" * 60)

        return 0

    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        return 1

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)

        # Try to send error notification
        try:
            if 'slack_client' in locals():
                send_error_notification(slack_client, str(e))
        except Exception:
            pass

        logger.info("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
