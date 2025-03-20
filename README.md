# Recall - Anki Plugin

This Anki plugin adds a new note type focused on active recall learning, helping you strengthen your memory through targeted question-answer pairs.

## Features

- Custom active recall note type with multiple options
- Support for configurable correct and incorrect answers
- Detailed explanations for all options
- Interactive card interface with randomized option presentation
- Visual feedback for chosen answers
- Markdown formatting support with syntax highlighting for code

## Installation

1. Download the plugin files
2. Locate your Anki addons folder:
   - Windows: `%APPDATA%\Anki2\addons21\`
   - Mac: `~/Library/Application Support/Anki2/addons21/`
   - Linux: `~/.local/share/Anki2/addons21/`
3. Create a new folder in the addons directory and copy all plugin files into it
4. Restart Anki

## Usage

1. In Anki, go to Tools → Create Recall Question
2. Select a deck for your new card
3. Fill in the question and answer options using the provided template
4. For each option, provide a detailed explanation of why it's correct or incorrect
5. Click "Create Card" to add the card to your selected deck

The default card type is "Recall" which has 1 correct and 1 incorrect option. Additional variants are automatically named based on their configuration (e.g., "Recall13" for 1 correct and 3 incorrect options).

## Version History

- 2.0.0: Rebranded as "Recall" with focus on active recall learning
- 1.0.0: Initial release as "Exam Simulator MCQ"