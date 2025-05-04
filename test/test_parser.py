import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add parent directory to path so we can import the plugin
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.mark.usefixtures("mock_anki")
class TestInputParser:
    
    @pytest.fixture
    def dialog(self):
        """Create a RecallInputDialog instance"""
        from __init__ import RecallInputDialog
        dialog = RecallInputDialog()
        return dialog
    
    def test_parse_simple_input(self, dialog):
        """Test parsing of simple input with one correct and one incorrect option"""
        # Simple input with one correct and one incorrect option
        input_text = """
        #### Question
        What is the capital of France?
        ___
        #### Correct Option
        Paris
        
        ##### Explanation
        Paris is the capital of France.
        ___
        #### Incorrect Option
        London
        
        ##### Explanation
        London is the capital of the United Kingdom, not France.
        """
        
        dialog.input_text = MagicMock()
        dialog.input_text.toPlainText.return_value = input_text
        
        result = dialog.parse_input()
        
        # Check that the question, correct and incorrect options were parsed correctly
        assert "What is the capital of France?" in result["question"]
        assert len(result["correct_options"]) == 1
        assert len(result["incorrect_options"]) == 1
        assert "Paris" in result["correct_options"][0]["option"]
        assert "London" in result["incorrect_options"][0]["option"]
    
    def test_parse_with_preview(self, dialog):
        """Test parsing of input with HTML preview sections"""
        # Input with preview sections
        input_text = """
        #### Question
        What HTML element is used for paragraphs?
        #### Preview
        ```html
        <p>This is a paragraph</p>
        ```
        ___
        #### Correct Option
        The p element
        
        ##### Explanation
        The p element is used to create paragraphs in HTML.
        
        #### Preview
        ```html
        <p>Example paragraph</p>
        ```
        ___
        #### Incorrect Option
        The para element
        
        ##### Explanation
        There is no para element in HTML.
        """
        
        dialog.input_text = MagicMock()
        dialog.input_text.toPlainText.return_value = input_text
        
        result = dialog.parse_input()
        
        # Check that preview sections were parsed correctly
        assert "question_preview" in result
        assert "<p>This is a paragraph</p>" in result["question_preview"]["html"]
        assert "<p>Example paragraph</p>" in result["correct_options"][0]["preview_html"]
    
    def test_parse_multiple_options(self, dialog):
        """Test parsing of input with multiple correct and incorrect options"""
        # Input with multiple options
        input_text = """
        #### Question
        Which of these are planets in our solar system?
        ___
        #### Correct Option
        Earth
        
        ##### Explanation
        Earth is the third planet from the Sun.
        ___
        #### Correct Option
        Mars
        
        ##### Explanation
        Mars is the fourth planet from the Sun.
        ___
        #### Incorrect Option
        Moon
        
        ##### Explanation
        The Moon is Earth's satellite, not a planet.
        ___
        #### Incorrect Option
        Sun
        
        ##### Explanation
        The Sun is a star, not a planet.
        """
        
        dialog.input_text = MagicMock()
        dialog.input_text.toPlainText.return_value = input_text
        
        result = dialog.parse_input()
        
        # Check that multiple options were parsed correctly
        assert len(result["correct_options"]) == 2
        assert len(result["incorrect_options"]) == 2
        assert "Earth" in result["correct_options"][0]["option"]
        assert "Mars" in result["correct_options"][1]["option"]
        assert "Moon" in result["incorrect_options"][0]["option"]
        assert "Sun" in result["incorrect_options"][1]["option"]
    
    def test_handle_malformed_input(self, dialog):
        """Test handling of malformed input"""
        # Malformed input (missing explanation)
        input_text = """
        #### Question
        What is the capital of France?
        ___
        #### Correct Option
        Paris
        ___
        #### Incorrect Option
        London
        
        ##### Explanation
        London is the capital of the United Kingdom, not France.
        """
        
        dialog.input_text = MagicMock()
        dialog.input_text.toPlainText.return_value = input_text
        
        result = dialog.parse_input()
        
        # Check that parsing handles the malformed input gracefully
        assert "What is the capital of France?" in result["question"]
        assert len(result["correct_options"]) == 0  # No explanation, so not parsed
        assert len(result["incorrect_options"]) == 1 