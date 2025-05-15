import pandas as pd
import streamlit as st
from fuzzywuzzy import process

# โหลดข้อมูล
file_path = "ava.xlsx"  # เปลี่ยนเป็น path ของไฟล์คุณ
df = pd.read_excel(file_path)

event = ["Remote unit state changed from Online to Telemetry Failure.",
         "Remote unit state changed from Online to Connecting.",
         "Remote unit state changed from Online to Initializing.",
         "Remote unit state changed from Online to Offline.",
         "Remote unit state changed from Telemetry Failure to Online.",
         "Remote unit state changed from Telemetry Failure to Connecting.",
         "Remote unit state changed from Telemetry Failure to Offline.",
         "Remote unit state changed from Telemetry Failure to Initializing.",
         "Remote unit state changed from Connecting to Initializing.",
         "Remote unit state changed from Connecting to Offline.",
         "Remote unit state changed from Initializing to Connecting.",
         "Remote unit state changed from Initializing to Online.",
         "Remote unit state changed from Initializing to Offline.",
         "Remote unit state changed from Offline to Connecting."]

# แสดงข้อความที่มีอยู่จริงในไฟล์
st.write("🔍 Checking unique messages in dataset:")
for msg in df["Message"].dropna().unique():
    st.write(f"👉 '{msg}'")

# ฟังก์ชันจับคู่ข้อความ
def get_best_match(message, choices, threshold=80):
    match = process.extractOne(message, choices)
    return match[0] if match and match[1] >= threshold else None

df["Best Match"] = df["Message"].apply(lambda x: get_best_match(x, event))

# กรองเฉพาะข้อความที่มีการจับคู่
df_filtered = df[df["Best Match"].notna()].copy()

# แปลงเวลาจาก String เป็น datetime
df_filtered["Field change time"] = pd.to_datetime(df_filtered["Field change time"], errors="coerce")

# แยก State ก่อนหน้าและหลังการเปลี่ยนแปลง
df_filtered[["Previous State", "Next State"]] = df_filtered["Message"].str.extract(r'from (.+) to (.+)')

# ลบค่า NaN
df_filtered = df_filtered.dropna(subset=["Previous State", "Next State"])
df_filtered = df_filtered.sort_values("Field change time")

# คำนวณ Duration
df_filtered["Duration"] = df_filtered.groupby(["Previous State", "Next State"])["Field change time"].diff().dt.total_seconds()
df_filtered = df_filtered.dropna(subset=["Duration"])

# แสดงผลลัพธ์
st.write(df_filtered)
