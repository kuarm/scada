import streamlit as st
import pandas as pd

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])
parquet_path = "./output_file/combined_output_rtu.parquet"

if uploaded_file:
    usecols = ["Name", "State", "Description", "Substation"]
    
    df = pd.read_excel(uploaded_file,skiprows=4,usecols=usecols)
    df = df[df["Substation"] == "S1 FRTU"]
    df.rename(columns={"Name": "Device"}, inplace=True)

    # แปลงทุกคอลัมน์เป็น string
    df = df.astype(str)
    
    # แปลงเป็น parquet (ถ้าต้องการบันทึกไว้)
    df.to_parquet(parquet_path, index=False)
    
    st.success("✅ แปลงเสร็จแล้วเป็น Parquet!")
    st.dataframe(df.head())
