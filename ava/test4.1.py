import pandas as pd
import streamlit as st

# โหลดข้อมูลจากไฟล์ Excel
file_path = "ava_test.xlsx"  # เปลี่ยนเป็น path ของไฟล์คุณ
df = pd.read_excel(file_path, sheet_name="Sheet5",header=0)

# แปลงคอลัมน์ "Field change time" เป็น datetime
df["Field change time"] = pd.to_datetime(df["Field change time"], errors="coerce")

# ตรวจสอบ Message ที่มีอยู่ทั้งหมด
st.write("🔍 Unique Messages in Dataset:")
st.write(df["Message"].unique())

# ตรวจสอบ Message ที่เกี่ยวข้องกับ "Initializing"
st.write("\n✅ Messages ที่เกี่ยวกับ 'Initializing':")
st.write(df[df["Message"].str.contains("Initializing", na=False, case=False)]["Message"].unique())

# ตรวจสอบ Message ที่เกี่ยวข้องกับ "Connecting"
st.write("\n✅ Messages ที่เกี่ยวกับ 'Connecting':")
st.write(df[df["Message"].str.contains("Connecting", na=False, case=False)]["Message"].unique())

# กรองข้อความที่เกี่ยวข้อง
df_start = df[df["Message"].str.contains("Connecting", na=False, case=False) & df["Message"].str.contains("Initializing", na=False, case=False)].copy()
df_end = df[df["Message"].str.contains("Initializing", na=False, case=False) & df["Message"].str.contains("Online", na=False, case=False)].copy()

# แสดงจำนวนข้อความที่พบ
st.write("✅ พบข้อความเริ่มต้น:", len(df_start))
st.write("✅ พบข้อความสิ้นสุด:", len(df_end))

if df_start.empty or df_end.empty:
    print("❌ ไม่มีข้อมูลที่ตรง กรุณาตรวจสอบไฟล์ Excel")
else:
    # รีเนมคอลัมน์เพื่อความชัดเจน
    df_start = df_start.rename(columns={"Field change time": "Start Time"})
    df_end = df_end.rename(columns={"Field change time": "End Time"})

    df_start = df_start.sort_values("Start Time")
    df_end = df_end.sort_values("End Time")

    df_merged = pd.merge_asof(df_start, df_end, left_on="Start Time", right_on="End Time", direction="forward")

    # คำนวณระยะเวลา
    df_merged["Duration (seconds)"] = (df_merged["End Time"] - df_merged["Start Time"]).dt.total_seconds()

    st.write("📊 ผลลัพธ์:")
    st.write(df_merged)

st.write("------------------------")
# เรียงข้อมูลตามเวลา
df = df.sort_values("Field change time").reset_index(drop=True)

# ตรวจสอบว่ามี Message อะไรบ้าง
st.write("🔍 ตรวจสอบ Message ทั้งหมดในไฟล์:")
st.write(df["Message"].unique())

# ตรวจสอบ Message ที่มี "Initializing" (Partial Match)
st.write("✅ Messages ที่เกี่ยวกับ 'Initializing':")
st.write(df[df["Message"].str.contains("Initializing", na=False, case=False)]["Message"].unique())

# ดึงเฉพาะข้อความที่เกี่ยวข้องกับ Initializing
state_start = "Remote unit state changed from Connecting to Initializing."
state_end = "Remote unit state changed from Initializing to Online."

# Partial Match เพื่อหาข้อความที่เกี่ยวข้อง
df_start = df[df["Message"].str.contains("Connecting to Initializing", na=False, case=False)].copy()
df_end = df[df["Message"].str.contains("Initializing to Online", na=False, case=False)].copy()

df_start = df[df["Message"] == state_start].rename(columns={"Field change time": "Start Time"})
df_end = df[df["Message"] == state_end].rename(columns={"Field change time": "End Time"})

# แสดงผลลัพธ์หลังกรอง
st.write("✅ Message Start พบทั้งหมด:", len(df_start))
st.write("✅ Message End พบทั้งหมด:", len(df_end))

# ตรวจสอบถ้ามีค่าใน df_start และ df_end
if df_start.empty or df_end.empty:
    st.write("❌ ไม่มีข้อมูลที่ตรงกับข้อความที่กำหนด กรุณาตรวจสอบในไฟล์ Excel")
else:
    # รวมข้อมูลโดยใช้เวลาเป็นตัวเชื่อม
    df_merged = pd.merge(df_start, df_end, how="outer")

# คำนวณระยะเวลา (Duration) ของ State "Initializing"
df_merged["Duration (seconds)"] = (df_merged["End Time"] - df_merged["Start Time"]).dt.total_seconds()

# แสดงผลลัพธ์
st.write("📊 ผลลัพธ์:")
st.write(df_merged)
