import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

# ---- Upload and Merge ----
uploaded_files = st.file_uploader("📁 อัปโหลดไฟล์ Excel (หลายไฟล์)", type=["xlsx", "xls"], accept_multiple_files=True)

if uploaded_files:
    all_data = []

    for uploaded_file in uploaded_files:
        df = pd.read_excel(uploaded_file)

        if "Availability Period" not in df.columns:
            st.warning(f"❌ ไม่มีคอลัมน์ 'Availability Period' ในไฟล์ {uploaded_file.name}")
            continue

        df["Month"] = pd.to_datetime(df["Availability Period"], format="%Y-%m", errors="coerce")
        df["Availability (%)"] = df["Availability (%)"].replace({",": "", "%": ""}, regex=True)
        df["Availability (%)"] = pd.to_numeric(df["Availability (%)"], errors="coerce")

        all_data.append(df)

    df_combined = pd.concat(all_data, ignore_index=True)

    # ---- Monthly Summary ----
    df_combined["Year"] = df_combined["Month"].dt.year
    selected_year = df_combined["Year"].mode()[0]  # ปีที่พบมากที่สุด

    # จำกัดแค่ปีเดียว เช่น 2025
    df_combined = df_combined[df_combined["Year"] == selected_year]

    monthly_avg = df_combined.groupby(df_combined["Month"].dt.month)["Availability (%)"].mean().reset_index()
    monthly_avg.columns = ["MonthNumber", "Availability (%)"]

    # เติมเดือนที่หายไป (ให้มีครบ 1-12)
    all_months_df = pd.DataFrame({"MonthNumber": list(range(1, 13))})
    monthly_avg = all_months_df.merge(monthly_avg, on="MonthNumber", how="left")
    #monthly_avg["Availability (%)"] = monthly_avg["Availability (%)"].fillna(0)

    # แปลงเลขเดือนเป็นชื่อ (ภาษาไทย/อังกฤษ)
    month_names = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
                   'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']
    monthly_avg["Month"] = monthly_avg["MonthNumber"].apply(lambda x: month_names[x-1])

    # ---- Bar Chart ----
    fig_bar = px.bar(
        monthly_avg,
        x="Month",
        y="Availability (%)",
        text=monthly_avg["Availability (%)"].round(1),
        color="Availability (%)",
        title=f"📊 Availability (%) เฉลี่ยรายเดือน (Bar Chart) - ปี {selected_year}"
    )
    fig_bar.update_layout(
        xaxis_title="เดือน",
        yaxis_title="Availability (%)",
        yaxis=dict(range=[0, 100]),
        showlegend=False,
        margin=dict(t=60, b=40)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # ---- Line Chart ----
    fig_line = px.line(
        monthly_avg,
        x="MonthNumber",
        y="Availability (%)",
        markers=True,
        text=monthly_avg["Availability (%)"].round(1),
        title=f"📈 Availability (%) เฉลี่ยรายเดือน (Line Chart) - ปี {selected_year}"
    )

    fig_line.update_traces(
        textposition="bottom center",  # 👈 อยู่ใต้ marker เพื่อลดปัญหาล้น
        connectgaps=False
    )

    fig_line.update_layout(
        xaxis=dict(
            title="เดือน",
            tickmode="array",
            tickvals=list(range(1, 13)),
            ticktext=month_names
        ),
        yaxis=dict(
            title="Availability (%)",
            range=[0, 105]  # 👈 เพิ่มเพดานนิดหน่อยกันล้น
        ),
        showlegend=False,
        margin=dict(t=80, b=40)  # 👈 เพิ่ม margin ด้านบน
    )

    st.plotly_chart(fig_line, use_container_width=True)
