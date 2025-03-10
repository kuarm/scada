import pandas as pd
import streamlit as st

# โหลดข้อมูล
file_path = "ava.xlsx"  # เปลี่ยนเป็น path ของไฟล์คุณ
df = pd.read_excel(file_path)

# รายการข้อความที่ต้องการจับคู่
messages = [
    "Remote unit state changed from Initializing to Online.",
    "Remote unit state changed from Connecting to Initializing.",
    "Remote unit state changed from Telemetry Failure to Connecting.",
    "Remote unit state changed from Online to Telemetry Failure.",
    "Remote unit state changed from Online to Connecting."
]

# กรองเฉพาะเหตุการณ์ที่สนใจ
df_filtered = df[df["Message"].isin(messages)].copy()

# ตรวจสอบว่าคอลัมน์ Field change time มีอยู่หรือไม่
if "Field change time" not in df_filtered.columns:
    raise ValueError("ไม่มีคอลัมน์ 'Field change time' ใน DataFrame")

# แปลงคอลัมน์ Field change time เป็น datetime
df_filtered["Field change time"] = pd.to_datetime(df_filtered["Field change time"], errors="coerce")

# กำจัดค่าที่เป็น NaT
df_filtered = df_filtered.dropna(subset=["Field change time"])

# เรียงลำดับข้อมูลตามเวลา
df_filtered = df_filtered.sort_values("Field change time").reset_index(drop=True)

# เพิ่มคอลัมน์ Previous Message และ Previous Time
df_filtered["Previous Message"] = df_filtered["Message"].shift(1)
df_filtered["Previous Time"] = df_filtered["Field change time"].shift(1)

# คำนวณ Duration
df_filtered["Duration"] = df_filtered["Field change time"] - df_filtered["Previous Time"]

# แทนค่า NaT ด้วย 0
df_filtered["Duration"] = df_filtered["Duration"].fillna(pd.Timedelta(seconds=0))

# แปลง Duration เป็นวินาที
df_filtered["Duration (seconds)"] = df_filtered["Duration"].dt.total_seconds().astype(int)

# แสดงเฉพาะคอลัมน์ที่สำคัญ
df_result = df_filtered[["Previous Message", "Message", "Previous Time", "Field change time", "Duration (seconds)"]]

# แสดงผลลัพธ์
st.write(df_result)
