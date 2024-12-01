from aqt import mw
from aqt import gui_hooks
from aqt.qt import *
from anki.models import ModelManager
from anki.notes import Note

def init_mcq_note_type():
    # Check if our note type already exists
    model_name = "MCQ Card"
    if model_name not in mw.col.models.all_names():
        # Create the note type
        mm = mw.col.models
        m = mm.new(model_name)
        
        # Add fields
        for field_name in [
            "Question",
            "OptionA",
            "OptionB",
            "OptionC",
            "OptionD",
            "CorrectOptions",
            "CorrectExplanations",
            "IncorrectOptions",
            "IncorrectExplanations"
        ]:
            field = mm.new_field(field_name)
            mm.add_field(m, field)

        # Add templates
        template = mm.new_template("MCQ Card")
        template['qfmt'] = """
        <div class="question">{{Question}}</div>
        <div class="options">
            <div class="option">A. {{OptionA}}</div>
            <div class="option">B. {{OptionB}}</div>
            <div class="option">C. {{OptionC}}</div>
            <div class="option">D. {{OptionD}}</div>
        </div>
        """
        template['afmt'] = """
        {{FrontSide}}
        <hr id="answer">
        <div class="answer">
            <div class="correct-options">
                <h3>Correct Options:</h3>
                {{CorrectOptions}}
            </div>
            <div class="explanations">
                <h3>Explanations:</h3>
                {{CorrectExplanations}}
            </div>
        </div>
        """
        mm.add_template(m, template)

        # Add CSS
        m['css'] = """
        .card {
            font-family: arial;
            font-size: 20px;
            text-align: left;
            color: black;
            background-color: white;
        }

        .question {
            margin-bottom: 20px;
        }

        .option {
            margin: 10px 0;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 5px;
        }

        .correct-options {
            border: 2px solid green;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
        }

        .explanations {
            border: 2px solid blue;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
        }
        """
        
        mm.add(m)
        return m

# Initialize the plugin
def init():
    init_mcq_note_type()

# Add the init hook
gui_hooks.profile_did_open.append(init) 