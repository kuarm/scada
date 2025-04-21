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

source_csv = "D:/ML/scada/ava/output_file/S1-REC_JAN-MAR2025.csv"
source_excel = "D:/ML/scada/ava/source_excel/S1-REC_JAN-MAR2025.xlsx"
event_path_parquet = "./Output_file/S1-REC-020X-021X-0220.parquet"
remote_path_parquet = "./Output_file/combined_output_rtu.parquet"
cols_event=["Field change time", "Message", "Device"]
normal_state = "Online"
abnormal_states = ["Initializing", "Telemetry Failure", "Connecting", "Offline"]
state = ["Online", "Initializing", "Telemetry Failure", "Connecting", "Offline"]
option_menu = ['สถานะอุปกรณ์','%ความพร้อมใช้งาน', '%การสั่งการ', 'ข้อมูลการสั่งการ']
bins_eva = [0, 80, 90, 100]
labels_eva = ["0 <= Availability (%) <= 80", "80 < Availability (%) <= 90", "90 < Availability (%) <= 100"] 
# Set page
st.set_page_config(page_title='Dashboard‍', page_icon=':bar_chart:', layout="wide", initial_sidebar_state="expanded", menu_items=None)
with open('./css/style.css')as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html = True)

@st.cache_data
def load_data_xls(uploaded_file):
    usecols1 = ["Name", "State", "Description", "Substation"]
    usecols2=["Field change time", "Message", "Device"]
    df = pd.read_excel(uploaded_file, usecols=usecols2)
    #df = df[df["Substation"] == "S1 FRTU"]
    #df.rename(columns={"Name": "Device"}, inplace=True)
    return df

@st.cache_data
def load_parquet(path):
    return pd.read_parquet(path, engine="pyarrow")

def merge_data(df1,df2):
    df_filters = df1.merge(df2, on="Device", how="outer", suffixes=("_old", ""))
    #df_filters = df_filters.drop(['State', 'Substation', 'Description'], axis=1, inplace=True) # ลบทีละหลายคอลัมน์ก็ได้
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
    # จัดกลุ่มตามเวลาที่ซ้ำกัน
    grouped = df.groupby("Field change time")
    result = []

    for group_time, group_df in grouped:
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

        result.append(sorted_group)

    # รวมผลลัพธ์ที่จัดเรียงแล้ว
    return pd.concat(result).reset_index(drop=True)

def adjust_stateandtime(df, startdate, enddate):
    if df.empty:
        return df  # ถ้า DataFrame ว่าง ให้ return กลับทันที
    df["Next Change Time"] = df["Field change time"].shift(-1) # คำนวณเวลาสิ้นสุดของแต่ละสถานะ
    # ✅ **เพิ่ม State เริ่มต้น ถ้าจำเป็น**
    first_change_time = df["Field change time"].iloc[0]
    if first_change_time > startdate:
        first_state = df["Previous State"].iloc[0]
        new_row = pd.DataFrame({
            "Device": df["Device"].iloc[0],
            "Field change time": [startdate],
            "Previous State": [first_state],
            "New State": [first_state],
            "Next Change Time": [first_change_time]
        })
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
                "Next Change Time": [enddate]
            })
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

    # ใส่ค่า start_time และ end_time ในทุกแถว
    df["Start Time Filter"] = startdate
    df["End Time Filter"] = enddate
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

@st.cache_data 
#@st.cache
def calculate_state_summary(df_filtered):
    # ✅ **สรุปผลรวมเวลาแต่ละ State**
    state_duration_summary = df_filtered.groupby("New State", dropna=True)["Adjusted Duration (seconds)"].sum().reset_index()
    #state_duration_summary[["Days", "Hours", "Minutes", "Seconds"]] = state_duration_summary["Adjusted Duration (seconds)"].apply(lambda x: pd.Series(split_duration(x)))
    #state_duration_summary["Formatted Duration"] = state_duration_summary.apply(format_duration, axis=1)
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
    df_merged = calculate_device_count(df_filtered,device_availability)
    return df_merged

@st.cache_data 
#@st.cache
def calculate_device_count(df_filtered,device_availability):
    # ✅ **จำนวนครั้งที่เกิด State ต่างๆ ของแต่ละ Device**
    #device_availability = calculate_device_availability(df_filtered)  # เพิ่มการคำนวณก่อนใช้งาน
    # คำนวณจำนวนครั้งของแต่ละ State
    state_count = df_filtered[df_filtered["New State"].isin(state)].groupby(["Device", "New State"]).size().unstack(fill_value=0)
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
    return merged_df

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
    df_add_value = df_add_value.drop(columns=["Substation","State"])
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
    
def main():
    st.title("📊 สถานะอุปกรณ์บนระบบ SCADA/TDMS")
    st.markdown("---------")
    st.sidebar.header("Menu:")
    menu_select = st.sidebar.radio(label="", options = option_menu)
    st.sidebar.markdown("---------")
    
    if menu_select == option_menu[1]:
        st.header("📊 %ความพร้อมใช้งาน ของอุปกรณ์ในสถานีไฟฟ้า และอุปกรณ์ในระบบฯ")
        #df_event = load_parquet(event_path_parquet)
        uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])
        if uploaded_file:
            df_event = load_data_xls(uploaded_file)
        else:
            df_event = load_data_xls(source_excel)
            #df_event = get_as_dataframe(sheet)
            #df_remote = load_parquet(remote_path_parquet)
    
        if df_event is not None:
            #if df_remote is not None and not df_remote.empty and df_filtered is not None and not df_filtered.empty:
            #sidebar เลือกเวลา
            with st.sidebar:
                
                # ✅ **ให้ผู้ใช้เลือก Start Time และ End Time**
                st.info(f"Menu : {menu_select}")
                #st.header("เลือกช่วงเวลา")
                df_event["Field change time"] = pd.to_datetime(df_event["Field change time"], format="%d/%m/%Y %I:%M:%S.%f", errors='coerce')
                #start_date = st.sidebar.date_input("Start Date", datetime(2025, 1, 1))
                #end_date = st.sidebar.date_input("End Date", datetime(2025, 12, 31))
                # หาค่า min/max จากข้อมูลที่โหลด
                min_date = df_event["Field change time"].min()
                max_date = df_event["Field change time"].max()
                # แปลงเป็นปี-เดือน
                month_range = pd.date_range(min_date, max_date, freq='MS')
                month_options = month_range.strftime('%Y-%m').tolist()
                if month_options:
                    # Sidebar สำหรับเลือกช่วงเดือน
                    start_month = st.selectbox("📅 เลือกเดือนเริ่มต้น", month_options, index=0)
                    end_month = st.selectbox("📅 เลือกเดือนสิ้นสุด", month_options, index=len(month_options)-1)
                    if start_month and end_month:
                        # แปลงเป็น datetime
                        start_date = datetime.strptime(start_month, "%Y-%m")
                        end_date = datetime.strptime(end_month, "%Y-%m") + relativedelta(months=1) - timedelta(seconds=1)
                        df_event = df_event[(df_event["Field change time"] >= start_date) & (df_event["Field change time"] <= end_date)]
                    else:
                        st.warning("กรุณาเลือกเดือนเริ่มต้นและสิ้นสุด")
                else:
                    st.warning("ไม่พบข้อมูลเดือนใน dataset")
                start_date = Timestamp(start_date)
                end_date = Timestamp(end_date)

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
            
            with st.sidebar:
                system_select = st.radio('เลือกระบบ', options = ['สถานีไฟฟ้า', 'ระบบฯ'])  
            ###-----Calc-----###
            df_filtered = split_state(df_event)
            df_filtered = sort_state_chain(df_filtered)
            #initial_date(df_filtered)
            df_filtered = adjust_stateandtime(df_filtered, start_date, end_date)
            st.dataframe(df_filtered)
            state_summary = calculate_state_summary(df_filtered) #Avail แต่ละ state
            device_availability = calculate_device_availability(df_filtered)
            #df_merged = merge_data(df_remote,device_availability)
            #df_merged_add = add_value(df_merged) 
            df_merged_add = device_availability
            
            #แสดงค่า ประเมินค่า %Avail, Bar Chart
            df_eva, summary_df, fig1, fig2 = evaluate(df_merged_add,bins_eva,labels_eva)
            #st.dataframe(summary_df)
            #st.plotly_chart(fig1, use_container_width=True)

            ###---ในระบบฯ---###
            if system_select == 'ระบบฯ':
                col1, col2, col3, col4 = st.columns(4)
                ###-----แสดงผล ฺฺBar chart : เกณฑ์การประเมิน-จำนวน Device
                #st.plotly_chart(fig1, use_container_width=True)
                ### เลือกช่วง Ava
                if st.checkbox("📌 เลือกช่วง % Availability ที่ต้องการดู:"):
                    def group_plot(df):
                        st.dataframe(df)
                        bins = [0, 20, 40, 60, 80, 90, 95, 100]
                        labels = ["0-20%", "21-40%", "41-60%", "61-80%", "81-90%", "91-95%", "96-100%"]
                        selected_group = st.multiselect("", labels)
                        #if not selected_group or "ทั้งหมด" in selected_group:
                        #    labels = ["0-20%", "21-40%", "41-60%", "61-80%", "81-90%", "91-95%", "96-100%"]
                        #else:
                        #    labels = labels
                        df["Availability Group"] = pd.cut(df["Availability (%)"], bins=bins, labels=labels, right=True)
                        filtered_by_group = df[df["Availability Group"].isin(selected_group)]
                        grouped_counts = filtered_by_group["Availability Group"].value_counts().sort_index().reset_index()
                        grouped_counts.rename(columns={"Availability Group": "ช่วง % Availability","count": "จำนวนอุปกรณ์"}, inplace=True)
                        #grouped_counts = grouped_counts[grouped_counts["จำนวนอุปกรณ์"] > 0]
                        fig3 = px.bar(
                            grouped_counts,
                            x="ช่วง % Availability",
                            y="จำนวนอุปกรณ์",
                            color="ช่วง % Availability",
                            text="จำนวนอุปกรณ์",
                            title="📊 จำนวนอุปกรณ์ในแต่ละช่วง % Availability",
                        )
                        fig3.update_layout(
                        xaxis_title="ช่วง % Availability",
                        yaxis_title="จำนวนอุปกรณ์",
                        showlegend=False,
                    )
                        return filtered_by_group, grouped_counts, fig3
        
                    df_group,grouped_count,fig3 = group_plot(df_merged_add)
                    display_select = st.radio('', options = ['BarChart', 'Dataframe'])  
                    if display_select == 'BarChart':
                        st.plotly_chart(fig3, use_container_width=True)
                    else:
                        st.dataframe(df_group)
                        st.dataframe(grouped_count)
                        def to_excel(df):
                            output = BytesIO()
                            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                                df.to_excel(writer, index=False, sheet_name='Sheet1')
                            processed_data = output.getvalue()
                            return processed_data
                        excel_data = to_excel(df_group)
                        st.download_button(
                label="📥 ดาวน์โหลดข้อมูลอุปกรณ์ทั้งหมด",
                data=excel_data,
                file_name='availability_data.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
                    st.markdown("---------")
                if st.checkbox("📌 เลือก Plot % Availability กับ อื่นๆ:"):
                    #ava_cols_select = ['จำนวนครั้ง Initializing']
                    #ava_relation = st.selectbox('Plot %Avaiability กับ',options=ava_cols_select)
                    #fig4 = px.bar(df_group, x='Description', y='Availability', color=ava_relation, title=f'% Availability vs {ava_relation}', hover_data=['Master'])
                    #fig4.update_layout(
                        #xaxis_title=ava_relation,
                        #yaxis_title="% Availability",
                        #showlegend=False) 
                    #st.plotly_chart(fig4, use_container_width=True)
                    fig4 = px.scatter(
                        df_merged_add,
                        x="จำนวนครั้ง Initializing",
                        y="Availability (%)",
                        color="Availability (%)",
                        size="จำนวนครั้ง Initializing",  # หรือใช้ขนาดเพื่อเพิ่มมิติ
                        hover_data=["Device"],
                        title="📈 ความสัมพันธ์ระหว่าง Availability (%) กับจำนวนครั้ง Initializing")
                    #st.plotly_chart(fig4, use_container_width=True)
                    fig5 = px.scatter_matrix(
                        df_merged_add,
                        dimensions=["Availability (%)", "จำนวนครั้ง Initializing", "จำนวนครั้ง Telemetry Failure", "จำนวนครั้ง Connecting"],
                        color="Availability (%)",
                        title="📊 Scatter Matrix ความสัมพันธ์ของตัวแปรต่าง ๆ")
                    #st.plotly_chart(fig5, use_container_width=True)
                    fig6 = px.scatter(
                        df_merged_add,
                        x="จำนวนครั้ง Telemetry Failure",
                        y="Availability (%)",
                        size="จำนวนครั้ง Initializing",
                        color="Availability (%)",
                        hover_name="Device",
                        title="🫧 Bubble Chart แสดงความสัมพันธ์ Availability (%) และเหตุการณ์")
                    #st.plotly_chart(fig6, use_container_width=True)
                    fig_matrix = px.scatter_matrix(
                        df_merged_add,
                        dimensions=[
                            "Availability (%)",
                            "ระยะเวลา Initializing (seconds)",
                            "ระยะเวลา Telemetry Failure (seconds)",
                            "ระยะเวลา Connecting (seconds)"
                        ],
                        color="Availability (%)",
                        title="📊 ความสัมพันธ์ Availability กับเวลารวมในสถานะต่าง ๆ")
                    st.plotly_chart(fig_matrix, use_container_width=True)
                state = ["Online", "Initializing", "Telemetry Failure", "Connecting", "Offline"]
                with col1:
                    st.metric(label="📈 Avg. Availability (%)", value=f"{df_merged_add['Availability (%)'].mean():.2f} %")
                with col2:
                    st.metric(label="🔢 Avg. จำนวนครั้ง Initializing", value=f"{df_merged_add['จำนวนครั้ง Initializing'].mean():.2f}")
                with col3:
                    st.metric(label="🔢 Avg. จำนวนครั้ง Connecting", value=f"{df_merged_add['จำนวนครั้ง Connecting'].mean():.2f}")
                with col4:
                    st.metric(label="🔢 Avg. จำนวนครั้ง Telemetry Failure", value=f"{df_merged_add['จำนวนครั้ง Telemetry Failure'].mean():.2f}")
            st.markdown("---------")
        else:
            st.info("ไม่มี Database")
            
        #sidebar เลือกค่า Avail เพื่อดู Dataframe
        # 🔹 ดูรายละเอียดอุปกรณ์ที่ Availability < 80%
        #bad_devices = df_merged_add_filter[df_merged_add_filter["Availability (%)"] < 80]
        #st.subheader("😴 รายชื่ออุปกรณ์ที่ Availability ต่ำกว่า 80% (ต้องนอน)")
        #st.dataframe(bad_devices[["Device", "Availability (%)"]], use_container_width=True)
        # คำนวณค่าเฉลี่ยของ Availability

       
        # เพิ่ม filter สำหรับดูเฉพาะ Device ที่ Availability < 90%
        #threshold = st.slider("Filter by Availability threshold (%)", min_value=0, max_value=100, value=90)
        #filtered = df_merged_add[df_merged_add["Availability (%)"] < threshold]
        #st.write(f"Devices with Availability < {threshold}%: {len(filtered)}")
        #st.dataframe(filtered, use_container_width=True)

        #Function การแสดงผล
        st.header("เลือกแสดงผล:")
        option_funct = ['ประเมินผล % Availability', 'ข้อมูลอุปกรณ์ตาม % Availability', 'เลือกช่วง % Availability']
        selected_funct = st.selectbox("Filter", option_funct, index=0)
        #cols_select = ['State', 'Description', 'สถานที่', 'การไฟฟ้า', 'ประเภทอุปกรณ์', 'จุดติดตั้ง', 'Master', 'โครงการติดตั้ง']
        
        if selected_funct =='ประเมินผล % Availability':       
            st.write("")
        elif selected_funct =='ข้อมูลอุปกรณ์ตาม % Availability':
            min_avail, max_avail = st.slider("เลือกช่วง Availability (%)", 0, 100, (70, 90), step=1)
            filtered_df = df_merged_add[(df_merged_add["Availability (%)"] >= min_avail) & (df_merged_add["Availability (%)"] <= max_avail)]
            st.dataframe(filtered_df)
        elif selected_funct == 'เลือกช่วง % Availability':
            labels = ["0-20%", "21-40%", "41-60%", "61-80%", "81-90%", "91-95%", "96-100%"]
            st.header("เลือกช่วง % Availability")
            selected_group = st.multiselect("เลือกช่วง % Availability ที่ต้องการดู:", labels)
            filtered_by_group = df_merged_add[df_merged_add["Availability Group"].isin(selected_group)]
            st.write(f"ข้อมูลอุปกรณ์ ช่วง Availability {selected_group} : {len(filtered_by_group)}")
            st.dataframe(filtered_by_group)
        elif selected_funct == "เลือกดูจำนวนครั้ง Device ใน State ต่างๆ":
            st.write("fff")
        #st.write("🔍 อุปกรณ์ในช่วง % Availability ที่เลือก:")
        #st.dataframe(filtered_df[["Device", "Availability (%)"]].drop_duplicates())
        st.markdown("---------")
        
            
        
        
            

if __name__ == "__main__":
    main()
        
