import pandas as pd
import streamlit as st

# โหลดข้อมูล
file_path = "ava.xlsx"  # เปลี่ยนเป็น path ของไฟล์คุณ
df = pd.read_excel(file_path)

# คู่ Message ที่ต้องการจับคู่
message_pairs = [
    ("Remote unit state changed from Initializing to Online.", "Remote unit state changed from Connecting to Initializing."),
    ("Remote unit state changed from Connecting to Initializing.", "Remote unit state changed from Online to Connecting."),
    ("Remote unit state changed from Initializing to Online.", "Remote unit state changed from Online to Connecting."),
    ("Remote unit state changed from Connecting to Initializing.", "Remote unit state changed from Telemetry Failure to Connecting."),
    ("Remote unit state changed from Telemetry Failure to Connecting.", "Remote unit state changed from Online to Telemetry Failure.")
]

# แปลงคอลัมน์ Field change time เป็น datetime
df["Field change time"] = pd.to_datetime(df["Field change time"], errors="coerce")

# ลบค่า NaT ออก
df = df.dropna(subset=["Field change time"])

# เรียงตามเวลา
df = df.sort_values("Field change time").reset_index(drop=True)

# สร้าง DataFrame สำหรับผลลัพธ์
results = []

# วนลูปหาคู่ Message ที่ตรงกัน
for start_msg, end_msg in message_pairs:
    start_events = df[df["Message"] == start_msg].copy()
    end_events = df[df["Message"] == end_msg].copy()

    for _, start_row in start_events.iterrows():
        # หาเหตุการณ์ถัดไปที่เป็น end_msg และเกิดหลัง start_row
        next_event = end_events[end_events["Field change time"] > start_row["Field change time"]].head(1)

        if not next_event.empty:
            end_row = next_event.iloc[0]
            duration = (end_row["Field change time"] - start_row["Field change time"]).total_seconds()
            results.append({
                "Start Message": start_msg,
                "End Message": end_msg,
                "Start Time": start_row["Field change time"],
                "End Time": end_row["Field change time"],
                "Duration (seconds)": duration
            })

# แปลงเป็น DataFrame
df_results = pd.DataFrame(results)

# คำนวณ Duration รวมของแต่ละคู่ Message
df_summary = df_results.groupby(["Start Message", "End Message"])["Duration (seconds)"].sum().reset_index()

# แสดงผลลัพธ์
st.write(df_summary)
