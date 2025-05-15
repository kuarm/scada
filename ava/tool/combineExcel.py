import streamlit as st
import pandas as pd
from io import BytesIO

st.title("📁 รวมไฟล์ Excel หลายไฟล์เป็นไฟล์เดียว")

uploaded_files = st.file_uploader("อัปโหลดหลายไฟล์ Excel", type=["xlsx",'xlsm'], accept_multiple_files=True)

if uploaded_files:
    usecols = ["Field change time", "Message", "Device"]  # เปลี่ยนตามคอลัมน์ที่ต้องการ
    all_data = []

    for file in uploaded_files:
        try:
            df = pd.read_excel(file, usecols=usecols)
            #df = pd.read_excel(file, sheet_name="Sheet1", engine="openpyxl")
            df["Source File"] = file.name  # บันทึกชื่อไฟล์ต้นทางไว้ด้วย
            all_data.append(df)
        except Exception as e:
            st.warning(f"❌ Error reading {file.name}: {e}")

    if all_data:
        merged_df = pd.concat(all_data, ignore_index=True)

        # แปลงเป็นไฟล์ Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            merged_df.to_excel(writer, index=False, sheet_name="Merged Data")
            writer.save()
        output.seek(0)

        st.success("✅ รวมข้อมูลและเซฟเป็นไฟล์ Excel เรียบร้อยแล้ว!")
        st.dataframe(merged_df.head())

        # ปุ่มดาวน์โหลด
        st.download_button(
            label="📥 ดาวน์โหลดไฟล์ Excel",
            data=output,
            file_name="merged_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
