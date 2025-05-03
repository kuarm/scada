import streamlit as st
import pandas as pd
import os

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])
#parquet_path = "D:/Develop/scada/ava/output_file/S1-REC-020X-021X-0220.parquet"
csv_path = "D:/Develop/scada/ava/source_csv/convert_csv"


if uploaded_file is not None:
    usecols1 = ["Name", "Substation", "Description", "สถานที่ติดตั้ง", "สถานที่", "การไฟฟ้า", "ประเภทอุปกรณ์", "ใช้งาน/ไม่ใช้งาน"]
    usecols2=["Field change time", "Message", "Device"]
    
    df = pd.read_excel(uploaded_file,skiprows=0,usecols=usecols1)
    df = df[df["ใช้งาน/ไม่ใช้งาน"] == "ใช้งาน"]
    #df = df[df["Substation"] != "S1 FRTU"]  
    #df = df[df["สถานที่ติดตั้ง"] == "สถานีไฟฟ้า"]
    #df.rename(columns={"Name": "Device"}, inplace=True)

    # ตั้งชื่อ CSV จากชื่อไฟล์เดิม
    base_name = uploaded_file.name.rsplit('.', 1)[0]
    csv_filename = base_name + "_filtered" + ".csv"

    # เซฟ CSV ในโฟลเดอร์ที่กำหนด
    csv_path = os.path.join("D:/ML/scada/ava/source_excel/excel file jan-mar", csv_filename)
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    st.success(f"✅ แปลงสำเร็จ: {csv_path}")