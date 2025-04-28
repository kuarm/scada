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

    # --- ส่วนสร้างกราฟ Auto Intelligent
    st.header("📈 Auto Intelligent Graph Generator")

    col_plot1, col_plot2 = st.columns(2)
    with col_plot1:
        selected_x = st.selectbox("เลือกแกน X (Auto)", options=filtered_df.columns)
    with col_plot2:
        selected_y = st.selectbox("เลือกแกน Y (Auto)", options=filtered_df.columns)

    auto_graph_type = st.radio("เลือกรูปแบบแนะนำ", ["Auto Suggest", "กำหนดเอง"], horizontal=True)

    if selected_x and selected_y:
        if selected_x == selected_y:
            st.warning("🚫 ต้องเลือก X และ Y คนละคอลัมน์กัน")
        else:
            if auto_graph_type == "Auto Suggest":
                # ตรวจสอบประเภทข้อมูล
                x_dtype = str(filtered_df[selected_x].dtype)
                y_dtype = str(filtered_df[selected_y].dtype)

                if "object" in x_dtype and "float" in y_dtype or "int" in y_dtype:
                    graph_type = "Bar"
                elif "float" in x_dtype or "int" in x_dtype and ("float" in y_dtype or "int" in y_dtype):
                    graph_type = "Scatter"
                else:
                    graph_type = "Bar"  # Default fallback

            else:
                graph_type = st.selectbox("เลือกประเภทกราฟ (Manual)", ["Scatter", "Line", "Bar", "Box", "Histogram"])

            # วาดกราฟตามประเภท
            if graph_type == "Scatter":
                fig = px.scatter(
                    filtered_df,
                    x=selected_x,
                    y=selected_y,
                    color_discrete_sequence=["#636EFA"],
                    trendline="ols",
                    title=f"Scatter: {selected_x} vs {selected_y}"
                )
            elif graph_type == "Line":
                fig = px.line(
                    filtered_df,
                    x=selected_x,
                    y=selected_y,
                    markers=True,
                    color_discrete_sequence=["#EF553B"],
                    title=f"Line Plot: {selected_x} vs {selected_y}"
                )
            elif graph_type == "Bar":
                fig = px.bar(
                    filtered_df,
                    x=selected_x,
                    y=selected_y,
                    text_auto=True,
                    color_discrete_sequence=["#00CC96"],
                    title=f"Bar Chart: {selected_x} vs {selected_y}"
                )
            elif graph_type == "Box":
                fig = px.box(
                    filtered_df,
                    x=selected_x,
                    y=selected_y,
                    title=f"Box Plot: {selected_x} vs {selected_y}"
                )
            elif graph_type == "Histogram":
                fig = px.histogram(
                    filtered_df,
                    x=selected_x,
                    title=f"Histogram: {selected_x}"
                )

            # อัปเดตขนาดและธีม
            fig.update_layout(
                height=600 if len(filtered_df) > 50 else 400,
                plot_bgcolor="#F9F9F9",
                paper_bgcolor="#F9F9F9",
                font=dict(size=14)
            )

            st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("🚨 กรุณาอัปโหลดไฟล์เพื่อเริ่มต้นวิเคราะห์")
