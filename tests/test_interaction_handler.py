import pytest
from src.interaction_handler import InteractionHandler, format_summary_blocks, format_no_unreads_blocks, format_error_blocks

class TestInteractionHandler:
    @pytest.fixture
    def handler(self):
        return InteractionHandler()

    def test_create_view_messages_button(self, handler):
        link = "https://slack.com/archives/C123"
        button = handler.create_view_messages_button(link)
        assert button["type"] == "button"
        assert button["url"] == link
        assert button["action_id"] == "view_messages"

    def test_create_button_actions(self, handler):
        link = "https://slack.com/archives/C123"
        actions = handler.create_button_actions("C123", "general", link)
        assert actions["type"] == "actions"
        assert len(actions["elements"]) == 1
        assert actions["elements"][0]["url"] == link

    def test_create_instructions_text(self, handler):
        text = handler.create_instructions_text()
        assert "marked as read" in text

    def test_format_no_unreads_blocks(self):
        blocks = format_no_unreads_blocks("Monday")
        assert len(blocks) == 2
        assert blocks[0]["type"] == "header"
        assert "no unread messages" in blocks[1]["text"]["text"].lower()

    def test_format_error_blocks(self):
        blocks = format_error_blocks("Some error", "Monday")
        assert len(blocks) == 3
        assert "Some error" in blocks[1]["text"]["text"]

    def test_format_summary_blocks(self, handler):
        conversations = [
            {
                'channel_id': 'C1',
                'channel_name': 'general',
                'total_count': 5,
                'summary': 'A summary',
                'channel_link': 'https://link'
            }
        ]
        blocks = format_summary_blocks(conversations, handler, "Monday")
        assert any(b.get("text", {}).get("text") == "A summary" for b in blocks if "text" in b)
        assert any("general" in b.get("text", {}).get("text", "") for b in blocks if "text" in b)

