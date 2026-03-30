import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def init_connection():
    try:
        # جلب البيانات
        creds_dict = dict(st.secrets["gcp_service_account"])
        
        # الحل السحري: تنظيف المفتاح وإعادة بناء الأسطر
        p_key = creds_dict["private_key"]
        if "\\n" in p_key:
            p_key = p_key.replace("\\n", "\n")
        
        # التأكد من عدم وجود مسافات خفية في البداية أو النهاية
        creds_dict["private_key"] = p_key.strip()
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        return client.open("Daily_Tasks").sheet1
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال: {e}")
        st.stop()

sheet = init_connection()
st.success("✅ تم الاتصال بنجاح! جاري تحميل المهام...")
