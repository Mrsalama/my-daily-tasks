import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import datetime

def init_connection():
    try:
        # قراءة النص من Secrets وتحويله لقاموس بايثون
        info = json.loads(st.secrets["service_account_info"])
        
        # التأكد من معالجة أسطر المفتاح الخاص
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
        client = gspread.authorize(creds)
        
        return client.open("Daily_Tasks").sheet1
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال: {e}")
        st.stop()

sheet = init_connection()

# --- واجهة المستخدم ---
st.title("🎯 مهامي اليومية")

# إضافة مهمة
task_text = st.text_input("أضف مهمة جديدة:")
if st.button("إضافة"):
    if task_text:
        sheet.append_row([datetime.now().strftime("%Y-%m-%d"), task_text, "FALSE"])
        st.success("تم الحفظ!")
        st.rerun()

# عرض المهام الموجودة في الشيت
try:
    data = sheet.get_all_records()
    if data:
        df = pd.DataFrame(data)
        for idx, row in df.iterrows():
            st.write(f"📅 {row['Date']} - 📝 {row['Task']}")
except:
    st.info("لا توجد مهام حالياً.")
