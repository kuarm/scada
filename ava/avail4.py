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

source_csv = "D:/ML/scada/ava/source_csv/availability_data_ม.ค. 2025.csv"
bins_eva = [0, 80, 90, 100]
labels_eva = ["0 <= Availability (%) <= 80", "80 < Availability (%) <= 90", "90 < Availability (%) <= 100"] 
option_menu = ['สถานะอุปกรณ์','%ความพร้อมใช้งาน', '%การสั่งการ', 'ข้อมูลการสั่งการ']

# Set page
st.set_page_config(page_title='Dashboard‍', page_icon=':bar_chart:', layout="wide", initial_sidebar_state="expanded", menu_items=None)
with open('./css/style.css')as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html = True)

@st.cache_data   
def load_data_csv(file_path):
    df = pd.read_csv(file_path)
    return df

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

def main():
    st.title("📊 สถานะอุปกรณ์บนระบบ SCADA/TDMS")
    st.markdown("---------")
    st.sidebar.header("Menu:")
    menu_select = st.sidebar.radio(label="", options = option_menu)
    st.sidebar.markdown("---------")
              
    if menu_select == option_menu[1]:
        st.header("📊 %ความพร้อมใช้งาน ของอุปกรณ์ในสถานีไฟฟ้า และอุปกรณ์ในระบบฯ")
        df = load_data_csv(source_csv)

        if df is not None and not df.empty: 
            with st.sidebar:
                # ✅ **ให้ผู้ใช้เลือก Start Time และ End Time**
                st.info(f"Menu : {menu_select}")
                df["Field change time"] = pd.to_datetime(df["Field change time"], format="%d/%m/%Y %I:%M:%S.%f", errors='coerce')
                #start_date = st.sidebar.date_input("Start Date", datetime(2025, 1, 1))
    else:
        st.write("error")