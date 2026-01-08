import pytest
from unittest.mock import MagicMock, patch
from src.message_fetcher import MessageFetcher

class TestMessageFetcher:
    @pytest.fixture
    def mock_slack_client(self):
        return MagicMock()

    def test_fetch_all_unread_messages_none(self, mock_slack_client):
        mock_slack_client.get_conversations_list.return_value = []
        fetcher = MessageFetcher(mock_slack_client)
        result = fetcher.fetch_all_unread_messages()
        assert result == {}

    def test_get_unread_conversations(self, mock_slack_client):
        fetcher = MessageFetcher(mock_slack_client)
        # Use realistic Slack timestamps (Unix epoch with microseconds)
        # String comparison works correctly for these format timestamps
        conversations = [
            {'id': 'C1', 'unread_count_display': 0, 'last_read': '1704067200.000000', 'latest': {'ts': '1704060000.000000'}}, # No unread (last_read > latest)
            {'id': 'C2', 'unread_count_display': 5}, # Has unread via count
            {'id': 'C3', 'unread_count_display': 0, 'last_read': '1704067200.000000', 'latest': {'ts': '1704070800.000000'}}, # Has unread via timestamp (latest > last_read)
        ]

        unread = fetcher._get_unread_conversations(conversations)
        assert len(unread) == 2
        assert unread[0]['id'] == 'C2'
        assert unread[1]['id'] == 'C3'

    def test_get_conversation_name_channel(self, mock_slack_client):
        fetcher = MessageFetcher(mock_slack_client)
        assert fetcher._get_conversation_name({'is_im': False, 'is_private': False, 'name': 'general'}) == "#general"
        assert fetcher._get_conversation_name({'is_im': False, 'is_private': True, 'name': 'secret'}) == "🔒secret"

    def test_get_conversation_name_im(self, mock_slack_client):
        mock_slack_client.get_user_info.return_value = {'real_name': 'Alice'}
        fetcher = MessageFetcher(mock_slack_client)
        
        # IM with user info success
        assert fetcher._get_conversation_name({'is_im': True, 'user': 'U1'}) == "DM with Alice"
        
        # IM with user info failure
        mock_slack_client.get_user_info.side_effect = Exception("Not found")
        assert fetcher._get_conversation_name({'is_im': True, 'user': 'U1', 'id': 'D1'}) == "DM (ID: D1)"

    def test_fetch_conversation_unreads(self, mock_slack_client):
        fetcher = MessageFetcher(mock_slack_client)
        
        convo = {'id': 'C1', 'last_read': '100'}
        mock_slack_client.get_conversation_history.return_value = [
            {'ts': '110', 'text': 'msg 1'},
            {'ts': '120', 'text': 'msg 2', 'reply_count': 1},
            {'ts': '115', 'text': 'reply 1', 'thread_ts': '120'}
        ]
        
        mock_slack_client.get_thread_replies.return_value = [
            {'ts': '120', 'text': 'msg 2'},
            {'ts': '125', 'text': 'reply 2'}
        ]
        
        result = fetcher._fetch_conversation_unreads(convo)
        
        assert len(result['messages']) == 1
        assert result['messages'][0]['ts'] == '110'
        assert len(result['threads']) == 1
        assert '120' in result['threads']
        assert len(result['threads']['120']['replies']) == 2

    def test_fetch_all_unread_messages_success(self, mock_slack_client):
        fetcher = MessageFetcher(mock_slack_client)
        
        mock_slack_client.get_conversations_list.return_value = [
            {'id': 'C1', 'name': 'general', 'unread_count_display': 1, 'last_read': '100', 'latest': {'ts': '110'}}
        ]
        
        mock_slack_client.get_conversation_history.return_value = [
            {'ts': '110', 'text': 'hello'}
        ]
        
        result = fetcher.fetch_all_unread_messages()
        
        assert 'C1' in result
        assert result['C1']['info']['name'] == 'general'
        assert len(result['C1']['messages']) == 1

