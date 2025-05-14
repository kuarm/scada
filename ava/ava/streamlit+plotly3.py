# 🚀 Ultra++ v3.0 : Dynamic Filtering + Auto Graphs + Heatmap + Timeline Trend

import streamlit as st
import pandas as pd
import plotly.express as px

# --- Helper Functions ---

def convert_thai_date(date_str):
    thai_months = {'ม.ค.': '01', 'ก.พ.': '02', 'มี.ค.': '03', 'เม.ย.': '04',
                   'พ.ค.': '05', 'มิ.ย.': '06', 'ก.ค.': '07', 'ส.ค.': '08',
                   'ก.ย.': '09', 'ต.ค.': '10', 'พ.ย.': '11', 'ธ.ค.': '12'}
    for th_month, num_month in thai_months.items():
        if th_month in date_str:
            return date_str.replace(th_month, num_month)
    return date_str

def convert_date(df):
    df['Availability Period'] = df['Availability Period'].astype(str).apply(convert_thai_date)
    df['Availability Period'] = pd.to_datetime(df['Availability Period'], format='%m %Y')
    df['Month'] = df['Availability Period'].dt.to_period('M')
    return df

# --- Load Data ---
st.set_page_config(page_title="Ultra++ Dashboard", layout="wide")
st.title("📊 Ultra++ v3.0 | SCADA Device Analytics")

uploaded_file = st.file_uploader("📥 อัปโหลดไฟล์ Excel หรือ CSV", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
    else:
        df = pd.read_excel(uploaded_file)

    df = convert_date(df)

    if 'Source File' in df.columns:
        df = df.drop(columns=['Source File'])

    # --- Dynamic Filter ---
    st.sidebar.header("🔎 ตัวกรองข้อมูลแบบ Dynamic")
    months = sorted(df['Month'].dropna().unique().astype(str))
    month_selected = st.sidebar.multiselect("เลือกเดือน (เลือกหลายเดือนได้)", months, default=months)

    filtered_df = df[df['Month'].astype(str).isin(month_selected)].copy()

    numeric_cols = filtered_df.select_dtypes(include=['number']).columns.tolist()
    text_cols = filtered_df.select_dtypes(include=['object']).columns.tolist()

    with st.sidebar.expander("🎚️ ตัวกรองตัวเลข"):
        for col in numeric_cols:
            min_val, max_val = float(filtered_df[col].min()), float(filtered_df[col].max())
            val_range = st.slider(f"เลือกช่วง {col}", min_val, max_val, (min_val, max_val))
            filtered_df = filtered_df[(filtered_df[col] >= val_range[0]) & (filtered_df[col] <= val_range[1])]

    #with st.sidebar.expander("📝 ตัวกรองข้อความ"):
    #    for col in text_cols:
    #        options = filtered_df[col].dropna().unique().tolist()
    #        selected = st.multiselect(f"เลือก {col}", options, default=options)
    #        filtered_df = filtered_df[filtered_df[col].isin(selected)]

    # --- Device Filter แบบ Search + Select All ใน Expander
    with st.expander("🎛 Device Filter (Search + Control)"):
        device_list = sorted(filtered_df['Device'].dropna().unique())

        # Search Box
        search_device = st.text_input("🔍 ค้นหา Device", value="")
        
        # Filter ตามข้อความที่พิมพ์
        if search_device:
            filtered_device_list = [d for d in device_list if search_device.lower() in d.lower()]
        else:
            filtered_device_list = device_list

        # Checkbox "Select All"
        select_all = st.checkbox("🔢 เลือกทั้งหมด", value=True)

        # Multi-select ตามที่ค้นหาได้
        if select_all:
            selected_devices = st.multiselect(
                "เลือก Device ที่ต้องการ",
                filtered_device_list,
                default=filtered_device_list
            )
        else:
            selected_devices = st.multiselect(
                "เลือก Device ที่ต้องการ",
                filtered_device_list,
                default=[]
            )

        # ปุ่ม เพิ่ม/ลบ
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ เลือกทั้งหมด"):
                selected_devices = filtered_device_list
        with col2:
            if st.button("❌ ล้างทั้งหมด"):
                selected_devices = []

        # Filter ตาม selected devices
        if selected_devices:
            filtered_df = filtered_df[filtered_df['Device'].isin(selected_devices)]
        else:
            st.warning("⚠️ กรุณาเลือก Device อย่างน้อย 1 ตัว หรือเลือกทั้งหมด")

    st.success(f"✅ พบข้อมูล {len(filtered_df)} รายการหลังกรอง")
    st.dataframe(filtered_df, use_container_width=True)

    # --- Download filtered
    csv = filtered_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("📥 ดาวน์โหลดข้อมูลกรองแล้ว", csv, file_name="filtered_data.csv", mime="text/csv")

    # --- Auto Graphs ---
    st.header("📈 สร้างกราฟวิเคราะห์อัตโนมัติ")
    col1, col2, col3 = st.columns(3)

    all_columns = filtered_df.columns.tolist()

    with col1:
        x_axis = st.selectbox("เลือกแกน X", all_columns)
    with col2:
        y_axis = st.selectbox("เลือกแกน Y (เลือก None ได้)", ["None"] + numeric_cols)
    with col3:
        graph_type = st.selectbox("เลือกประเภทกราฟ", ["Auto", "Scatter", "Line", "Bar", "Histogram"])

    if graph_type == "Auto":
        if x_axis in numeric_cols and (y_axis != "None" and y_axis in numeric_cols):
            graph_type = "Scatter"
        elif x_axis in text_cols and (y_axis != "None" and y_axis in numeric_cols):
            graph_type = "Bar"
        elif x_axis in numeric_cols and y_axis == "None":
            graph_type = "Histogram"

    if graph_type == "Scatter" and x_axis != y_axis:
        fig = px.scatter(filtered_df, x=x_axis, y=y_axis, trendline="ols", color_discrete_sequence=["#00BFFF"])
        st.plotly_chart(fig, use_container_width=True)
    elif graph_type == "Line" and x_axis != y_axis:
        fig = px.line(filtered_df, x=x_axis, y=y_axis, markers=True, color_discrete_sequence=["#FF7F50"])
        st.plotly_chart(fig, use_container_width=True)
    elif graph_type == "Bar":
        fig = px.bar(filtered_df, x=x_axis, y=y_axis, color_discrete_sequence=["#32CD32"])
        st.plotly_chart(fig, use_container_width=True)
    elif graph_type == "Histogram":
        fig = px.histogram(filtered_df, x=x_axis, color_discrete_sequence=["#800080"])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("❗ ต้องเลือก X, Y ให้ไม่ซ้ำกันสำหรับ Scatter หรือ Line")

    # --- Bonus: Heatmap ---
    st.header("🔥 Heatmap ความสัมพันธ์ตัวเลข")
    if len(numeric_cols) >= 2:
        corr = filtered_df[numeric_cols].corr()
        fig = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale="RdBu_r")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ ต้องมีตัวเลขอย่างน้อย 2 คอลัมน์เพื่อสร้าง Heatmap")

    # --- Bonus: Timeline Trend ---
    st.header("📅 Timeline Trend (Device) ✨")
    if 'Device' in filtered_df.columns:
        timeline_col = st.selectbox("เลือกคอลัมน์ค่า Timeline", numeric_cols)
        timeline_df = filtered_df.copy()
        timeline_df['Month'] = pd.to_datetime(timeline_df['Month'].astype(str))
        fig = px.line(timeline_df, x='Month', y=timeline_col, color='Device', markers=True)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("🚨 กรุณาอัปโหลดไฟล์เพื่อเริ่มต้นวิเคราะห์")
