# Recall - Anki Plugin

This Anki plugin adds a versatile and interactive note type designed for active recall learning, particularly suitable for multiple-choice questions with detailed explanations and code examples.

## Features

*   **Custom Note Type:** Creates dynamic note types named `Recall` (for 1 correct, 1 incorrect option) or `RecallXY` (X correct, Y incorrect options, e.g., `Recall13`). A `Recall12` type (1 correct, 2 incorrect) is created by default.
*   **Dedicated Input Dialog:** Accessible via `Tools -> Create Recall Question` or `Ctrl+Shift+R`.
*   **Markdown-Based Input:** Uses a simple structure with headers (`#### Question`, `#### Correct Option`, `#### Incorrect Option`, `##### Explanation`, `#### Preview`) and `___` separators.
*   **Rich Formatting Support:**
    *   Converts Markdown headers, lists, emphasis (`*`/`_`), strong (`**`/`__`), links, inline code (` `` `), and strikethrough (`~~`) to HTML.
    *   **Code Blocks:** Supports fenced code blocks (```` ```lang ... ``` ````) with syntax highlighting via PrismJS (loaded from CDN) using a "One Dark Pro" theme.
    *   **Image Handling:** Converts `![]()` image syntax. Downloads external images (http/https) to Anki's media collection and updates links automatically.
    *   **HTML Previews:** Allows embedding raw HTML within `#### Preview` sections (using `` ```html ... ``` ``) which are rendered in an `<iframe>` within the explanation on the card.
*   **Interactive Card Interface:**
    *   Presents options (correct and incorrect) in a randomized order on the front card.
    *   Users select answers via checkboxes.
    *   A "Submit" button reveals the back card.
    *   The back card displays explanations in the same randomized order, visually indicating correct, incorrect, and user-selected options.
*   **Styling:** Applies a "One Dark Pro" theme via CSS for a consistent look.

## Installation

1.  Download the plugin files from the repository.
2.  Locate your Anki addons folder:
    *   Windows: `%APPDATA%\Anki2\addons21\`
    *   Mac: `~/Library/Application Support/Anki2/addons21/`
    *   Linux: `~/.local/share/Anki2/addons21/`
3.  Create a new folder inside the `addons21` directory (e.g., `ExamSimulator` or `RecallPlugin`).
4.  Copy all the plugin files and directories into the newly created folder, preserving the structure:
    ```
    ExamSimulator/
    ├── __init__.py             # Main entry point
    ├── manifest.json           # Add-on metadata
    └── src/                    # Main module directory 
        ├── __init__.py         # Package marker
        ├── markdown/           # Markdown processing
        │   ├── __init__.py
        │   └── converter.py    
        ├── ui/                 # User interface components
        │   ├── __init__.py
        │   └── dialog.py       
        └── card_templates/     # Card templates and styling
            ├── __init__.py
            └── note_types.py
    ```
5.  Restart Anki.

## Code Organization

The plugin is organized in a modular structure for better maintainability:

* **Main Module (`__init__.py`)**: Entry point and initialization
* **Markdown Module (`src/markdown/`)**: Handles markdown parsing and HTML conversion
  * `converter.py`: Contains the core markdown processing and HTML generation logic
* **UI Module (`src/ui/`)**: Contains the user interface components
  * `dialog.py`: Implements the input dialog and card creation logic
* **Card Templates (`src/card_templates/`)**: Handles note type creation and styling
  * `note_types.py`: Defines card templates, styling, and JavaScript functionality

This modular organization makes the codebase easier to maintain and extend.

## Usage

This plugin is designed to work with Markdown content structured in a specific way. The recommended workflow involves using an AI assistant (like ChatGPT, Claude, Gemini, etc.) in three stages to generate the required format:

**Stage 1: Fact Extraction**

Use the following prompt to extract key facts, code examples, and images from a source passage:

```plaintext
Given the following passage:

---
[Insert passage here]
---

Instructions:

1.  **Extract distinct, standalone facts** from the provided passage. Each fact must explicitly relate to the central topic or primary theme of the passage, ensuring relevance and coherence.

2.  **Present each fact explicitly in bullet-point form**.

3.  **If images are present**, include each image directly under its relevant bullet-point(s) in markdown format (`![]()`), strictly as supporting evidence for the stated fact. **Do NOT create a fact based solely around an image**; images should only substantiate clearly stated textual facts.

4.  If the fact is relevant enough to include a code example, add the code example directly beneath the associated fact.
    *   For examples involving **CSS only**, provide one single, complete HTML code block explicitly embedding the CSS within a `<style>` tag inside the HTML's `<head>` section.
    *   For examples involving **JavaScript**, similarly provide a single complete HTML code block embedding any required JavaScript within a `<script>` tag positioned at the end of the HTML's `<body>` section.
    *   If a code example combines **HTML, CSS, and JavaScript**, provide a single, fully self-contained HTML snippet embedding CSS in `<style>` tags in `<head>` and JavaScript within `<script>` tags before the closing `</body>` tag.

    **In all cases**, the resulting HTML snippet must be immediately ready to render directly in a browser without requiring external resources or additional separate code blocks.

5.  **Avoid using pronouns or ambiguous terms** (e.g., "it," "they," "this," "that"). Clearly and explicitly reference the specific subjects or entities involved to maintain maximum clarity and precision.

6.  **Ensure each bullet-point is fully self-contained**:
    *   **Do NOT reference "the article," "this passage," or any similar context-dependent terms.**
    *   Each bullet-point must stand alone logically and contextually, fully understandable to someone unfamiliar with the original passage.

7.  If a fact involves HTML, CSS, or JavaScript examples intended to visually demonstrate or illustrate the fact's concept clearly, **add a "Preview" block directly below the fact in the following exact format**:

    ```markdown
    #### Preview
    ```html
    [Insert the complete, directly renderable HTML snippet here, explicitly including embedded CSS or JavaScript when necessary]
    ```
```

**Stage 2: Multiple-Choice Question Generation**

Using the facts extracted in Stage 1, use the following prompt to generate multiple-choice questions:

```plaintext
Now, using each self-contained bullet-point fact extracted, create separate multiple-choice questions adhering strictly to these enhanced criteria:

1.  **Begin each question explicitly with the header "Question"** (no numbering or variations).

2.  **Write a concise, bite-sized question directly testing the single extracted fact** from the corresponding bullet-point.

3.  **The question itself must be completely self-contained.**

    *   Do **not** reference external examples, code snippets, preview blocks, or context that isn't explicitly and fully included within the question's text itself—even if such information is available in the answer choices or elsewhere.

4.  Provide exactly **3 answer choices**, clearly formatted as bullet points:

    *   Exactly **one choice** must accurately reflect the extracted bullet-point fact.

    *   Generate exactly **two plausible distractors** that:

        *   Are positively phrased, realistic, logically coherent, and believable.

        *   Are carefully crafted to be conceptually similar and equally plausible at first glance, requiring genuine understanding rather than superficial recognition to distinguish from the correct choice.

        *   **Avoid explicitly using key terminology or exact phrases directly mentioned in the question within the answer choices. Instead, phrase answers in general or abstract conceptual terms.**

5.  Include any supporting images directly beneath the Answer Key.

6.  Include any supporting code examples and/or **Preview blocks** (HTML/CSS/JavaScript for browser rendering) directly beneath the Answer Key exactly as extracted from the original fact. The Preview block, if present, should retain its original markdown formatting precisely as provided, without alterations or additional headings.

7.  Ensure all three answer choices:

    *   Are similar in length, complexity, formatting, and phrasing.

    *   Avoid noticeable differences in positivity, negativity, or specificity that might unintentionally reveal the correct answer.

8.  Guarantee each question is fully independent and understandable without additional context. **No external or implied context, examples, or references outside the explicit text of the question itself are permitted, even if included elsewhere.**

9.  Immediately follow each question with an **Answer Key**, clearly labeled and containing only the exact text of the correct choice.

10. Explicitly confirm:

    *   **No correct answer choice is repeated** across the entire question set, maintaining uniqueness.

    *   All three choices in every question are phrased positively or neutrally, avoiding negative phrasing or unrealistic exaggerations that hint at incorrect answers.

---

**Example of Correct Implementation (General, Conceptually Challenging):**

**Question**
What effect does applying a certain CSS display property have when used on an inline element nested within text, enabling it to respect dimensions and spacing settings without disrupting the flow of surrounding text?

*   It makes the element remain part of the inline flow, while enabling it to respect width, height, padding, and margin settings.

*   It positions the element on a separate line, occupying available horizontal space while respecting width, height, padding, and margin settings.

*   It allows the element to dynamically adjust internal layout and spacing, independently from surrounding inline content.

**Answer Key**
It makes the element remain part of the inline flow, while enabling it to respect width, height, padding, and margin settings.
```

**Stage 3: Final Formatting for Anki Plugin**

Take the output from Stage 2 and use the following prompt to format it correctly for the Recall plugin's input dialog:

```plaintext
For each question, convert to the following structured format:

#### Question

[Insert question text here]

---
#### Correct Option

[Insert correct option text here]

##### Explanation

[Provide a clear, educational explanation that teaches the concept, terminology, or principle behind why this option is correct. Assume the User has no prior knowledge of the terms or concepts mentioned, and explain from fundamental principles, building understanding progressively.]

[If an image or code example is associated with the correct option, insert the image or code example here to support understanding.]

[If a "Preview" markdown block was provided in the question, directly include it immediately following the Correct Option's Explanation section, without adding any additional headings or explanatory text.]

---
#### Incorrect Option

[Insert incorrect option text here]

##### Explanation

[Provide a brief, clear explanation of the misconception or specific reason this option is incorrect, helping the User understand common mistakes or misinterpretations. Avoid simply stating it is incorrect; instead, clarify the misunderstanding.]

---
#### Incorrect Option

[Insert incorrect option text here]

##### Explanation

[Provide a brief, clear explanation of the misconception or specific reason this option is incorrect, helping the User understand common mistakes or misinterpretations. Avoid simply stating it is incorrect; instead, clarify the misunderstanding.]
___

Remember to:

*   Retain all existing headings and subheadings exactly, including their sizes.
*   Always list the **Correct Option** first, followed by **Incorrect Option**.
*   Explanations must focus on teaching and building foundational knowledge rather than merely stating correctness.
*   If any images are associated with the correct choice, always include these under the Correct Option's Explanation section.
*   Ensure each Question is fully self-contained and does not reference external passages or other questions.
*   Your response should strictly adhere to the provided structural format without additional commentary or deviations.
```

**Pasting into Anki**

1.  The final output from Stage 3 should look similar to this example:

    ````markdown
    #### Question

    In a demonstration where a general rule sets font size and color for level-two headings and separate category-based rules adjust just one of those properties, what outcome occurs?

    ---

    #### Correct Option

    Only the properties restated in the category-based rules change, while the other properties from the general rule continue to apply.

    ##### Explanation

    CSS applies declarations **property-by-property**. After the initial element selector assigns `font-size` and `color`, a class selector with higher specificity may override, for instance, `color` only. Because the class selector omits `font-size`, the earlier value persists. This fine-grained merging lets developers tweak individual aspects without redefining every property, demonstrating how specificity and property independence work together.

    #### Preview

    ```html
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="utf-8">
    <title>Specificity Demo</title>
    <style>
    h2 {
      font-size: 2em;
      color: #000;
      font-family: Georgia, "Times New Roman", Times, serif;
    }

    .small {
      font-size: 1em;
    }

    .bright {
      color: rebeccapurple;
    }
    </style>
    </head>
    <body>
    <h2>Heading with no class</h2>
    <h2 class="small">Heading with class of small</h2>
    <h2 class="bright">Heading with class of bright</h2>
    </body>
    </html>
    ```

    ---

    #### Incorrect Option

    The category-based rules completely replace every declaration from the general rule, leaving none of its original styling active.

    ##### Explanation

    An overriding rule affects only properties it declares. It does not erase unrelated declarations, so the general rule's untouched properties still apply.

    ---

    #### Incorrect Option

    Both the general and category-based rules are ignored because their similar scope produces a conflict that the browser discards.

    ##### Explanation

    Browsers do not discard conflicting rules; they resolve them. The cascade decides property-by-property which value wins, ensuring that at least one declaration supplies each final property value.

    ---
    ````

2.  Open the Recall plugin dialog in Anki (`Tools -> Create Recall Question` or `Ctrl+Shift+R`).
3.  Select the desired deck.
4.  Paste the entire formatted output from Stage 3 into the main text area.
5.  Click "Create Card". The plugin will parse this structured Markdown and create the interactive Anki card.

## Card Interaction

*   **Front:** The question appears, followed by all options presented in a random order with checkboxes. Select one or more options and click "Submit".
*   **Back:** The original question and selected options are shown. Below the separator (`<hr id="answer">`), each option is listed again *in the same randomized order* as on the front, along with its corresponding explanation.
    *   Correct options are highlighted (e.g., green border).
    *   Incorrect options are highlighted (e.g., red border).
    *   Options you selected are highlighted (e.g., blue border/background).
    *   Code blocks within explanations are syntax-highlighted.
    *   HTML previews within explanations are rendered in iframes.

## Development

If you want to contribute to the development of this plugin:

1. Fork or clone the repository
2. Make your changes following the modular structure
3. Test your changes thoroughly with Anki
4. Submit a pull request or share your modifications

The modular structure makes it easier to locate and modify specific components:
* For markdown processing changes, look in `src/markdown/converter.py`
* For UI changes, look in `src/ui/dialog.py`
* For card template changes, look in `src/card_templates/note_types.py`

## Version History

*   2.1.0: Refactored codebase for better maintainability with modular architecture
*   2.0.0: Rebranded as "Recall" with focus on active recall learning, dynamic note types, Markdown enhancements (images, previews, PrismJS), interactive cards, and One Dark Pro styling.
*   1.0.0: Initial release as "Exam Simulator MCQ".