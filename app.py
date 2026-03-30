import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import base64
from datetime import datetime

# إعداد الصفحة
st.set_page_config(page_title="مخطط المهام الذكي", layout="wide")

def init_connection():
    try:
        # جلب النص المشفر من Secrets وفك التشفير
        b64_creds = st.secrets["service_account_base64"]
        decoded_creds = base64.b64decode(b64_creds).decode("utf-8")
        creds_dict = json.loads(decoded_creds)
        
        # تصحيح المفتاح الخاص لضمان عمله على السيرفر
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # الاتصال بالشيت (تأكد أن الاسم Daily_Tasks صحيح)
        return client.open("Daily_Tasks").sheet1
    except Exception as e:
        st.error(f"❌ فشل الاتصال النهائي: {e}")
        st.stop()

sheet = init_connection()

# --- واجهة المستخدم ---
st.title("🎯 مهامي اليومية")

# إضافة مهمة
with st.form("task_form"):
    task_text = st.text_input("ما هي مهمتك الجديدة؟")
    submit = st.form_submit_button("إضافة")
    if submit and task_text:
        sheet.append_row([datetime.now().strftime("%Y-%m-%d"), task_text, "FALSE"])
        st.success("تمت الإضافة!")
        st.rerun()

# عرض المهام
try:
    data = sheet.get_all_records()
    if data:
        df = pd.DataFrame(data)
        st.write("### قائمة المهام الحالية:")
        for idx, row in df.iterrows():
            is_done = str(row['Status']).upper() == "TRUE"
            if st.checkbox(f"{row['Date']} - {row['Task']}", value=is_done, key=f"chk_{idx}"):
                if not is_done:
                    sheet.update_cell(idx + 2, 3, "TRUE")
                    st.rerun()
            else:
                if is_done:
                    sheet.update_cell(idx + 2, 3, "FALSE")
                    st.rerun()
except:
    st.info("لا توجد مهام مسجلة بعد.")
