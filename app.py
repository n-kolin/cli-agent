import gradio as gr
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load system prompt from markdown file
def load_system_prompt(filepath: str = "system_prompt.md") -> str:
    """Load system prompt from a markdown file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"System prompt file '{filepath}' not found. Please create it before running the app.")

SYSTEM_PROMPT = load_system_prompt()

def convert_to_cli(user_input: str) -> str:
    """
    Convert natural language instruction to CLI command using OpenAI API.

    Args:
        user_input: Natural language instruction in Hebrew or English

    Returns:
        CLI command as a string
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"שגיאה: {str(e)}"

# Create Gradio interface
with gr.Blocks(title="CLI Command Generator", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🤖 CLI Agent - ממיר הוראות לפקודות")

    with gr.Row():
        with gr.Column():
            input_text = gr.Textbox(
                label="הוראה בשפה טבעית",
                placeholder='לדוגמה: "מה כתובת ה-IP של המחשב שלי"',
                lines=3,
                rtl=True
            )
            submit_btn = gr.Button("תרגם לפקודה", variant="primary")

        with gr.Column():
            output_text = gr.Textbox(
                label="פקודת CLI",
                placeholder="הפקודה תופיע כאן...",
                lines=3,
                interactive=False
            )

    gr.Markdown("### דוגמאות לניסיון:")
    gr.Examples(
        examples=[
            ["מה כתובת ה-IP של המחשב שלי"],
            ["אני רוצה למחוק את כל הקבצים עם סיומת .tmp בתיקייה downloads"],
            ["לסדר את רשימת הקבצים לפי גודל מהגדול לקטן"],
            ["איזה תהליכים רצים כרגע במערכת"],
            ["הצג את תוכן התיקייה הנוכחית"],
            ["צור תיקייה חדשה בשם test"],
        ],
        inputs=input_text,
    )

    submit_btn.click(fn=convert_to_cli, inputs=input_text, outputs=output_text)
    input_text.submit(fn=convert_to_cli, inputs=input_text, outputs=output_text)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
