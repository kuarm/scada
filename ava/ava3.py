import pandas as pd
import streamlit as st
from datetime import datetime

df = pd.read_excel("ava.xlsx", sheet_name="Sheet2")

# แปลงคอลัมน์เป็น datetime
df["Field change time"] = pd.to_datetime(df["Field change time"])
#df["Field change time"] = df["Field change time"].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
#df['Field change time'] = df['Field change time'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])

# แปลงเป็น timestamp
#df['Field change time'] = df['Field change time'].apply(lambda x: x.timestamp())
#st.write(df['Field change time'].dtype)

# กรองเฉพาะ event ที่ต้องการ
df_filtered = df[df["Message"].isin(["Remote unit state changed from Initializing to Online.", "Remote unit state changed from Connecting to Initializing."])].copy()

# เพิ่มคอลัมน์ duration และคำนวณค่า
df_filtered["duration"] = None
start_time = None
durations = []
total_duration = 0.0  # เก็บค่ารวมของ duration ทั้งหมด (หน่วย: ชั่วโมง)

for index, row in df_filtered.iterrows():
    if row["Message"] == "Remote unit state changed from Initializing to Online.":
        start_time = row["Field change time"]
    elif row["Message"] == "Remote unit state changed from Connecting to Initializing." and start_time is not None:
        duration = (start_time - row["Field change time"]).total_seconds() / (60) # แปลงเป็น นาที
        df_filtered.at[index, "duration"] = duration  # เพิ่มค่า duration ใน DataFrame
        durations.append(duration)
        start_time = None  # รีเซ็ตค่า

        # รวมค่า duration
        total_duration += duration

st.write(df_filtered)

st.write("### Total Duration (hours)", total_duration)