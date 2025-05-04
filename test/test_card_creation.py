import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add parent directory to path so we can import the plugin
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.mark.usefixtures("mock_anki")
class TestCardCreation:
    
    @pytest.fixture
    def dialog(self):
        """Create a RecallInputDialog instance"""
        from __init__ import RecallInputDialog
        dialog = RecallInputDialog()
        return dialog
    
    def test_create_simple_card(self, dialog):
        """Test creating a simple card with one correct and one incorrect option"""
        # Mock the input parsing
        dialog.parse_input = MagicMock(return_value={
            "question": "What is the capital of France?",
            "correct_options": [{
                "option": "Paris",
                "explanation": "Paris is the capital of France.",
                "preview_html": None,
                "preview_code": None
            }],
            "incorrect_options": [{
                "option": "London",
                "explanation": "London is the capital of the United Kingdom, not France.",
                "preview_html": None,
                "preview_code": None
            }]
        })
        
        # Mock the deck selection
        dialog.deck_combo = MagicMock()
        dialog.deck_combo.currentData = MagicMock(return_value=1)  # Deck ID 1
        
        # Mock the input text
        dialog.input_text = MagicMock()
        
        # Test that the card creation function runs without errors
        dialog.create_card()
        
        # Verify that add_note was called
        from aqt import mw
        mw.col.add_note.assert_called_once()
    
    def test_create_card_with_multiple_options(self, dialog):
        """Test creating a card with multiple correct and incorrect options"""
        # Mock the input parsing
        dialog.parse_input = MagicMock(return_value={
            "question": "Which are planets in our solar system?",
            "correct_options": [
                {
                    "option": "Earth",
                    "explanation": "Earth is the third planet from the Sun.",
                    "preview_html": None,
                    "preview_code": None
                },
                {
                    "option": "Mars",
                    "explanation": "Mars is the fourth planet from the Sun.",
                    "preview_html": None,
                    "preview_code": None
                }
            ],
            "incorrect_options": [
                {
                    "option": "Moon",
                    "explanation": "The Moon is Earth's satellite, not a planet.",
                    "preview_html": None,
                    "preview_code": None
                },
                {
                    "option": "Sun",
                    "explanation": "The Sun is a star, not a planet.",
                    "preview_html": None,
                    "preview_code": None
                }
            ]
        })
        
        # Mock the deck selection
        dialog.deck_combo = MagicMock()
        dialog.deck_combo.currentData = MagicMock(return_value=1)  # Deck ID 1
        
        # Mock the input text
        dialog.input_text = MagicMock()
        
        # Test that the card creation function runs without errors
        dialog.create_card()
        
        # Verify that add_note was called
        from aqt import mw
        mw.col.add_note.assert_called_once()
        
        # Verify that the correct model was used (Recall22 for 2 correct, 2 incorrect)
        from anki.notes import Note
        assert Note.call_args[0][1] == mw.col.models.by_name.return_value
        mw.col.models.by_name.assert_called_with("Recall22")
    
    def test_create_card_with_preview(self, dialog):
        """Test creating a card with HTML preview sections"""
        # Mock the input parsing
        dialog.parse_input = MagicMock(return_value={
            "question": "What HTML element is used for paragraphs?",
            "question_preview": {
                "code": "<p>This is a paragraph</p>",
                "html": "<p>This is a paragraph</p>"
            },
            "correct_options": [{
                "option": "The p element",
                "explanation": "The p element is used to create paragraphs in HTML.",
                "preview_html": "<p>Example paragraph</p>",
                "preview_code": "<p>Example paragraph</p>"
            }],
            "incorrect_options": [{
                "option": "The para element",
                "explanation": "There is no para element in HTML.",
                "preview_html": None,
                "preview_code": None
            }]
        })
        
        # Mock the deck selection
        dialog.deck_combo = MagicMock()
        dialog.deck_combo.currentData = MagicMock(return_value=1)  # Deck ID 1
        
        # Mock create_preview_html method
        dialog.create_preview_html = MagicMock(return_value="<div class='preview-container'>Preview HTML</div>")
        
        # Mock the input text
        dialog.input_text = MagicMock()
        
        # Test that the card creation function runs without errors
        dialog.create_card()
        
        # Verify that create_preview_html was called twice (once for question, once for correct option)
        assert dialog.create_preview_html.call_count == 2
        
        # Verify that add_note was called
        from aqt import mw
        mw.col.add_note.assert_called_once()
    
    def test_create_note_type(self):
        """Test creation of the note type"""
        from __init__ import create_recall_note_type
        
        # Test creating Recall note type (1 correct, 1 incorrect)
        model = create_recall_note_type(1, 1)
        
        # Verify that the necessary fields were created
        from aqt import mw
        mm = mw.col.models
        
        # Check model was added to collection
        mm.add.assert_called_once()
        
        # Check template was added
        mm.add_template.assert_called_once()
        
    def test_create_complex_note_type(self):
        """Test creation of a complex note type with multiple options"""
        from __init__ import create_recall_note_type
        
        # Test creating Recall23 note type (2 correct, 3 incorrect)
        model = create_recall_note_type(2, 3)
        
        # Verify that the necessary fields were created
        from aqt import mw
        mm = mw.col.models
        
        # Check model name is correct
        mm.new.assert_called_with("Recall23")
        
        # Check model was added to collection
        mm.add.assert_called_once()
        
        # Check template was added
        mm.add_template.assert_called_once() 