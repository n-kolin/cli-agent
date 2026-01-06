import gradio as gr
import os
from openai import OpenAI
from dotenv import load_dotenv
import csv
from typing import List, Dict
import difflib
from datetime import datetime
import json

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initial prompt for the LLM
DEFAULT_SYSTEM_PROMPT = """אתה עוזר שמתמחה בתרגום הוראות בשפה טבעית לפקודות CLI של Windows.

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

current_system_prompt = DEFAULT_SYSTEM_PROMPT

def convert_to_cli(user_input: str, system_prompt: str = None) -> str:
    """
    Convert natural language instruction to CLI command using OpenAI API.
    
    Args:
        user_input: Natural language instruction in Hebrew or English
        system_prompt: Optional custom system prompt to use
        
    Returns:
        CLI command as a string
    """
    prompt_to_use = system_prompt if system_prompt else current_system_prompt
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt_to_use},
                {"role": "user", "content": user_input}
            ],
            temperature=0.3,
            max_tokens=500
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

def save_results_to_csv(results: List[Dict], system_prompt: str, csv_file: str = "test_cases.csv"):
    """
    Save test results back to the original CSV file with actual_output, match_status, and system_prompt columns.
    """
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
            existing_cases[i]['system_prompt'] = system_prompt[:100] + "..." if len(system_prompt) > 100 else system_prompt
    
    # Write back to CSV
    fieldnames = ['input', 'expected_output', 'complexity', 'actual_output', 'similarity_score', 'match_status', 'system_prompt']
    with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing_cases)

def run_single_test(user_input: str, expected: str, system_prompt: str, complexity: str = "לא ידוע") -> Dict:
    """Run a single test and return results."""
    actual = convert_to_cli(user_input, system_prompt)
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
        'is_exact_match': is_exact_match,
        'complexity': complexity  # Added complexity tracking
    }

def run_all_tests(complexity_filter: str = "הכל", system_prompt: str = None) -> tuple:
    """Run all tests from CSV and return formatted results + files for download."""
    prompt_to_use = system_prompt if system_prompt else current_system_prompt
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    test_cases = load_test_cases()
    if not test_cases:
        return "לא נמצא קובץ test_cases.csv או שהוא ריק", None, None, None
    
    if complexity_filter != "הכל":
        test_cases = [tc for tc in test_cases if tc.get('complexity', 'פשוט') == complexity_filter]
    
    if not test_cases:
        return f"לא נמצאו פקודות ברמת מורכבות: {complexity_filter}", None, None, None
    
    results = []
    for test_case in test_cases:
        result = run_single_test(
            test_case['input'], 
            test_case['expected_output'], 
            prompt_to_use,
            test_case.get('complexity', 'פשוט')
        )
        results.append(result)
    
    # Save all the files
    results_file = save_run_results(results, prompt_to_use, complexity_filter, timestamp)
    summary_file = save_run_summary(results, prompt_to_use, complexity_filter, timestamp)
    update_global_summary(timestamp, prompt_to_use, complexity_filter, results)
    
    # Calculate summary
    total = len(results)
    passed = sum(1 for r in results if '✅' in r['status'])
    avg_similarity = sum(r['similarity'] for r in results) / total if total > 0 else 0
    
    # Format output
    output = f"📊 **סיכום בדיקות - {complexity_filter}**\n\n"
    output += f"🕒 תאריך הרצה: {timestamp}\n\n"
    output += f"סך הכל: {total} | עברו: {passed} | נכשלו: {total-passed}\n"
    output += f"אחוז הצלחה: {round(passed/total*100, 1)}% | דמיון ממוצע: {round(avg_similarity, 1)}%\n\n"
    output += f"✅ **קבצים נשמרו:**\n"
    output += f"  - תוצאות מפורטות: `{results_file}`\n"
    output += f"  - סיכום הרצה: `{summary_file}`\n"
    output += f"  - סיכום גלובלי עודכן: `global_summary.csv`\n\n"
    output += "---\n\n"
    
    for i, result in enumerate(results, 1):
        output += f"**בדיקה {i}:** {result['status']} [{result['complexity']}]\n"
        output += f"📝 הוראה: {result['input']}\n"
        output += f"✅ צפוי: `{result['expected']}`\n"
        output += f"🤖 התקבל: `{result['actual']}`\n"
        output += f"📈 דמיון: {result['similarity']}%\n\n"
    
    return output, results_file, summary_file, "global_summary.csv"

def save_run_results(results: List[Dict], system_prompt: str, complexity_filter: str, timestamp: str):
    """
    Save individual run results to a separate CSV file with timestamp.
    """
    filename = f"results_{timestamp}.csv"
    fieldnames = ['input', 'expected_output', 'actual_output', 'similarity_score', 'match_status', 'complexity']
    
    with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow({
                'input': result['input'],
                'expected_output': result['expected'],
                'actual_output': result['actual'],
                'similarity_score': f"{result['similarity']}%",
                'match_status': result['status'],
                'complexity': result.get('complexity', 'לא ידוע')
            })
    
    return filename

def save_run_summary(results: List[Dict], system_prompt: str, complexity_filter: str, timestamp: str):
    """
    Save a summary file for this specific run with the system prompt and statistics.
    """
    total = len(results)
    passed = sum(1 for r in results if '✅' in r['status'])
    failed = total - passed
    avg_similarity = sum(r['similarity'] for r in results) / total if total > 0 else 0
    
    # Group by complexity
    complexity_stats = {}
    for result in results:
        comp = result.get('complexity', 'לא ידוע')
        if comp not in complexity_stats:
            complexity_stats[comp] = {'total': 0, 'passed': 0, 'similarities': []}
        complexity_stats[comp]['total'] += 1
        if '✅' in result['status']:
            complexity_stats[comp]['passed'] += 1
        complexity_stats[comp]['similarities'].append(result['similarity'])
    
    filename = f"summary_{timestamp}.txt"
    with open(filename, 'w', encoding='utf-8-sig') as f:
        f.write("=" * 80 + "\n")
        f.write(f"סיכום הרצה - {timestamp}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("SYSTEM PROMPT:\n")
        f.write("-" * 80 + "\n")
        f.write(system_prompt + "\n")
        f.write("-" * 80 + "\n\n")
        
        f.write("סטטיסטיקות כלליות:\n")
        f.write(f"  סינון לפי מורכבות: {complexity_filter}\n")
        f.write(f"  סך הכל בדיקות: {total}\n")
        f.write(f"  עברו: {passed} ({round(passed/total*100, 1)}%)\n")
        f.write(f"  נכשלו: {failed} ({round(failed/total*100, 1)}%)\n")
        f.write(f"  דמיון ממוצע: {round(avg_similarity, 2)}%\n\n")
        
        f.write("פילוח לפי רמת מורכבות:\n")
        for comp, stats in complexity_stats.items():
            comp_total = stats['total']
            comp_passed = stats['passed']
            comp_avg_sim = sum(stats['similarities']) / len(stats['similarities']) if stats['similarities'] else 0
            f.write(f"  {comp}:\n")
            f.write(f"    בדיקות: {comp_total}\n")
            f.write(f"    הצלחה: {comp_passed}/{comp_total} ({round(comp_passed/comp_total*100, 1)}%)\n")
            f.write(f"    דמיון ממוצע: {round(comp_avg_sim, 2)}%\n\n")
    
    return filename

def update_global_summary(timestamp: str, system_prompt: str, complexity_filter: str, results: List[Dict]):
    """
    Update the global summary file that tracks all runs across different system prompts.
    """
    global_file = "global_summary.csv"
    
    total = len(results)
    passed = sum(1 for r in results if '✅' in r['status'])
    avg_similarity = sum(r['similarity'] for r in results) / total if total > 0 else 0
    
    # Calculate stats by complexity
    by_complexity = {}
    for result in results:
        comp = result.get('complexity', 'לא ידוע')
        if comp not in by_complexity:
            by_complexity[comp] = {'total': 0, 'passed': 0, 'avg_sim': 0, 'sims': []}
        by_complexity[comp]['total'] += 1
        if '✅' in result['status']:
            by_complexity[comp]['passed'] += 1
        by_complexity[comp]['sims'].append(result['similarity'])
    
    for comp in by_complexity:
        sims = by_complexity[comp]['sims']
        by_complexity[comp]['avg_sim'] = sum(sims) / len(sims) if sims else 0
    
    # Check if file exists
    file_exists = os.path.exists(global_file)
    
    with open(global_file, 'a', encoding='utf-8-sig', newline='') as f:
        fieldnames = [
            'timestamp', 'complexity_filter', 'system_prompt_preview',
            'total_tests', 'passed', 'failed', 'success_rate', 'avg_similarity',
            'simple_tests', 'simple_passed', 'simple_success_rate', 'simple_avg_sim',
            'medium_tests', 'medium_passed', 'medium_success_rate', 'medium_avg_sim',
            'complex_tests', 'complex_passed', 'complex_success_rate', 'complex_avg_sim'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        row = {
            'timestamp': timestamp,
            'complexity_filter': complexity_filter,
            'system_prompt_preview': system_prompt[:100].replace('\n', ' '),
            'total_tests': total,
            'passed': passed,
            'failed': total - passed,
            'success_rate': round(passed/total*100, 1) if total > 0 else 0,
            'avg_similarity': round(avg_similarity, 2)
        }
        
        # Add complexity-specific stats
        for comp_name, csv_prefix in [('פשוט', 'simple'), ('בינוני', 'medium'), ('מורכב', 'complex')]:
            if comp_name in by_complexity:
                stats = by_complexity[comp_name]
                row[f'{csv_prefix}_tests'] = stats['total']
                row[f'{csv_prefix}_passed'] = stats['passed']
                row[f'{csv_prefix}_success_rate'] = round(stats['passed']/stats['total']*100, 1) if stats['total'] > 0 else 0
                row[f'{csv_prefix}_avg_sim'] = round(stats['avg_sim'], 2)
            else:
                row[f'{csv_prefix}_tests'] = 0
                row[f'{csv_prefix}_passed'] = 0
                row[f'{csv_prefix}_success_rate'] = 0
                row[f'{csv_prefix}_avg_sim'] = 0
        
        writer.writerow(row)

def update_system_prompt(new_prompt: str) -> str:
    """Update the global system prompt."""
    global current_system_prompt
    if new_prompt.strip():
        current_system_prompt = new_prompt
        return f"✅ System Prompt עודכן בהצלחה!\n\nהפרומפט החדש:\n{new_prompt[:200]}..."
    else:
        return "❌ שגיאה: System Prompt לא יכול להיות ריק"

def download_csv() -> str:
    """Return the path to the CSV file for download."""
    csv_file = "test_cases.csv"
    if os.path.exists(csv_file):
        return csv_file
    else:
        return None

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
        
        with gr.Tab("⚙️ הגדרות System Prompt"):
            gr.Markdown("### ערוך את ה-System Prompt")
            gr.Markdown("כאן תוכל לשנות את ההוראות שה-AI מקבל לפני כל תרגום")
            
            with gr.Row():
                with gr.Column():
                    system_prompt_input = gr.Textbox(
                        label="System Prompt",
                        value=DEFAULT_SYSTEM_PROMPT,
                        lines=15,
                        placeholder="הכנס את ה-System Prompt החדש כאן...",
                        rtl=True
                    )
                    
                    with gr.Row():
                        update_prompt_btn = gr.Button("💾 עדכן System Prompt", variant="primary")
                        reset_prompt_btn = gr.Button("🔄 אפס לברירת מחדל")
                    
                    prompt_status = gr.Markdown()
            
            def reset_prompt():
                global current_system_prompt
                current_system_prompt = DEFAULT_SYSTEM_PROMPT
                return DEFAULT_SYSTEM_PROMPT, "✅ System Prompt אופס לברירת מחדל"
            
            update_prompt_btn.click(
                fn=update_system_prompt,
                inputs=system_prompt_input,
                outputs=prompt_status
            )
            
            reset_prompt_btn.click(
                fn=reset_prompt,
                inputs=None,
                outputs=[system_prompt_input, prompt_status]
            )
        
        with gr.Tab("🧪 בדיקות אוטומטיות"):
            gr.Markdown("### הרץ את כל מקרי הבדיקה מקובץ test_cases.csv")
            gr.Markdown("הבדיקות שוות את הפלט של המודל לפקודות הצפויות ומחשבות אחוז דמיון")
            gr.Markdown("**כל הרצה יוצרת:** קובץ תוצאות מפורט, קובץ סיכום, ומעדכנת סיכום גלובלי")
            
            with gr.Row():
                complexity_dropdown = gr.Dropdown(
                    choices=["הכל", "פשוט", "בינוני", "מורכב"],
                    value="הכל",
                    label="🎚️ סנן לפי רמת מורכבות",
                    interactive=True
                )
            
            test_btn = gr.Button("🚀 הרץ בדיקות", variant="primary", size="lg")
            
            test_output = gr.Markdown(label="תוצאות בדיקות")
            
            with gr.Row():
                results_file_output = gr.File(label="📄 תוצאות מפורטות", visible=True)
                summary_file_output = gr.File(label="📊 סיכום הרצה", visible=True)
                global_file_output = gr.File(label="🌍 סיכום גלובלי", visible=True)
            
            def run_tests_wrapper(complexity):
                return run_all_tests(complexity)
            
            test_btn.click(
                fn=run_tests_wrapper,
                inputs=complexity_dropdown,
                outputs=[test_output, results_file_output, summary_file_output, global_file_output]
            )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
