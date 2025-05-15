import streamlit as st
import pandas as pd
import plotly.express as px

# -- โหลดไฟล์
st.title("📊 Ultra++ v5.1 : Dynamic Device Analyzer")

uploaded_file = st.file_uploader("📥 อัปโหลดไฟล์ Excel หรือ CSV", type=["xlsx", "csv"])

# แปลงเดือนภาษาไทย
def convert_thai_date(date_str):
    thai_months = {
        'ม.ค.': '01', 'ก.พ.': '02', 'มี.ค.': '03', 'เม.ย.': '04',
        'พ.ค.': '05', 'มิ.ย.': '06', 'ก.ค.': '07', 'ส.ค.': '08',
        'ก.ย.': '09', 'ต.ค.': '10', 'พ.ย.': '11', 'ธ.ค.': '12'
    }
    for th_month, num_month in thai_months.items():
        if th_month in date_str:
            return date_str.replace(th_month, num_month)
    return date_str

# แปลงฟิลด์วันที่
def convert_date(df):
    df['Availability Period'] = df['Availability Period'].astype(str).apply(convert_thai_date)
    df['Availability Period'] = pd.to_datetime(df['Availability Period'], format='%Y-%m')
    df['Month'] = df['Availability Period'].dt.to_period('M')
    months = sorted(df['Month'].dropna().unique().astype(str))
    return df, months

# -- Main
if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
    else:
        df = pd.read_excel(uploaded_file)

    df, months = convert_date(df)
    st.success(f"✅ โหลดไฟล์ {uploaded_file.name} เรียบร้อย")

    # -- Filter Section
    st.sidebar.header("🎛️ ฟิลเตอร์ข้อมูล")
    selected_month = st.sidebar.multiselect("เลือกเดือน", months, default=months)
    filtered_df = df[df['Month'].astype(str).isin(selected_month)]

    # --- Device Filtering Section ---
    st.sidebar.markdown("## 🔍 ค้นหาและเลือก Device")
    device_list_all = filtered_df['Device'].dropna().unique().tolist()
    device_list_all.sort()

    if "selected_devices" not in st.session_state:
        st.session_state.selected_devices = []
    if "search_text" not in st.session_state:
        st.session_state.search_text = ""
    if "reset_filter" not in st.session_state:
        st.session_state.reset_filter = False

    if st.session_state.reset_filter:
        st.session_state.selected_devices = []
        st.session_state.search_input = ""
        st.session_state.reset_filter = False
        st.rerun()

    search_text = st.sidebar.text_input("🔎 ค้นหา Device", value=st.session_state.search_text, key="search_input")

    if search_text:
        filtered_device_list = [d for d in device_list_all if search_text.lower() in d.lower()]
    else:
        filtered_device_list = device_list_all.copy()

    with st.sidebar.expander("📋 รายการ Device ที่พบ", expanded=True):
        st.dataframe(pd.DataFrame(filtered_device_list, columns=["Device"]), height=150)

    if st.sidebar.button("✅ เลือก Device ทั้งหมดที่พบ"):
        st.session_state.selected_devices = filtered_device_list.copy()

    if st.sidebar.button("❌ ล้างตัวเลือก"):
        st.session_state.reset_filter = True
        st.rerun()

    merged_options = list(set(filtered_device_list) | set(st.session_state.selected_devices))
    merged_options.sort()

    selected_devices = st.sidebar.multiselect(
        "📌 เลือก Device",
        options=merged_options,
        default=st.session_state.selected_devices,
        key="selected_devices"
    )

    if not selected_devices:
        st.sidebar.warning("⚠️ ยังไม่ได้เลือก Device ใดเลย")

    if selected_devices:
        filtered_df = filtered_df[filtered_df["Device"].isin(selected_devices)]

    st.info(f"🔎 พบข้อมูล: {len(filtered_df)} records หลังกรอง")
    st.dataframe(filtered_df, use_container_width=True)

    # --- Monthly Summary Section ---
    st.header("📈 สรุปข้อมูลแยกตามเดือน")
    df['Month'] = df['Month'].astype(str)
    cols_to_agg = [
        'Availability (%)',
        'จำนวนครั้ง Initializing', 'ระยะเวลา Initializing (seconds)',
        'จำนวนครั้ง Telemetry Failure', 'ระยะเวลา Telemetry Failure (seconds)',
        'จำนวนครั้ง Connecting', 'ระยะเวลา Connecting (seconds)'
    ]

    monthly_summary = df.groupby('Month')[cols_to_agg].mean().reset_index()
    st.dataframe(monthly_summary, use_container_width=True)

    st.subheader("📊 Availability (%) รายเดือน")
    fig_monthly = px.line(monthly_summary, x="Month", y="Availability (%)", markers=True)
    st.plotly_chart(fig_monthly, use_container_width=True)

    # --- Custom Plot Section ---
    exclude_cols = ["Description", "Source File", "Availability Period", "Month"]
    available_columns = [col for col in filtered_df.columns if col not in exclude_cols]

    st.header("🎨 Customize Your Plot (Ultra++ v5.1)")
    col1, col2 = st.columns(2)
    with col1:
        selected_x = st.selectbox("เลือกแกน X", options=available_columns)
    with col2:
        selected_y = st.selectbox("เลือกแกน Y", options=available_columns)

    col3, col4 = st.columns(2)
    with col3:
        graph_theme = st.selectbox("🎨 ธีมสี", ["Blue", "Coral", "Green", "Purple"])
    with col4:
        chart_size = st.select_slider("📐 ขนาดกราฟ", options=["เล็ก", "กลาง", "ใหญ่"], value="กลาง")

    add_trendline = st.checkbox("➕ เพิ่มเส้นเทรนด์ไลน์ (เฉพาะ Scatter)")
    show_marker = st.checkbox("✨ เพิ่มขนาด Marker (เฉพาะ Scatter)", value=True)

    theme_color = {
        "Blue": "#00BFFF",
        "Coral": "#FF7F50",
        "Green": "#32CD32",
        "Purple": "#800080"
    }[graph_theme]

    size_map = {
        "เล็ก": 500,
        "กลาง": 700,
        "ใหญ่": 1000
    }

    if selected_x and selected_y:
        if selected_x == selected_y:
            st.warning("🚫 ต้องเลือก X และ Y ที่ไม่ซ้ำกัน")
        else:
            fig = px.scatter(
                filtered_df,
                x=selected_x,
                y=selected_y,
                color_discrete_sequence=[theme_color],
                trendline="ols" if add_trendline else None
            ) if show_marker else px.scatter(
                filtered_df,
                x=selected_x,
                y=selected_y,
                color_discrete_sequence=[theme_color],
                trendline="ols" if add_trendline else None,
                markers=False
            )

            fig.update_layout(
                width=size_map[chart_size],
                height=int(size_map[chart_size] * 0.6),
                title=f"{selected_x} vs {selected_y}",
                margin=dict(l=40, r=40, t=40, b=40)
            )

            st.plotly_chart(fig, use_container_width=True)

    # --- Download Button
    csv_filtered = filtered_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="📥 ดาวน์โหลดข้อมูลที่กรองแล้ว",
        data=csv_filtered,
        file_name="filtered_data_v5.csv",
        mime="text/csv"
    )
    # --- Line Chart เปรียบเทียบ Availability รายเดือน แยกตาม Device ---
    st.header("📈 เปรียบเทียบ Availability (%) รายเดือนตาม Device")

    # สร้างตาราง pivot
    pivot_df = (
        filtered_df.groupby(['Month', 'Device'])['Availability (%)']
        .mean()
        .reset_index()
    )

    # แปลง Period เป็น datetime สำหรับ plot
    pivot_df['Month'] = pivot_df['Month'].astype(str)
    pivot_df['Month'] = pd.to_datetime(pivot_df['Month'])

    # Plot กราฟ
    fig_line = px.line(
        pivot_df,
        x='Month',
        y='Availability (%)',
        color='Device',
        markers=True,
        title='Availability (%) เปรียบเทียบรายเดือน',
    )

    fig_line.update_layout(
        xaxis_title='เดือน',
        yaxis_title='Availability (%)',
        width=900,
        height=500,
        hovermode='x unified',
        margin=dict(l=40, r=40, t=40, b=40)
    )

    st.plotly_chart(fig_line, use_container_width=True)

else:
    st.warning("🚨 กรุณาอัปโหลดไฟล์ข้อมูลก่อนเริ่ม")
