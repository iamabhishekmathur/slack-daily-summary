import pytest
from unittest.mock import MagicMock
from src.mark_as_read import MarkAsReadHandler

class TestMarkAsReadHandler:
    @pytest.fixture
    def mock_slack_client(self):
        client = MagicMock()
        client.user_client = MagicMock()
        return client

    def test_get_latest_timestamp(self, mock_slack_client):
        handler = MarkAsReadHandler(mock_slack_client)
        conv = {
            'messages': [{'timestamp': '100'}, {'timestamp': '300'}],
            'threads': [
                {
                    'parent': {'timestamp': '200'},
                    'replies': [{'timestamp': '400'}]
                }
            ]
        }
        assert handler._get_latest_timestamp(conv) == '400'

    def test_get_latest_timestamp_empty(self, mock_slack_client):
        handler = MarkAsReadHandler(mock_slack_client)
        assert handler._get_latest_timestamp({}) == ''

    def test_mark_conversation_read_success(self, mock_slack_client):
        mock_slack_client.user_client.conversations_mark.return_value = {'ok': True}
        handler = MarkAsReadHandler(mock_slack_client)
        assert handler._mark_conversation_read("C1", "100") is True
        mock_slack_client.user_client.conversations_mark.assert_called_with(channel="C1", ts="100")

    def test_mark_conversations_read_empty(self, mock_slack_client):
        handler = MarkAsReadHandler(mock_slack_client)
        result = handler.mark_conversations_read([])
        assert result == {'success': [], 'failed': []}

    def test_mark_conversations_read_mixed(self, mock_slack_client):
        mock_slack_client.user_client.conversations_mark.side_effect = [
            {'ok': True},
            Exception("API Error")
        ]
        handler = MarkAsReadHandler(mock_slack_client)
        conversations = [
            {'channel_id': 'C1', 'channel_name': 'general', 'messages': [{'timestamp': '100'}]},
            {'channel_id': 'C2', 'channel_name': 'random', 'messages': [{'timestamp': '200'}]}
        ]
        
        result = handler.mark_conversations_read(conversations)
        assert len(result['success']) == 1
        assert len(result['failed']) == 1
        assert result['success'][0]['channel_id'] == 'C1'
        assert result['failed'][0]['channel_id'] == 'C2'

