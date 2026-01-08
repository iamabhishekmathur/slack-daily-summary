import pytest
from unittest.mock import MagicMock, patch
from slack_sdk.errors import SlackApiError
from src.slack_client import SlackClient

class TestSlackClient:
    def test_initialization(self):
        client = SlackClient("user-token", "bot-token")
        assert client.user_client.token == "user-token"
        assert client.bot_client.token == "bot-token"

    @patch('src.slack_client.WebClient')
    def test_get_conversations_list(self, mock_web_client):
        user_mock = MagicMock()
        user_mock.conversations_list.return_value = {
            'channels': [{'id': 'C1', 'name': 'general'}],
            'response_metadata': {'next_cursor': ''}
        }
        
        with patch('src.slack_client.WebClient', side_effect=[user_mock, MagicMock()]):
            client = SlackClient("u", "b")
            convs = client.get_conversations_list(types=['public_channel'])
            assert len(convs) == 1
            assert convs[0]['name'] == 'general'

    @patch('src.slack_client.WebClient')
    def test_get_user_info_success(self, mock_web_client):
        user_mock = MagicMock()
        user_mock.users_info.return_value = {'user': {'id': 'U1', 'real_name': 'Alice'}}
        
        with patch('src.slack_client.WebClient', side_effect=[user_mock, MagicMock()]):
            client = SlackClient("u", "b")
            info = client.get_user_info("U1")
            assert info['real_name'] == 'Alice'

    @patch('src.slack_client.WebClient')
    def test_get_user_info_error(self, mock_web_client):
        user_mock = MagicMock()
        # Create a proper SlackApiError
        response = MagicMock()
        response.data = {'error': 'user_not_found'}
        user_mock.users_info.side_effect = SlackApiError("Error", response)
        
        with patch('src.slack_client.WebClient', side_effect=[user_mock, MagicMock()]):
            client = SlackClient("u", "b")
            info = client.get_user_info("U1")
            assert info['name'] == 'Unknown User'

    @patch('src.slack_client.WebClient')
    def test_send_dm(self, mock_web_client):
        bot_mock = MagicMock()
        bot_mock.conversations_open.return_value = {'channel': {'id': 'D1'}}
        bot_mock.chat_postMessage.return_value = {'ts': '123'}
        
        with patch('src.slack_client.WebClient', side_effect=[MagicMock(), bot_mock]):
            client = SlackClient("u", "b")
            response = client.send_dm("U1", [{"type": "section"}], "text")
            assert response['ts'] == '123'
            bot_mock.conversations_open.assert_called_with(users="U1")

