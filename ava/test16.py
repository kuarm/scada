import re
import streamlit as st
import pandas as pd

# โหลดข้อมูลจากไฟล์
df = pd.read_excel("EventSummary_Jan2025.xlsx", sheet_name="EventSummary_Jan2025",header=7)
#df = pd.read_excel("ava_test.xlsx", sheet_name="Sheet5")
#df = df.iloc[7:].reset_index(drop=True) # ลบแถว 1-7
df= df[['Field change time', 'Message', 'Device', 'Alias']]
#df = df.drop(columns=["#"])

# แปลง "Field change time" เป็น datetime
#df["Field change time"] = pd.to_datetime(df["Field change time"], format="%d/%m/%Y %H:%M:%S.%f")
df["Field change time"] = pd.to_datetime(df["Field change time"], format="%d/%m/%Y %I:%M:%S.%f %p", errors='coerce')
# Sort data by time
df = df.sort_values("Field change time").reset_index(drop=True)

# ฟังก์ชันดึงค่า Previous State และ New State และลบจุดท้ายข้อความ
def extract_states(message):
    # ตรวจสอบว่าข้อความเป็น "Remote Unit is now in expected state (Online)."
    if "Remote Unit is now in expected state (Online)." in str(message):
        return (None, None)  # ถ้าข้อความเป็นแบบนี้ ไม่ต้องคำนวณค่า
    match = re.search(r"Remote unit state changed from (.+?) to (.+)", str(message))
    return (match.group(1), match.group(2).strip(".")) if match else (None, None)

# ใช้ฟังก์ชันในการแยก Previous State และ New State
df[["Previous State", "New State"]] = df["Message"].apply(lambda x: pd.Series(extract_states(x)))

# ลบแถวที่ไม่มีข้อมูล
df = df.dropna(subset=["Previous State", "New State"]).reset_index(drop=True)

# คำนวณเวลาสิ้นสุดของแต่ละสถานะ
df["Next Change Time"] = df["Field change time"].shift(-1)

# ✅ **กรองข้อมูล Device**
device_options = ["ทั้งหมด"] + list(df["Device"].unique())
selected_device = st.sidebar.selectbox("เลือก Device", device_options, index=0)
if selected_device != "ทั้งหมด":
    df = df[df["Device"] == selected_device].reset_index(drop=True)
else:
    df = df
    
# ✅ **ให้ผู้ใช้เลือก Start Time และ End Time**
st.sidebar.header("เลือกช่วงเวลา")
# ดึงวันที่และเวลาปัจจุบัน
now = pd.Timestamp.now()
start_date = st.sidebar.date_input("เลือกวันที่เริ่มต้น", value=pd.to_datetime("2025-01-01"), key="start_date")
start_time = st.sidebar.time_input("เลือกเวลาที่เริ่มต้น", value=pd.to_datetime("00:00:00").time(), key="start_time")
end_date = st.sidebar.date_input("เลือกวันที่สิ้นสุด", value=now.date(), key="end_date")
end_time = st.sidebar.time_input("เลือกเวลาที่สิ้นสุด", value=now.time(), key="end_time")

start_time = pd.Timestamp.combine(start_date, start_time)
end_time = pd.Timestamp.combine(end_date, end_time)

# ✅ **เพิ่ม State เริ่มต้น ถ้าจำเป็น**
first_change_time = df["Field change time"].iloc[0]
if first_change_time > start_time:
    first_state = df["Previous State"].iloc[0]
    new_row = pd.DataFrame({
        "Device": df["Device"].iloc[0],
        "Field change time": [start_time],
        "Previous State": [first_state],
        "New State": [first_state],
        "Next Change Time": [first_change_time]
    })
    df = pd.concat([new_row, df], ignore_index=True)
    
# ✅ **เพิ่ม State สุดท้าย ถ้าจำเป็น**
last_change_time = df["Next Change Time"].iloc[-2]
if pd.notna(last_change_time) and last_change_time < end_time:
    last_state = df["New State"].iloc[-1]
    new_row = pd.DataFrame({
         "Device": df["Device"].iloc[-1],
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
state_duration_summary = df_filtered.groupby("New State", dropna=True)["Adjusted Duration (seconds)"].sum().reset_index()

state_duration_summary[["Days", "Hours", "Minutes", "Seconds"]] = state_duration_summary["Adjusted Duration (seconds)"].apply(
    lambda x: pd.Series(split_duration(x))
)
state_duration_summary["Formatted Duration"] = state_duration_summary.apply(format_duration, axis=1)
state_duration_summary.rename(columns={"New State": "State"}, inplace=True)

# ✅ **แสดงผลลัพธ์ใน Streamlit**
#st.write(f"### ตาราง State จาก {start_time} ถึง {end_time}")
#st.dataframe(df_filtered[["Device", "Field change time", "Previous State", "New State", "Adjusted Start", "Adjusted End", "Days", "Hours", "Minutes", "Seconds", "Formatted Duration"]])
#st.write(f"### สรุปเวลารวมของแต่ละ State ของ Device : {selected_device}")
#st.dataframe(state_duration_summary[["State", "Days", "Hours", "Minutes", "Seconds", "Formatted Duration"]]


# ✅ **คำนวณ Availability (%)**
total_duration = df_filtered["Adjusted Duration (seconds)"].sum()

normal_state = "Online"
normal_duration = df_filtered[df_filtered["New State"] == normal_state]["Adjusted Duration (seconds)"].sum()

faulty_states = ["Telemetry Failure", "Connecting", "Initializing"]
faulty_duration = df_filtered[df_filtered["New State"].isin(faulty_states)]["Adjusted Duration (seconds)"].sum()

if total_duration > 0:
    availability = (normal_duration / total_duration) * 100
    faulty_percentage = (faulty_duration / total_duration) * 100
else:
    availability = 0
    faulty_percentage = 0

# ✅ **คำนวณ Availability (%) ของแต่ละ State**
state_duration_summary["Availability (%)"] = (state_duration_summary["Adjusted Duration (seconds)"] / total_duration) * 100

# ✅ **แสดงผล**
#st.write(df_filtered)
#st.write(state_duration_summary)
#st.write(f"### ค่า Availability ของระบบ: {availability:.4f}%")
#st.write(f"### เวลาที่ทำงานผิดปกติ: {faulty_percentage:.2f}%")
#st.write("### ค่า Availability (%) ของแต่ละ State")
#st.dataframe(state_duration_summary[["State", "Days", "Hours", "Minutes", "Seconds", "Formatted Duration", "Availability (%)"]])

# ✅ **คำนวณ Availability (%) ของแต่ละ Device**
# คำนวณเวลารวมของแต่ละ Device
device_total_duration = df_filtered.groupby("Device")["Adjusted Duration (seconds)"].sum().reset_index()
device_total_duration.columns = ["Device", "Total Duration (seconds)"]

# คำนวณเวลาที่ Device อยู่ในสถานะปกติ
device_online_duration = df_filtered[df_filtered["New State"] == normal_state].groupby("Device")["Adjusted Duration (seconds)"].sum().reset_index()
device_online_duration.columns = ["Device", "Online Duration (seconds)"]

# รวมข้อมูลทั้งสองตาราง
device_availability = device_total_duration.merge(device_online_duration, on="Device", how="left").fillna(0)

# คำนวณ Availability (%)
device_availability["Availability (%)"] = (device_availability["Online Duration (seconds)"] / device_availability["Total Duration (seconds)"]) * 100

# แปลงวินาทีเป็น วัน ชั่วโมง นาที วินาที
device_availability[["Online Days", "Online Hours", "Online Minutes", "Online Seconds"]] = device_availability["Online Duration (seconds)"].apply(
    lambda x: pd.Series(split_duration(x))
)
device_availability[["Total Days", "Total Hours", "Total Minutes", "Total Seconds"]] = device_availability["Total Duration (seconds)"].apply(
    lambda x: pd.Series(split_duration(x))
)
# แสดงผลลัพธ์ใน Streamlit
#st.write("### Availability (%) ของแต่ละ Device")
#st.dataframe(device_availability[["Device", "Availability (%)", "Online Days", "Online Hours", "Online Minutes", "Online Seconds","Total Days", "Total Hours", "Total Minutes", "Total Seconds"]])

# ✅ **จำนวนครั้งที่เกิด State ต่างๆ ของแต่ละ Device**
# กำหนดรายชื่อ State ผิดปกติ
abnormal_states = ["Initializing", "Telemetry Failure", "Connecting"]

# คำนวณจำนวนครั้งของแต่ละ State
state_count = df_filtered[df_filtered["New State"].isin(abnormal_states)].groupby(["Device", "New State"]).size().unstack(fill_value=0)

# คำนวณระยะเวลารวมของแต่ละ State
state_duration = df_filtered[df_filtered["New State"].isin(abnormal_states)].groupby(["Device", "New State"])["Adjusted Duration (seconds)"].sum().unstack(fill_value=0)

# รวมจำนวนครั้งและระยะเวลาของแต่ละ State
summary_df = state_count.merge(state_duration, left_index=True, right_index=True, suffixes=(" Count", " Duration (seconds)"))

# จัดลำดับคอลัมน์ให้เป็นไปตามที่ต้องการ
summary_df = summary_df.reindex(columns=[
    "Initializing Count", "Initializing Duration (seconds)",
    "Telemetry Failure Count", "Telemetry Failure Duration (seconds)",
    "Connecting Count", "Connecting Duration (seconds)"
])

# แสดงผลใน Streamlit
#st.write("### สรุปจำนวนครั้งและระยะเวลาของ State ผิดปกติ แยกตาม Device")
#st.dataframe(summary_df)

# ✅ **รวมตารางโดยใช้ "Device" เป็น key**
merged_df = pd.merge(device_availability, summary_df, on="Device", how="left")
# จัดลำดับคอลัมน์ตามที่ต้องการ
merged_df = merged_df[[
    "Device", "Availability (%)",
    "Initializing Count", "Initializing Duration (seconds)",
    "Telemetry Failure Count", "Telemetry Failure Duration (seconds)",
    "Connecting Count", "Connecting Duration (seconds)"
]]

# เปลี่ยนชื่อคอลัมน์ตามที่ต้องการ
merged_df = merged_df.rename(columns={
    "Initializing Count": "จำนวนครั้ง Initializing",
    "Initializing Duration (seconds)": "ระยะเวลา Initializing (seconds)",
    "Telemetry Failure Count": "จำนวนครั้ง Telemetry Failure",
    "Telemetry Failure Duration (seconds)": "ระยะเวลา Telemetry Failure (seconds)",
    "Connecting Count": "จำนวนครั้ง Connecting",
    "Connecting Duration (seconds)": "ระยะเวลา Connecting (seconds)"
})

# แสดงผล
st.write("### Availability (%), จำนวนครั้ง, ระยะเวลาของ State ที่ผิดปกติ แยกตาม Device")
st.dataframe(merged_df)



