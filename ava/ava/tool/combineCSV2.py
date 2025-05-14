import os
import pandas as pd
import streamlit as st

# 🔹 กำหนดพาธ

input_folder = "D:/Develop/scada/ava/source_csv/convert_csv"
output_folder = os.path.join(input_folder, "combine_csv")
output_file = os.path.join(output_folder, "S1_JAN-MAR2025.csv")

def combine_csv_recursive(input_folder, output_file):
    try:
        # ตรวจสอบว่าโฟลเดอร์มีอยู่จริง
        if not os.path.exists(input_folder):
            st.error(f"❌ โฟลเดอร์ {input_folder} ไม่พบ")
            return None

        # ใช้ os.walk() เพื่อหาไฟล์ CSV ในทุกโฟลเดอร์ย่อย
        csv_files = []
        for root, _, files in os.walk(input_folder):
            for file in files:
                if file.endswith(".csv"):
                    csv_files.append(os.path.join(root, file))

        if not csv_files:
            st.warning("⚠️ ไม่มีไฟล์ CSV ในโฟลเดอร์ที่ระบุ")
            return None

        df_list = []

        for file_path in csv_files:
            try:
                df = pd.read_csv(file_path, skiprows=0)  # ปรับ skiprows ตามต้องการ
                df = df.dropna(how="all")  # ✅ ตัดบรรทัดว่างออก
                if df.empty:
                    st.warning(f"⚠️ ไฟล์ {file_path} ว่างเปล่าหลังจากลบบรรทัดว่าง!")
                else:
                    df_list.append(df)
            except Exception as e:
                st.error(f"❌ ไม่สามารถอ่านไฟล์ {file_path}: {e}")

        if df_list:
            df_combined = pd.concat(df_list, ignore_index=True)

            # ตรวจสอบและสร้างโฟลเดอร์ปลายทาง
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # บันทึกไฟล์ CSV
            df_combined.to_csv(output_file, index=False)
            st.success(f"✅ รวมไฟล์สำเร็จ! บันทึกที่ {output_file}")

            return df_combined
        else:
            st.warning("⚠️ ไม่มีข้อมูลที่สามารถรวมได้")
            return None

    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาด: {e}")
        return None

if __name__ == "__main__":
    df = combine_csv_recursive(input_folder, output_file)
    if df is not None:
        st.dataframe(df)
