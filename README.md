# CLI Agent - MVP שלב א'

Agent שממיר הוראות בשפה טבעית לפקודות CLI של Windows.

## 🚀 התקנה והרצה

### שלב 1: התקן את uv (אם עדיין לא מותקן)

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### שלב 2: צור את הפרויקט והתקן את החבילות

```bash
# צור סביבה וירטואלית והתקן תלויות
uv venv
uv pip install -r requirements.txt
```

### שלב 3: הגדר את מפתח ה-API

1. צור קובץ `.env` בתיקיית הפרויקט
2. העתק את התוכן מ-`.env.example`
3. החלף את `your_openai_api_key_here` במפתח API אמיתי מ-OpenAI

```bash
# .env
OPENAI_API_KEY=sk-...
```

### שלב 4: הרץ את האפליקציה

```bash
# הפעל את האפליקציה
uv run python app.py
```

האפליקציה תהיה זמינה בכתובת: http://localhost:7860

## 🧪 בדיקות אוטומטיות

הפרויקט כולל מערכת בדיקות אוטומטית מובנית עם שתי אפשרויות:

### אפשרות 1: ממשק Gradio (מומלץ)

1. הרץ את האפליקציה: `uv run python app.py`
2. עבור לטאב "🧪 בדיקות אוטומטיות"
3. לחץ על "🚀 הרץ את כל הבדיקות"
4. קבל דוח מפורט עם אחוזי הצלחה, דמיון, ופירוט לכל בדיקה
5. **התוצאות נשמרות אוטומטית ב-CSV** עם עמודות:
   - `actual_output` - הפקודה שהתקבלה מה-Agent
   - `similarity_score` - אחוז הדמיון לפקודה הצפויה
   - `match_status` - האם הבדיקה עברה (✅ PASS) או נכשלה (❌ FAIL)

### אפשרות 2: שורת פקודה

```bash
# הרץ את כל הבדיקות משורת הפקודה
uv run python test_runner.py
```

התוצאות נשמרות אוטומטית ב-`test_cases.csv` עם כל העמודות המעודכנות.

### מבנה קובץ הבדיקות (test_cases.csv)

הקובץ מכיל את העמודות הבאות:

| עמודה | תיאור | מתעדכן אוטומטית |
|-------|--------|-----------------|
| `input` | ההוראה בשפה טבעית | לא |
| `expected_output` | הפקודה הצפויה | לא |
| `category` | קטגוריית הבדיקה | לא |
| `actual_output` | הפקודה שהתקבלה מה-Agent | **כן ✅** |
| `similarity_score` | אחוז הדמיון | **כן ✅** |
| `match_status` | האם עבר/נכשל | **כן ✅** |

### מקרי בדיקה

הקובץ `test_cases.csv` כולל 20 מקרי בדיקה עם:
- הוראות בשפה טבעית
- פקודות צפויות
- קטגוריות (network, file_operations, system_info, וכו')

אתה יכול להוסיף מקרי בדיקה נוספים פשוט על ידי הוספת שורות חדשות ל-CSV.

### מדדי הצלחה

- ✅ **PASS** - הפקודה זהה או דומה ב-80%+ לפקודה הצפויה
- ❌ **FAIL** - דמיון נמוך מ-80%
- המערכת מחשבת גם אחוז הצלחה כולל ודמיון ממוצע

## 📊 עבודה עם תוצאות הבדיקות

לאחר הרצת הבדיקות, ניתן:
1. לפתוח את `test_cases.csv` ב-Excel או Google Sheets
2. לנתח את העמודות `actual_output` ו-`match_status`
3. לזהות דפוסים של כשלונות
4. לשפר את הפרומפט על בסיס התוצאות
5. להשוות בין ריצות שונות

## 🔧 העלאה לענן

### Hugging Face Spaces (מומלץ)

1. צור חשבון ב-[Hugging Face](https://huggingface.co/)
2. צור Space חדש עם Gradio SDK
3. העלה את הקבצים:
   - `app.py`
   - `requirements.txt`
   - `test_cases.csv`
4. הוסף את ה-API Key כ-Secret במקטע Settings

### Google Colab

```python
# התקנה עם uv
!pip install uv
!uv pip install gradio openai python-dotenv

# הרצה
!uv run python app.py
```

### Railway / Render

העלה את הקבצים ל-GitHub והתחבר ל-Railway/Render.
הגדר את `OPENAI_API_KEY` כמשתנה סביבה.

## 📁 מבנה הפרויקט

```
.
├── app.py                 # אפליקציית Gradio עם ממשק בדיקות
├── test_runner.py         # סקריפט בדיקות לשורת פקודה
├── test_cases.csv         # 20 מקרי בדיקה + תוצאות אוטומטיות
├── requirements.txt       # תלויות Python
├── pyproject.toml        # הגדרות uv
├── .env.example          # דוגמה למשתני סביבה
└── README.md             # המדריך הזה
```

## 📝 הערות

- הפרומפט הראשוני פשוט ומכיל 4 דוגמאות בסיסיות
- המודל: gpt-4o-mini (מהיר וזול)
- טמפרטורה נמוכה (0.1) לעקביות
- מערכת הבדיקות משתמשת באלגוריתם דמיון מחרוזות (difflib)
- ניתן בקלות להוסיף מקרי בדיקה נוספים ל-CSV
- **התוצאות נשמרות אוטומטית ב-CSV** - אין צורך בתיעוד ידני!

## 🎯 זרימת עבודה מומלצת

1. הרץ בדיקות ראשוניות: `uv run python app.py`
2. בדוק את `test_cases.csv` - ראה את ה-`actual_output` וה-`match_status`
3. זהה בעיות חוזרות בפלט של המודל
4. שפר את הפרומפט ב-`app.py` ו-`test_runner.py`
5. הרץ שוב והשווה תוצאות
6. חזור על התהליך עד לשיפור משמעותי
