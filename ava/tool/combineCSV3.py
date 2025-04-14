import streamlit as st
import pandas as pd
from io import BytesIO

st.title("📁 รวมไฟล์ CSV หลายไฟล์เป็นไฟล์ Excel เดียว")

uploaded_files = st.file_uploader("อัปโหลดหลายไฟล์ CSV", type=["csv"], accept_multiple_files=True)

if uploaded_files:
    all_data = []

    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            df["Source File"] = file.name  # เพิ่มชื่อไฟล์ไว้ใน DataFrame
            all_data.append(df)
        except Exception as e:
            st.warning(f"❌ ไม่สามารถอ่านไฟล์ {file.name}: {e}")

    if all_data:
        merged_df = pd.concat(all_data, ignore_index=True)

        # แปลง DataFrame เป็น CSV string
        csv_output = merged_df.to_csv(index=False)
        
        st.success("✅ รวมข้อมูลจากไฟล์ CSV เสร็จเรียบร้อย!")
        st.dataframe(merged_df.head())
        
        # ปุ่มดาวน์โหลดไฟล์ CSV
        st.download_button(
            label="📥 ดาวน์โหลดไฟล์ CSV",
            data=csv_output,
            file_name="merged_data.csv",
            mime="text/csv"
        )
        
        """
        # แปลง DataFrame เป็น Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            merged_df.to_excel(writer, index=False, sheet_name='Merged CSV')
        output.seek(0)

        st.success("✅ รวมข้อมูลจาก CSV และแปลงเป็น Excel สำเร็จแล้ว!")
        st.dataframe(merged_df.head())

        st.download_button(
            label="📥 ดาวน์โหลดไฟล์ Excel",
            data=output,
            file_name="merged_csv_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        """