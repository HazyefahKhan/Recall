import unittest
import sys
import re
import urllib.parse # Added for URL encoding/decoding simulation
from unittest.mock import MagicMock

# Mock Anki-specific modules before importing anything from src
aqt_mock = MagicMock()
aqt_mock.mw = MagicMock()
aqt_mock.mw.col = MagicMock()
aqt_mock.mw.col.models = MagicMock()

# Mock aqt.qt and specific Qt classes that might be imported directly
aqt_mock.qt = MagicMock()
aqt_mock.qt.QDialog = MagicMock() # Mock QDialog specifically
aqt_mock.qt.Qt = MagicMock() # Also common to see Qt.WindowFlags etc.

sys.modules['aqt'] = aqt_mock
sys.modules['aqt.qt'] = aqt_mock.qt

anki_mock = MagicMock()
# Mock anki.notes and anki.notes.Note
anki_mock.notes = MagicMock()
anki_mock.notes.Note = MagicMock()
# Mock anki.models and anki.models.ModelManager
anki_mock.models = MagicMock()
anki_mock.models.ModelManager = MagicMock()

sys.modules['anki'] = anki_mock
sys.modules['anki.notes'] = anki_mock.notes
sys.modules['anki.models'] = anki_mock.models # Ensure anki.models is in sys.modules

# Now import the function to be tested
from src.card_templates.note_types import create_back_template

class TestNoteTypes(unittest.TestCase):
    def test_back_template_structure_and_field_referencing(self):
        correct_options = 1
        incorrect_options = 1
        
        back_template_html = create_back_template(correct_options, incorrect_options)

        # 1. Check allItems array structure for explanation_id
        match = re.search(r"var allItems\s*=\s*\[([\s\S]*?)\];", back_template_html)
        self.assertIsNotNone(match, "Could not find allItems array in template")
        all_items_content_str = match.group(1).strip()
        
        # # DEBUG: Print the content string that is about to be split
        # print(f"--- DEBUG all_items_content_str ---")
        # print(repr(all_items_content_str)) # Use repr to see exact characters like newlines
        # print(f"---------------------------------")

        # Split by comma and newline character, then strip whitespace from each item
        item_strings_from_split = [item.strip() for item in all_items_content_str.split(',\n')]
        
        # # DEBUG: Print the result of the split
        # print(f"--- DEBUG item_strings_from_split ---")
        # print(item_strings_from_split)
        # print(f"Length: {len(item_strings_from_split)}")
        # print(f"-----------------------------------")

        self.assertTrue(len(item_strings_from_split) >= 2, "Expected at least two items in allItems array.")

        # Expected JS object strings for allItems
        # CorrectOption still uses decodeURIComponent(url:...) for its content
        expected_item_correct_js = '{ content: decodeURIComponent("{{url:CorrectOption}}"), explanation_id: "recall_explanation_correct_", isCorrect: true }'
        expected_item_incorrect_js = '{ content: decodeURIComponent("{{url:IncorrectOption1}}"), explanation_id: "recall_explanation_incorrect_1", isCorrect: false }'
        
        self.assertEqual(expected_item_correct_js, item_strings_from_split[0])
        self.assertEqual(expected_item_incorrect_js, item_strings_from_split[1])

        # 2. Check for hidden data divs for explanations
        # CorrectExplanation (no suffix for single correct option)
        expected_hidden_div_correct = '<div id="recall_explanation_correct_" style="display:none;">{{CorrectExplanation}}</div>'
        self.assertIn(expected_hidden_div_correct, back_template_html)

        # IncorrectExplanation1
        expected_hidden_div_incorrect = '<div id="recall_explanation_incorrect_1" style="display:none;">{{IncorrectExplanation1}}</div>'
        self.assertIn(expected_hidden_div_incorrect, back_template_html)

        # 3. Ensure old direct explanation embedding is gone from allItems
        self.assertNotIn('explanation: decodeURIComponent', item_strings_from_split[0])
        self.assertNotIn('explanation: `', item_strings_from_split[0])
        self.assertNotIn('explanation: decodeURIComponent', item_strings_from_split[1])
        self.assertNotIn('explanation: `', item_strings_from_split[1])

    def test_complex_html_content_integrity_simulation_for_option(self):
        # This test is now more relevant for 'CorrectOption' or 'IncorrectOption' fields 
        # as they still use the decodeURIComponent(url:...) method.
        sample_html_content = "Option with <html> & special chars like \" ' ` < > characters & entities."""
        url_encoded_content = urllib.parse.quote(sample_html_content, safe='')
        decoded_content_in_js_simulation = urllib.parse.unquote(url_encoded_content)
        self.assertEqual(sample_html_content, decoded_content_in_js_simulation,
                         "URL encoding/decoding should preserve option content integrity.")

if __name__ == '__main__':
    unittest.main() 