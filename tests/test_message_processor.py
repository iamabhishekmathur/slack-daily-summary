"""Tests for message processor module"""

import pytest
from unittest.mock import Mock, MagicMock
from src.message_processor import MessageProcessor
from tests.fixtures import SAMPLE_MESSAGE, SAMPLE_CONVERSATION, SAMPLE_USER


class TestMessageProcessor:
    """Test message processing functionality"""

    @pytest.fixture
    def mock_slack_client(self):
        """Create a mock Slack client"""
        client = Mock()
        client.get_user_info = Mock(return_value=SAMPLE_USER.copy())
        client.get_team_info = Mock(return_value={
            'id': 'T01234',
            'domain': 'testworkspace'
        })
        return client

    @pytest.fixture
    def processor(self, mock_slack_client):
        """Create MessageProcessor instance with mocked client"""
        return MessageProcessor(mock_slack_client)

    def test_process_empty_messages(self, processor):
        """Test processing empty messages dict"""
        result = processor.process_messages({})
        assert result == []

    def test_enrich_message_with_metadata(self, processor):
        """Test message enrichment adds user info and permalink"""
        message = SAMPLE_MESSAGE.copy()
        channel_id = 'C123'

        enriched = processor._enrich_message(channel_id, message)

        assert enriched is not None
        assert enriched['text'] == message['text']
        assert enriched['user_name'] == SAMPLE_USER['real_name']
        assert 'permalink' in enriched
        assert 'testworkspace.slack.com' in enriched['permalink']

    def test_enrich_message_skips_empty_text(self, processor):
        """Test that messages without text are skipped"""
        message = SAMPLE_MESSAGE.copy()
        message['text'] = ''

        enriched = processor._enrich_message('C123', message)
        assert enriched is None

    def test_get_conversation_display_name_channel(self, processor):
        """Test display name for public channel"""
        conv = SAMPLE_CONVERSATION.copy()

        name = processor._get_conversation_display_name(conv)
        assert '#general' in name

    def test_get_conversation_display_name_private(self, processor):
        """Test display name for private channel"""
        conv = SAMPLE_CONVERSATION.copy()
        conv['is_private'] = True

        name = processor._get_conversation_display_name(conv)
        assert '🔒' in name

    def test_get_conversation_display_name_dm(self, processor):
        """Test display name for DM"""
        conv = {
            'id': 'D123',
            'is_im': True,
            'user': 'U01234ABCDE'
        }

        name = processor._get_conversation_display_name(conv)
        assert 'DM with' in name
        assert 'Test User' in name

    def test_get_conversation_type(self, processor):
        """Test conversation type detection"""
        # Public channel
        conv = SAMPLE_CONVERSATION.copy()
        assert processor._get_conversation_type(conv) == 'public_channel'

        # Private channel
        conv['is_private'] = True
        assert processor._get_conversation_type(conv) == 'private_channel'

        # DM
        conv = {'is_im': True}
        assert processor._get_conversation_type(conv) == 'dm'

        # Group DM
        conv = {'is_mpim': True}
        assert processor._get_conversation_type(conv) == 'group_dm'

    def test_prioritize_conversations(self, processor):
        """Test conversation prioritization"""
        conversations = [
            {'channel_type': 'public_channel', 'total_count': 10},
            {'channel_type': 'dm', 'total_count': 5},
            {'channel_type': 'private_channel', 'total_count': 15},
        ]

        prioritized = processor._prioritize_conversations(conversations)

        # DMs should be first
        assert prioritized[0]['channel_type'] == 'dm'
        # Private channels second
        assert prioritized[1]['channel_type'] == 'private_channel'
        # Public channels last
        assert prioritized[2]['channel_type'] == 'public_channel'

    def test_generate_permalink_format(self, processor):
        """Test permalink generation format"""
        channel_id = 'C01234ABCDE'
        message_ts = '1234567890.123456'

        permalink = processor._generate_permalink(channel_id, message_ts)

        assert 'testworkspace.slack.com' in permalink
        assert channel_id in permalink
        assert 'p1234567890123456' in permalink

    def test_user_info_caching(self, processor, mock_slack_client):
        """Test that user info is cached to reduce API calls"""
        user_id = 'U01234ABCDE'

        # First call
        user1 = processor._get_user_info_cached(user_id)
        # Second call
        user2 = processor._get_user_info_cached(user_id)

        # Should only call API once
        assert mock_slack_client.get_user_info.call_count == 1
        assert user1 == user2
