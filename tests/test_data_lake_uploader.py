import unittest
from unittest.mock import patch, MagicMock
import src.data_lake_uploader as uploader

class TestDataLakeUploader(unittest.TestCase):
    @patch('src.data_lake_uploader.requests.get')
    @patch('src.data_lake_uploader.requests.post')
    @patch('src.data_lake_uploader.os.remove')
    @patch('src.data_lake_uploader.open', create=True)
    def test_main_success(self, mock_open, mock_remove, mock_post, mock_get):
        # Mock directory listing
        html = '<a href="file1.log">file1.log</a>'
        mock_get.side_effect = [
            MagicMock(status_code=200, text=html),  # directory listing
            MagicMock(status_code=200, content=b'logdata')  # file download
        ]
        # Mock file open
        mock_open.return_value.__enter__.return_value.read.return_value = b'logdata'
        # Mock upload
        mock_post.return_value.status_code = 201
        mock_post.return_value.text = 'OK'
        # Patch sys.exit to prevent exit
        with patch('sys.exit') as mock_exit:
            uploader.main()
            mock_exit.assert_not_called()
        # Check calls
        self.assertTrue(mock_post.called)
        self.assertTrue(mock_remove.called)

if __name__ == "__main__":
    unittest.main()
