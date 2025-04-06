import pandas as pd
import streamlit as st
import os

# โหลดไฟล์ CSV
csv_path = r".\source_csv\Jan\Output_file\combined_output.csv"
df = pd.read_csv(csv_path)

# แปลงและบันทึกเป็น Parquet
parquet_path = r".\source_csv\Jan\Output_file\combined_output.parquet"
df.to_parquet(parquet_path, index=False)

st.write("บันทึกไฟล์ Parquet เรียบร้อย:", parquet_path)
