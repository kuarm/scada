import re
import streamlit as st
import pandas as pd

# โหลดข้อมูลจากไฟล์
df = pd.read_excel("ava_test.xlsx", sheet_name="Sheet1")
st.write(df)
# แปลง "Field change time" เป็น datetime
df["Field change time"] = pd.to_datetime(df["Field change time"], format="%d/%m/%Y %H:%M:%S.%f")

# ฟังก์ชันดึงค่า Previous State และ New State จากข้อความ Message และลบจุดออกจาก New State
def extract_states(message):
    match = re.search(r"Remote unit state changed from (.+?) to (.+)", str(message))
    if match:
        prev_state, new_state = match.groups()
        return prev_state, new_state.strip(".")  # ลบจุดท้ายข้อความ
    return None, None

# ใช้ฟังก์ชัน extract_states กับคอลัมน์ Message
df[["Previous State", "New State"]] = df["Message"].apply(lambda x: pd.Series(extract_states(x)))

# คำนวณเวลาสิ้นสุดของแต่ละสถานะ (Next Change Time)
df["Next Change Time"] = df["Field change time"].shift(-1)

# ✅ **ให้ผู้ใช้เลือก Start Time และ End Time พร้อม key ที่แตกต่างกัน**
st.sidebar.header("เลือกช่วงเวลา")
start_date = st.sidebar.date_input("เลือกวันที่เริ่มต้น", value=pd.to_datetime("2025-02-16"), key="start_date")
start_time = st.sidebar.time_input("เลือกเวลาที่เริ่มต้น", value=pd.to_datetime("00:00:00").time(), key="start_time")
end_date = st.sidebar.date_input("เลือกวันที่สิ้นสุด", value=pd.to_datetime("2025-02-17"), key="end_date")
end_time = st.sidebar.time_input("เลือกเวลาที่สิ้นสุด", value=pd.to_datetime("00:00:00").time(), key="end_time")

# รวมวันที่และเวลาเข้าด้วยกัน
start_time = pd.Timestamp.combine(start_date, start_time)
end_time = pd.Timestamp.combine(end_date, end_time)

# ✅ ตรวจสอบและเพิ่ม state เริ่มต้น (ถ้ามี)
first_change_time = df["Field change time"].iloc[0]
if first_change_time > start_time:
    first_state = df["Previous State"].iloc[0]
    new_row = pd.DataFrame({
        "Field change time": [start_time],
        "Previous State": [first_state],
        "New State": [df["Previous State"].iloc[0]],  
        "Next Change Time": [first_change_time]
    })
    df = pd.concat([new_row, df], ignore_index=True)

# ✅ ตรวจสอบและเพิ่ม state สุดท้าย (ถ้ามี)
last_change_time = df["Next Change Time"].iloc[-1]
if pd.notna(last_change_time) and last_change_time < end_time:
    last_state = df["New State"].iloc[-1]
    new_row = pd.DataFrame({
        "Field change time": [last_change_time],
        "Previous State": [last_state],
        "New State": [last_state],
        "Next Change Time": [end_time]
    })
    df = pd.concat([df, new_row], ignore_index=True)

# ปรับค่าเวลาให้อยู่ในช่วงที่กำหนด
df["Adjusted Start"] = df["Field change time"].clip(lower=start_time, upper=end_time)
df["Adjusted End"] = df["Next Change Time"].clip(lower=start_time, upper=end_time)

# คำนวณช่วงเวลาที่แต่ละ State คงอยู่ (เป็นวินาที)
df["Adjusted Duration (seconds)"] = (df["Adjusted End"] - df["Adjusted Start"]).dt.total_seconds()

# ลบแถวที่มีค่า NaN ในคอลัมน์ Adjusted Duration
df_filtered = df.dropna(subset=["Adjusted Duration (seconds)"])

# กรองเฉพาะข้อมูลที่อยู่ในช่วง start_time และ end_time
df_filtered = df_filtered[
    (df_filtered["Adjusted Start"] >= start_time) & (df_filtered["Adjusted End"] <= end_time)
]

# ใส่ค่า start_time และ end_time ในทุกแถวของ df_filtered
df_filtered["Start Time Filter"] = start_time
df_filtered["End Time Filter"] = end_time

# ฟังก์ชันแปลงวินาทีให้เป็นรูปแบบวัน ชั่วโมง นาที วินาที
def format_duration(seconds):
    days = seconds // (24 * 3600)
    hours = (seconds % (24 * 3600)) // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    parts = []
    if days > 0:
        parts.append(f"{days} วัน")
    if hours > 0:
        parts.append(f"{hours} ชั่วโมง")
    if minutes > 0:
        parts.append(f"{minutes} นาที")
    if seconds > 0:
        parts.append(f"{seconds} วินาที")

    return " ".join(parts) if parts else "0 วินาที"

# คำนวณค่าแยกเป็นคอลัมน์
df_filtered["Days"] = df_filtered["Adjusted Duration (seconds)"] // (24 * 3600)
df_filtered["Hours"] = (df_filtered["Adjusted Duration (seconds)"] % (24 * 3600)) // 3600
df_filtered["Minutes"] = (df_filtered["Adjusted Duration (seconds)"] % 3600) // 60
df_filtered["Seconds"] = df_filtered["Adjusted Duration (seconds)"] % 60

# ใช้ฟังก์ชัน format_duration สำหรับคอลัมน์ข้อความ
df_filtered["Formatted Duration"] = df_filtered["Adjusted Duration (seconds)"].apply(format_duration)

# ✅ **สรุปเวลารวมของแต่ละ State**
state_duration_summary = df_filtered.groupby("Previous State")[["Formatted Duration"]].sum().reset_index()
state_duration_summary.rename(columns={"Previous State": "State"}, inplace=True)

# ✅ **แสดงผลลัพธ์ใน Streamlit**
st.write(f"### State Durations from {start_time} to {end_time}")
st.dataframe(df_filtered[[
    "Previous State", "New State", "Adjusted Start", "Adjusted End", "Days", "Hours", 
    "Minutes", "Seconds", "Formatted Duration"
    ]])

st.write("### Summary of Total Duration for Each State")
st.dataframe(state_duration_summary)