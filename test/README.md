# Test Suite for Recall Anki Plugin

This test suite is designed to verify the functionality of the Recall plugin for Anki. It uses pytest to create a comprehensive set of tests.

## Requirements

- pytest
- pytest-mock
- pytest-cov
- pyfakefs
- markdown

Install all requirements:

```bash
pip install -r requirements.txt
```

## Running Tests

From the project root directory:

```bash
python -m pytest
```

For test coverage report:

```bash
python -m pytest --cov=. --cov-report=html
```

## Test Structure

- **conftest.py**: Mock setup for Anki environment
- **test_markdown_converter.py**: Tests for markdown processing
- **test_parser.py**: Tests for input parsing
- **test_card_creation.py**: Tests for card creation and note types
- **test_dialog_ui.py**: Tests for dialog UI functionality
- **test_image_handling.py**: Tests for image processing

## Mocked Components

The test suite mocks the following Anki components:

- `aqt.mw`: Main window
- `aqt.qt`: Qt UI components
- `anki.models`: Note type creation
- `anki.notes`: Note creation
- `anki.utils`: Utility functions

## Adding New Tests

1. Create a new test file following the naming convention `test_*.py`
2. Add the `@pytest.mark.usefixtures("mock_anki")` decorator to test classes
3. Import the plugin functionality after the mock setup

Example:

```python
@pytest.mark.usefixtures("mock_anki")
class TestNewFeature:
    def test_something(self):
        from __init__ import some_function
        result = some_function()
        assert result == expected_value
``` 