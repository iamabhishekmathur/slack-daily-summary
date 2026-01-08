"""Test fixtures and sample data for testing"""

import pytest


# Sample Slack conversation response
SAMPLE_CONVERSATION = {
    'id': 'C01234ABCDE',
    'name': 'general',
    'is_channel': True,
    'is_private': False,
    'is_im': False,
    'is_mpim': False,
    'unread_count_display': 5,
    'last_read': '1234567890.000000',
    'latest': {
        'ts': '1234567895.000000'
    }
}

# Sample Slack message
SAMPLE_MESSAGE = {
    'type': 'message',
    'user': 'U01234ABCDE',
    'text': 'Hello, this is a test message',
    'ts': '1234567891.000000'
}

# Sample Slack thread
SAMPLE_THREAD = {
    'type': 'message',
    'user': 'U01234ABCDE',
    'text': 'This is a thread parent',
    'ts': '1234567892.000000',
    'reply_count': 2,
    'latest_reply': '1234567894.000000'
}

# Sample Slack user
SAMPLE_USER = {
    'id': 'U01234ABCDE',
    'name': 'testuser',
    'real_name': 'Test User',
    'is_bot': False
}

# Sample OpenAI response
SAMPLE_OPENAI_RESPONSE = {
    'choices': [{
        'message': {
            'content': 'This is a summary of the messages.'
        }
    }]
}


@pytest.fixture
def sample_conversation():
    """Fixture for sample conversation"""
    return SAMPLE_CONVERSATION.copy()


@pytest.fixture
def sample_message():
    """Fixture for sample message"""
    return SAMPLE_MESSAGE.copy()


@pytest.fixture
def sample_thread():
    """Fixture for sample thread"""
    return SAMPLE_THREAD.copy()


@pytest.fixture
def sample_user():
    """Fixture for sample user"""
    return SAMPLE_USER.copy()
