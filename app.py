import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import sqlite3
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import uuid
import os
import logging
from dotenv import load_dotenv
import json

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    filename='logs/app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
DB_PATH = os.getenv('DB_PATH', 'meal_logs.db')

# Register Arabic font for PDF
try:
    pdfmetrics.registerFont(TTFont('NotoSansArabic', 'NotoSansArabic-Regular.ttf'))
except Exception as e:
    logger.error(f"Failed to load font: {e}")
    st.error("خطأ في تحميل الخط العربي. تأكد من وجود ملف NotoSansArabic-Regular.ttf.")

# Simulated nutritional data
food_data = {
    "البروتينات": [
        ("صدر دجاج مشوي", ["بروتين عالي", "فوسفور منخفض"], {"protein": 31, "potassium": 220, "phosphorus": 210, "calories": 165}),
        ("بياض البيض", ["بروتين عالي", "بوتاسيوم منخفض"], {"protein": 3.6, "potassium": 54, "phosphorus": 15, "calories": 17}),
        ("سمك التونة المعلب", ["بروتين عالي"], {"protein": 26, "potassium": 200, "phosphorus": 180, "calories": 120}),
        ("سردين", ["بروتين عالي"], {"protein": 25, "potassium": 397, "phosphorus": 490, "calories": 208}),
        ("لحم بقر طازج", ["بروتين عالي"], {"protein": 26, "potassium": 318, "phosphorus": 200, "calories": 250}),
        ("أسماك أخرى طازجة", ["بروتين عالي"], {"protein": 22, "potassium": 350, "phosphorus": 250, "calories": 140}),
    ],
    "خضروات منخفضة البوتاسيوم": [
        ("خس", ["بوتاسيوم منخفض"], {"protein": 1.4, "potassium": 194, "phosphorus": 20, "calories": 15}),
        ("خيار", ["بوتاسيوم منخفض"], {"protein": 0.7, "potassium": 147, "phosphorus": 24, "calories": 16}),
        ("بصل", ["بوتاسيوم منخفض"], {"protein": 1.1, "potassium": 146, "phosphorus": 29, "calories": 40}),
        ("باذنجان", ["بوتاسيوم منخفض"], {"protein": 1, "potassium": 229, "phosphorus": 24, "calories": 25}),
        ("فلفل رومي", ["بوتاسيوم منخفض"], {"protein": 1, "potassium": 211, "phosphorus": 26, "calories": 31}),
        ("قرنبيط", ["بوتاسيوم منخفض"], {"protein": 1.9, "potassium": 299, "phosphorus": 44, "calories": 25}),
        ("ملفوف", ["بوتاسيوم منخفض"], {"protein": 1.3, "potassium": 170, "phosphorus": 26, "calories": 25}),
        ("كرفس", ["بوتاسيوم منخفض"], {"protein": 0.7, "potassium": 260, "phosphorus": 24, "calories": 16}),
    ],
    "فواكه منخفضة البوتاسيوم": [
        ("تفاح", ["بوتاسيوم منخفض"], {"protein": 0.3, "potassium": 107, "phosphorus": 11, "calories": 52}),
        ("توت", ["بوتاسيوم منخفض"], {"protein": 1.4, "potassium": 77, "phosphorus": 22, "calories": 57}),
        ("عنب", ["بوتاسيوم منخفض"], {"protein": 0.7, "potassium": 191, "phosphorus": 20, "calories": 69}),
        ("أناناس", ["بوتاسيوم منخفض"], {"protein": 0.5, "potassium": 109, "phosphorus": 8, "calories": 50}),
        ("برقوق", ["بوتاسيوم منخفض"], {"protein": 0.7, "potassium": 157, "phosphorus": 16, "calories": 46}),
        ("شمام", ["بوتاسيوم منخفض"], {"protein": 0.8, "potassium": 267, "phosphorus": 15, "calories": 34}),
    ],
    "الكربوهيدرات والحبوب": [
        ("خبز أبيض", ["فوسفور منخفض"], {"protein": 3.2, "potassium": 115, "phosphorus": 99, "calories": 77}),
        ("أرز أبيض", ["فوسفور منخفض"], {"protein": 2.7, "potassium": 35, "phosphorus": 43, "calories": 130}),
        ("مكرونة", ["فوسفور منخفض"], {"protein": 5, "potassium": 44, "phosphorus": 58, "calories": 131}),
        ("مقرمشات الذرة", ["فوسفور منخفض"], {"protein": 1, "potassium": 36, "phosphorus": 30, "calories": 110}),
        ("رقائق التورتيلا غير مملحة", ["صوديوم منخفض"], {"protein": 2, "potassium": 100, "phosphorus": 140, "calories": 140}),
    ],
    "معززات النكهة": [
        ("ليمون", ["صوديوم منخفض"], {"protein": 1.1, "potassium": 138, "phosphorus": 16, "calories": 29}),
        ("ثوم", ["صوديوم منخفض"], {"protein": 6.4, "potassium": 401, "phosphorus": 153, "calories": 149}),
        ("بصل", ["صوديوم منخفض"], {"protein": 1.1, "potassium": 146, "phosphorus": 29, "calories": 40}),
        ("كزبرة", ["صوديوم منخفض"], {"protein": 2.1, "potassium": 521, "phosphorus": 48, "calories": 23}),
        ("شبت", ["صوديوم منخفض"], {"protein": 3.5, "potassium": 738, "phosphorus": 66, "calories": 43}),
        ("زعتر", ["صوديوم منخفض"], {"protein": 5.6, "potassium": 609, "phosphorus": 106, "calories": 101}),
        ("إكليل الجبل", ["صوديوم منخفض"], {"protein": 3.3, "potassium": 668, "phosphorus": 66, "calories": 131}),
    ]
}

# Meal plan templates
meal_templates = {
    "يوم غسيل الكلى القياسي": {
        "الإفطار": [
            {"food": "بياض البيض", "category": "البروتينات", "portion": 100},
            {"food": "خبز أبيض", "category": "الكربوهيدرات والحبوب", "portion": 50},
            {"food": "تفاح", "category": "فواكه منخفضة البوتاسيوم", "portion": 100}
        ],
        "الغداء": [
            {"food": "صدر دجاج مشوي", "category": "البروتينات", "portion": 100},
            {"food": "أرز أبيض", "category": "الكربوهيدرات والحبوب", "portion": 100},
            {"food": "خس", "category": "خضروات منخفضة البوتاسيوم", "portion": 50}
        ],
        "العشاء": [
            {"food": "سمك التونة المعلب", "category": "البروتينات", "portion": 100},
            {"food": "ملفوف", "category": "خضروات منخفضة البوتاسيوم", "portion": 50},
            {"food": "ليمون", "category": "معززات النكهة", "portion": 10}
        ]
    },
    "يوم منخفض السعرات": {
        "الإفطار": [
            {"food": "بياض البيض", "category": "البروتينات", "portion": 50},
            {"food": "توت", "category": "فواكه منخفضة البوتاسيوم", "portion": 100}
        ],
        "الغداء": [
            {"food": "صدر دجاج مشوي", "category": "البروتينات", "portion": 80},
            {"food": "خيار", "category": "خضروات منخفضة البوتاسيوم", "portion": 100}
        ],
        "العشاء": [
            {"food": "سمك التونة المعلب", "category": "البروتينات", "portion": 80},
            {"food": "قرنبيط", "category": "خضروات منخفضة البوتاسيوم", "portion": 50}
        ]
    },
    "يوم عالي البروتين": {
        "الإفطار": [
            {"food": "بياض البيض", "category": "البروتينات", "portion": 150},
            {"food": "خبز أبيض", "category": "الكربوهيدرات والحبوب", "portion": 50}
        ],
        "الغداء": [
            {"food": "صدر دجاج مشوي", "category": "البروتينات", "portion": 150},
            {"food": "أرز أبيض", "category": "الكربوهيدرات والحبوب", "portion": 100},
            {"food": "فلفل رومي", "category": "خضروات منخفضة البوتاسيوم", "portion": 50}
        ],
        "العشاء": [
            {"food": "لحم بقر طازج", "category": "البروتينات", "portion": 100},
            {"food": "ملفوف", "category": "خضروات منخفضة البوتاسيوم", "portion": 50}
        ]
    }
}

# Recommended daily intake for dialysis patients
DRI = {
    "protein": 60,  # g
    "potassium": 2000,  # mg
    "phosphorus": 800,  # mg
    "calories": 2000  # kcal
}

# SQLite database setup
try:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS meal_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'guest',
            date TEXT,
            foods TEXT,
            protein REAL,
            potassium REAL,
            phosphorus REAL,
            calories REAL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS shared_plans (
            id TEXT PRIMARY KEY,
            user_id TEXT DEFAULT 'guest',
            foods TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
except Exception as e:
    logger.error(f"Database setup failed: {e}")
    st.error("خطأ في إعداد قاعدة البيانات. تحقق من مسار قاعدة البيانات.")

# Initialize session state
if 'selected_foods' not in st.session_state:
    st.session_state.selected_foods = []

# Main app
st.set_page_config(page_title="قائمة الأطعمة لمرضى غسيل الكلى", layout="wide")
st.markdown("""
    <style>
    body, h1, h2, h3, h4, h5, h6, p, div, span, input, select, button {
        font-family: 'Noto Sans Arabic', sans-serif !important;
        direction: rtl;
        background-color: #ffffff;
        color: #000000;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: #ffffff;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    @media (max-width: 600px) {
        .stColumn {
            width: 100% !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar for filters
with st.sidebar:
    st.header("🔍 خيارات التصفية")
    all_tags = sorted(set(tag for items in food_data.values() for _, tags, _ in items for tag in tags))
    selected_tags = st.multiselect("فلترة حسب الخصائص الغذائية:", all_tags, help="اختر الخصائص المناسبة لنظامك الغذائي")
    search_query = st.text_input("ابحث عن طعام:", placeholder="أدخل اسم الطعام (مثل: تفاح، دجاج)")

# Tabs for workflow
tab1, tab2, tab3 = st.tabs(["اختيار الأطعمة", "خطة النظام الغذائي", "تتبع الوجبات"])

with tab1:
    st.header("اختيار الأطعمة")
    # Meal plan template selection
    st.subheader("تحميل نموذج خطة وجبات")
    template_name = st.selectbox("اختر نموذج خطة وجبات:", ["لا شيء"] + list(meal_templates.keys()))
    if template_name != "لا شيء" and st.button("تحميل النموذج"):
        st.session_state.selected_foods = []
        try:
            for meal, foods in meal_templates[template_name].items():
                for item in foods:
                    for cat, cat_items in food_data.items():
                        for food, tags, nutrients in cat_items:
                            if food == item["food"] and cat == item["category"]:
                                food_info = {
                                    "food": food,
                                    "category": cat,
                                    "portion": item["portion"] / 100,
                                    "protein": nutrients["protein"] * (item["portion"] / 100),
                                    "potassium": nutrients["potassium"] * (item["portion"] / 100),
                                    "phosphorus": nutrients["phosphorus"] * (item["portion"] / 100),
                                    "calories": nutrients["calories"] * (item["portion"] / 100),
                                    "tags": tags
                                }
                                st.session_state.selected_foods.append(food_info)
            logger.info(f"Guest user loaded template {template_name}")
            st.success(f"تم تحميل نموذج {template_name}!")
        except Exception as e:
            logger.error(f"Template loading failed: {e}")
            st.error("خطأ في تحميل النموذج.")

    # Manual food selection
    for category, items in food_data.items():
        with st.expander(f"{category}", expanded=True):
            for food, tags, nutrients in items:
                if (not selected_tags or all(tag in tags for tag in selected_tags)) and (not search_query or search_query.lower() in food.lower()):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.markdown(f"**{food}** — _{'، '.join(tags)}_")
                    with col2:
                        portion = st.number_input(
                            f"الكمية (جم) لـ {food}",
                            min_value=0.0, max_value=500.0, value=100.0, step=10.0,
                            key=f"portion_{food}_{category}"
                        )
                    with col3:
                        if st.button("إضافة", key=f"add_{food}_{category}"):
                            if portion <= 0:
                                st.error("يرجى إدخال كمية صالحة (أكبر من 0).")
                            else:
                                food_info = {
                                    "food": food,
                                    "category": category,
                                    "portion": portion / 100,
                                    "protein": nutrients["protein"] * (portion / 100),
                                    "potassium": nutrients["potassium"] * (portion / 100),
                                    "phosphorus": nutrients["phosphorus"] * (portion / 100),
                                    "calories": nutrients["calories"] * (portion / 100),
                                    "tags": tags
                                }
                                st.session_state.selected_foods.append(food_info)
                                logger.info(f"Guest user added food {food}")
                                st.success(f"تمت إضافة {food}")

    # Display selected foods
    if st.session_state.selected_foods:
        st.subheader("الأطعمة المختارة")
        df_selected = pd.DataFrame(st.session_state.selected_foods)
        st.dataframe(df_selected[["food", "category", "portion", "protein", "potassium", "phosphorus", "calories"]].rename(columns={
            "food": "الطعام",
            "category": "الفئة",
            "portion": "الكمية (100 جم)",
            "protein": "البروتين (جم)",
            "potassium": "البوتاسيوم (ملجم)",
            "phosphorus": "الفوسفور (ملجم)",
            "calories": "السعرات (كيلو كالوري)"
        }))

        # Remove selected foods
        for food in st.session_state.selected_foods:
            if st.button(f"إزالة {food['food']}", key=f"remove_{food['food']}_{food['category']}"):
                st.session_state.selected_foods = [f for f in st.session_state.selected_foods if f['food'] != food['food'] or f['category'] != food['category']]
                logger.info(f"Guest user removed food {food['food']}")
                st.rerun()

with tab2:
    st.header("خطة النظام الغذائي")
    if not st.session_state.selected_foods:
        st.warning("يرجى اختيار أطعمة من علامة التبويب السابقة.")
    else:
        df_selected = pd.DataFrame(st.session_state.selected_foods)
        
        # Calculate totals
        total_protein = df_selected["protein"].sum()
        total_potassium = df_selected["potassium"].sum()
        total_phosphorus = df_selected["phosphorus"].sum()
        total_calories = df_selected["calories"].sum()

        # Nutrient recommendations AI
        recommendations = []
        if total_protein < DRI["protein"] * 0.8:
            recommendations.append("زيادة تناول البروتين! جرب إضافة صدر دجاج مشوي أو بياض البيض.")
        if total_potassium > DRI["potassium"] * 0.9:
            recommendations.append("تقليل البوتاسيوم! تجنب أطعمة مثل ثوم أو شبت، واختر خس أو خيار.")
        if total_phosphorus > DRI["phosphorus"] * 0.9:
            recommendations.append("تقليل الفوسفور! قلل من أطعمة مثل سردين، واختر خبز أبيض.")
        if total_calories < DRI["calories"] * 0.8:
            recommendations.append("زيادة السعرات! أضف أرز أبيض أو مكرونة إلى وجباتك.")

        # Display nutrient progress with recommendations
        st.subheader("ملخص التغذية")
        cols = st.columns(4)
        with cols[0]:
            st.metric("البروتين", f"{total_protein:.1f} جم", f"{total_protein/DRI['protein']*100:.1f}% من الحد اليومي")
            if total_protein > DRI["protein"]:
                st.warning("تحذير: تجاوزت كمية البروتين الحد اليومي! قلل من أطعمة مثل لحم بقر طازج.")
        with cols[1]:
            st.metric("البوتاسيوم", f"{total_potassium:.1f} ملجم", f"{total_potassium/DRI['potassium']*100:.1f}% من الحد اليومي")
            if total_potassium > DRI["potassium"]:
                st.warning("تحذير: تجاوزت كمية البوتاسيوم الحد اليومي! تجنب أطعمة مثل ثوم أو شبت.")
        with cols[2]:
            st.metric("الفوسفور", f"{total_phosphorus:.1f} ملجم", f"{total_phosphorus/DRI['phosphorus']*100:.1f}% من الحد اليومي")
            if total_phosphorus > DRI["phosphorus"]:
                st.warning("تحذير: تجاوزت كمية الفوسفور الحد اليومي! قلل من أطعمة مثل سردين.")
        with cols[3]:
            st.metric("السعرات", f"{total_calories:.1f} كيلو كالوري", f"{total_calories/DRI['calories']*100:.1f}% من الحد اليومي")

        if recommendations:
            st.subheader("توصيات التغذية")
            for rec in recommendations:
                st.info(rec)

        # Nutrient distribution chart
        st.subheader("توزيع العناصر الغذائية")
        nutrient_data = pd.DataFrame({
            "العنصر": ["البروتين", "البوتاسيوم", "الفوسفور", "السعرات"],
            "القيمة": [total_protein, total_potassium / 100, total_phosphorus / 100, total_calories / 100]
        })
        fig = px.pie(nutrient_data, values='القيمة', names='العنصر', title='توزيع العناصر الغذائية')
        st.plotly_chart(fig, use_container_width=True)

        # Save meal plan to database
        if st.button("حفظ الخطة الغذائية لليوم"):
            try:
                foods_json = df_selected.to_json(orient='records', force_ascii=False)
                c.execute('''
                    INSERT INTO meal_logs (user_id, date, foods, protein, potassium, phosphorus, calories)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    "guest",
                    datetime.datetime.now().strftime('%Y-%m-%d'),
                    foods_json,
                    total_protein,
                    total_potassium,
                    total_phosphorus,
                    total_calories
                ))
                conn.commit()
                logger.info("Guest user saved meal plan")
                st.success("تم حفظ الخطة الغذائية بنجاح!")
                st.session_state.selected_foods = []
                st.rerun()
            except Exception as e:
                logger.error(f"Meal plan save failed: {e}")
                st.error("خطأ في حفظ الخطة الغذائية.")

        # Share meal plan
        if st.button("مشاركة الخطة الغذائية"):
            try:
                share_id = str(uuid.uuid4())
                foods_json = df_selected.to_json(orient='records', force_ascii=False)
                c.execute('INSERT INTO shared_plans (id, user_id, foods, created_at) VALUES (?, ?, ?, ?)',
                          (share_id, "guest", foods_json, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                conn.commit()
                share_url = f"https://your-app-url/share/{share_id}"  # Replace with actual deployment URL
                logger.info(f"Guest user shared meal plan {share_id}")
                st.success(f"تم إنشاء رابط المشاركة: {share_url}")
            except Exception as e:
                logger.error(f"Meal plan sharing failed: {e}")
                st.error("خطأ في مشاركة الخطة الغذائية.")

        # Download options
        csv = df_selected.to_csv(index=False)
        st.download_button("تنزيل الخطة كملف CSV", csv, f"خطة_غذائية_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv")

        # PDF export
        try:
            buffer = io.BytesIO()
            c_pdf = canvas.Canvas(buffer, pagesize=letter)
            c_pdf.setFont("NotoSansArabic", 12)
            c_pdf.drawString(500, 750, "خطة النظام الغذائي")
            y = 700
            for _, row in df_selected.iterrows():
                c_pdf.drawString(500, y, f"{row['food']} ({row['portion']*100} جم): {row['calories']:.1f} كيلو كالوري")
                y -= 20
            c_pdf.save()
            buffer.seek(0)
            st.download_button("تنزيل الخطة كملف PDF", buffer, f"خطة_غذائية_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", "application/pdf")
        except Exception as e:
            logger.error(f"PDF export failed: {e}")
            st.error("خطأ في تصدير PDF.")

with tab3:
    st.header("تتبع الوجبات")
    # Date range selection
    st.subheader("تحديد الفترة الزمنية")
    period = st.selectbox("اختر الفترة:", ["يومي", "أسبوعي", "شهري"])
    selected_date = st.date_input("اختر التاريخ أو نطاق التاريخ:", value=datetime.datetime.now())

    # Fetch meal logs
    try:
        if period == "يومي":
            query_date = selected_date.strftime('%Y-%m-%d')
            c.execute('SELECT * FROM meal_logs WHERE user_id = ? AND date = ?', ("guest", query_date))
        elif period == "أسبوعي":
            start_date = selected_date - datetime.timedelta(days=selected_date.weekday())
            end_date = start_date + datetime.timedelta(days=6)
            c.execute('SELECT * FROM meal_logs WHERE user_id = ? AND date BETWEEN ? AND ?',
                      ("guest", start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        else:  # شهري
            start_date = selected_date.replace(day=1)
            end_date = (start_date + datetime.timedelta(days=31)).replace(day=1) - datetime.timedelta(days=1)
            c.execute('SELECT * FROM meal_logs WHERE user_id = ? AND date BETWEEN ? AND ?',
                      ("guest", start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        
        logs = c.fetchall()
    except Exception as e:
        logger.error(f"Meal log fetch failed: {e}")
        st.error("خطأ في جلب سجلات الوجبات.")

    if not logs:
        st.warning("لا توجد سجلات وجبات للفترة المحددة.")
    else:
        # Process logs
        log_data = []
        for log in logs:
            foods_df = pd.read_json(log[3], orient='records')
            log_data.append({
                "date": log[2],
                "protein": log[4],
                "potassium": log[5],
                "phosphorus": log[6],
                "calories": log[7],
                "foods": foods_df
            })
        
        # Display summary
        st.subheader(f"سجل الوجبات ({period})")
        df_logs = pd.DataFrame([(log['date'], log['protein'], log['potassium'], log['phosphorus'], log['calories']) for log in log_data],
                               columns=["التاريخ", "البروتين (جم)", "البوتاسيوم (ملجم)", "الفوسفور (ملجم)", "السعرات (كيلو كالوري)"])
        st.dataframe(df_logs)

        # Nutrient trends chart
        st.subheader("اتجاهات العناصر الغذائية")
        trend_data = pd.DataFrame({
            "التاريخ": [log['date'] for log in log_data],
            "البروتين": [log['protein'] for log in log_data],
            "البوتاسيوم": [log['potassium'] / 100 for log in log_data],
            "الفوسفور": [log['phosphorus'] / 100 for log in log_data],
            "السعرات": [log['calories'] / 100 for log in log_data]
        })
        fig_trend = px.line(trend_data, x="التاريخ", y=["البروتين", "البوتاسيوم", "الفوسفور", "السعرات"],
                            title="اتجاهات العناصر الغذائية عبر الوقت")
        st.plotly_chart(fig_trend, use_container_width=True)

        # Detailed food logs
        st.subheader("تفاصيل الوجبات")
        for log in log_data:
            st.write(f"**التاريخ: {log['date']}**")
            st.dataframe(log['foods'][["food", "category", "portion", "protein", "potassium", "phosphorus", "calories"]].rename(columns={
                "food": "الطعام",
                "category": "الفئة",
                "portion": "الكمية (100 جم)",
                "protein": "البروتين (جم)",
                "potassium": "البوتاسيوم (ملجم)",
                "phosphorus": "الفوسفور (ملجم)",
                "calories": "السعرات (كيلو كالوري)"
            }))

        # Export logs
        try:
            csv_logs = df_logs.to_csv(index=False)
            st.download_button("تنزيل سجل الوجبات كملف CSV", csv_logs, f"سجل_وجبات_{period}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv")

            buffer = io.BytesIO()
            c_pdf = canvas.Canvas(buffer, pagesize=letter)
            c_pdf.setFont("NotoSansArabic", 12)
            c_pdf.drawString(500, 750, f"سجل الوجبات ({period})")
            y = 700
            for log in log_data:
                c_pdf.drawString(500, y, f"التاريخ: {log['date']}")
                y -= 20
                for _, row in log['foods'].iterrows():
                    c_pdf.drawString(500, y, f"{row['food']} ({row['portion']*100} جم): {row['calories']:.1f} كيلو كالوري")
                    y -= 20
                y -= 10
            c_pdf.save()
            buffer.seek(0)
            st.download_button("تنزيل سجل الوجبات كملف PDF", buffer, f"سجل_وجبات_{period}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", "application/pdf")
        except Exception as e:
            logger.error(f"Log export failed: {e}")
            st.error("خطأ في تصدير سجل الوجبات.")

# Close database connection
try:
    conn.close()
except Exception as e:
    logger.error(f"Database connection close failed: {e}")