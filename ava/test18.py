import re
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime

# ✅ **โหลดข้อมูล Remote**
df_remote = pd.read_excel("RemoteUnit.xlsx", sheet_name="RemoteUnitReport_Friday, March ", skiprows=4)

# กรองเฉพาะแถวที่คอลัมน์ "Substation" มีค่า "S1 FRTU"
df_remote = df_remote[df_remote["Substation"] == "S1 FRTU"]

# เลือกเฉพาะคอลัมน์ที่สนใจ
columns_to_keep_remote = ["Name", "State", "Failure time", "Success time", "Description"]
df_remote = df_remote[columns_to_keep_remote]

# เพิ่มคอลัมน์ใหม่และกำหนดค่าเริ่มต้นเป็น 0
new_columns = [
    "Availability (%)",
    "Initializing Count",
    "Initializing Duration (seconds)",
    "Telemetry Failure Count",
    "Telemetry Failure Duration (seconds)",
    "Connecting Count",
    "Connecting Duration (seconds)"
]

for col in new_columns:
    df_remote[col] = 0  # กำหนดค่าเริ่มต้นเป็น 0 หรือ NaN ตามต้องการ

# ถ้าใช้ใน Streamlit ให้แสดง DataFrame
st.write("### ข้อมูล RemoteUnit.xlsx พร้อมคอลัมน์ใหม่")
st.dataframe(df_remote)

# เลือกเฉพาะคอลัมน์ที่สนใจ
columns_to_keep_remote = ["Name", "State", "Failure time", "Success time", "Description"]
columns_to_keep_event = ["Field change time", "Message", "Name"]
df_remote = df_remote[columns_to_keep_remote]

# ✅ รวมข้อมูลเป็น DataFrame เดียวกัน
#df_combined = pd.concat([df_event, df_remote], ignore_index=True)
#df_combined = pd.merge(df_remote, df_event, on="Name", how="left")

# ถ้าใช้ใน Streamlit ให้แสดง DataFrame
#st.write("### ข้อมูล RemoteUnit.xlsx พร้อมคอลัมน์ใหม่")
#st.dataframe(df_remote)

def calculate_availability(uptime, total_time):
    """คำนวณค่า Availability (%) = (เวลาทำงาน / เวลารวม) * 100"""
    if total_time == 0:
        return 0
    return (uptime / total_time) * 100


 # คำนวณค่า Availability
normal_state = "Online"
uptime = df[df["New State"] == normal_state][time_column].sum()
total_time = df[time_column].sum()
availability = calculate_availability(uptime, total_time)

# แปลงคอลัมน์วันที่เป็น datetime
df_remote["Failure time"] = pd.to_datetime(df_remote["Failure time"])
df_remote["Success time"] = pd.to_datetime(df_remote["Success time"])

# คำนวณระยะเวลาแต่ละสถานะ (เฉพาะที่มีค่า Success time)
df_remote["Duration"] = (df_remote["Success time"] - df_remote["Failure time"]).dt.total_seconds()

# คำนวณเวลารวมของอุปกรณ์แต่ละตัว
df_device_time = df_remote.groupby("Name").agg(
    Failure_Duration=("Duration", "sum"),
    Start_Time=("Failure time", "min"),
    End_Time=("Success time", "max")
).reset_index()

# คำนวณ Total_Time โดยใช้ช่วงเวลาที่กว้างขึ้น
df_device_time["Total_Time"] = (df_device_time["End_Time"] - df_device_time["Start_Time"]).dt.total_seconds()

# แก้ไขค่า Total_Time ที่เป็น 0
#df_device_time["Total_Time"] = df_device_time["Total_Time"].replace(0, df_remote.groupby("Name")["Failure time"].apply(lambda x: (x.max() - x.min()).total_seconds()))

# คำนวณ Uptime และ Availability
df_device_time["Uptime"] = df_device_time["Total_Time"] - df_device_time["Failure_Duration"]
df_device_time["Availability (%)"] = (df_device_time["Uptime"] / df_device_time["Total_Time"]) * 100

# รวมข้อมูล Availability กลับไปที่ df_remote
df_result = df_remote.merge(df_device_time[["Name", "Availability (%)"]], on="Name", how="left")

# แทนค่าที่ไม่มีข้อมูลเป็น 100% (สมมติว่าไม่มี Failure)
#df_result["Availability (%)"] = df_result["Availability (%)"].fillna(100)

# แสดงผลลัพธ์
st.write(df_result[["Name", "Availability (%)"]].head())

#st.write("### รวมข้อมูลจาก EventSummary และ RemoteUnit")
#df_combined = df_combined[["Name", "Description", "State", "Failure time", "Success time", "Field change time", "Message"]]
#st.dataframe(df_combined)




