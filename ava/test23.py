import re
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime
import os

source_excel = "./source_excel"
source_csv = "./source_csv"

def load_alldata(path):
    try:
        csv_files = [f for f in os.listdir(path) if f.endswith(".csv")]
        df_list = []
        for file in csv_files:
            file_path = os.path.join(path, file)
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
    
        #output_path = os.path.join("source_excel", "event.xlsx")  # บันทึกในโฟลเดอร์ "output_folder"
        #df_combined.to_excel(output_path, index=False)
        return df_combined
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการโหลดไฟล์: {e}")
        return None


if __name__ == "__main__":
    df = load_alldata(source_csv)
    st.write(df)