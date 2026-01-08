import pytest
from unittest.mock import MagicMock, patch
from src.summarizer import Summarizer
from tests.fixtures import SAMPLE_OPENAI_RESPONSE

class TestSummarizer:
    @pytest.fixture
    def mock_openai(self):
        with patch('src.summarizer.OpenAI') as mock:
            client_instance = mock.return_value
            client_instance.chat.completions.create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content="This is a summary."))]
            )
            yield client_instance

    def test_summarizer_initialization(self, mock_openai):
        summarizer = Summarizer(api_key="test-key", model="gpt-4")
        assert summarizer.model == "gpt-4"
        assert summarizer.client is not None

    def test_summarize_conversations_empty(self, mock_openai):
        summarizer = Summarizer(api_key="test-key")
        result = summarizer.summarize_conversations([])
        assert result == []

    def test_summarize_conversations_success(self, mock_openai):
        summarizer = Summarizer(api_key="test-key")
        conversations = [
            {
                'channel_name': 'general',
                'messages': [{'timestamp': '12:00', 'user_name': 'alice', 'text': 'hello'}],
                'threads': [],
                'total_count': 1
            }
        ]
        
        result = summarizer.summarize_conversations(conversations)
        
        assert len(result) == 1
        assert result[0]['summary'] == "This is a summary."
        mock_openai.chat.completions.create.assert_called_once()

    def test_summarize_conversations_with_threads(self, mock_openai):
        summarizer = Summarizer(api_key="test-key")
        conversations = [
            {
                'channel_name': 'project-x',
                'messages': [],
                'threads': [
                    {
                        'parent': {'user_name': 'bob', 'text': 'any updates?', 'ts': '123'},
                        'replies': [{'user_name': 'charlie', 'text': 'not yet'}],
                        'reply_count': 1,
                        'showing_count': 1
                    }
                ],
                'total_count': 2
            }
        ]
        
        result = summarizer.summarize_conversations(conversations)
        assert len(result) == 1
        assert result[0]['summary'] == "This is a summary."

    def test_create_fallback_summary(self, mock_openai):
        summarizer = Summarizer(api_key="test-key")
        conversation = {
            'channel_name': 'general',
            'total_count': 5,
            'messages': [
                {'user_name': 'alice', 'text': 'message 1'},
                {'user_name': 'bob', 'text': 'message 2'},
                {'user_name': 'charlie', 'text': 'message 3'}
            ],
            'threads': [
                {
                    'parent': {'user_name': 'dan', 'text': 'thread parent'},
                    'reply_count': 2
                }
            ]
        }
        
        fallback = summarizer._create_fallback_summary(conversation)
        assert "**5 unread messages in general**" in fallback
        assert "alice: message 1" in fallback
        assert "[Thread] dan: thread parent" in fallback
        assert "(AI summary unavailable" in fallback

    def test_summarize_conversation_error_fallback(self, mock_openai):
        mock_openai.chat.completions.create.side_effect = Exception("API Error")
        summarizer = Summarizer(api_key="test-key")
        
        conversations = [
            {
                'channel_name': 'general',
                'messages': [{'timestamp': '12:00', 'user_name': 'alice', 'text': 'hello'}],
                'threads': [],
                'total_count': 1
            }
        ]
        
        result = summarizer.summarize_conversations(conversations)
        assert len(result) == 1
        assert "(AI summary unavailable" in result[0]['summary']

