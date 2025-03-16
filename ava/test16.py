import re
import streamlit as st
import pandas as pd

# โหลดข้อมูลจากไฟล์
df = pd.read_excel("ava_test.xlsx", sheet_name="Sheet1")

# แปลง "Field change time" เป็น datetime
df["Field change time"] = pd.to_datetime(df["Field change time"], format="%d/%m/%Y %H:%M:%S.%f")

# Sort data by time
df = df.sort_values("Field change time").reset_index(drop=True)

# ฟังก์ชันดึงค่า Previous State และ New State และลบจุดท้ายข้อความ
def extract_states(message):
    match = re.search(r"Remote unit state changed from (.+?) to (.+)", str(message))
    return (match.group(1), match.group(2).strip(".")) if match else (None, None)

df[["Previous State", "New State"]] = df["Message"].apply(lambda x: pd.Series(extract_states(x)))

# คำนวณเวลาสิ้นสุดของแต่ละสถานะ
df["Next Change Time"] = df["Field change time"].shift(-1)

# ✅ **ให้ผู้ใช้เลือก Start Time และ End Time**
st.sidebar.header("เลือกช่วงเวลา")
start_date = st.sidebar.date_input("เลือกวันที่เริ่มต้น", value=pd.to_datetime("2025-02-16"), key="start_date")
start_time = st.sidebar.time_input("เลือกเวลาที่เริ่มต้น", value=pd.to_datetime("00:00:00").time(), key="start_time")
end_date = st.sidebar.date_input("เลือกวันที่สิ้นสุด", value=pd.to_datetime("2025-02-17"), key="end_date")
end_time = st.sidebar.time_input("เลือกเวลาที่สิ้นสุด", value=pd.to_datetime("00:00:00").time(), key="end_time")

start_time = pd.Timestamp.combine(start_date, start_time)
end_time = pd.Timestamp.combine(end_date, end_time)

# ✅ **เพิ่ม State เริ่มต้น ถ้าจำเป็น**
first_change_time = df["Field change time"].iloc[0]
if first_change_time > start_time:
    first_state = df["Previous State"].iloc[0]
    new_row = pd.DataFrame({
        "Field change time": [start_time],
        "Previous State": [first_state],
        "New State": [first_state],
        "Next Change Time": [first_change_time]
    })
    df = pd.concat([new_row, df], ignore_index=True)

# ✅ **เพิ่ม State สุดท้าย ถ้าจำเป็น**
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

# ปรับเวลาให้อยู่ในช่วงที่กำหนด
df["Adjusted Start"] = df["Field change time"].clip(lower=start_time, upper=end_time)
df["Adjusted End"] = df["Next Change Time"].clip(lower=start_time, upper=end_time)

# คำนวณช่วงเวลาของแต่ละ State (วินาที)
df["Adjusted Duration (seconds)"] = (df["Adjusted End"] - df["Adjusted Start"]).dt.total_seconds()
df_filtered = df.dropna(subset=["Adjusted Duration (seconds)"])

# กรองข้อมูลเฉพาะที่อยู่ในช่วงเวลาที่กำหนด
df_filtered = df_filtered[(df_filtered["Adjusted Start"] >= start_time) & (df_filtered["Adjusted End"] <= end_time)]

# ใส่ค่า start_time และ end_time ในทุกแถว
df_filtered["Start Time Filter"] = start_time
df_filtered["End Time Filter"] = end_time

# ✅ **แปลงวินาทีเป็นวัน ชั่วโมง นาที วินาที**
def split_duration(seconds):
    days = int(seconds // (24 * 3600))
    hours = int((seconds % (24 * 3600)) // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return days, hours, minutes, seconds

df_filtered[["Days", "Hours", "Minutes", "Seconds"]] = df_filtered["Adjusted Duration (seconds)"].apply(
    lambda x: pd.Series(split_duration(x), index=["Days", "Hours", "Minutes", "Seconds"])
)

# ✅ **ฟังก์ชันแสดงผลเป็นข้อความ**
def format_duration(row):
    parts = []
    if row["Days"] > 0:
        parts.append(f"{row['Days']} วัน")
    if row["Hours"] > 0:
        parts.append(f"{row['Hours']} ชั่วโมง")
    if row["Minutes"] > 0:
        parts.append(f"{row['Minutes']} นาที")
    if row["Seconds"] > 0:
        parts.append(f"{row['Seconds']} วินาที")
    return " ".join(parts) if parts else "0 วินาที"

df_filtered["Formatted Duration"] = df_filtered.apply(format_duration, axis=1)

# ✅ **สรุปผลรวมเวลาแต่ละ State**
state_duration_summary = df_filtered.groupby("Previous State", dropna=True)["Adjusted Duration (seconds)"].sum().reset_index()

state_duration_summary[["Days", "Hours", "Minutes", "Seconds"]] = state_duration_summary["Adjusted Duration (seconds)"].apply(
    lambda x: pd.Series(split_duration(x))
)
state_duration_summary["Formatted Duration"] = state_duration_summary.apply(format_duration, axis=1)
state_duration_summary.rename(columns={"Previous State": "State"}, inplace=True)

# ✅ **แสดงผลลัพธ์ใน Streamlit**
st.write(f"### ตาราง State จาก {start_time} ถึง {end_time}")
st.dataframe(df_filtered[[
    "Previous State", "New State", "Adjusted Start", "Adjusted End", 
    "Days", "Hours", "Minutes", "Seconds", "Formatted Duration"
]])

st.write("### สรุปเวลารวมของแต่ละ State")
st.dataframe(state_duration_summary[["State", "Days", "Hours", "Minutes", "Seconds", "Formatted Duration"]])
