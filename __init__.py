"""
Recall Anki Plugin - Enhanced Multiple Choice Card Creator
"""

from aqt import mw
from aqt import gui_hooks
from aqt.qt import *

# Import from our modular structure using relative imports
from .src.markdown.converter import convert_markdown_to_html, format_code_block
from .src.ui.dialog import RecallInputDialog, show_recall_input_dialog
from .src.card_templates.note_types import create_recall_note_type

# Add menu item
action = QAction("Create Recall Question", mw)
action.triggered.connect(show_recall_input_dialog)
action.setShortcut(QKeySequence("Ctrl+Shift+R"))  # Updated keyboard shortcut
mw.form.menuTools.addAction(action)

def init():
    """Initialize the plugin."""
    # Create default Recall12 card (1 correct, 2 incorrect options)
    create_recall_note_type(1, 2)

# Add the init hook
gui_hooks.profile_did_open.append(init)

# Version information
__version__ = "2.0.0" 