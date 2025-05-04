import pytest
import sys
from unittest.mock import MagicMock, patch

# Create mocks for Anki classes and modules
class MockCollection:
    def __init__(self):
        self.models = MagicMock()
        self.decks = MagicMock()
        self.media = MagicMock()
        
        # Setup commonly used methods
        self.decks.all_names_and_ids.return_value = [
            MagicMock(name="Default", id=1),
            MagicMock(name="Test::Subdeck", id=2)
        ]
        
        # Setup models methods
        self.models.new.return_value = {'id': 1, 'css': ''}
        self.models.add_field = MagicMock()
        self.models.new_field = MagicMock(return_value={'name': '', 'ord': 0})
        self.models.add_template = MagicMock()
        self.models.new_template = MagicMock(return_value={'name': '', 'qfmt': '', 'afmt': ''})
        self.models.add = MagicMock()
        self.models.by_name = MagicMock(return_value=None)  # Initially no models exist
        self.models.all_names = MagicMock(return_value=[])
        
        # Media directory
        self.media.dir = MagicMock(return_value="/mock/media/dir")
        
    def add_note(self, note, deck_id):
        return 1  # Return a note ID

class MockMainWindow:
    def __init__(self):
        self.col = MockCollection()
        self.form = MagicMock()
        self.form.menuTools = MagicMock()
        self.reset = MagicMock()
        self.pm = MagicMock()
        self.pm.profile = {}

class MockNote:
    def __init__(self, col, model):
        self.col = col
        self.model = model
        self._fmap = {}
        
    def __setitem__(self, key, value):
        self._fmap[key] = value
    
    def __getitem__(self, key):
        return self._fmap.get(key, "")

@pytest.fixture
def mock_anki():
    """Setup mock Anki environment"""
    # Create mock modules
    mock_modules = {
        'aqt': MagicMock(),
        'aqt.gui_hooks': MagicMock(),
        'aqt.qt': MagicMock(),
        'anki.models': MagicMock(),
        'anki.notes': MagicMock(),
        'anki.utils': MagicMock()
    }
    
    # Add the QT classes needed
    mock_modules['aqt.qt'].QDialog = MagicMock
    mock_modules['aqt.qt'].QVBoxLayout = MagicMock
    mock_modules['aqt.qt'].QHBoxLayout = MagicMock
    mock_modules['aqt.qt'].QLabel = MagicMock
    mock_modules['aqt.qt'].QComboBox = MagicMock
    mock_modules['aqt.qt'].QPlainTextEdit = MagicMock
    mock_modules['aqt.qt'].QPushButton = MagicMock
    mock_modules['aqt.qt'].QMessageBox = MagicMock
    mock_modules['aqt.qt'].QKeySequence = MagicMock
    mock_modules['aqt.qt'].QAction = MagicMock
    
    # Setup main window
    mock_modules['aqt'].mw = MockMainWindow()
    
    # Setup Note class
    mock_modules['anki.notes'].Note = MockNote
    
    # Add to sys.modules so imports work
    for name, mock in mock_modules.items():
        sys.modules[name] = mock
    
    yield mock_modules
    
    # Clean up after test
    for name in mock_modules.keys():
        if name in sys.modules:
            del sys.modules[name]

try:
    import pyfakefs.fake_filesystem_unittest
    @pytest.fixture
    def fs():
        """Get pyfakefs fixture if available"""
        try:
            from pyfakefs.fake_filesystem_unittest import Patcher
            with Patcher() as patcher:
                yield patcher.fs
        except ImportError:
            pytest.skip("pyfakefs not available")
            yield None
except ImportError:
    @pytest.fixture
    def fs():
        pytest.skip("pyfakefs not available")
        yield None

@pytest.fixture
def fs_setup(fs):
    """Setup a fake filesystem with required files"""
    if fs is not None:
        # Create media directory
        fs.create_dir('/mock/media/dir')
    return fs 