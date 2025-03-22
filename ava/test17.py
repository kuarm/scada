import re
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime

def load_data(uploaded_file,rows):
    #if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, skiprows=rows)
    df["Field change time"] = pd.to_datetime(df["Field change time"], format="%d/%m/%Y %I:%M:%S.%f %p", errors='coerce')
    #df = df.drop(columns=["#"])
    return df
    #return None

def filter_data(df, start_date, end_date, selected_device):
    if selected_device != "ทั้งหมด":
        df = df[df["Device"] == selected_device].reset_index(drop=True)
    else:
        df = df
    df_filtered = df[(df['Field change time'].between(start_date, end_date))]
    st.write(df_filtered)
    df_filtered['Adjusted Duration (seconds)'] = df_filtered['Duration (seconds)'].fillna(0)
    df_filtered= df_filtered[['Field change time', 'Message', 'Device', 'Alias']]
    df_filtered = df_filtered.sort_values("Field change time").reset_index(drop=True) # Sort data by time
    df_filtered[["Previous State", "New State"]] = df_filtered["Message"].apply(lambda x: pd.Series(extract_states(x))) # ใช้ฟังก์ชันในการแยก Previous State และ New State
    df_filtered= df_filtered.dropna(subset=["Previous State", "New State"]).reset_index(drop=True) # ลบแถวที่ไม่มีข้อมูล
    return df_filtered

# ฟังก์ชันดึงค่า Previous State และ New State และลบจุดท้ายข้อความ
def extract_states(message):
    # ตรวจสอบว่าข้อความเป็น "Remote Unit is now in expected state (Online)."
    if "Remote Unit is now in expected state (Online)." in str(message):
        return (None, None)  # ถ้าข้อความเป็นแบบนี้ ไม่ต้องคำนวณค่า
    match = re.search(r"Remote unit state changed from (.+?) to (.+)", str(message))
    return (match.group(1), match.group(2).strip(".")) if match else (None, None)

def adjust_stateandtime(df, start_time, end_time):
    if df.empty:
        return df  # ถ้า DataFrame ว่าง ให้ return กลับทันที

    df["Next Change Time"] = df["Field change time"].shift(-1) # คำนวณเวลาสิ้นสุดของแต่ละสถานะ
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
    if len(df) > 1:  # ป้องกัน IndexError จาก iloc[-2]
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
    df = df.dropna(subset=["Adjusted Duration (seconds)"])

    # กรองข้อมูลเฉพาะที่อยู่ในช่วงเวลาที่กำหนด
    df = df[(df["Adjusted Start"] >= start_time) & (df["Adjusted End"] <= end_time)]

    # ใส่ค่า start_time และ end_time ในทุกแถว
    df["Start Time Filter"] = start_time
    df["End Time Filter"] = end_time
    df[["Days", "Hours", "Minutes", "Seconds"]] = df["Adjusted Duration (seconds)"].apply(
        lambda x: pd.Series(split_duration(x), index=["Days", "Hours", "Minutes", "Seconds"]))
    df["Formatted Duration"] = df.apply(format_duration, axis=1)
    return df

# ✅ **แปลงวินาทีเป็นวัน ชั่วโมง นาที วินาที**
def split_duration(seconds):
    days = int(seconds // (24 * 3600))
    hours = int((seconds % (24 * 3600)) // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return days, hours, minutes, seconds

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

def calculate_state_summary(df_filtered):
    # ✅ **สรุปผลรวมเวลาแต่ละ State**
    state_duration_summary = df_filtered.groupby("New State", dropna=True)["Adjusted Duration (seconds)"].sum().reset_index()
    state_duration_summary[["Days", "Hours", "Minutes", "Seconds"]] = state_duration_summary["Adjusted Duration (seconds)"].apply(
        lambda x: pd.Series(split_duration(x)))
    state_duration_summary["Formatted Duration"] = state_duration_summary.apply(format_duration, axis=1)
    state_duration_summary.rename(columns={"New State": "State"}, inplace=True)

    # ✅ **คำนวณ Availability (%)**
    normal_state = "Online"
    faulty_states = ["Telemetry Failure", "Connecting", "Initializing"]
    normal_duration = df_filtered[df_filtered["New State"] == normal_state]["Adjusted Duration (seconds)"].sum()
    faulty_duration = df_filtered[df_filtered["New State"].isin(faulty_states)]["Adjusted Duration (seconds)"].sum()
    total_duration = df_filtered["Adjusted Duration (seconds)"].sum()
    if total_duration > 0:
        availability = (normal_duration / total_duration) * 100
        faulty_percentage = (faulty_duration / total_duration) * 100
        # ✅ **คำนวณ Availability (%) ของแต่ละ State**
        state_duration_summary["Availability (%)"] = (state_duration_summary["Adjusted Duration (seconds)"] / total_duration) * 100
    else:
        availability = 0
        faulty_percentage = 0
        state_duration_summary["Availability (%)"] = 0 
    
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
        lambda x: pd.Series(split_duration(x)))
    device_availability[["Total Days", "Total Hours", "Total Minutes", "Total Seconds"]] = device_availability["Total Duration (seconds)"].apply(
        lambda x: pd.Series(split_duration(x)))
    return state_duration_summary

# โหลดข้อมูลจากไฟล์
event_summary_path = "EventSummary_Jan2025.xlsx"
skiprows = 7
df = load_data(event_summary_path,skiprows)
if df is not None:
    # เลือกวันที่ เวลา
    start_date = st.sidebar.date_input("Start Date", df['Field change time'].min().date(), key="start_date")
    end_date = st.sidebar.date_input("End Date", df['Field change time'].max().date(), key="end_date")
    start_time = st.sidebar.text_input("Start Time", df["Field change time"].min().strftime("%H:%M:%S"), key="start_time")
    end_time = st.sidebar.text_input("End Time", df['Field change time'].max().strftime("%H:%M:%S"), key="end_time")
    # แปลงเป็น datetime.time()
    try:
        start_time = pd.to_datetime(start_time, format="%H:%M:%S").time()
        end_time = pd.to_datetime(end_time, format="%H:%M:%S").time()
    except ValueError:
        st.error("❌ Invalid Time Format! Please use HH:MM:SS")
    start_date = pd.Timestamp.combine(start_date, start_time)
    end_date = pd.Timestamp.combine(end_date, end_time)
    device_options = ["ทั้งหมด"] + list(df["Device"].unique())
    selected_device = st.sidebar.selectbox("เลือก Device", device_options, index=0)
    #start_date = st.sidebar.date_input("เลือกวันที่เริ่มต้น", value=datetime.date(2025, 1, 1), key="start_date")
    #start_time = st.sidebar.time_input("เลือกเวลาที่เริ่มต้น", value=datetime.time(0, 0, 0), key="start_time")
    #end_date = st.sidebar.date_input("เลือกวันที่สิ้นสุด", value=now.date(), key="end_date")
    #end_time = st.sidebar.time_input("เลือกเวลาที่สิ้นสุด", value=datetime.time(0, 0, 0), key="end_time")
    #start_time = pd.Timestamp.combine(start_date, start_time)
    #end_time = pd.Timestamp.combine(end_date, end_time)

    df_filtered = filter_data(df, start_date, end_date, selected_device)
    df_filtered = adjust_stateandtime(df_filtered, start_time, end_time)
    state_summary = calculate_state_summary(df_filtered)
    st.write(df_filters)
    st.write(state_summary)













# ✅ **แสดงผลลัพธ์ใน Streamlit**
#st.write(f"### ตาราง State จาก {start_time} ถึง {end_time}")
#st.dataframe(df_filtered[["Device", "Field change time", "Previous State", "New State", "Adjusted Start", "Adjusted End", "Days", "Hours", "Minutes", "Seconds", "Formatted Duration"]])
#st.write(f"### สรุปเวลารวมของแต่ละ State ของ Device : {selected_device}")
#st.dataframe(state_duration_summary[["State", "Days", "Hours", "Minutes", "Seconds", "Formatted Duration"]]

# ✅ **แสดงผล**
#st.write(df_filtered)
#st.write(state_duration_summary)
#st.write(f"### ค่า Availability ของระบบ: {availability:.4f}%")
#st.write(f"### เวลาที่ทำงานผิดปกติ: {faulty_percentage:.2f}%")
#st.write("### ค่า Availability (%) ของแต่ละ State")
#st.dataframe(state_duration_summary[["State", "Days", "Hours", "Minutes", "Seconds", "Formatted Duration", "Availability (%)"]])

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
#st.write("### Availability (%), จำนวนครั้ง, ระยะเวลาของ State ที่ผิดปกติ แยกตาม Device")
#st.dataframe(merged_df)

# ✅ **BarChart**
# กำหนดช่วงของ Availability (%) เป็นช่วงละ 10%
bins1 = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
labels1 = [f"{bins1[i]}-{bins1[i+1]}" for i in range(len(bins1)-1)]  # ["0-10", "10-20", ..., "90-100"]

merged_df_copy = merged_df.copy()

# จัดกลุ่มข้อมูล Availability (%) ตามช่วงที่กำหนด
merged_df_copy["Availability Range"] = pd.cut(
    merged_df_copy["Availability (%)"], bins=bins1, labels=labels1, right=False
)

# นับจำนวน Device ในแต่ละช่วง Availability (%)
availability_counts = merged_df_copy["Availability Range"].value_counts().reindex(labels1, fill_value=0).reset_index()
availability_counts.columns = ["Availability Range", "Device Count"]

# สร้าง Histogram โดยใช้ px.bar() เพื่อควบคุม bin edges ได้ตรง
fig = px.bar(
    availability_counts,
    x="Availability Range",
    y="Device Count",
    title="จำนวน Device ในแต่ละช่วง Availability (%)",
    labels={"Availability Range": "Availability (%)", "Device Count": "จำนวน Device"},
    text_auto=True  # แสดงค่าบนแท่งกราฟ
)

# ปรับแต่งรูปแบบกราฟ
fig.update_layout(
    xaxis_title="Availability (%)",
    yaxis_title="จำนวน Device",
    title_font_size=20,
    xaxis_tickangle=-45,  # หมุนตัวอักษรแกน X
    bargap=0.005
)

# แสดงกราฟใน Streamlit
#st.plotly_chart(fig)

# ✅ **ประเมิน**
# กำหนดช่วง Availability (%)
bins2 = [0, 80, 90, 100]
labels2 = ["90 < Availability (%) <= 100", "80 < Availability (%) <= 90", "0 <= Availability (%) <= 80"]  # ชื่อช่วงใหม่

merged_df2_copy = merged_df.copy()

# เพิ่มคอลัมน์ "เกณฑ์การประเมิน"
merged_df2_copy ["เกณฑ์การประเมิน"] = pd.cut(merged_df2_copy ["Availability (%)"], bins=bins2, labels=labels2, right=True)

# กำหนดเงื่อนไขสำหรับผลการประเมิน
def evaluate_result(row):
    if row["เกณฑ์การประเมิน"] == "90 < Availability (%) <= 100":
        return "✅ ไม่แฮงค์"
    elif row["เกณฑ์การประเมิน"] == "80 < Availability (%) <= 90":
        return "⚠️ ทรงๆ"
    else:
        return "❌ ต้องนอน"

# เพิ่มคอลัมน์ "ผลการประเมิน"
merged_df2_copy["ผลการประเมิน"] = merged_df2_copy.apply(evaluate_result, axis=1)

# สรุปจำนวน Device ในแต่ละเกณฑ์
summary_df = merged_df2_copy["ผลการประเมิน"].value_counts().reset_index()
summary_df.columns = ["ผลการประเมิน", "จำนวน Device"]

# สรุปจำนวน Device ในแต่ละ "เกณฑ์การประเมิน" และ "ผลการประเมิน"
summary_df = merged_df2_copy.groupby(["เกณฑ์การประเมิน", "ผลการประเมิน"]).size().reset_index(name="จำนวน Device")

# ลบแถวที่ "จำนวน Device" เป็น 0 ออก
summary_df = summary_df[summary_df["จำนวน Device"] > 0]

# ลบ index ออกจาก summary_df
summary_df = summary_df.reset_index(drop=True)

# จัดกลุ่มข้อมูล Availability (%) ตามช่วงที่กำหนด
merged_df2_copy["Availability Range"] = pd.cut(
    merged_df2_copy["Availability (%)"], bins=bins2, labels=labels2, right=True
)

# คำนวณจำนวนทั้งหมดของ Device
total_devices = summary_df["จำนวน Device"].sum()

# คำนวณ % ของแต่ละช่วง
summary_df["เปอร์เซ็นต์ (%)"] = (summary_df["จำนวน Device"] / total_devices) * 100

# จัดรูปแบบค่าเปอร์เซ็นต์ให้เป็นทศนิยม 2 ตำแหน่ง
summary_df["เปอร์เซ็นต์ (%)"] = summary_df["เปอร์เซ็นต์ (%)"].map("{:.2f}%".format)

# แสดง DataFrame พร้อมเปอร์เซ็นต์
#st.write("### จำนวน Device ในแต่ละเกณฑ์การประเมิน")
#st.dataframe(summary_df, use_container_width=True)

# แสดงผลเป็นแผนภูมิแท่ง
fig = px.bar(
    summary_df,
    x="เกณฑ์การประเมิน",
    y="จำนวน Device",
    color="ผลการประเมิน",
    text="จำนวน Device",
    barmode="group",
    title="จำนวน Device ตามเกณฑ์การประเมินและผลการประเมิน",
)

#st.plotly_chart(fig)

# ฟังก์ชันคืนค่า DataFrame
#def get_merged_df():
#    return merged_df

df_event_ava = merged_df.copy

if __name__ == "__main__":
    # ✅ **ให้ผู้ใช้เลือก Start Time และ End Time**
    st.sidebar.header("เลือกช่วงเวลา")


    
    


