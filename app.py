import gradio as gr
import os
from openai import OpenAI
from dotenv import load_dotenv
import csv
from typing import List, Dict
import difflib

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initial prompt for the LLM
SYSTEM_PROMPT = """אתה עוזר שמתמחה בתרגום הוראות בשפה טבעית לפקודות CLI של Windows.

המשימה שלך:
- קבל הוראה בעברית או אנגלית בשפה טבעית
- תרגם אותה לפקודת CLI מדויקת לטרמינל Windows
- החזר רק את הפקודה עצמה, ללא הסברים נוספים

דוגמאות:
הוראה: "מה כתובת ה-IP של המחשב שלי"
פקודה: ipconfig

הוראה: "אני רוצה למחוק את כל הקבצים עם סיומת .tmp בתיקייה downloads"
פקודה: del downloads\\*.tmp

הוראה: "לסדר את רשימת הקבצים לפי גודל מהגדול לקטן"
פקודה: dir /o-s

הוראה: "איזה תהליכים רצים כרגע במערכת"
פקודה: tasklist

חשוב: החזר רק את הפקודה, ללא תוספות."""

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
            temperature=0.1,  # Low temperature for more consistent outputs
            max_tokens=150
        )
        
        cli_command = response.choices[0].message.content.strip()
        return cli_command
        
    except Exception as e:
        return f"שגיאה: {str(e)}"

def calculate_similarity(str1: str, str2: str) -> float:
    """Calculate similarity ratio between two strings."""
    return difflib.SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

def load_test_cases(csv_file: str = "test_cases.csv") -> List[Dict[str, str]]:
    """Load test cases from CSV file."""
    test_cases = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                test_cases.append(row)
    except FileNotFoundError:
        return []
    return test_cases

def save_results_to_csv(results: List[Dict], csv_file: str = "test_cases.csv"):
    """
    Save test results back to the original CSV file with actual_output and match_status columns.
    """
    # Read existing test cases
    existing_cases = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing_cases.append(row)
    
    # Update with results
    for i, result in enumerate(results):
        if i < len(existing_cases):
            existing_cases[i]['actual_output'] = result['actual']
            existing_cases[i]['similarity_score'] = f"{result['similarity']}%"
            existing_cases[i]['match_status'] = result['status']
    
    # Write back to CSV
    fieldnames = ['input', 'expected_output', 'category', 'actual_output', 'similarity_score', 'match_status']
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing_cases)

def run_single_test(user_input: str, expected: str) -> Dict:
    """Run a single test and return results."""
    actual = convert_to_cli(user_input)
    similarity = calculate_similarity(expected, actual)
    is_exact_match = expected.lower() == actual.lower()
    is_similar = similarity >= 0.8
    status = "✅ PASS" if is_exact_match or is_similar else "❌ FAIL"
    
    return {
        'input': user_input,
        'expected': expected,
        'actual': actual,
        'similarity': round(similarity * 100, 2),
        'status': status,
        'is_exact_match': is_exact_match
    }

def run_all_tests() -> str:
    """Run all tests from CSV and return formatted results."""
    test_cases = load_test_cases()
    if not test_cases:
        return "לא נמצא קובץ test_cases.csv או שהוא ריק"
    
    results = []
    for test_case in test_cases:
        result = run_single_test(test_case['input'], test_case['expected_output'])
        results.append(result)
    
    save_results_to_csv(results)
    
    # Calculate summary
    total = len(results)
    passed = sum(1 for r in results if '✅' in r['status'])
    avg_similarity = sum(r['similarity'] for r in results) / total if total > 0 else 0
    
    # Format output
    output = f"📊 **סיכום בדיקות**\n\n"
    output += f"סך הכל: {total} | עברו: {passed} | נכשלו: {total-passed}\n"
    output += f"אחוז הצלחה: {round(passed/total*100, 1)}% | דמיון ממוצע: {round(avg_similarity, 1)}%\n\n"
    output += f"✅ **התוצאות נשמרו אוטומטית ב-test_cases.csv**\n\n"
    output += "---\n\n"
    
    for i, result in enumerate(results, 1):
        output += f"**בדיקה {i}:** {result['status']}\n"
        output += f"📝 הוראה: {result['input']}\n"
        output += f"✅ צפוי: `{result['expected']}`\n"
        output += f"🤖 התקבל: `{result['actual']}`\n"
        output += f"📈 דמיון: {result['similarity']}%\n\n"
    
    return output

# Create Gradio interface
with gr.Blocks(title="CLI Command Generator", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🤖 CLI Agent - ממיר הוראות לפקודות")
    
    with gr.Tabs():
        with gr.Tab("🔧 ממיר פקודות"):
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
            
            # Example inputs
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
        
        with gr.Tab("🧪 בדיקות אוטומטיות"):
            gr.Markdown("### הרץ את כל מקרי הבדיקה מקובץ test_cases.csv")
            gr.Markdown("הבדיקות שוות את הפלט של המודל לפקודות הצפויות ומחשבות אחוז דמיון")
            
            test_btn = gr.Button("🚀 הרץ את כל הבדיקות", variant="primary", size="lg")
            test_output = gr.Markdown(label="תוצאות בדיקות")
            
            test_btn.click(fn=run_all_tests, inputs=None, outputs=test_output)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
