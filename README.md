# CLI Agent

Agent שממיר הוראות בשפה טבעית לפקודות CLI של Windows.

## 🚀 התקנה והרצה

### שלב 1: התקן את uv (אם עדיין לא מותקן)

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### שלב 2: התקן תלויות

```bash
uv venv
uv pip install -r requirements.txt
```

### שלב 3: הגדר את מפתח ה-API

צור קובץ `.env` בתיקיית הפרויקט:

```bash
OPENAI_API_KEY=sk-...
```

### שלב 4: הרץ את האפליקציה

```bash
uv run python app.py
```

האפליקציה תהיה זמינה בכתובת: http://localhost:7860

## ⚙️ שינוי System Prompt

הפרומפט נמצא בקובץ `system_prompt.md` בתיקיית הפרויקט.

כדי לשנות אותו — ערוך את הקובץ ועשה deploy מחדש. אין ממשק לעריכה בזמן ריצה.

## 🧪 בדיקות אוטומטיות

### ממשק Gradio

1. הרץ את האפליקציה: `uv run python app.py`
2. עבור לטאב "🧪 בדיקות אוטומטיות"
3. בחר רמת מורכבות (הכל / פשוט / בינוני / מורכב)
4. לחץ על "🚀 הרץ בדיקות"

**כל הרצה יוצרת:**
- קובץ תוצאות מפורט (`results_TIMESTAMP.csv`)
- קובץ סיכום (`summary_TIMESTAMP.txt`)
- עדכון לסיכום גלובלי (`global_summary.csv`)

### שורת פקודה

```bash
uv run python test_runner.py
```

### מבנה קובץ הבדיקות (test_cases.csv)

| עמודה | תיאור | מתעדכן אוטומטית |
|-------|--------|-----------------|
| `input` | ההוראה בשפה טבעית | לא |
| `expected_output` | הפקודה הצפויה | לא |
| `complexity` | רמת מורכבות (פשוט/בינוני/מורכב) | לא |
| `actual_output` | הפקודה שהתקבלה מה-Agent | **כן ✅** |
| `similarity_score` | אחוז הדמיון | **כן ✅** |
| `match_status` | האם עבר/נכשל | **כן ✅** |

### מדדי הצלחה

- ✅ **PASS** — הפקודה זהה או דומה ב-80%+ לפקודה הצפויה
- ❌ **FAIL** — דמיון נמוך מ-80%

## 🔧 העלאה לענן (Render)

1. העלה את הפרויקט ל-GitHub
2. התחבר ל-[Render](https://render.com/) וצור Web Service חדש
3. הגדר את `OPENAI_API_KEY` כמשתנה סביבה
4. הגדר את Start Command: `python app.py`

## 📁 מבנה הפרויקט

```
.
├── app.py                 # אפליקציית Gradio
├── test_runner.py         # סקריפט בדיקות לשורת פקודה
├── system_prompt.md       # System Prompt — ערוך כאן לשינוי התנהגות המודל
├── test_cases.csv         # מקרי בדיקה + תוצאות אוטומטיות
├── requirements.txt       # תלויות Python
├── pyproject.toml         # הגדרות uv
└── README.md
```

## 📝 הערות

- המודל: gpt-4o-mini (מהיר וזול)
- מערכת הבדיקות משתמשת באלגוריתם דמיון מחרוזות (difflib)
- לשינוי הפרומפט — ערוך את `system_prompt.md` ועשה deploy מחדש

## 🎯 זרימת עבודה מומלצת

1. הרץ בדיקות: `uv run python app.py`
2. בדוק את התוצאות — ראה `actual_output` ו-`match_status`
3. זהה דפוסי כשלונות
4. ערוך את `system_prompt.md`
5. עשה deploy והרץ שוב
6. חזור עד לשיפור משמעותי
