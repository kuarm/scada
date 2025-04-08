import pandas as pd
import streamlit as st
import os

# โหลดไฟล์ CSV
cols=["Field change time", "Message", "Device"]
csv_path = "D:/ML/scada/ava/source_csv/Jan/Output_file/combined_output-10.csv"
df = pd.read_csv(csv_path,skiprows=0,usecols=cols)

# แปลงและบันทึกเป็น Parquet
parquet_path = "D:/ML/scada/ava/Output_file/combined_output_event-10.parquet"
df.to_parquet(parquet_path, index=False)

st.write("บันทึกไฟล์ Parquet เรียบร้อย:", parquet_path)
