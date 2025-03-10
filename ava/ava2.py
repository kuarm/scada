import streamlit as st
import pandas as pd
import numpy as np

event = ["Remote unit state changed from Initializing to Online.","Remote unit state changed from Connecting to Initializing."]

def main():
    # 2. สร้าง UI ให้ผู้ใช้สามารถอัปโหลดไฟล์ Excel
    uploaded_file = st.file_uploader("เลือกไฟล์ Excel", type=["xlsx"])

    if uploaded_file is not None:
        #เลือก sheet
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        select_sheet = st.selectbox(label ='sheet', options = sheet_names)

        # อ่านข้อมูลจากไฟล์ Excel
        df = pd.read_excel(xls, sheet_name=select_sheet,header=0)
        df = df.reset_index(drop=True)
        df = df.drop(columns=["#"])
        df_filtered = df[df["Message"].isin([event[0], event[1]])].copy()

        # แปลงเป็น timestamp เป็น datetime
        #df["Field change time"] = pd.to_datetime(df["Field change time"], format="%d/%m/%Y %H:%M:%S.%f")
        df_filtered["Field change time"] = pd.to_datetime(df_filtered["Field change time"])

        # สร้างคอลัมน์ timestamp
        #df["Field change time_ms"] = df["Field change time"].astype("int64") // 10**9  # Unix Timestamp (วินาที)
        #df["Field change time_ms"] = pd.to_datetime(df["Field change time"], format="%d/%m/%Y %H:%M:%S.%f")

        # แทรกคอลัมน์ "Field change time_ms" หลังคอลัมน์ "Field change time"
        #col_index = df.columns.get_loc("Field change time") + 1  # หาตำแหน่งของ "datetime" แล้ว +1
        #df.insert(col_index, "Field change time_ms", df.pop("Field change time_ms"))  # แทรกคอลัมน์ใหม่
        
        # แปลงเป็น datetime เป็น timestamp
        #df["Field change time_ms"] = df["Field change time_ms"].view("int64") // 10**6  # แปลงเป็น Milliseconds
        #df["end_time"] = pd.to_datetime(df["end_time"], format="%d/%m/%Y %H:%M:%S.%f")

        # เพิ่มคอลัมน์ duration และคำนวณค่า
        df_filtered["duration"] = None
        start_time = None
        durations = []

        for index, row in df_filtered.iterrows():
            if row["Message"] == event[0]:
                start_time = row["Field change time"]
            elif row["Message"] == event[1] and start_time is not None:
                duration = (row["Field change time"] - start_time).total_seconds() / 60  # แปลงเป็นนาที
                df_filtered.at[index, "duration"] = duration  # เพิ่มค่า duration ใน DataFrame
                durations.append(duration)
                start_time = None  # รีเซ็ตค่า

        # 3. แสดงข้อมูลเบื้องต้น
        st.subheader("ข้อมูลจากไฟล์ Excel")
        st.write(df_filtered)  # แสดง 5 แถวแรกจาก DataFrame

if __name__ == '__main__':
    main()