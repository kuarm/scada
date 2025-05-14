import pandas as pd
import streamlit as st

# โหลดข้อมูล
file_path = "ava_test.xlsx"
df = pd.read_excel(file_path, sheet_name="Sheet4",header=0)

# แปลง Field change time เป็น datetime
df["Field change time"] = pd.to_datetime(df["Field change time"], errors="coerce")

# กำหนดช่วงเวลาที่ต้องการคำนวณ (ตัวอย่าง: 24 ชั่วโมงล่าสุด)
start_time = df["Field change time"].min()  # หรือกำหนดค่า เช่น pd.Timestamp("2024-03-08 00:00:00")
end_time = df["Field change time"].max()    # หรือกำหนดค่า เช่น pd.Timestamp("2024-03-08 23:59:59")

# กรองข้อมูลให้อยู่ในช่วงเวลาที่กำหนด
df_filtered = df[(df["Field change time"] >= start_time) & (df["Field change time"] <= end_time)].copy()

# ตรวจสอบว่ามีข้อมูลในช่วงเวลานั้นหรือไม่
if df_filtered.empty:
    st.write("❌ No data available in the selected time range!")
else:
    # เรียงข้อมูลตามเวลา
    df_filtered = df_filtered.sort_values("Field change time").reset_index(drop=True)

    # ดึงค่า Previous State และ Next State ของช่วงเวลานั้น
    first_state = df_filtered.iloc[0]["Message"]
    last_state = df_filtered.iloc[-1]["Message"]

    # คำนวณ Duration รวมระหว่างเวลาเริ่มต้นและสิ้นสุด
    total_duration = (df_filtered["Field change time"].max() - df_filtered["Field change time"].min()).total_seconds()

    # แสดงผลลัพธ์
    st.write(f"📌 **First State in Time Range:** {first_state}")
    st.write(f"📌 **Last State in Time Range:** {last_state}")
    st.write(f"⏳ **Total Duration in Selected Time Range:** {total_duration} seconds ({total_duration / 60:.2f} minutes)")

    # แสดงตารางผลลัพธ์
    st.write(df_filtered)
