import pytest
from unittest.mock import MagicMock, patch
from src.main import get_current_date_string, send_error_notification

class TestMain:
    def test_get_current_date_string(self):
        with patch('src.main.datetime') as mock_date:
            mock_date.now.return_value.strftime.return_value = "Monday, January 01, 2024"
            assert get_current_date_string() == "Monday, January 01, 2024"

    def test_send_error_notification(self):
        mock_client = MagicMock()
        with patch('src.main.format_error_blocks', return_value=[]):
            send_error_notification(mock_client, "Test Error")
            mock_client.send_dm.assert_called_once()

