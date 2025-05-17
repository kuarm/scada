import pandas as pd
import streamlit as st
from io import BytesIO

# ตัวแปรเก็บข้อมูลทุกเดือนที่ upload มา
all_data = []

st.title("📊 เปรียบเทียบ Availability (%) รายเดือน")

uploaded_files = st.file_uploader("📁 อัปโหลดไฟล์ Excel (หลายไฟล์)", type=["xlsx", "xls"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        # อ่านไฟล์ Excel เป็น DataFrame
        df = pd.read_excel(uploaded_file)

        # ตรวจสอบว่ามีคอลัมน์ "Availability Period" หรือไม่
        if "Availability Period" not in df.columns:
            st.error(f"❌ ไฟล์ {uploaded_file.name} ไม่มีคอลัมน์ 'Availability Period'")
            continue

        # แปลงคอลัมน์ Availability Period เป็น datetime
        df["Month"] = pd.to_datetime(df["Availability Period"], format="%Y-%m", errors="coerce")

        # ลบ comma และ % แล้วแปลงเป็น float
        df["Availability (%)"] = df["Availability (%)"].replace({",": "", "%": ""}, regex=True)
        df["Availability (%)"] = pd.to_numeric(df["Availability (%)"], errors="coerce")

        # เก็บไว้รวมกันภายหลัง
        all_data.append(df)

    # รวมข้อมูลทุกไฟล์
    df_combined = pd.concat(all_data, ignore_index=True)

    # -------------------------------
    # คำนวณค่าเฉลี่ยรายเดือน
    monthly_summary = df_combined.groupby("Month")["Availability (%)"].mean().reset_index()

    # สร้างช่วงเดือนที่ต้องการแสดง (เช่น 2025-01 ถึง 2025-12)
    all_months = pd.date_range(start="2025-01-01", end="2025-12-01", freq='MS')
    df_full = pd.DataFrame({"Month": all_months})
    monthly_summary = df_full.merge(monthly_summary, on="Month", how="left")

    monthly_summary["Availability (%)"] = monthly_summary["Availability (%)"].fillna(0)

    # แสดงกราฟ bar chart
    import plotly.express as px

    fig_bar = px.bar(
        monthly_summary,
        x="Month",
        y="Availability (%)",
        text=monthly_summary["Availability (%)"].round(1),
        color="Availability (%)",
        title="📊 Availability (%) รายเดือน (Bar Chart)"
    )
    fig_bar.update_layout(
        xaxis_title="เดือน",
        yaxis_title="Availability (%)",
        yaxis=dict(range=[0, 100]),
        xaxis=dict(tickformat="%b %Y", tickangle=-45),
        showlegend=False,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # แสดงกราฟเส้น
    fig_line = px.line(
        monthly_summary,
        x="Month",
        y="Availability (%)",
        markers=True,
        title="📈 Availability (%) รายเดือน (Line Graph)"
    )
    fig_line.update_layout(
        xaxis=dict(tickformat="%b %Y", tickangle=-45),
        yaxis=dict(range=[0, 100]),
        showlegend=False,
    )
    st.plotly_chart(fig_line, use_container_width=True)
