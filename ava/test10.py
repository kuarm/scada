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
#def extract_states(msg):
 #   match = re.search(r"from (.+) to (.+)", msg)
 #   if match:
  #      return match.group(1), match.group(2)
  #  return None, None
  
# ฟังก์ชันดึงค่า Previous State และ New State จากข้อความ Message
def extract_states(message):
        match = re.search(r"Remote unit state changed from (.+?) to (.+)", str(message))
        return match.groups() if match else (None, None)

# ใช้ฟังก์ชัน extract_states กับคอลัมน์ Message
df[["Previous State", "New State"]] = df["Message"].apply(lambda x: pd.Series(extract_states(x)))

# คำนวณเวลาสิ้นสุดของแต่ละสถานะ (Next Change Time)
df["Next Change Time"] = df["Field change time"].shift(-1)

# กำหนดช่วงเวลาที่ต้องการ
start_time = pd.Timestamp("2025-02-16 00:00:00")
end_time = pd.Timestamp("2025-02-17 00:00:00")

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
df_filtered["Start Time Filter"] = pd.to_datetime(start_time)
df_filtered["End Time Filter"] = pd.to_datetime(end_time)

# 🔹 สรุปเวลาที่แต่ละ State อยู่รวมกันทั้งหมด
state_duration_summary = df_filtered.groupby("New State")["Adjusted Duration (seconds)"].sum().reset_index()
state_duration_summary.rename(columns={"Previous State": "State", "Adjusted Duration (seconds)": "Total Duration (seconds)"}, inplace=True)

# แสดงผลลัพธ์
st.write("### State Durations from {} to {}".format(start_time, end_time))
st.dataframe(df_filtered[[
    "Previous State", "New State", "Adjusted Start", 
    "Adjusted End", "Adjusted Duration (seconds)"
]])

st.write("### Summary of Total Duration for Each State")
st.write(state_duration_summary)
