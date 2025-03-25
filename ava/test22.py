import pandas as pd
import streamlit as st

# สร้าง DataFrame หลัก
df_remote = pd.DataFrame({
    "Device ID": ["A1", "B2", "C3"],
    "Availability (%)": [95, 87, 78],
    "จำนวนครั้ง Initializing": [5, 2, 6],
    "ระยะเวลา Initializing (seconds)": [120, 60, 180]
})

# สร้าง DataFrame ที่คำนวณค่าใหม่
device_count_duration = pd.DataFrame({
    "Device ID": ["A1", "B2", "C3"],
    "Availability (%)": [97, 85, 80],  
    "จำนวนครั้ง Initializing": [6, 3, 777],  
    "ระยะเวลา Initializing (seconds)": [130, 70, 190]
})

# ✅ อัปเดตข้อมูลโดยใช้ merge (ให้ df_remote มีข้อมูลใหม่เสมอ)
df_remote = df_remote.merge(device_count_duration, on="Device ID", suffixes=("_old", ""))

# ลบคอลัมน์เก่าที่ไม่ต้องการออก
df_remote.drop(columns=[col for col in df_remote.columns if col.endswith("_old")], inplace=True)

# แสดงข้อมูลที่อัปเดตใน Streamlit
st.write(df_remote)