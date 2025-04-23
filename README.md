# Dialysis Diet Planner
A Streamlit app for dialysis patients to plan and track meals, with meal templates and nutrient tracking.

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Add `NotoSansArabic-Regular.ttf` for PDF exports.
3. Create `.env` with `DB_PATH=meal_logs.db`.
4. Run: `streamlit run appp.py`

## Deployment
- Use Streamlit Cloud or Heroku.
- Set `DB_PATH` in the hosting platform.
- Ensure `meal_logs.db` is writable.
