import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import os

# --- إعدادات الصفحة ---
st.set_page_config(page_title="مخطط المهام الذكي", page_icon="🎯", layout="wide")

# استايل CSS لتحسين المظهر وتجربة المستخدم
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stCheckbox { 
        font-size: 20px; 
        padding: 12px; 
        border-radius: 12px; 
        background: white; 
        margin-bottom: 8px; 
        box-shadow: 0px 2px 4px rgba(0,0,0,0.05); 
        transition: 0.3s;
    }
    .stCheckbox:hover { box-shadow: 0px 4px 8px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- دالة الاتصال الآمن بـ Google Sheets ---
import base64

def init_connection():
    try:
        creds_info = dict(st.secrets["gcp_service_account"])
        
        # تنظيف شامل للمفتاح من المسافات والأسطر الزائدة
        raw_key = creds_info["private_key"].strip()
        
        # معالجة مشكلة الـ base64 (تأكد أن الطول يقبل القسمة على 4)
        # هذا السطر يحل مشكلة الـ (65 characters) التي تظهر لك
        creds_info["private_key"] = raw_key.replace("\\n", "\n")
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        
        return client.open("Daily_Tasks").sheet1
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال: {e}")
        st.stop()

# تفعيل الاتصال
sheet = init_connection()

# --- دالة جلب ومعالجة البيانات ---
def get_data():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date']).dt.date
    else:
        df = pd.DataFrame(columns=['Date', 'Task', 'Status'])
    return df

# --- واجهة المستخدم الرئيسية ---
st.title("☀️ مخطط يومي ذكي")
st.subheader(f"اليوم: {datetime.now().strftime('%A, %d %B %Y')}")

# --- قسم إضافة مهمة جديدة ---
with st.container():
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        new_task = st.text_input("", placeholder="ما الذي تريد إنجازه اليوم؟", label_visibility="collapsed")
    with col_btn:
        if st.button("➕ إضافة المهمة", use_container_width=True):
            if new_task:
                today = datetime.now().strftime("%Y-%m-%d")
                # إضافة الصف لجوجل شيت (التاريخ، المهمة، الحالة)
                sheet.append_row([today, new_task, "FALSE"])
                st.toast("تم حفظ المهمة بنجاح!", icon='✅')
                st.rerun()

st.divider()

# جلب البيانات المحدثة
df = get_data()

# --- تقسيم الصفحة للمتابعة والتحليل ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown("### 📝 مهام اليوم")
    today_date = datetime.now().date()
    # تصفية المهام لتظهر مهام اليوم فقط
    today_tasks = df[df['Date'] == today_date] if not df.empty else pd.DataFrame()

    if not today_tasks.empty:
        for index, row in today_tasks.iterrows():
            current_status = str(row['Status']).upper() == "TRUE"
            
            # عرض المهمة مع Checkbox
            checked = st.checkbox(row['Task'], value=current_status, key=f"task_{index}")
            
            # إذا تغيرت الحالة، نحدث جوجل شيت فوراً
            if checked != current_status:
                # ترتيب الصف = الفهرس في الباندا + 2 (لأن جوجل يبدأ بـ 1 ولدينا صف عناوين)
                real_row_in_sheet = index + 2
                sheet.update_cell(real_row_in_sheet, 3, str(checked).upper())
                st.rerun()
    else:
        st.info("قائمة اليوم فارغة. أضف مهامك لتبدأ الإنجاز!")

with col_right:
    st.markdown("### 📊 ملخص الأداء")
    if not df.empty:
        # حساب إحصائيات آخر 7 أيام
        last_7_days = datetime.now().date() - timedelta(days=7)
        weekly_df = df[df['Date'] >= last_7_days]
        
        done = (weekly_df['Status'].astype(str).str.upper() == "TRUE").sum()
        total = len(weekly_df)
        
        st.metric("مهام مكتملة (أسبوعياً)", f"{done} من {total}")
        
        progress = (done / total) if total > 0 else 0
        st.progress(progress)
        
        if progress == 1 and total > 0:
            st.balloons()
            st.success("أنت بطل! أتممت كل مهام الأسبوع!")
    
    st.markdown("---")
    st.markdown("### 📅 آخر المهام المضافة")
    if not df.empty:
        # عرض آخر 5 مهام زمنياً
        history = df.sort_values(by=['Date'], ascending=False).head(5)
        for _, h_row in history.iterrows():
            status_icon = "✅" if str(h_row['Status']).upper() == "TRUE" else "⏳"
            st.caption(f"{status_icon} {h_row['Date'].strftime('%d/%m')} - {h_row['Task']}")
