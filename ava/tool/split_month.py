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

#source_csv_event = "D:/ML/scada/ava/source_csv/S1-AVR-LBS-RCS-REC_VSP_JAN-MAR2025.csv"

uploaded_file = st.file_uploader("📥 อัปโหลดไฟล์ Excel หรือ CSV", type=["xlsx", "csv"])

@st.cache_data   
def load_data_csv(file_path):
    df = pd.read_csv(file_path)
    return df
# แปลงเดือนภาษาไทย
def convert_thai_date(date_str):
    thai_months = {
        'ม.ค.': '01', 'ก.พ.': '02', 'มี.ค.': '03', 'เม.ย.': '04',
        'พ.ค.': '05', 'มิ.ย.': '06', 'ก.ค.': '07', 'ส.ค.': '08',
        'ก.ย.': '09', 'ต.ค.': '10', 'พ.ย.': '11', 'ธ.ค.': '12'
    }
    for th_month, num_month in thai_months.items():
        if th_month in date_str:
            return date_str.replace(th_month, num_month)
    return date_str

# แปลงฟิลด์วันที่
def convert_date(df):
    df['Availability Period'] = df['Availability Period'].astype(str).apply(convert_thai_date)
    df['Availability Period'] = pd.to_datetime(df['Availability Period'], format='%m %Y')
    df['Month'] = df['Availability Period'].dt.to_period('M')
    months = sorted(df['Month'].dropna().unique().astype(str))
    return df, months

def add_peroid(df, startdate, enddate):
    locale_setting = "th_TH"

    # แปลงเดือนแบบย่อ เช่น ม.ค., ก.พ.
    start_month = format_date(startdate, format="LLL", locale=locale_setting)
    end_month = format_date(enddate, format="LLL", locale=locale_setting)
    
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

def main():
    if uploaded_file:
        usecols1 = ["Name", "Description", "Substation"]
        usecols2=["Field change time", "Message", "Device"]
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
        else:
            df = pd.read_excel(uploaded_file,usecols=usecols2)
            
        
        #df, months = convert_date(df)
        st.success(f"✅ โหลดไฟล์ {uploaded_file.name} เรียบร้อย")
        
        df_event = df.copy()
        #st.write(df_event["Field change time"].unique())
        #df_event["Field change time"] = pd.to_datetime(df_event["Field change time"], format="%d/%m/%Y %I:%M:%S.%f", errors='coerce')
        
        #df_event = df_event[['Field change time', 'Message', 'Device']].sort_values("Field change time").reset_index(drop=True)
        #df['Availability Period'] = df['Availability Period'].astype(str).apply(convert_thai_date)
        #df_event["Field change time"] = pd.to_datetime(df_event["Field change time"], format="%d/%m/%Y %I:%M:%S", errors='coerce')
        df_event["Field change time"] = pd.to_datetime(df_event["Field change time"],errors='coerce',dayfirst=True)  # ถ้า format เป็น dd/mm/yyyy)
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
        
        df_event, peroid_name = add_peroid(df_event, start_date, end_date)
        
        def to_csv(df):
            output = StringIO()
            df.to_csv(output, index=False, encoding='utf-8-sig')  # รองรับภาษาไทย
            return output.getvalue()
        
        # ตั้งชื่อ CSV จากชื่อไฟล์เดิม
        base_name = uploaded_file.name.rsplit('.', 1)[0]
        csv_filename = base_name + peroid_name + ".csv"
        
        #csv_filename = 'availability_data' + '_' + peroid_name + ".csv"
        
        # แปลง DataFrame เป็น CSV text
        csv_data = to_csv(df_event)
        
        # ปุ่มดาวน์โหลด CSV
        st.download_button(
            label="📥 ดาวน์โหลดข้อมูลอุปกรณ์ทั้งหมด (CSV)",
            data=csv_data,
            file_name=csv_filename,
            mime='text/csv'
        )
        #df_event = load_data_csv(source_csv_event)
        
        
        
if __name__ == "__main__":
    main()