from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np

# โหลดข้อมูล
df = pd.read_excel("ava.xlsx", sheet_name="Sheet2")

# กรองเฉพาะข้อความที่ต้องการ
messages = [
    "Remote unit state changed from Initializing to Online.",
    "Remote unit state changed from Connecting to Initializing.",
    "Remote unit state changed from Telemetry Failure to Connecting.",
    "Remote unit state changed from Online to Telemetry Failure.",
    "Remote unit state changed from Online to Connecting."
]

# กรองเฉพาะข้อความที่ต้องการ
df_filtered = df[df["Message"].isin(messages)].copy()

# แปลงคอลัมน์ Timestamp ให้เป็น datetime
df_filtered["Field change time"] = pd.to_datetime(df_filtered["Field change time"])

# เรียงลำดับข้อมูลตาม Remote unit และ Timestamp
df_filtered = df_filtered.sort_values(["Message","Field change time"]).reset_index(drop=True)

# สร้างคอลัมน์ Duration
df_filtered["Dura"] = None

# วนลูปคำนวณระยะเวลา
for i in range(1, len(df_filtered)):
    if df_filtered.loc[i, "Message"] == df_filtered.loc[i - 1, "Message"]:
        df_filtered.loc[i, "Dura"] = df_filtered.loc[i, "Field change time"] - df_filtered.loc[i - 1, "Field change time"]

# แสดงผลลัพธ์
st.write(df_filtered)



