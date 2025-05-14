import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------
# ฟังก์ชันแปลงวันที่ไทย -> สากล
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

# --- เตรียมข้อมูล
def prepare_data(df):
    # แปลงวันที่
    if 'Availability Period' in df.columns:
        df['Availability Period'] = df['Availability Period'].astype(str).apply(convert_thai_date)
        df['Availability Period'] = pd.to_datetime(df['Availability Period'], format='%m %Y', errors='coerce')

    # แก้ไข Month ให้เป็น datetime
    if 'Month' not in df.columns and 'Availability Period' in df.columns:
        df['Month'] = df['Availability Period'].dt.to_period('M')

    if 'Month' in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df['Month']):
            try:
                df['Month'] = pd.to_datetime(df['Month'].astype(str), format="%Y-%m")
            except:
                df['Month'] = pd.to_datetime(df['Month'], errors='coerce')

    # ลบคอลัมน์ที่ไม่ใช้
    for col in ['Availability Period', 'Source File']:
        if col in df.columns:
            df = df.drop(columns=[col])

    return df

# --- เริ่มแอป
st.title("📊 วิเคราะห์ข้อมูลอุปกรณ์ (Ultra Bonus Version)")

uploaded_file = st.file_uploader("📥 อัปโหลดไฟล์ Excel หรือ CSV", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
    else:
        df = pd.read_excel(uploaded_file)

    st.success(f"✅ โหลดไฟล์: {uploaded_file.name} เรียบร้อย")

    df = prepare_data(df)
    
    # --- Filter Area
    st.header("🔎 ตัวกรองข้อมูล (Dynamic + Reset)")

    filtered_df = df.copy()

    # Button รีเซ็ต Filters
    if st.button("🔄 รีเซ็ตตัวกรองทั้งหมด"):
        st.experimental_rerun()

    numeric_cols = filtered_df.select_dtypes(include=['number']).columns.tolist()
    text_cols = filtered_df.select_dtypes(include=['object']).columns.tolist()
    datetime_cols = filtered_df.select_dtypes(include=['datetime', 'datetimetz']).columns.tolist()

    with st.expander("🎛️ ตัวกรองข้อมูล (Numeric)", expanded=True):
        for col in numeric_cols:
            min_val = float(filtered_df[col].min())
            max_val = float(filtered_df[col].max())
            start_val, end_val = st.number_input(
                f"ช่วง {col}",
                min_value=min_val,
                max_value=max_val,
                value=(min_val, max_val),
                step=1.0,
                format="%.2f"
            )
            filtered_df = filtered_df[(filtered_df[col] >= start_val) & (filtered_df[col] <= end_val)]

    with st.expander("🔤 ตัวกรองข้อมูล (Text)", expanded=True):
        for col in text_cols:
            options = filtered_df[col].dropna().unique().tolist()
            selected_options = st.multiselect(f"เลือก {col}", options, default=options)
            if selected_options:
                filtered_df = filtered_df[filtered_df[col].isin(selected_options)]

    with st.expander("🕒 ตัวกรองข้อมูล (Datetime)", expanded=False):
        for col in datetime_cols:
            min_date = filtered_df[col].min()
            max_date = filtered_df[col].max()
            selected_date_range = st.date_input(f"เลือกช่วง {col}", (min_date, max_date))
            if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
                start_date, end_date = selected_date_range
                filtered_df = filtered_df[(filtered_df[col] >= start_date) & (filtered_df[col] <= end_date)]

    st.info(f"🔍 พบข้อมูลหลังกรองทั้งหมด: {len(filtered_df)} rows")
    st.dataframe(filtered_df, use_container_width=True)

    # --- ดาวน์โหลดข้อมูล
    csv_filtered = filtered_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="📥 ดาวน์โหลดข้อมูลที่กรอง (CSV)",
        data=csv_filtered,
        file_name="filtered_data.csv",
        mime="text/csv"
    )

    # --- Plot Area
    st.header("📈 สร้างกราฟความสัมพันธ์ระหว่างคอลัมน์")

    col1, col2, col3 = st.columns(3)
    with col1:
        x_axis = st.selectbox("เลือกแกน X", options=numeric_cols)
    with col2:
        y_axis = st.selectbox("เลือกแกน Y", options=numeric_cols)
    with col3:
        graph_type = st.selectbox("เลือกประเภทกราฟ", ["Scatter Plot", "Line Plot", "Bar Plot"])

    if x_axis and y_axis:
        if graph_type == "Scatter Plot":
            fig = px.scatter(
                filtered_df,
                x=x_axis,
                y=y_axis,
                trendline="ols",
                title=f"Scatter Plot: {x_axis} vs {y_axis}"
            )
        elif graph_type == "Line Plot":
            fig = px.line(
                filtered_df,
                x=x_axis,
                y=y_axis,
                markers=True,
                title=f"Line Plot: {x_axis} vs {y_axis}"
            )
        elif graph_type == "Bar Plot":
            fig = px.bar(
                filtered_df,
                x=x_axis,
                y=y_axis,
                title=f"Bar Plot: {x_axis} vs {y_axis}"
            )

        st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("🚨 กรุณาอัปโหลดไฟล์ Excel หรือ CSV ก่อนเริ่มวิเคราะห์")
