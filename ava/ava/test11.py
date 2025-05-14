import re
import streamlit as st
import pandas as pd

# โหลดข้อมูลจากไฟล์
df = pd.read_excel("ava_test.xlsx", sheet_name="Sheet5")

# แปลง "Field change time" เป็น datetime
df["Field change time"] = pd.to_datetime(df["Field change time"], format="%d/%m/%Y %H:%M:%S.%f")

# Sort data by time
df = df.sort_values("Field change time").reset_index(drop=True)

# ฟังก์ชันดึงค่า Previous State และ New State จากข้อความ Message
def extract_states(message):
    match = re.search(r"Remote unit state changed from (.+?) to (.+)", str(message))
    return match.groups() if match else (None, None)

# ใช้ฟังก์ชัน extract_states กับคอลัมน์ Message
df[["Previous State", "New State"]] = df["Message"].apply(lambda x: pd.Series(extract_states(x)))

# ลบจุดท้ายของค่าในคอลัมน์ "New State"
df["New State"] = df["New State"].str.rstrip(".")

# คำนวณเวลาสิ้นสุดของแต่ละสถานะ (Next Change Time)
df["Next Change Time"] = df["Field change time"].shift(-1)

# กำหนดช่วงเวลาที่ต้องการ
start_time = pd.Timestamp("2025-02-16 00:00:00")
end_time = pd.Timestamp("2025-02-17 00:00:00")

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
df_cleaned = df.dropna(subset=["Adjusted Duration (seconds)"])

# กรองเฉพาะข้อมูลที่อยู่ในช่วง start_time และ end_time
df_filtered = df_cleaned[
    (df_cleaned["Adjusted Start"] >= start_time) & (df_cleaned["Adjusted End"] <= end_time)
]

# ใส่ค่า start_time และ end_time ในทุกแถวของ df_filtered
#df_filtered["Start Time Filter"] = pd.to_datetime(start_time)
#df_filtered["End Time Filter"] = pd.to_datetime(end_time)

# ✅ สรุปเวลาที่แต่ละ State อยู่รวมกันทั้งหมด
state_duration_summary = df_filtered.groupby("New State")["Adjusted Duration (seconds)"].sum().reset_index()
state_duration_summary.rename(columns={"Previous State": "State", "Adjusted Duration (seconds)": "Total Duration (seconds)"}, inplace=True)

# แสดงผลลัพธ์
st.write("### State Durations from {} to {}".format(start_time, end_time))
st.dataframe(df_filtered[[
    "Previous State", "New State", "Adjusted Start", 
    "Adjusted End", "Adjusted Duration (seconds)"
]])

st.write("### Summary of Total Duration for Each State")
st.dataframe(state_duration_summary)
