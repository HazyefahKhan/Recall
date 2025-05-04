import pytest
import sys
import os
import hashlib
import urllib.parse
from unittest.mock import MagicMock, patch

# Add parent directory to path so we can import the plugin
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.mark.usefixtures("mock_anki", "fs_setup")
class TestImageHandling:
    
    @patch('urllib.request.urlopen')
    def test_retrieve_external_image(self, mock_urlopen):
        """Test the functionality to download and save external images"""
        from __init__ import convert_markdown_to_html
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.read.return_value = b'fake image data'
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Test markdown with external image
        markdown = "![Test Image](https://example.com/image.jpg)"
        
        # Patch open to avoid actual file writes
        with patch('builtins.open', new_callable=MagicMock()) as mock_open:
            html = convert_markdown_to_html(markdown)
            
            # Verify urllib.request.urlopen was called with the correct URL
            url_arg = mock_urlopen.call_args[0][0].get_full_url()
            assert url_arg == "https://example.com/image.jpg"
            
            # Verify file was opened for writing
            assert mock_open.call_args[0][1] == 'wb'
    
    @patch('urllib.request.urlopen')
    def test_image_name_from_url(self, mock_urlopen, fs_setup):
        """Test that image filenames are correctly generated from URLs"""
        from __init__ import convert_markdown_to_html
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.read.return_value = b'fake image data'
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Test with a URL that has a valid filename
        markdown = "![Test Image](https://example.com/path/to/image.jpg)"
        
        # Patch os.path.exists to return False so file is saved
        with patch('os.path.exists', return_value=False):
            with patch('builtins.open', new_callable=MagicMock()) as mock_open:
                html = convert_markdown_to_html(markdown)
                
                # Verify filename is extracted correctly
                expected_filename = 'image.jpg'
                expected_path = os.path.join('/mock/media/dir', expected_filename)
                
                # Check for filename in the HTML
                assert expected_filename in html
                
                # Verify correct file path was used
                assert mock_open.call_args[0][0] == expected_path
    
    @patch('urllib.request.urlopen')
    def test_image_name_hash_for_invalid_filename(self, mock_urlopen, fs_setup):
        """Test that a hash is used when URL doesn't contain a valid filename"""
        from __init__ import convert_markdown_to_html
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.read.return_value = b'fake image data'
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Test with a URL that has no filename
        url = "https://example.com/"
        markdown = f"![Test Image]({url})"
        
        # Calculate expected hash filename
        expected_hash = hashlib.md5(url.encode('utf-8')).hexdigest() + '.jpg'
        expected_path = os.path.join('/mock/media/dir', expected_hash)
        
        # Patch os.path.exists to return False so file is saved
        with patch('os.path.exists', return_value=False):
            with patch('builtins.open', new_callable=MagicMock()) as mock_open:
                html = convert_markdown_to_html(markdown)
                
                # Verify correct hash filename is used
                assert expected_hash in html
                assert mock_open.call_args[0][0] == expected_path
    
    @patch('urllib.request.urlopen')
    def test_skip_download_if_file_exists(self, mock_urlopen, fs_setup):
        """Test that download is skipped if the file already exists"""
        from __init__ import convert_markdown_to_html
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.read.return_value = b'fake image data'
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Test markdown with external image
        markdown = "![Test Image](https://example.com/image.jpg)"
        
        # Patch os.path.exists to return True, indicating file exists
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', new_callable=MagicMock()) as mock_open:
                html = convert_markdown_to_html(markdown)
                
                # Verify file was not opened for writing
                mock_open.assert_not_called()
                
                # Verify the image tag still contains the local filename
                assert "image.jpg" in html
    
    @patch('urllib.request.urlopen')
    def test_handle_download_error(self, mock_urlopen):
        """Test handling of image download errors"""
        from __init__ import convert_markdown_to_html
        
        # Setup mock to raise an exception
        mock_urlopen.side_effect = Exception("Download error")
        
        # Test markdown with external image
        markdown = "![Test Image](https://example.com/image.jpg)"
        
        # The function should handle the error gracefully and return the original URL
        html = convert_markdown_to_html(markdown)
        
        # Verify the image tag contains the original URL
        assert "https://example.com/image.jpg" in html 