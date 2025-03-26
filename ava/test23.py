import re
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime
import os

# 📂 ระบุโฟลเดอร์ที่เก็บไฟล์ CSV (เปลี่ยนเป็น path ของคุณ)
source_excel = r"D:\Develop\scada\ava\source_excel"
source_csv = r"D:\Develop\scada\ava\source_csv"

#csv_folder = "./csv_files"  # เปลี่ยนตามที่ใช้จริง
csv_files = [f for f in os.listdir(source_csv) if f.endswith(".csv")]

df_list = []
for file in csv_files:
    file_path = os.path.join(source_csv, file)
    
    # ลองอ่านไฟล์ CSV ทีละไฟล์
    df = pd.read_csv(file_path, skiprows=6)
    
    if df.empty:
        st.write(f"⚠️ ไฟล์ {file} ว่างเปล่า! ข้ามไฟล์นี้ไป")
    else:
        df_list.append(df)

# ตรวจสอบว่ามี DataFrame ที่ไม่ว่างเปล่าหรือไม่ก่อน concat
if df_list:
    df_combined = pd.concat(df_list, ignore_index=True)
else:
    st.write("❌ ไม่มีข้อมูลในไฟล์ CSV ที่อ่านได้")

output_path = os.path.join("source_excel", "event.xlsx")  # บันทึกในโฟลเดอร์ "output_folder"
df_combined.to_excel(output_path, index=False)

def load_alldata(file_path):
    try:
        # อ่านไฟล์ทั้งหมดพร้อมข้าม 7 แถวแรก
        df_list = [pd.read_excel(file, skiprows=7) for file in excel_files]
        df_combined = pd.concat(df_list, ignore_index=True)  # รวมเป็น DataFrame เดียว
        return df_combined
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการโหลดไฟล์: {e}")
        return None

if __name__ == "__main__":
    #df = load_alldata(excel_files)
    st.write(df_combined.head())