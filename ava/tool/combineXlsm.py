import pandas as pd
from pathlib import Path
import streamlit as st

# โฟลเดอร์ที่เก็บไฟล์ Excel
folder_path = Path("D:\ML\scada\ava\source_csv\convert_csv\ไฟล์ข้อมูล_%AVA")  # ปรับตาม path ของคุณ

# หาไฟล์ทั้งหมดที่นามสกุล .xlsm และ .xlsx
all_files = list(folder_path.glob("*.xlsm")) + list(folder_path.glob("*.xlsx"))

combined_df = pd.DataFrame()

for file in all_files:
    try:
        # โหลดไฟล์และอ่านชื่อ sheet แรก
        xls = pd.ExcelFile(file, engine="openpyxl")
        sheet_name = xls.sheet_names[0]

        # อ่านข้อมูลใน sheet แรก
        df = pd.read_excel(xls, sheet_name=sheet_name)

        # เพิ่มคอลัมน์แหล่งที่มา (optional)
        df['source_file'] = file.name
        # รวมข้อมูล
        combined_df = pd.concat([combined_df, df], ignore_index=True)
    except Exception as e:
        print(f"❌ Error reading {file.name}: {e}")

# บันทึกผลลัพธ์รวม
combined_df.to_excel("combined_result.xlsx", index=False)
