import re
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import os
from dateutil.relativedelta import relativedelta
from pandas import Timestamp
from io import BytesIO
from io import StringIO
from babel.dates import format_date

# Set page
st.set_page_config(page_title='Dashboard‍', page_icon=':bar_chart:', layout="wide", initial_sidebar_state="expanded", menu_items=None)
with open('./css/style.css')as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html = True)
    
source_csv_remote = "./source_excel/DataforCalc_CSV/excel/RemoteUnit_01052025_filtered.xlsx"
source_excel = "./source_excel/S1-REC_JAN-MAR2025.xlsx"
event_path_parquet = "./Output_file/S1-REC-020X-021X-0220.parquet"
remote_path_parquet = "./Output_file/combined_output_rtu.parquet"
cols_event=["Field change time", "Message", "Device"]
normal_state = "Online"
abnormal_states = ["Initializing", "Telemetry Failure", "Connecting", "Offline"]
state = ["Online", "Initializing", "Telemetry Failure", "Connecting", "Offline"]
option_menu = ['สถานะอุปกรณ์','%ความพร้อมใช้งาน', '%การสั่งการ', 'ข้อมูลการสั่งการ']
bins_eva = [0, 80, 90, 100]
labels_eva = ["0 <= Availability (%) <= 80", "80 < Availability (%) <= 90", "90 < Availability (%) <= 100"] 

@st.cache_data
def load_data_xls(uploaded_file):
    usecols1 = ["Name", "State", "Description", "Substation"]
    usecols2=["Field change time", "Message", "Device"]
    df = pd.read_excel(uploaded_file)
    #df = df[df["Substation"] == "S1 FRTU"]
    #df.rename(columns={"Name": "Device"}, inplace=True)
    return df

@st.cache_data
def load_parquet(path):
    return pd.read_parquet(path, engine="pyarrow")

@st.cache_data   
def load_data_csv(file_path):
    df = pd.read_csv(file_path)
    return df

def merge_data(df1,df2,flag):
    #st.write(f" merge data: ")
    #st.dataframe(df2)
    df1.rename(columns={"Name": "Device"}, inplace=True)
    if flag == 'substation':
        df1 = df1[
            ((df1["สถานที่ติดตั้ง"] == "สถานีไฟฟ้า")) |
            ((df1["สถานที่ติดตั้ง"] == "โรงไฟฟ้า") & df1["ประเภทอุปกรณ์"].isin(["SPP-Substation", "VSPP-Substation"]))
            ]
    else:
        df1 = df1[df1["Substation"] == "S1 FRTU"]
    
    df_filters = df1.merge(df2, on="Device", how="outer", suffixes=("_old", ""))
    #df_filters = df_filters.drop(['Substation'], axis=1, inplace=True) # ลบทีละหลายคอลัมน์ก็ได้
    df_filters = df_filters.drop(columns=["Substation","ใช้งาน/ไม่ใช้งาน"], errors='ignore')  # ป้องกันกรณีไม่มีคอลัมน์นี้
    df_filters = df_filters[[
    "Device", "Description", "สถานที่", "การไฟฟ้า", "สถานที่ติดตั้ง", "ประเภทอุปกรณ์", 
    "Availability (%)", 
    "จำนวนครั้ง Online", "ระยะเวลา Online (seconds)", 
    "จำนวนครั้ง Connecting","ระยะเวลา Connecting (seconds)",
    "จำนวนครั้ง Initializing", "ระยะเวลา Initializing (seconds)",
    "จำนวนครั้ง Telemetry Failure", "ระยะเวลา Telemetry Failure (seconds)",
    "จำนวนครั้ง Offline", "ระยะเวลา Offline (seconds)" 
]]
    return df_filters

# ฟังก์ชันดึงค่า Previous State และ New State และลบจุดท้ายข้อความ
def extract_states(message):
    # ตรวจสอบว่าข้อความเป็น "Remote Unit is now in expected state (Online)."
    if "Remote Unit is now in expected state (Online)." in str(message):
        return (None, None)  # ถ้าข้อความเป็นแบบนี้ ไม่ต้องคำนวณค่า
    match = re.search(r"Remote unit state changed from (.+?) to (.+)", str(message))
    return (match.group(1), match.group(2).strip(".")) if match else (None, None)

def split_state(df):
    #df = df.drop(columns=["#"], errors="ignore")
    #df["Field change time"] = pd.to_datetime(df["Field change time"], format="%d/%m/%Y %I:%M:%S.%f %p", errors='coerce')
    df = df.dropna(subset=["Field change time"])  # ลบแถวที่มี NaT ใน "Field change time"
    #df_filtered = df[(df['Field change time'].between(startdate, enddate))]
    df_filtered = df[['Field change time', 'Message', 'Device']].sort_values("Field change time").reset_index(drop=True)
    

    #df_filtered['Adjusted Duration (seconds)'] = df_filtered['Adjusted Duration (seconds)'].fillna(0)
    df_filtered[["Previous State", "New State"]] = df_filtered["Message"].apply(lambda x: pd.Series(extract_states(x))) # ใช้ฟังก์ชันในการแยก Previous State และ New State
    #df_filtered['Previous State'], df_filtered['New State'] = zip(*df_filtered['Message'].apply(extract_states))
    df_filtered= df_filtered.dropna(subset=["Previous State", "New State"]).reset_index(drop=True) # ลบแถวที่ไม่มีข้อมูล
    return df_filtered

def sort_state_chain(df):
    """จัดเรียงแถวที่มี Field change time ซ้ำกัน โดยให้ New State ของแถวบน = Previous State ของแถวถัดไป"""
    # ✅ กลุ่มแยกตาม Device และเวลา
    grouped = df.groupby(["Device", "Field change time"])
    result = []

    for (device_id, group_time), group_df in grouped:
        if len(group_df) == 1:
            result.append(group_df)
            continue

        # สร้าง map ของ Previous -> Row
        state_map = {row["Previous State"]: row for _, row in group_df.iterrows()}
        new_states = set(group_df["New State"])
        prev_states = set(group_df["Previous State"])

        # หา "จุดเริ่มต้น" คือ Previous State ที่ไม่ใช่ New State ของใครเลย
        start_candidates = list(prev_states - new_states)
        if not start_candidates:
            # ถ้าไม่มีจุดเริ่มต้นที่ชัดเจน (เช่น loop หรือ incomplete), ใช้ลำดับเดิมไปก่อน
            sorted_group = group_df
            st.dataframe(group_df)
        else:
            current_state = start_candidates[0]
            rows = []
            visited = set()

            while current_state in state_map and current_state not in visited:
                row = state_map[current_state]
                rows.append(row)
                visited.add(current_state)
                current_state = row["New State"]

            sorted_group = pd.DataFrame(rows)
        st.dataframe(sorted_group)
        result.append(sorted_group)

    # รวมผลลัพธ์ที่จัดเรียงแล้ว
    return pd.concat(result).reset_index(drop=True)

def sort_state_chain1(df):
    """จัดเรียง chain ภายในแต่ละกลุ่ม Device + Field change time"""
    df["Field change time"] = pd.to_datetime(df["Field change time"])

    result = []
    grouped = df.groupby(["Device", "Field change time"])
    

    for (_, timestamp), group_df in grouped:
        if len(group_df) == 1:
            result.append(group_df)
            continue

        state_map = {row["Previous State"]: row for _, row in group_df.iterrows()}
        new_states = set(group_df["New State"])
        prev_states = set(group_df["Previous State"])

        start_candidates = list(prev_states - new_states)

        if not start_candidates:
            # ถ้าไม่มี state เริ่มชัดเจน (วงกลมหรือซ้ำ), คืนลำดับเดิม
            sorted_group = group_df
        else:
            current_state = start_candidates[0]
            visited = set()
            rows = []

            while current_state in state_map and current_state not in visited:
                row = state_map[current_state]
                rows.append(row)
                visited.add(current_state)
                current_state = row["New State"]

            sorted_group = pd.DataFrame(rows)

            # เพิ่มแถวที่ไม่ถูกเชน (เช่น duplicate state)
            if len(sorted_group) < len(group_df):
                extras = group_df[~group_df.index.isin(sorted_group.index)]
                sorted_group = pd.concat([sorted_group, extras])

        result.append(sorted_group)
        st.write(result)
    return pd.concat(result).sort_values(by=["Field change time"]).reset_index(drop=True)

def adjust_stateandtime(df, startdate, enddate):
    
    # แปลงให้เป็น datetime ถ้ายังเป็น str อยู่
    if isinstance(startdate, str):
        startdate = pd.to_datetime(startdate)

    if isinstance(enddate, str):
        enddate = pd.to_datetime(enddate)

    if df.empty:
        return df

    df["Next Change Time"] = df["Field change time"].shift(-1) # คำนวณเวลาสิ้นสุดของแต่ละสถานะ
    #st.write(df["Field change time"].iloc[123])
    #st.write(df["Next Change Time"].iloc[123])
    st.write(df)
    # ✅ **เพิ่ม State เริ่มต้น ถ้าจำเป็น**
    first_change_time = df["Field change time"].iloc[0]
    if first_change_time > startdate:
        first_state = df["Previous State"].iloc[0]
        new_row = pd.DataFrame({
            "Device": df["Device"].iloc[0],
            "Field change time": [startdate],
            "Previous State": [first_state],
            "New State": [first_state],
            "Next Change Time": [first_change_time],
            "Message": df["Message"].iloc[0]
        })
        #counter_func_first += 1
        #st.write(f"counter_func_first: {counter_func_first}")
        #df = pd.concat([new_row, df], ignore_index=True).reindex(columns=df.columns)
        df = pd.concat([new_row, df], ignore_index=True)
    # ✅ **เพิ่ม State สุดท้าย ถ้าจำเป็น**
    if len(df) > 1:  # ป้องกัน IndexError จาก iloc[-2]
        last_change_time = df["Next Change Time"].iloc[-2]
        if pd.notna(last_change_time) and last_change_time < enddate:
            last_state = df["New State"].iloc[-1]
            new_row = pd.DataFrame({
                "Device": df["Device"].iloc[-1],
                "Field change time": [last_change_time],
                "Previous State": [last_state],
                "New State": [last_state],
                "Next Change Time": [enddate],
                "Message": df["Message"].iloc[-1]
            })
            #counter_func_last += 1
            #st.write(f"counter_func_last: {counter_func_last}")
            #df = pd.concat([df, new_row], ignore_index=True).reindex(columns=df.columns)
            df = pd.concat([new_row, df], ignore_index=True)
    # ปรับเวลาให้อยู่ในช่วงที่กำหนด
    df["Adjusted Start"] = df["Field change time"].clip(lower=startdate, upper=enddate)
    df["Adjusted End"] = df["Next Change Time"].clip(lower=startdate, upper=enddate)
    df["Adjusted Start"] = pd.to_datetime(df["Adjusted Start"], errors='coerce')
    df["Adjusted End"] = pd.to_datetime(df["Adjusted End"], errors='coerce')
    
    # คำนวณช่วงเวลาของแต่ละ State (วินาที)
    df["Adjusted Duration (seconds)"] = (df["Adjusted End"] - df["Adjusted Start"]).dt.total_seconds()
    df = df.dropna(subset=["Adjusted Duration (seconds)"])
    
    # กรองข้อมูลเฉพาะที่อยู่ในช่วงเวลาที่กำหนด
    df = df[(df["Adjusted Start"] >= startdate) & (df["Adjusted End"] <= enddate)]
    st.write(df)
    # ใส่ค่า start_time และ end_time ในทุกแถว
    df["Start Time Filter"] = startdate
    df["End Time Filter"] = enddate
    df[["Days", "Hours", "Minutes", "Seconds"]] = df["Adjusted Duration (seconds)"].apply(
        lambda x: pd.Series(split_duration(x), index=["Days", "Hours", "Minutes", "Seconds"]))
    df["Formatted Duration"] = df.apply(format_duration, axis=1)
    #df["Month_stamp"] = pd.to_datetime(df["Field change time"], format="%d/%m/%Y %I:%M:%S.%f", errors='coerce').dt.strftime('%Y-%m')
    df = df.sort_values("Field change time").reset_index(drop=True) # Sort data by time
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

@st.cache_data 
#@st.cache
def calculate_state_summary(df_filtered):
    # ✅ **สรุปผลรวมเวลาแต่ละ State**
    state_duration_summary = df_filtered.groupby("New State", dropna=True)["Adjusted Duration (seconds)"].sum().reset_index()
    state_duration_summary[["Days", "Hours", "Minutes", "Seconds"]] = state_duration_summary["Adjusted Duration (seconds)"].apply(lambda x: pd.Series(split_duration(x)))
    state_duration_summary["Formatted Duration"] = state_duration_summary.apply(format_duration, axis=1)
    state_duration_summary.rename(columns={"New State": "State"}, inplace=True)
    # ✅ **คำนวณ Availability (%)**
    #normal_duration = df_filtered[df_filtered["New State"] == normal_state]["Adjusted Duration (seconds)"].sum()
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
    #st.info(f'normal_duration= {normal_duration}')
    #st.info(f'abnormal_duration= {abnormal_duration}')
    #st.info(f'total_duration= {normal_duration + abnormal_duration}')
    # ✅ **คำนวณ Availability (%) ของแต่ละ Device**
    # คำนวณเวลารวมของแต่ละ Device
    device_total_duration = df_filtered.groupby(["Device"])["Adjusted Duration (seconds)"].sum().reset_index()
    #st.dataframe(device_total_duration)
    device_total_duration.columns = ["Device", "Total Duration (seconds)"]
    # คำนวณเวลาที่ Device อยู่ในสถานะปกติ
    device_online_duration = df_filtered[df_filtered["New State"] == normal_state].groupby("Device")["Adjusted Duration (seconds)"].sum().reset_index()
    device_online_duration.columns = ["Device", "Online Duration (seconds)"]

    st.dataframe(df_filtered[df_filtered["Device"] == 'RNA_S'])
    st.dataframe(device_online_duration[device_online_duration["Device"] == 'RNA_S'])
    # รวมข้อมูลทั้งสองตาราง
    device_availability = device_total_duration.merge(device_online_duration, on="Device", how="left").fillna(0)
    # คำนวณ Availability (%)
    device_availability["Availability (%)"] = (device_availability["Online Duration (seconds)"] / device_availability["Total Duration (seconds)"]) * 100
    # แปลงวินาทีเป็น วัน ชั่วโมง นาที วินาที
    device_availability[["Online Days", "Online Hours", "Online Minutes", "Online Seconds"]] = device_availability["Online Duration (seconds)"].apply(
        lambda x: pd.Series(split_duration(x)))
    device_availability[["Total Days", "Total Hours", "Total Minutes", "Total Seconds"]] = device_availability["Total Duration (seconds)"].apply(
        lambda x: pd.Series(split_duration(x)))
    #st.dataframe(device_availability)
    return device_availability

@st.cache_data 
#@st.cache
def calculate_device_count(df_filtered,device_availability):
    
    # ✅ **จำนวนครั้งที่เกิด State ต่างๆ ของแต่ละ Device**
    #device_availability = calculate_device_availability(df_filtered)  # เพิ่มการคำนวณก่อนใช้งาน
    # คำนวณจำนวนครั้งของแต่ละ State
    state_count = df_filtered[df_filtered["New State"].isin(state)].groupby(["Device", "New State"]).size().unstack(fill_value=0)
    # คำนวณระยะเวลารวมของแต่ละ State
    state_duration = df_filtered[df_filtered["New State"].isin(state)].groupby(["Device", "New State"])["Adjusted Duration (seconds)"].sum().unstack(fill_value=0)
    # รวมจำนวนครั้งและระยะเวลาของแต่ละ State
    summary_df = state_count.merge(state_duration, left_index=True, right_index=True, suffixes=(" Count", " Duration (seconds)"))
    #df_filtered1 = df_filtered[['Device', 'Availability Period']]
    #summary_df = summary_df.merge(df_filtered1, on="Device", how="outer", suffixes=("_old", ""))
    #summary_df = pd.merge(summary_df,  df_filtered1, on="Device", how="left")
    # จัดลำดับคอลัมน์ให้เป็นไปตามที่ต้องการ
    summary_df = summary_df.reindex(columns=[
        "Initializing Count", "Initializing Duration (seconds)",
        "Telemetry Failure Count", "Telemetry Failure Duration (seconds)",
        "Connecting Count", "Connecting Duration (seconds)",
        "Offline Count", "Offline Duration (seconds)",
        "Online Count", "Availability Period"
    ])
    # ✅ **รวมตารางโดยใช้ "Device" เป็น key**
    merged_df = pd.merge(device_availability, summary_df, on="Device", how="left")
    # จัดลำดับคอลัมน์ตามที่ต้องการ
    merged_df = merged_df[[
        "Device", "Availability (%)",
        "Online Count", "Online Duration (seconds)",
        "Connecting Count", "Connecting Duration (seconds)",
        "Initializing Count", "Initializing Duration (seconds)",
        "Telemetry Failure Count", "Telemetry Failure Duration (seconds)",
        "Offline Count", "Offline Duration (seconds)", 'Availability Period'
    ]]
    # เปลี่ยนชื่อคอลัมน์ตามที่ต้องการ 
    merged_df = merged_df.rename(columns={
        "Online Count": "จำนวนครั้ง Online", 
        "Online Duration (seconds)": "ระยะเวลา Online (seconds)",
        "Connecting Count": "จำนวนครั้ง Connecting",
        "Connecting Duration (seconds)": "ระยะเวลา Connecting (seconds)",
        "Initializing Count": "จำนวนครั้ง Initializing",
        "Initializing Duration (seconds)": "ระยะเวลา Initializing (seconds)",
        "Telemetry Failure Count": "จำนวนครั้ง Telemetry Failure",
        "Telemetry Failure Duration (seconds)": "ระยะเวลา Telemetry Failure (seconds)",
        "Offline Count": "จำนวนครั้ง Offline",
        "Offline Duration (seconds)": "ระยะเวลา Offline (seconds)"
    })
    #st.info("state_count")
    #st.dataframe(state_count)
    #st.info("state_duration")
    #st.dataframe(state_duration)
    return merged_df, state_count, state_duration

def plot(df):
    # ✅ **BarChart**
    # กำหนดช่วงของ Availability (%) เป็นช่วงละ 10%
    bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    labels = [f"{bins[i]}-{bins[i+1]}" for i in range(len(bins)-1)]  # ["0-10", "10-20", ..., "90-100"]
    # จัดกลุ่มข้อมูล Availability (%) ตามช่วงที่กำหนด
    df_plot = df.copy()  # ป้องกัน SettingWithCopyWarning
    df_plot.loc[:, "Availability Range"] = pd.cut(df_plot["Availability (%)"], bins=bins, labels=labels, right=True, include_lowest=True)
    # นับจำนวน Device ในแต่ละช่วง Availability (%)
    availability_counts = df_plot["Availability Range"].value_counts().reindex(labels, fill_value=0).reset_index()
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

def evaluate(df,bins,labels):
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
    #summary_df["เปอร์เซ็นต์ (%)"] = summary_df["เปอร์เซ็นต์ (%)"].map("{:.2f}%".format)
    summary_df["เปอร์เซ็นต์ (%)"] = summary_df["เปอร์เซ็นต์ (%)"].round(2)
    fig1 = px.bar(
        summary_df,
        x="เกณฑ์การประเมิน",
        y="จำนวน Device",
        color="ผลการประเมิน",
        text="จำนวน Device",
        barmode="group",
        title="จำนวน Device ตามเกณฑ์การประเมิน",
    )
    # ✅ Pie Chart สัดส่วนผลการประเมิน
    fig2 = px.pie(
        summary_df,
        names="ผลการประเมิน",
        values="จำนวน Device",
        title="ประเมิน",
        hole=0.4
    )
    fig2.update_traces(textinfo='percent+label')
    #st.plotly_chart(fig2, use_container_width=True)
    return df, summary_df, fig1, fig2

def add_value(df_filters):
    #new_columns = ["Availability (%)","จำนวนครั้ง Initializing","ระยะเวลา Initializing (seconds)","จำนวนครั้ง Telemetry Failure","ระยะเวลา Telemetry Failure (seconds)","จำนวนครั้ง Connecting","ระยะเวลา Connecting (seconds)"]
    # ลบคอลัมน์เก่าที่ไม่ต้องการออก
    #df_remote.drop(columns=[col for col in df_remote.columns if col.endswith("_old")], inplace=True)
    df_add_value = df_filters.fillna({
        "Availability (%)": 100.00,
        "จำนวนครั้ง Online": 0, 
        "ระยะเวลา Online (seconds)": 0,
        "จำนวนครั้ง Connecting": 0,
        "ระยะเวลา Connecting (seconds)": 0,
        "จำนวนครั้ง Initializing": 0,
        "ระยะเวลา Initializing (seconds)": 0,
        "จำนวนครั้ง Telemetry Failure": 0,
        "ระยะเวลา Telemetry Failure (seconds)": 0,
        "จำนวนครั้ง Offline": 0,
        "ระยะเวลา Offline (seconds)": 0
        #"เกณฑ์การประเมิน": "90 < Availability (%) <= 100",
        #"ผลการประเมิน": "✅ ไม่แฮงค์",
        #"Availability Range": "90 < Availability (%) <= 100"
    })
    return df_add_value

# กำหนดค่าเริ่มต้นให้ session_state
def initial_date(df):
    df["Field change time"] = pd.to_datetime(df["Field change time"], format="%d/%m/%Y %I:%M:%S.%f %p", errors='coerce')
    if "selected_devices" not in st.session_state:
        st.session_state.selected_devices = "ทั้งหมด"
    if "start_date" not in st.session_state:
        st.session_state.start_date = df["Field change time"].min().date()
        #st.session_state.start_date = pd.to_datetime("01/01/2024").date()
    if "end_date" not in st.session_state:
        st.session_state.end_date = df["Field change time"].max().date()
        #st.session_state.end_date = pd.to_datetime("31/12/2024").date()
    if "start_time" not in st.session_state:
        st.session_state.start_time = df["Field change time"].min().strftime("%H:%M:%S.%f")[:-3]
        #st.session_state.start_time = pd.to_datetime("00:00:00").strftime("%H:%M:%S")
    if "end_time" not in st.session_state:
        st.session_state.end_time = df["Field change time"].max().strftime("%H:%M:%S.%f")[:-3]
        #st.session_state.end_time = pd.to_datetime("00:00:00").strftime("%H:%M:%S")

# ฟังก์ชัน Callback เพื่ออัปเดตค่า session_state
def update_dates():
    st.session_state.start_date = st.session_state.start_date
    st.session_state.end_date = st.session_state.end_date
    st.session_state.start_time = st.session_state.start_time
    st.session_state.end_time = st.session_state.end_time

def add_peroid(df, startdate, enddate):
    locale_setting = "th_TH"

    # แปลงเดือนแบบย่อ เช่น ม.ค., ก.พ.
    start_month = format_date(startdate, format="LLL")
    end_month = format_date(enddate, format="LLL")
    
    start_year = startdate.year
    end_year = enddate.year

    if start_year == end_year:
        if startdate.month == enddate.month:
            period_label = f"{start_month} {start_year}"
        else:
            period_label = f"{start_month} - {end_month} {start_year}"
    else:
        period_label = f"{start_month} {start_year} - {end_month} {end_year}"
    
    df["Availability Period"] = period_label
    return df, period_label

def format_selected_columns(df):
    formatted_df = df.copy()
    for col in formatted_df.columns:
        if col in ["จำนวนครั้ง Online", "จำนวนครั้ง Connecting", "จำนวนครั้ง Initializing", "จำนวนครั้ง Telemetry Failure", "จำนวนครั้ง Offline"]:
            # คอลัมน์ใส่ comma, ไม่ใส่ทศนิยม
            formatted_df[col] = formatted_df[col].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else "")
            # คอลัมน์ใส่ทศนิยม
        elif col == "Availability (%)":
            formatted_df[col] = formatted_df[col].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "")
        elif pd.api.types.is_numeric_dtype(formatted_df[col]):
            # ปัดทศนิยม 2 ตำแหน่ง + ใส่ ,
            formatted_df[col] = formatted_df[col].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) else "")
    return formatted_df

def main():
    #st.title("📊 สถานะอุปกรณ์บนระบบ SCADA/TDMS")
    #st.markdown("---------")
    #st.sidebar.header("Menu:")
    #menu_select = st.sidebar.radio(label="", options = option_menu)
    #st.sidebar.markdown("---------")
    
    #st.header("📊 %ความพร้อมใช้งาน ของอุปกรณ์ในสถานีไฟฟ้า และอุปกรณ์ในระบบฯ")
    #df_event = load_parquet(event_path_parquet)
    #uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx","csv"])
    uploaded_file = st.file_uploader("📥 อัปโหลดไฟล์ Excel หรือ CSV", type=["xlsx", "csv"])
    if uploaded_file:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            st.success(f"✅ โหลดไฟล์ {uploaded_file.name} เรียบร้อย")
        else:
            usecols2=["Field change time", "Message", "Device"]
            df = pd.read_excel(uploaded_file,usecols=usecols2)
            st.success(f"✅ โหลดไฟล์ {uploaded_file.name} ไม่เรียบร้อย")
    
        df_event = df.copy()
        df_remote = load_data_xls(source_csv_remote)
        df_remote_sub = df_remote.copy()
        #df_event = df_event[df_event["Device"] == '1BPC01_S']

        if df_event is not None and not df_remote.empty:
            #if df_remote is not None and not df_remote.empty and df_filtered is not None and not df_filtered.empty:
            #sidebar เลือกเวลา
            df_event["Field change time"] = pd.to_datetime(df_event["Field change time"], format="%Y-%m-%d %I:%M:%S.%f", errors='coerce')
            #df_event["Field change time"] = pd.to_datetime(df_event["Field change time"],errors='coerce',dayfirst=True)
            # แสดงค่าพร้อม millisecond
            #df_event["Field change time"].dt.strftime("%Y-%m-%d %H:%M:%S.%f")
            #st.dataframe(df_event["Field change time"].dt.strftime('%Y-%m-%d %H:%M:%S.%f').unique())

            with st.sidebar:
                #start_date = st.sidebar.date_input("Start Date", datetime(2025, 1, 1))
                #end_date = st.sidebar.date_input("End Date", datetime(2025, 12, 31))
                # หาค่า min/max จากข้อมูลที่โหลด
                min_date = df_event["Field change time"].min()
                max_date = df_event["Field change time"].max()
                #st.write(max_date)

                # แปลงเป็นปี-เดือน
                month_range = pd.date_range(min_date, max_date, freq='MS')
                
                #month_options = ['2025-01', '2025-02', '2025-03']
                #st.write(month_options)

                if month_options:
                    # Sidebar สำหรับเลือกช่วงเดือน
                    start_month = st.selectbox("📅 เลือกเดือนเริ่มต้น", month_options, index=0) #ได้ String
                    end_month = st.selectbox("📅 เลือกเดือนสิ้นสุด", month_options, index=len(month_options)-1)

                    if start_month and end_month:
                        # แปลงเป็น datetime
                        start_date = datetime.strptime(start_month, "%Y-%m")
                        end_date = datetime.strptime(end_month, "%Y-%m") + relativedelta(months=1) # - timedelta(seconds=1)

                        start_date1 = start_date.strftime("%Y-%m-%d %H:%M:%S.%f") #datetime object
                        end_date1 = end_date.strftime("%Y-%m-%d %H:%M:%S.%f")
                        
                        df_event = df_event[(df_event["Field change time"] >= start_date1) & (df_event["Field change time"] <= end_date1)]
                    else:
                        st.warning("กรุณาเลือกเดือนเริ่มต้นและสิ้นสุด")
                else:
                    st.warning("ไม่พบข้อมูลเดือนใน dataset")
                
                #start_str = Timestamp(start_date)
                #end_str = Timestamp(end_date)

            #start_date = start_str.strftime("%Y-%m-%d %H:%M:%S.%f") .strftime() ใช้กับ datetime object 
            #end_date = end_str.strftime("%Y-%m-%d %H:%M:%S.%f")

            # แปลงจาก str กลับเป็น datetime
            #start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S.%f")
            #end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S.%f")

            """
            #sidebar เลือกอุปกรณ์
            with st.sidebar:
                #st.header("เลือกอุปกรณ์")
                # 🔹 ตัวกรอง: เลือกอุปกรณ์ที่ต้องการวิเคราะห์
                device_list = ["ทั้งหมด"] + list(df_event["Device"].unique())
                selected_devices = st.multiselect("เลือกอุปกรณ์", device_list, default=["ทั้งหมด"])   
                # กรองข้อมูลเฉพาะอุปกรณ์ที่เลือก
                #df_merged_add = df_merged_add[df_merged_add["Device"].isin(selected_devices)]
                # ตรวจสอบว่าเลือก "ทั้งหมด" หรือไม่
                if not selected_devices or "ทั้งหมด" in selected_devices:
                    df_event = df_event.copy()  # แสดงข้อมูลทั้งหมด
                else:
                    df_event = df_event[df_event["Device"].isin(selected_devices)]  # กรองเฉพาะที่เลือก
                st.markdown("---------")
            """
        
        ###-----Calc-----###
        df_event = df_event[df_event["Device"] == "RNA_S"]
        df_split = split_state(df_event)
        df_combined_sort = sort_state_chain(df_split)
        #df_combined_sort["Field change time"].dt.strftime("%Y-%m-%d %H:%M:%S.%f")


        
        #adjusted_all_1 = []
        #for device_id in df_split["Device"].unique():
        #    df_device_1 = df_split[df_split["Device"] == device_id].copy()
        #    df_adjusted_1 = sort_state_chain(df_device_1)
        #    adjusted_all_1.append(df_adjusted_1)
        #df_combined_sort = pd.concat(adjusted_all_1, ignore_index=True)
        #df_combined_sort["Field change time"].dt.strftime('%Y-%m-%d %H:%M:%S.%f')
        #st.dataframe(df_combined_sort[df_combined_sort["Device"] == 'PBA_S'])
        #st.dataframe(df_combined_sort["Field change time"].dt.strftime('%Y-%m-%d %H:%M:%S.%f').unique())
        #st.info("หลัง เพิ่ม state")
        #st.dataframe(df_combined_sort)

        adjusted_all_2 = []
        for device_id in df_combined_sort["Device"].unique():
            df_device = df_combined_sort[df_combined_sort["Device"] == device_id].copy()
            df_adjusted = adjust_stateandtime(df_device, start_date1, end_date1)
            adjusted_all_2.append(df_adjusted)
        df_combined = pd.concat(adjusted_all_2, ignore_index=True)
        #st.info("df_combine")
        #st.dataframe(df_combined)

        state_summary = calculate_state_summary(df_combined) #Avail แต่ละ state
        device_availability = calculate_device_availability(df_combined)
        df_merged, state_count, state_duration = calculate_device_count(df_combined,device_availability)
        #mode_select = st.radio("Sub or Frtu", options=["substation","frtu"])
        #if mode_select == 'substation':
        #    flag = 'substation'
        #else:
        #flag = 'frtu'
        flag = 'substation'
        df_merged = merge_data(df_remote_sub,df_merged,flag)
        df_merged_add = add_value(df_merged)

        peroid_name = st.radio("peroid_name", options=month_options)
        df_merged_add['Availability Period'] = peroid_name
        df_final = df_merged_add.copy()
        #df_final = format_selected_columns(df_merged_add)
        #st.dataframe(df_final)

        #df_ava_, peroid_name = add_peroid(df_merged_add, start_date1, end_date1)
        #st.dataframe(df_ava_)
        
        # ตั้งชื่อ CSV จากชื่อไฟล์เดิม
        base_name = uploaded_file.name.rsplit('.', 1)[0]
        xlsx_filename = base_name + "_AVA" + ".xlsx"
        csv_filename = base_name + "_AVA" + ".csv"
        
        def to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            processed_data = output.getvalue()
            return processed_data
        
        excel_data = to_excel(df_final)
        
        # ตั้งชื่อ xlsx,csv จากชื่อไฟล์เดิม
        xlsx_filename = 'availability_data' + '_' + flag + '_' + peroid_name + ".xlsx"
        csv_filename = 'availability_data' + '_' + flag + '_' + peroid_name + ".csv"

        st.download_button(
            label="📥 ดาวน์โหลดข้อมูลอุปกรณ์ทั้งหมด",
            data=excel_data,
            file_name=xlsx_filename,
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

        df_export = df_merged_add.rename(columns={
            "Device": "อุปกรณ์",
            "Description": "รายละเอียด",
            "Availability (%)": "ความพร้อมใช้งาน (%)",
            "Availability Period": "ช่วงเวลาความพร้อมใช้งาน"
        })
        
        def to_csv(df):
            output = StringIO()
            df.to_csv(output, index=False, encoding='utf-8-sig', float_format="%.2f")  # รองรับภาษาไทย
            return output.getvalue()
        
        # แปลง DataFrame เป็น CSV text
        csv_data = to_csv(df_final)
        # ปุ่มดาวน์โหลด CSV
        st.download_button(
            label="📥 ดาวน์โหลดข้อมูลอุปกรณ์ทั้งหมด (CSV)",
            data=csv_data,
            file_name=csv_filename,
            mime='text/csv'
        )

if __name__ == "__main__":
    main()
        
