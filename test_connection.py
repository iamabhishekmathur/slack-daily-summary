"""Test script to verify Slack and OpenAI connectivity"""

import sys
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from openai import OpenAI
from src.config import Config, logger


def test_slack_user_token():
    """Test Slack user token connectivity and scopes"""
    logger.info("Testing Slack user token...")

    try:
        client = WebClient(token=Config.SLACK_USER_TOKEN)
        response = client.auth_test()

        logger.info(f"✓ User token valid")
        logger.info(f"  User: {response['user']}")
        logger.info(f"  Team: {response['team']}")
        logger.info(f"  User ID: {response['user_id']}")

        # Test conversations.list to verify scopes
        convos = client.conversations_list(types="public_channel,private_channel,mpim,im", limit=5)
        logger.info(f"✓ Can list conversations ({len(convos['channels'])} found)")

        return True

    except SlackApiError as e:
        logger.error(f"✗ User token error: {e.response['error']}")
        if e.response['error'] == 'missing_scope':
            logger.error(f"  Missing scopes. Check Slack app OAuth configuration.")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        return False


def test_slack_bot_token():
    """Test Slack bot token connectivity and scopes"""
    logger.info("\nTesting Slack bot token...")

    try:
        client = WebClient(token=Config.SLACK_BOT_TOKEN)
        response = client.auth_test()

        logger.info(f"✓ Bot token valid")
        logger.info(f"  Bot: {response['user']}")
        logger.info(f"  Team: {response['team']}")
        logger.info(f"  Bot User ID: {response['user_id']}")

        # Test if bot can open a conversation with user
        im = client.conversations_open(users=Config.SLACK_USER_ID)
        logger.info(f"✓ Can open DM with user (channel: {im['channel']['id']})")

        return True

    except SlackApiError as e:
        logger.error(f"✗ Bot token error: {e.response['error']}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        return False


def test_openai_connection():
    """Test OpenAI API connectivity"""
    logger.info("\nTesting OpenAI API...")

    try:
        client = OpenAI(api_key=Config.OPENAI_API_KEY)

        # Test with a simple completion
        response = client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=[{"role": "user", "content": "Say 'test successful' if you can read this."}],
            max_tokens=10
        )

        result = response.choices[0].message.content.strip()
        logger.info(f"✓ OpenAI API connection successful")
        logger.info(f"  Model: {Config.OPENAI_MODEL}")
        logger.info(f"  Response: {result}")

        return True

    except Exception as e:
        logger.error(f"✗ OpenAI API error: {e}")
        return False


def test_unread_detection():
    """Test fetching conversations with unread messages"""
    logger.info("\nTesting unread message detection...")

    try:
        client = WebClient(token=Config.SLACK_USER_TOKEN)

        # Get conversations with types
        response = client.conversations_list(
            types="public_channel,private_channel,mpim,im",
            limit=20
        )

        channels_with_unreads = []
        for channel in response['channels']:
            if channel.get('unread_count_display', 0) > 0:
                channels_with_unreads.append({
                    'name': channel.get('name', 'DM'),
                    'id': channel['id'],
                    'unread_count': channel['unread_count_display'],
                    'is_channel': channel.get('is_channel', False),
                    'is_im': channel.get('is_im', False)
                })

        if channels_with_unreads:
            logger.info(f"✓ Found {len(channels_with_unreads)} conversation(s) with unread messages:")
            for ch in channels_with_unreads[:5]:  # Show first 5
                ch_type = "Channel" if ch['is_channel'] else ("DM" if ch['is_im'] else "Group")
                logger.info(f"  - {ch_type}: {ch['name']} ({ch['unread_count']} unread)")
        else:
            logger.info("  No unread messages found (this is normal if you've read everything)")

        return True

    except SlackApiError as e:
        logger.error(f"✗ Error fetching conversations: {e.response['error']}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        return False


def main():
    """Run all connection tests"""
    logger.info("=" * 60)
    logger.info("Slack Summarizer Connection Test")
    logger.info("=" * 60)

    # Validate configuration
    if not Config.validate():
        logger.error("\n✗ Configuration validation failed")
        logger.error("Please check your .env file or environment variables")
        sys.exit(1)

    # Run tests
    results = {
        "Slack User Token": test_slack_user_token(),
        "Slack Bot Token": test_slack_bot_token(),
        "OpenAI API": test_openai_connection(),
        "Unread Detection": test_unread_detection()
    }

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{test_name}: {status}")

    all_passed = all(results.values())
    if all_passed:
        logger.info("\n✓ All tests passed! You're ready to run the summarizer.")
        sys.exit(0)
    else:
        logger.error("\n✗ Some tests failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
