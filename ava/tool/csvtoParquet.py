import pandas as pd
import streamlit as st
import os

# โหลดไฟล์ CSV
cols=["Field change time", "Message", "Device"]
csv_path = r".\source_csv\Jan\Output_file\combined_output.csv"
df = pd.read_csv(csv_path,skiprows=0,usecols=cols)

# แปลงและบันทึกเป็น Parquet
parquet_path = "./Output_file/combined_output_event.parquet"
df.to_parquet(parquet_path, index=False)

st.write("บันทึกไฟล์ Parquet เรียบร้อย:", parquet_path)
