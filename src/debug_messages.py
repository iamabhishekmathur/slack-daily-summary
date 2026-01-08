"""Debug script to diagnose why messages aren't being read"""

import sys
import json
import logging
from src.config import Config, logger
from src.slack_client import SlackClient

# Enable verbose logging
logging.getLogger().setLevel(logging.DEBUG)


def debug_message_reading():
    """Debug why messages might not be showing up"""
    print("\n" + "=" * 70)
    print("SLACK MESSAGE READING DEBUG")
    print("=" * 70)

    # Step 1: Validate config
    print("\n[1] Configuration")
    print("-" * 40)
    if not Config.validate():
        print("ERROR: Configuration validation failed")
        return 1
    print(f"User ID: {Config.SLACK_USER_ID}")
    print(f"Conversation types: {Config.CONVERSATION_TYPES}")
    print(f"User token starts with: {Config.SLACK_USER_TOKEN[:10]}...")

    # Step 2: Initialize client
    print("\n[2] Initializing Slack Client")
    print("-" * 40)
    slack_client = SlackClient(
        user_token=Config.SLACK_USER_TOKEN,
        bot_token=Config.SLACK_BOT_TOKEN
    )

    # Test auth
    try:
        user_auth = slack_client.user_client.auth_test()
        print(f"User token: OK (user: {user_auth['user']}, team: {user_auth['team']})")
    except Exception as e:
        print(f"User token: FAILED - {e}")
        return 1

    try:
        bot_auth = slack_client.bot_client.auth_test()
        print(f"Bot token: OK (bot: {bot_auth['user']})")
    except Exception as e:
        print(f"Bot token: FAILED - {e}")
        return 1

    # Step 3: Get conversations
    print("\n[3] Fetching Conversations")
    print("-" * 40)
    conversations = slack_client.get_conversations_list()
    print(f"Total conversations fetched: {len(conversations)}")

    # Categorize
    conv_by_type = {'im': [], 'mpim': [], 'public': [], 'private': []}
    for c in conversations:
        if c.get('is_im'):
            conv_by_type['im'].append(c)
        elif c.get('is_mpim'):
            conv_by_type['mpim'].append(c)
        elif c.get('is_private'):
            conv_by_type['private'].append(c)
        else:
            conv_by_type['public'].append(c)

    print(f"  - DMs (im): {len(conv_by_type['im'])}")
    print(f"  - Group DMs (mpim): {len(conv_by_type['mpim'])}")
    print(f"  - Public channels: {len(conv_by_type['public'])}")
    print(f"  - Private channels: {len(conv_by_type['private'])}")

    # Step 4: Check unread counts
    print("\n[4] Checking Unread Counts")
    print("-" * 40)

    # Check conversations with unread_count_display > 0
    unread_display = [c for c in conversations if c.get('unread_count_display', 0) > 0]
    print(f"Conversations with unread_count_display > 0: {len(unread_display)}")

    if unread_display:
        print("\nConversations with unreads:")
        for c in unread_display[:10]:
            name = c.get('name') or f"DM:{c.get('user', c['id'])}"
            print(f"  - {name}: {c.get('unread_count_display')} unread")
    else:
        print("\n*** NO CONVERSATIONS HAVE unread_count_display > 0 ***")

    # Step 5: Check last_read timestamps
    print("\n[5] Checking Last Read vs Latest Message")
    print("-" * 40)

    potentially_unread = []
    for c in conversations:
        last_read = c.get('last_read')
        latest = c.get('latest', {})
        latest_ts = latest.get('ts') if isinstance(latest, dict) else None

        if last_read and latest_ts and last_read < latest_ts:
            potentially_unread.append({
                'name': c.get('name') or f"DM:{c.get('user', c['id'])}",
                'id': c['id'],
                'last_read': last_read,
                'latest_ts': latest_ts,
                'unread_count_display': c.get('unread_count_display', 0)
            })

    print(f"Conversations where last_read < latest.ts: {len(potentially_unread)}")

    if potentially_unread:
        print("\nPotentially unread (first 10):")
        for p in potentially_unread[:10]:
            print(f"  - {p['name']}")
            print(f"      last_read: {p['last_read']}")
            print(f"      latest_ts: {p['latest_ts']}")
            print(f"      unread_count_display: {p['unread_count_display']}")

    # Step 6: Sample DM conversation details (DMs should have unread_count_display)
    print("\n[6] DM Conversation Details (where unread_count_display SHOULD work)")
    print("-" * 40)

    dms = [c for c in conversations if c.get('is_im')]
    print(f"Total DMs found: {len(dms)}")

    for c in dms[:10]:
        print(f"\nDM ID: {c['id']}")
        print(f"  user: {c.get('user', 'N/A')}")
        print(f"  is_im: {c.get('is_im', False)}")
        print(f"  is_open: {c.get('is_open', 'N/A')}")
        print(f"  unread_count: {c.get('unread_count', 'NOT IN RESPONSE')}")
        print(f"  unread_count_display: {c.get('unread_count_display', 'NOT IN RESPONSE')}")
        print(f"  last_read: {c.get('last_read', 'NOT IN RESPONSE')}")
        latest = c.get('latest', {})
        if latest:
            if isinstance(latest, dict):
                print(f"  latest.ts: {latest.get('ts', 'N/A')}")
                print(f"  latest.text: {(latest.get('text', '')[:40] + '...') if latest.get('text') else 'N/A'}")
            else:
                print(f"  latest: {latest}")
        else:
            print(f"  latest: NOT IN RESPONSE")

    # Step 6.5: Show RAW API response for one DM
    print("\n[6.5] RAW API Response (first DM)")
    print("-" * 40)
    if dms:
        # Get raw response to see all fields
        try:
            raw_response = slack_client.user_client.conversations_list(
                types="im",
                limit=1
            )
            if raw_response['channels']:
                print("Raw DM data from API:")
                print(json.dumps(raw_response['channels'][0], indent=2, default=str))
        except Exception as e:
            print(f"Error getting raw response: {e}")

    # Step 7: Try fetching messages from a conversation
    print("\n[7] Testing Message Fetch")
    print("-" * 40)

    # Pick a conversation that might have messages
    test_convs = potentially_unread[:2] if potentially_unread else conversations[:2]

    for tc in test_convs:
        conv_id = tc['id'] if isinstance(tc, dict) and 'id' in tc else tc.get('id', tc)
        conv_name = tc.get('name', conv_id) if isinstance(tc, dict) else conv_id

        print(f"\nTesting: {conv_name} ({conv_id})")

        try:
            # Get history without oldest filter first
            messages = slack_client.user_client.conversations_history(
                channel=conv_id,
                limit=5
            )
            msg_list = messages.get('messages', [])
            print(f"  Total recent messages: {len(msg_list)}")

            for msg in msg_list[:3]:
                subtype = msg.get('subtype', 'regular')
                user = msg.get('user', 'N/A')
                text = (msg.get('text', '')[:50] + '...') if msg.get('text') else '[no text]'
                print(f"    - [{subtype}] user:{user} - {text}")

        except Exception as e:
            print(f"  ERROR: {e}")

    # Step 8: Try users.conversations API (different from conversations.list)
    print("\n[8] Testing users.conversations API")
    print("-" * 40)

    try:
        response = slack_client.user_client.users_conversations(
            user=Config.SLACK_USER_ID,
            types="im,mpim,public_channel,private_channel",
            exclude_archived=True,
            limit=10
        )
        print(f"users.conversations returned {len(response.get('channels', []))} conversations")
        for c in response.get('channels', [])[:5]:
            print(f"  - {c.get('name', c.get('id'))}: unread_count_display={c.get('unread_count_display', 'N/A')}")
    except Exception as e:
        print(f"users.conversations failed: {e}")

    # Step 9: Check if exclude_archived makes a difference
    print("\n[9] Testing with exclude_archived=True")
    print("-" * 40)

    try:
        response = slack_client.user_client.conversations_list(
            types="im",
            exclude_archived=True,
            limit=5
        )
        print(f"conversations_list (exclude_archived=True) returned:")
        for c in response.get('channels', []):
            print(f"  - {c.get('id')}: unread={c.get('unread_count_display', 'N/A')}, is_open={c.get('is_open', 'N/A')}")
    except Exception as e:
        print(f"Error: {e}")

    # Step 10: Check auth.test for scopes
    print("\n[10] Token Scopes from auth.test")
    print("-" * 40)

    try:
        # Use the client directly to get full response
        response = slack_client.user_client.auth_test()
        print(f"User: {response.get('user')}")
        print(f"Team: {response.get('team')}")
        print(f"User ID: {response.get('user_id')}")

        # Note: auth.test doesn't return scopes, but we can try api.test
        print("\nNote: Verify scopes at https://api.slack.com/apps -> OAuth & Permissions")
    except Exception as e:
        print(f"Could not check auth: {e}")

    print("\n" + "=" * 70)
    print("DEBUG COMPLETE")
    print("=" * 70)
    print("\nSUMMARY:")
    print(f"- Total conversations: {len(conversations)}")
    print(f"- DMs: {len(dms)}")
    print(f"- With unread_count_display > 0: {len(unread_display)}")
    print(f"- With last_read < latest.ts: {len(potentially_unread)}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(debug_message_reading())
