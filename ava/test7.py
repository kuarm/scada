import pandas as pd
import streamlit as st

# โหลดข้อมูล
file_path = "ava.xlsx"
df = pd.read_excel(file_path)

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

    # หา First State และ Last State
    first_state_time = df_filtered.iloc[0]["Field change time"]
    last_state_time = df_filtered.iloc[-1]["Field change time"]
    first_state = df_filtered.iloc[0]["Message"]
    last_state = df_filtered.iloc[-1]["Message"]

    # คำนวณ Duration ก่อน First State
    before_first_state_duration = (first_state_time - start_time).total_seconds()

    # คำนวณ Duration หลัง Last State
    after_last_state_duration = (end_time - last_state_time).total_seconds()

    # คำนวณ Duration ภายในช่วงเวลา
    total_duration = (last_state_time - first_state_time).total_seconds()

    # แสดงผลลัพธ์
    st.write(f"📌 **First State:** {first_state} at {first_state_time}")
    st.write(f"📌 **Last State:** {last_state} at {last_state_time}")
    st.write(f"⏳ **Duration Before First State:** {before_first_state_duration} seconds ({before_first_state_duration / 60:.2f} minutes)")
    st.write(f"⏳ **Duration After Last State:** {after_last_state_duration} seconds ({after_last_state_duration / 60:.2f} minutes)")
    st.write(f"⏳ **Total Duration in Selected Time Range:** {total_duration} seconds ({total_duration / 60:.2f} minutes)")

    # สร้าง DataFrame แสดงผลช่วงเวลา
    duration_data = [
        {"Description": "Before First State", "Start Time": start_time, "End Time": first_state_time, "Duration (seconds)": before_first_state_duration},
        {"Description": "First to Last State", "Start Time": first_state_time, "End Time": last_state_time, "Duration (seconds)": total_duration},
        {"Description": "After Last State", "Start Time": last_state_time, "End Time": end_time, "Duration (seconds)": after_last_state_duration}
    ]

    df_duration = pd.DataFrame(duration_data)

    # แสดงตารางผลลัพธ์
    st.write("### ⏳ Duration Breakdown")
    st.write(df_duration)
