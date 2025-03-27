import re
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime
import os

# 🔹 กำหนดพาธ
input_folder = r"D:\Develop\scada\ava\source_csv"
output_file = r"D:\Develop\scada\ava\source_csv\combined_output.csv"

def combine_csv(input_folder, output_file):
    try:
        # ตรวจสอบว่าโฟลเดอร์มีอยู่จริง
        if not os.path.exists(input_folder):
            st.write(f"❌ โฟลเดอร์ {input_folder} ไม่พบ")
            return
        
        # หาไฟล์ CSV ด้วย os.scandir()
        csv_files = [entry.path for entry in os.scandir(input_folder) if entry.is_file() and entry.name.endswith(".csv")]

        if not csv_files:
            st.write("❌ ไม่มีไฟล์ CSV ในโฟลเดอร์ที่ระบุ")
            return

        df_list = []

        for file_path in csv_files:
            try:
                df = pd.read_csv(file_path, skiprows=6)  # ปรับ skiprows ตามต้องการ
                if df.empty:
                    print(f"⚠️ ไฟล์ {file_path} ว่างเปล่า!")
                else:
                    df_list.append(df)
            except Exception as e:
                print(f"❌ ไม่สามารถอ่านไฟล์ {file_path}: {e}")

        if df_list:
            df_combined = pd.concat(df_list, ignore_index=True)
            df_combined.to_csv(output_file, index=False)
            st.write(f"✅ รวมไฟล์สำเร็จ! บันทึกที่ {output_file}")
        else:
            st.write("❌ ไม่มีข้อมูลที่สามารถรวมได้")

    except Exception as e:
        st.write(f"เกิดข้อผิดพลาด: {e}")

if __name__ == "__main__":
    df = combine_csv(input_folder, output_file)
    if df is not None:
        st.write(df)