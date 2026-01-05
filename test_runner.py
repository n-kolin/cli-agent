import csv
import os
from typing import List, Dict, Tuple
from openai import OpenAI
from dotenv import load_dotenv
import difflib

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initial prompt (same as in app.py)
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
    """Convert natural language instruction to CLI command using OpenAI API."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            temperature=0.1,
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"


def calculate_similarity(str1: str, str2: str) -> float:
    """Calculate similarity ratio between two strings."""
    return difflib.SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def load_test_cases(csv_file: str = "test_cases.csv") -> List[Dict[str, str]]:
    """Load test cases from CSV file."""
    test_cases = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            test_cases.append(row)
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
    
    print(f"\n✅ תוצאות נשמרו ב-CSV: {csv_file}")


def run_tests(csv_file: str = "test_cases.csv", 
              similarity_threshold: float = 0.8) -> Tuple[List[Dict], Dict[str, any]]:
    """
    Run all tests from CSV file and return results.
    
    Args:
        csv_file: Path to CSV file with test cases
        similarity_threshold: Minimum similarity ratio to consider as pass (0-1)
        
    Returns:
        Tuple of (detailed_results, summary_stats)
    """
    test_cases = load_test_cases(csv_file)
    results = []
    
    print(f"Running {len(test_cases)} tests...\n")
    
    for i, test_case in enumerate(test_cases, 1):
        user_input = test_case['input']
        expected = test_case['expected_output']
        category = test_case.get('category', 'general')
        
        print(f"Test {i}/{len(test_cases)}: {user_input[:50]}...")
        
        # Get actual output from LLM
        actual = convert_to_cli(user_input)
        
        # Calculate similarity
        similarity = calculate_similarity(expected, actual)
        
        # Determine pass/fail
        is_exact_match = expected.lower() == actual.lower()
        is_similar = similarity >= similarity_threshold
        status = "✅ PASS" if is_exact_match or is_similar else "❌ FAIL"
        
        result = {
            'test_number': i,
            'input': user_input,
            'expected': expected,
            'actual': actual,
            'similarity': round(similarity * 100, 2),
            'status': status,
            'category': category,
            'is_exact_match': is_exact_match
        }
        
        results.append(result)
        
        print(f"  Expected: {expected}")
        print(f"  Actual:   {actual}")
        print(f"  Status:   {status} (Similarity: {result['similarity']}%)\n")
    
    # Calculate summary statistics
    total_tests = len(results)
    passed = sum(1 for r in results if r['status'] == '✅ PASS')
    failed = total_tests - passed
    exact_matches = sum(1 for r in results if r['is_exact_match'])
    avg_similarity = sum(r['similarity'] for r in results) / total_tests if total_tests > 0 else 0
    
    # Category breakdown
    categories = {}
    for result in results:
        cat = result['category']
        if cat not in categories:
            categories[cat] = {'total': 0, 'passed': 0}
        categories[cat]['total'] += 1
        if result['status'] == '✅ PASS':
            categories[cat]['passed'] += 1
    
    summary = {
        'total_tests': total_tests,
        'passed': passed,
        'failed': failed,
        'exact_matches': exact_matches,
        'pass_rate': round((passed / total_tests * 100), 2) if total_tests > 0 else 0,
        'avg_similarity': round(avg_similarity, 2),
        'categories': categories,
        'similarity_threshold': similarity_threshold * 100
    }
    
    return results, summary


def print_summary(summary: Dict):
    """Print test summary statistics."""
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total Tests:       {summary['total_tests']}")
    print(f"Passed:            {summary['passed']} ({summary['pass_rate']}%)")
    print(f"Failed:            {summary['failed']}")
    print(f"Exact Matches:     {summary['exact_matches']}")
    print(f"Avg Similarity:    {summary['avg_similarity']}%")
    print(f"Threshold:         {summary['similarity_threshold']}%")
    
    print("\nCategory Breakdown:")
    print("-"*70)
    for category, stats in summary['categories'].items():
        pass_rate = round((stats['passed'] / stats['total'] * 100), 2) if stats['total'] > 0 else 0
        print(f"  {category:20s}: {stats['passed']}/{stats['total']} ({pass_rate}%)")
    
    print("="*70)


if __name__ == "__main__":
    # Run tests
    results, summary = run_tests(
        csv_file="test_cases.csv",
        similarity_threshold=0.8  # 80% similarity to pass
    )
    
    # Save results
    save_results_to_csv(results, csv_file="test_cases.csv")
    
    # Print summary
    print_summary(summary)
    
    # Print failed tests details
    failed_tests = [r for r in results if "FAIL" in r['status']]
    if failed_tests:
        print("\nFAILED TESTS DETAILS:")
        print("-"*70)
        for test in failed_tests:
            print(f"\nTest #{test['test_number']}: {test['input']}")
            print(f"  Expected: {test['expected']}")
            print(f"  Got:      {test['actual']}")
            print(f"  Similarity: {test['similarity']}%")
