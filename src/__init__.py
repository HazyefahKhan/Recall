"""
Recall Anki Plugin - Enhanced Multiple Choice Card Creator
Main package for the modular components.
"""

# Import and expose key components
from .markdown.converter import convert_markdown_to_html, format_code_block
from .ui.dialog import RecallInputDialog, show_recall_input_dialog
from .card_templates.note_types import create_recall_note_type

# Version information
__version__ = "2.0.0"

# Make sure this is recognized as a proper Python package 