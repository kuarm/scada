import pandas as pd
import streamlit as st
from fuzzywuzzy import process

# โหลดข้อมูล
file_path = "ava_test.xlsx"  # เปลี่ยนเป็น path ของไฟล์คุณ
df = pd.read_excel(file_path, sheet_name="Sheet4",header=0)
st.write(df)

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

# ตรวจสอบข้อความที่คล้ายกันในไฟล์
#df["Message"] = df["Message"].astype(str).str.strip()
#df["Best Match"] = df["Message"].apply(lambda x: process.extractOne(x, event)[0])

# ดูข้อความที่ใกล้เคียงกัน
#st.write(df[["Message", "Best Match"]].head(20))

# ตรวจสอบค่าทั้งหมดที่อยู่ในคอลัมน์ Message
#st.write("🔍 Checking unique messages in dataset:")
#unique_messages = df["Message"].dropna().unique()
#for msg in unique_messages:
#    st.write(f"👉 '{msg}'")

# ฟังก์ชันจับคู่ข้อความ
def get_best_match(message, choices, threshold=80):
    match = process.extractOne(message, choices)
    return match[0] if match and match[1] >= threshold else None

df["Best Match"] = df["Message"].apply(lambda x: get_best_match(x, event))

# กรองเฉพาะข้อความที่มีการจับคู่
df_filtered = df[df["Best Match"].notna()].copy()
st.write("-------------")

# ดู Message ทั้งหมดในไฟล์ (เพื่อตรวจสอบว่าข้อความมีอะไรบ้าง)
#st.write("Unique Messages in Dataset:")
#st.write(df["Message"].dropna().unique())

# ลบค่า NaN ใน Message
#df = df.dropna(subset=["Message"])

# แปลง Message เป็น String ทั้งหมด และลบช่องว่าง
#df["Message"] = df["Message"].astype(str).str.strip()

# filter Excel
#df = df.reset_index(drop=True)
#df = df.drop(columns=["#"])

# กรองเฉพาะ Message ที่อยู่ในรายการ
#df_filtered = df[df["Message"].isin(event)].copy()

# ถ้าไม่มีข้อมูลหลังจากกรอง แสดงข้อความแจ้งเตือน
if df_filtered.empty:
    st.write("❌ No matching messages found! Check spelling and spaces in 'event'.")

    for message in event:
        matched_rows = df_filtered[df_filtered["Message"].str.contains(message[:30], na=False, regex=False)]  # ใช้เฉพาะ 30 ตัวแรกของข้อความ
        if not matched_rows.empty:
            st.write(f"✅ Found partial match for: {message[:30]}...")

# แสดง DataFrame หลังจากกรอง
#st.write(df_filtered.head())

# แปลงคอลัมน์ Field change time เป็น datetime
df_filtered["Field change time"] = pd.to_datetime(df_filtered["Field change time"], errors="coerce")

# ใช้ regex แยก State ก่อนหน้า และหลังการเปลี่ยนแปลง
df_filtered[["Previous State", "Next State"]] = df_filtered["Message"].str.extract(r'from (.+) to (.+)')

# ลบค่า NaN ออกจาก Previous State และ Next State
df_filtered = df_filtered.dropna(subset=["Previous State", "Next State"])

# จัดกลุ่มตาม Previous State และ Next State
df_filtered = df_filtered.sort_values("Field change time")

# เรียงตามเวลา
#df_filtered = df_filtered.sort_values("Field change time").reset_index(drop=True)

# คำนวณ Duration
df_filtered["Duration (second)"] = df_filtered.groupby(["Previous State", "Next State"])["Field change time"].diff().dt.total_seconds()

# ลบค่า NaN ที่เกิดจาก diff()
df_filtered = df_filtered.dropna(subset=["Duration (second)"])

result_col = ["Field change time","Previous State","Next State","Duration (second)"]

# คำนวณผลรวมของ Duration สำหรับแต่ละคู่ Previous State -> Next State
df_duration_summary = df_filtered.groupby(["Previous State", "Next State"])["Duration (second)"].sum().reset_index()

# เปลี่ยนหน่วยเวลาให้เข้าใจง่าย (เช่น นาที, ชั่วโมง ถ้าจำเป็น)
df_duration_summary["Duration (minutes)"] = df_duration_summary["Duration (second)"] / 60
df_duration_summary["Duration (hours)"] = df_duration_summary["Duration (second)"] / 3600

# แสดงผลลัพธ์
st.write("🔹 Summary of Total Duration for Each State Transition:")
st.write(df_duration_summary)

# แสดงผลลัพธ์
st.write(df_filtered[(result_col)])

df_duration_summary = df_duration_summary.sort_values("Duration (minutes)", ascending=False)
st.bar_chart(df_duration_summary, x="Previous State", y="Duration (minutes)")
