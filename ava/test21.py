import re
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime
import os

#event_summary_path = "./source_csv/combined_output.csv"
event_summary_path = "/Users/theoldman/Documents/Develop/scada/ava/source_csv/combined_output.csv"
#input_folder = "./source_csv"
input_folder = "/Users/theoldman/Documents/Develop/scada/ava/source_csv/"
#event_summary_path = r".\csv_file_test\combined_output.csv"
#input_folder = r".\csv_file_test"

remote_path = "RemoteUnit.xlsx"
skiprows_event = 0
skiprows_remote = 4
normal_state = "Online"
abnormal_states = ["Initializing", "Telemetry Failure", "Connecting"]


# Set page
st.set_page_config(page_title='Dashboard‍', page_icon=':bar_chart:', layout="wide", initial_sidebar_state="expanded", menu_items=None)
with open('./css/style.css')as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html = True)
    
def load_data_csv(file_path,rows):
    cols=["Field change time", "Message", "Device"]
    # หาไฟล์ CSV ด้วย os.scandir()
    csv_files = [entry.path for entry in os.scandir(input_folder) if entry.is_file() and entry.name.endswith(".csv")]
    for file_path in csv_files:
        try:
            chunks = pd.read_csv(file_path, skiprows=rows, chunksize=100000, usecols=cols, encoding="utf-8")
            df = pd.concat(chunks, ignore_index=True)
            if df.empty:
                st.write(f"⚠️ ไฟล์ {file_path} ว่างเปล่า!")
            else:
                return df
        except Exception as e:
            st.write(f"❌ ไม่สามารถอ่านไฟล์ {file_path}: {e}")

def load_data(uploaded_file,rows):
    #if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, skiprows=rows)
    df = df[df["Substation"] == "S1 FRTU"]
    # เลือกเฉพาะคอลัมน์ที่สนใจ
    columns_to_keep_remote = ["Name", "State", "Description"]
    df = df[columns_to_keep_remote]
    df.rename(columns={"Name": "Device"}, inplace=True)
    return df

def merge_data(df1,df2):
    df_filters = df1.merge(df2, on="Device", how="outer", suffixes=("_old", ""))
    return df_filters

# ฟังก์ชันดึงค่า Previous State และ New State และลบจุดท้ายข้อความ
def extract_states(message):
    # ตรวจสอบว่าข้อความเป็น "Remote Unit is now in expected state (Online)."
    if "Remote Unit is now in expected state (Online)." in str(message):
        return (None, None)  # ถ้าข้อความเป็นแบบนี้ ไม่ต้องคำนวณค่า
    match = re.search(r"Remote unit state changed from (.+?) to (.+)", str(message))
    return (match.group(1), match.group(2).strip(".")) if match else (None, None)

def filter_data(df, start_date, end_date):
    df = df.drop(columns=["#"], errors="ignore")
    df["Field change time"] = pd.to_datetime(df["Field change time"], format="%d/%m/%Y %I:%M:%S.%f %p", errors='coerce')
    df = df.dropna(subset=["Field change time"])  # ลบแถวที่มี NaT ใน "Field change time"
    df_filtered = df[(df['Field change time'].between(start_date, end_date))]
    df_filtered = df_filtered[['Field change time', 'Message', 'Device']].sort_values("Field change time") #.reset_index(drop=True)
    #df_filtered['Adjusted Duration (seconds)'] = df_filtered['Adjusted Duration (seconds)'].fillna(0)
    #df_filtered[["Previous State", "New State"]] = df_filtered["Message"].apply(lambda x: pd.Series(extract_states(x))) # ใช้ฟังก์ชันในการแยก Previous State และ New State
    df_filtered['Previous State'], df_filtered['New State'] = zip(*df_filtered['Message'].apply(extract_states))
    df_filtered= df_filtered.dropna(subset=["Previous State", "New State"]).reset_index(drop=True) # ลบแถวที่ไม่มีข้อมูล
    return df_filtered

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
        df = pd.concat([new_row, df], ignore_index=True).reindex(columns=df.columns)
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
            df = pd.concat([df, new_row], ignore_index=True).reindex(columns=df.columns)
    
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

@st.cache
def calculate_state_summary(df_filtered):
    # ✅ **สรุปผลรวมเวลาแต่ละ State**
    state_duration_summary = df_filtered.groupby("New State", dropna=True)["Adjusted Duration (seconds)"].sum().reset_index()
    state_duration_summary[["Days", "Hours", "Minutes", "Seconds"]] = state_duration_summary["Adjusted Duration (seconds)"].apply(
        lambda x: pd.Series(split_duration(x)))
    state_duration_summary["Formatted Duration"] = state_duration_summary.apply(format_duration, axis=1)
    state_duration_summary.rename(columns={"New State": "State"}, inplace=True)
    # ✅ **คำนวณ Availability (%)**
    normal_duration = df_filtered[df_filtered["New State"] == normal_state]["Adjusted Duration (seconds)"].sum()
    abnormal_duration = df_filtered[df_filtered["New State"].isin(abnormal_states)]["Adjusted Duration (seconds)"].sum()
    total_duration = df_filtered["Adjusted Duration (seconds)"].sum()
    if total_duration > 0:
        normal_percentage = (normal_duration / total_duration) * 100
        abnormal_percentage = (abnormal_duration / total_duration) * 100
        # ✅ **คำนวณ Availability (%) ของแต่ละ State**
        state_duration_summary["Availability (%)"] = (state_duration_summary["Adjusted Duration (seconds)"] / total_duration) * 100
    else:
        normal_percentage = 0
        abnormal_percentage = 0
        state_duration_summary["Availability (%)"] = 0 
    return state_duration_summary

def calculate_device_availability(df_filtered):
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
    return device_availability

@st.cache
def calculate_device_count(df_filtered):
    st.write(df_filtered)
    # ✅ **จำนวนครั้งที่เกิด State ต่างๆ ของแต่ละ Device**
    device_availability = calculate_device_availability(df_filtered)  # เพิ่มการคำนวณก่อนใช้งาน
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
    st.write(merged_df)
    return merged_df

def plot(df):
    # ✅ **BarChart**
    # กำหนดช่วงของ Availability (%) เป็นช่วงละ 10%
    bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    labels = [f"{bins[i]}-{bins[i+1]}" for i in range(len(bins)-1)]  # ["0-10", "10-20", ..., "90-100"]
    # จัดกลุ่มข้อมูล Availability (%) ตามช่วงที่กำหนด
    df = df.copy()  # ป้องกัน SettingWithCopyWarning
    df.loc[:, "Availability Range"] = pd.cut(df["Availability (%)"], bins=bins, labels=labels, right=True, include_lowest=True)
    # นับจำนวน Device ในแต่ละช่วง Availability (%)
    availability_counts = df["Availability Range"].value_counts().reindex(labels, fill_value=0).reset_index()
    availability_counts.columns = ["Availability Range", "Device Count"]
    total_device_count = availability_counts["Device Count"].sum()
    # สร้าง Histogram โดยใช้ px.bar() เพื่อควบคุม bin edges ได้ตรง
    fig = px.bar(
        availability_counts,
        x="Availability Range",
        y="Device Count",
        title=f"Plot จำนวน {total_device_count} Device ในแต่ละช่วง Availability (%)",
        labels={"Availability Range": "Availability (%)", "Device Count": "จำนวน Device"},
        text_auto=True  # แสดงค่าบนแท่งกราฟ
    )
    # ปรับแต่งรูปแบบกราฟ
    fig.update_layout(
        xaxis_title="Availability (%)",
        yaxis_title="จำนวน Device",
        title_font_size=20,
        xaxis_tickangle=-45,  # หมุนตัวอักษรแกน X"
        bargap=0.005
    )
    return fig

def evaluate(df):
    # ✅ **ประเมิน**
    # กำหนดช่วง Availability (%)
    bins = [0, 80, 90, 100]
    #labels = ["90 < Availability (%) <= 100", "80 < Availability (%) <= 90", "0 <= Availability (%) <= 80"]  # ชื่อช่วงใหม่
    labels = ["0 <= Availability (%) <= 80", "80 < Availability (%) <= 90", "90 < Availability (%) <= 100"]  # ชื่อช่วงใหม่
    # เพิ่มคอลัมน์ "เกณฑ์การประเมิน"
    df["เกณฑ์การประเมิน"] = pd.cut(df["Availability (%)"], bins=bins, labels=labels, right=True)
    # กำหนดเงื่อนไขสำหรับผลการประเมิน
    def evaluate_result(row):
        if row["เกณฑ์การประเมิน"] == "90 < Availability (%) <= 100":
            return "✅ ไม่แฮงค์"
        elif row["เกณฑ์การประเมิน"] == "80 < Availability (%) <= 90":
            return "⚠️ ทรงๆ"
        else:
            return "❌ ต้องนอน"
    # เพิ่มคอลัมน์ "ผลการประเมิน"
    df["ผลการประเมิน"] = df.apply(evaluate_result, axis=1)
    # สรุปจำนวน Device ในแต่ละเกณฑ์
    summary_df = df["ผลการประเมิน"].value_counts().reset_index()
    summary_df.columns = ["ผลการประเมิน", "จำนวน Device"]
    # สรุปจำนวน Device ในแต่ละ "เกณฑ์การประเมิน" และ "ผลการประเมิน"
    summary_df = df.groupby(["เกณฑ์การประเมิน", "ผลการประเมิน"]).size().reset_index(name="จำนวน Device")
    # ลบแถวที่ "จำนวน Device" เป็น 0 ออก
    summary_df = summary_df[summary_df["จำนวน Device"] > 0]
    # ลบ index ออกจาก summary_df
    summary_df = summary_df.reset_index(drop=True)
    # จัดกลุ่มข้อมูล Availability (%) ตามช่วงที่กำหนด
    df["Availability Range"] = pd.cut(
        df["Availability (%)"], bins=bins, labels=labels, right=True
    )
    # คำนวณจำนวนทั้งหมดของ Device
    total_devices = summary_df["จำนวน Device"].sum()
    # คำนวณ % ของแต่ละช่วง
    summary_df["เปอร์เซ็นต์ (%)"] = (summary_df["จำนวน Device"] / total_devices) * 100
    # จัดรูปแบบค่าเปอร์เซ็นต์ให้เป็นทศนิยม 2 ตำแหน่ง
    summary_df["เปอร์เซ็นต์ (%)"] = summary_df["เปอร์เซ็นต์ (%)"].map("{:.2f}%".format)
    # แสดง DataFrame พร้อมเปอร์เซ็นต์
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
    return fig

def display(ava,plot,eva):
    st.write("### Availability (%), จำนวนครั้ง, ระยะเวลา แยกตาม Device") #merged_df #device_availability % #
    st.write(ava)
    st.write(plot)
    st.write(eva)

def remote(df_filters):
    new_columns = [
        "Availability (%)",
        "จำนวนครั้ง Initializing",
        "ระยะเวลา Initializing (seconds)",
        "จำนวนครั้ง Telemetry Failure",
        "ระยะเวลา Telemetry Failure (seconds)",
        "จำนวนครั้ง Connecting",
        "ระยะเวลา Connecting (seconds)"
    ]
    
    # ลบคอลัมน์เก่าที่ไม่ต้องการออก
    #df_remote.drop(columns=[col for col in df_remote.columns if col.endswith("_old")], inplace=True)
    
    df_remote = df_filters.fillna({
        "Availability (%)": 100.00,
        "จำนวนครั้ง Initializing": 0,
        "ระยะเวลา Initializing (seconds)": 0,
        "จำนวนครั้ง Telemetry Failure": 0,
        "ระยะเวลา Telemetry Failure (seconds)": 0,
        "จำนวนครั้ง Connecting": 0,
        "ระยะเวลา Connecting (seconds)": 0,
        "เกณฑ์การประเมิน": "90 < Availability (%) <= 100",
        "ผลการประเมิน": "✅ ไม่แฮงค์",
        "Availability Range": "90 < Availability (%) <= 100"
    })
    return df_remote

def main():
    st.title("📊 สถานะอุปกรณ์บนระบบ SCADA")
    st.markdown("---------")
    df = load_data_csv(event_summary_path,skiprows_event)
    #st.write(df)
    
    df_remote = load_data(remote_path,skiprows_remote)
    df_merge = merge_data(df_remote,df)
    if df_merge is not None and not df_merge.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with st.sidebar:
            # ✅ **ให้ผู้ใช้เลือก Start Time และ End Time**
            st.sidebar.header("เลือกช่วงเวลา")
            # แปลงเป็น datetime.time()
            df_merge["Field change time"] = pd.to_datetime(df_merge["Field change time"], format="%d/%m/%Y %I:%M:%S.%f %p", errors='coerce')
            start_date = st.date_input("Start Date", df_merge['Field change time'].min().date(), key="start_date")
            end_date = st.date_input("End Date", df_merge['Field change time'].max().date(), key="end_date")
            start_time = st.text_input("Start Time", df_merge["Field change time"].min().strftime("%H:%M:%S"), key="start_time")
            end_time = st.text_input("End Time", df_merge['Field change time'].max().strftime("%H:%M:%S"), key="end_time")
            try:
                start_time = pd.to_datetime(start_time, format="%H:%M:%S").time()
                end_time = pd.to_datetime(end_time, format="%H:%M:%S").time()
            except ValueError:
                st.error("❌ Invalid Time Format! Please use HH:MM:SS")
            start_date = pd.Timestamp.combine(start_date, start_time)
            end_date = pd.Timestamp.combine(end_date, end_time)
            st.markdown("---------")
            st.header("เลือกอุปกรณ์")
            device_options = ["ทั้งหมด"] + list(df_merge["Device"].unique())
            # ใช้ multiselect และให้ค่าเริ่มต้นเป็น "ทั้งหมด"
            selected_devices = st.multiselect("เลือก Device", options=device_options, default=["ทั้งหมด"])
            # ตรวจสอบว่าเลือก "ทั้งหมด" หรือไม่
            if not selected_devices or "ทั้งหมด" in selected_devices:
                df_filtered = df_merge.copy()  # แสดงข้อมูลทั้งหมด
            else:
                df_filtered = df_merge[df_merge["Device"].isin(selected_devices)]  # กรองเฉพาะที่เลือก

            #selected_device = st.selectbox("เลือก Device", device_options, index=0)
            df_filtered = filter_data(df_filtered, start_date, end_date)
            st.sidebar.markdown("---------")
            option_funct = ['%Avaiability']
            cols_select = ['State', 'Description', 'สถานที่', 'การไฟฟ้า', 'ประเภทอุปกรณ์', 'จุดติดตั้ง', 'Master', 'โครงการติดตั้ง']
            st.header("Functions:")
            funct_select = st.radio(label="", options = option_funct)
            st.markdown("---------")

        df_filtered = adjust_stateandtime(df_filtered, start_date, end_date)
        state_summary = calculate_state_summary(df_filtered)
        device_availability = calculate_device_availability(df_filtered)
        device_count_duration = calculate_device_count(df_filtered)
        #st.write(device_count_duration)
        plot_availability = plot(device_count_duration)
        evaluate_availability= evaluate(device_count_duration)
        remoteunit = remote(device_count_duration)
        #st.write(remoteunit)
        #display(device_count_duration,plot_availability,evaluate_availability,plot_availability,evaluate_availability,remoteunit)
        
if __name__ == "__main__":
    main()
        
    
    
        #st.write(remoteunit)
        #st.write("### Plot Remote")
        #plot_ava = plot(remoteunit)
        #st.write(plot_ava)
        
