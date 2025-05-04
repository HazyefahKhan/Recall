import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add parent directory to path so we can import the plugin
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.mark.usefixtures("mock_anki")
class TestDialogUI:
    
    @pytest.fixture
    def dialog(self):
        """Create a RecallInputDialog instance"""
        from __init__ import RecallInputDialog
        dialog = RecallInputDialog()
        return dialog
    
    def test_setup_ui(self, dialog):
        """Test that the UI is set up correctly"""
        # Check that UI components are created
        assert hasattr(dialog, 'deck_combo')
        assert hasattr(dialog, 'input_text')
        assert hasattr(dialog, 'create_button')
        assert hasattr(dialog, 'cancel_button')
    
    def test_populate_deck_list(self, dialog):
        """Test that the deck list is populated correctly"""
        # Mock the deck list
        from aqt import mw
        mw.col.decks.all_names_and_ids.return_value = [
            MagicMock(name="Default", id=1),
            MagicMock(name="Test::Subdeck", id=2)
        ]
        
        # Create a mock combo box
        dialog.deck_combo = MagicMock()
        
        # Call the method
        dialog.populate_deck_list()
        
        # Verify that addItem was called twice (once for each deck)
        assert dialog.deck_combo.addItem.call_count == 2
    
    def test_load_last_deck(self, dialog):
        """Test loading the last selected deck"""
        # Set up mock profile data
        from aqt import mw
        mw.pm.profile = {'recall_last_deck': 2}  # Deck ID 2
        
        # Mock the deck combo box
        dialog.deck_combo = MagicMock()
        dialog.deck_combo.findData.return_value = 1  # Index 1
        
        # Call the method
        dialog.load_last_deck()
        
        # Verify that setCurrentIndex was called with the correct index
        dialog.deck_combo.setCurrentIndex.assert_called_with(1)
    
    def test_save_last_deck(self, dialog):
        """Test saving the last selected deck"""
        # Mock the deck combo box
        dialog.deck_combo = MagicMock()
        dialog.deck_combo.currentData.return_value = 2  # Deck ID 2
        
        # Mock the profile
        from aqt import mw
        mw.pm.profile = {}
        
        # Call the method
        dialog.save_last_deck()
        
        # Verify that the deck ID was saved to the profile
        assert mw.pm.profile['recall_last_deck'] == 2
    
    def test_create_preview_html(self, dialog):
        """Test creating preview HTML"""
        # Call the method
        preview_html = dialog.create_preview_html("console.log('hello')", "<p>Hello</p>")
        
        # Verify that the preview HTML contains the necessary elements
        assert "preview-container" in preview_html
        assert "code-display" in preview_html
        assert "preview-display" in preview_html
        assert "iframe" in preview_html
        assert "Hello" in preview_html
    
    @patch('__init__.QMessageBox')
    def test_show_error_message(self, mock_message_box, dialog):
        """Test showing an error message"""
        # Mock the parse_input method to raise an exception
        dialog.parse_input = MagicMock(side_effect=Exception("Test error"))
        
        # Mock the deck selection
        dialog.deck_combo = MagicMock()
        dialog.deck_combo.currentData = MagicMock(return_value=1)  # Deck ID 1
        
        # Mock the input text
        dialog.input_text = MagicMock()
        
        # Call the create_card method, which should show an error
        dialog.create_card()
        
        # Verify that QMessageBox.critical was called
        mock_message_box.critical.assert_called_once()
    
    @patch('__init__.QMessageBox')
    def test_show_success_message(self, mock_message_box, dialog):
        """Test showing a success message"""
        # Mock the methods to avoid errors
        dialog.parse_input = MagicMock(return_value={
            "question": "Test question",
            "correct_options": [{"option": "Correct", "explanation": "Explanation", "preview_html": None, "preview_code": None}],
            "incorrect_options": [{"option": "Incorrect", "explanation": "Explanation", "preview_html": None, "preview_code": None}]
        })
        
        # Mock the deck selection
        dialog.deck_combo = MagicMock()
        dialog.deck_combo.currentData = MagicMock(return_value=1)  # Deck ID 1
        
        # Mock the input text
        dialog.input_text = MagicMock()
        
        # Call the create_card method
        dialog.create_card()
        
        # Verify that QMessageBox.information was called
        mock_message_box.information.assert_called_once() 