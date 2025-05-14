import streamlit as st
import pandas as pd

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])
parquet_path = "D:/Develop/scada/ava/output_file/S1-REC-020X-021X-0220.parquet"

if uploaded_file:
    usecols1 = ["Name", "State", "Description", "Substation"]
    usecols2=["Field change time", "Message", "Device"]
    
    df = pd.read_excel(uploaded_file,skiprows=0,usecols=usecols2)
    #df = df[df["Substation"] == "S1 FRTU"]
    #df.rename(columns={"Name": "Device"}, inplace=True)

    df = df.astype(str)
    df.to_parquet(parquet_path, index=False)
    
    st.success("✅ แปลงเสร็จแล้วเป็น Parquet!")
    st.dataframe(df.head())
