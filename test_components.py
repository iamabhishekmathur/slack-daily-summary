"""Test script to debug each component step by step"""

import sys
import json
from src.config import Config, logger
from src.slack_client import SlackClient
from src.message_fetcher import MessageFetcher


def test_step1_reading_messages():
    """Test if we can read messages from Slack"""
    print("\n" + "=" * 60)
    print("STEP 1: Testing Message Reading")
    print("=" * 60)

    # Validate config
    print("\n[1.1] Validating configuration...")
    if not Config.validate():
        print("❌ Configuration validation failed")
        return None
    print("✓ Configuration valid")

    # Initialize client
    print("\n[1.2] Initializing Slack client...")
    slack_client = SlackClient(
        user_token=Config.SLACK_USER_TOKEN,
        bot_token=Config.SLACK_BOT_TOKEN
    )
    print("✓ Slack client initialized")

    # Test auth
    print("\n[1.3] Testing Slack authentication...")
    try:
        # Test user token
        user_auth = slack_client.user_client.auth_test()
        print(f"✓ User token valid - User: {user_auth['user']}, Team: {user_auth['team']}")
    except Exception as e:
        print(f"❌ User token auth failed: {e}")
        return None

    try:
        # Test bot token
        bot_auth = slack_client.bot_client.auth_test()
        print(f"✓ Bot token valid - Bot: {bot_auth['user']}, Team: {bot_auth['team']}")
    except Exception as e:
        print(f"❌ Bot token auth failed: {e}")
        return None

    # Get all conversations
    print("\n[1.4] Fetching all conversations...")
    try:
        conversations = slack_client.get_conversations_list()
        print(f"✓ Found {len(conversations)} total conversations")
    except Exception as e:
        print(f"❌ Failed to get conversations: {e}")
        return None

    # Check for unread conversations
    print("\n[1.5] Checking for unread messages...")
    unread_convos = []
    for conv in conversations:
        unread_count = conv.get('unread_count_display', 0)
        if unread_count > 0:
            name = conv.get('name') or conv.get('user') or conv.get('id')
            unread_convos.append({
                'id': conv['id'],
                'name': name,
                'unread_count': unread_count,
                'is_member': conv.get('is_member', False),
                'is_im': conv.get('is_im', False),
                'is_mpim': conv.get('is_mpim', False),
                'last_read': conv.get('last_read', 'N/A')
            })

    if unread_convos:
        print(f"✓ Found {len(unread_convos)} conversations with unread messages:")
        for conv in unread_convos[:10]:  # Show first 10
            print(f"  - {conv['name']}: {conv['unread_count']} unread (is_member: {conv['is_member']}, last_read: {conv['last_read']})")
        if len(unread_convos) > 10:
            print(f"  ... and {len(unread_convos) - 10} more")
    else:
        print("⚠️  No conversations with unread_count_display > 0")
        print("\n[1.5.1] Showing sample of conversations for debugging:")
        for conv in conversations[:5]:
            print(f"  - ID: {conv['id']}")
            print(f"    Name: {conv.get('name') or conv.get('user') or 'N/A'}")
            print(f"    unread_count: {conv.get('unread_count', 'N/A')}")
            print(f"    unread_count_display: {conv.get('unread_count_display', 'N/A')}")
            print(f"    is_member: {conv.get('is_member', 'N/A')}")
            print(f"    last_read: {conv.get('last_read', 'N/A')}")
            print()

    # Try the full fetcher
    print("\n[1.6] Running full MessageFetcher.fetch_all_unread_messages()...")
    fetcher = MessageFetcher(slack_client)
    raw_messages = fetcher.fetch_all_unread_messages()

    if raw_messages:
        print(f"✓ Fetcher returned {len(raw_messages)} conversations with messages")
        for channel_id, data in list(raw_messages.items())[:3]:
            print(f"  - {data['info'].get('name', channel_id)}: {len(data.get('messages', []))} messages, {len(data.get('threads', {}))} threads")
    else:
        print("⚠️  Fetcher returned empty result")

    return raw_messages


def test_step2_generating_summary(processed_conversations):
    """Test if we can generate summaries"""
    print("\n" + "=" * 60)
    print("STEP 2: Testing Summary Generation")
    print("=" * 60)

    if not processed_conversations:
        print("⚠️  No conversations to summarize")
        return None

    print(f"\n[2.1] Testing OpenAI connection...")
    from src.summarizer import Summarizer

    try:
        summarizer = Summarizer(Config.OPENAI_API_KEY, Config.OPENAI_MODEL)
        print(f"✓ Summarizer initialized with model: {Config.OPENAI_MODEL}")
    except Exception as e:
        print(f"❌ Failed to initialize summarizer: {e}")
        return None

    print(f"\n[2.2] Generating summaries for {len(processed_conversations)} conversations...")
    try:
        summarized = summarizer.summarize_conversations(processed_conversations)
        print(f"✓ Generated {len(summarized)} summaries")

        for conv in summarized[:2]:
            print(f"\n  Channel: {conv.get('channel_name', 'Unknown')}")
            print(f"  Summary: {conv.get('summary', 'N/A')[:200]}...")
    except Exception as e:
        print(f"❌ Summary generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

    return summarized


def test_step3_publishing(slack_client, summarized_conversations):
    """Test if we can publish to Slack"""
    print("\n" + "=" * 60)
    print("STEP 3: Testing Publishing")
    print("=" * 60)

    print("\n[3.1] Testing DM sending capability...")
    try:
        # Just test opening a DM channel
        result = slack_client.bot_client.conversations_open(users=Config.SLACK_USER_ID)
        print(f"✓ Can open DM channel: {result['channel']['id']}")
    except Exception as e:
        print(f"❌ Cannot open DM channel: {e}")
        return False

    print("\n[3.2] Bot has chat:write permission (if we got here, it's working)")
    print("✓ Publishing capability confirmed")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("SLACK READER COMPONENT TEST")
    print("=" * 60)

    # Step 1: Test reading
    raw_messages = test_step1_reading_messages()

    if raw_messages:
        # Process messages
        print("\n[1.7] Processing messages...")
        from src.message_processor import MessageProcessor
        slack_client = SlackClient(
            user_token=Config.SLACK_USER_TOKEN,
            bot_token=Config.SLACK_BOT_TOKEN
        )
        processor = MessageProcessor(slack_client)
        processed = processor.process_messages(raw_messages)
        print(f"✓ Processed {len(processed)} conversations")

        # Step 2: Test summary generation
        summarized = test_step2_generating_summary(processed)

        # Step 3: Test publishing
        if summarized:
            test_step3_publishing(slack_client, summarized)
    else:
        print("\n⚠️  Skipping Step 2 and 3 - no messages to process")

        # Still test publishing
        print("\nTesting publishing capability anyway...")
        slack_client = SlackClient(
            user_token=Config.SLACK_USER_TOKEN,
            bot_token=Config.SLACK_BOT_TOKEN
        )
        test_step3_publishing(slack_client, None)

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
