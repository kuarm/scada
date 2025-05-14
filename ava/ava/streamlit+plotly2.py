import streamlit as st
import pandas as pd
import plotly.express as px

# ✅ Helper - Convert Thai month names to standard date
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

# ✅ Function - Prepare and clean data
def prepare_data(df):
    if 'Availability Period' in df.columns:
        df['Availability Period'] = df['Availability Period'].astype(str).apply(convert_thai_date)
        df['Availability Period'] = pd.to_datetime(df['Availability Period'], format='%m %Y', errors='coerce')
        df['Month'] = df['Availability Period'].dt.to_period('M')
    if 'Source File' in df.columns:
        df = df.drop(columns=['Source File'], axis=0)
    return df

# ✅ เริ่มหน้า App
st.set_page_config(page_title="Ultra++ Analyzer", page_icon="🚀", layout="wide")
st.title("🚀 Ultra++ Dynamic Analyzer")

# ✅ Upload section
uploaded_file = st.file_uploader("📥 อัปโหลดไฟล์ Excel หรือ CSV", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
    else:
        df = pd.read_excel(uploaded_file)

    df = prepare_data(df)

    st.success(f"✅ โหลดไฟล์: {uploaded_file.name} สำเร็จแล้ว")
    
    # -----------------------
    # 🔥 Filter Section
    # -----------------------
    st.header("🎛️ ตัวกรองข้อมูล (Dynamic)")
    reset_filter = st.button("🔄 รีเซ็ตตัวกรอง")

    if reset_filter:
        st.session_state['filtered_df'] = df.copy()

    # เตรียมข้อมูล
    if 'filtered_df' not in st.session_state:
        st.session_state['filtered_df'] = df.copy()

    filtered_df = st.session_state['filtered_df']

    numeric_cols = filtered_df.select_dtypes(include=['number']).columns.tolist()
    text_cols = filtered_df.select_dtypes(include=['object']).columns.tolist()

    with st.expander("🔢 กรองข้อมูลตัวเลข", expanded=True):
        for col in numeric_cols:
            col_data = filtered_df[col].dropna()
            if col_data.empty:
                continue
            if pd.api.types.is_integer_dtype(col_data) or (col_data == col_data.astype(int)).all():
                min_val = int(col_data.min())
                max_val = int(col_data.max())
                step = 1
            else:
                min_val = float(col_data.min())
                max_val = float(col_data.max())
                step = 0.01

            value = st.slider(
                f"{col}",
                min_value=min_val,
                max_value=max_val,
                value=(min_val, max_val),
                step=step
            )

            filtered_df = filtered_df[(filtered_df[col] >= value[0]) & (filtered_df[col] <= value[1])]

    with st.expander("🔤 กรองข้อมูลตัวอักษร", expanded=False):
        for col in text_cols:
            options = filtered_df[col].dropna().unique().tolist()
            selected = st.multiselect(f"{col}", options, default=options)
            filtered_df = filtered_df[filtered_df[col].isin(selected)]

    # -----------------------
    # 📥 Download Section
    # -----------------------
    st.info(f"📊 พบข้อมูลทั้งหมด {len(filtered_df)} records หลังการกรอง")
    st.dataframe(filtered_df, use_container_width=True)

    csv_filtered = filtered_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="📥 ดาวน์โหลดข้อมูลที่กรอง (CSV)",
        data=csv_filtered,
        file_name="filtered_data.csv",
        mime="text/csv"
    )

    # -----------------------
    # 📈 Graph Section
    # -----------------------
        # 📈 วิเคราะห์ความสัมพันธ์ระหว่างตัวแปร (Ultra++ v2.6)

    st.header("📈 วิเคราะห์ความสัมพันธ์ระหว่างตัวแปร (Ultra++ v2.6 ป้องกัน Duplicate Columns)")

    graph_col1, graph_col2, graph_col3 = st.columns(3)

    all_columns = filtered_df.columns.tolist()
    numeric_cols = filtered_df.select_dtypes(include=['number']).columns.tolist()
    text_cols = filtered_df.select_dtypes(include=['object']).columns.tolist()

    with graph_col1:
        x_axis = st.selectbox("เลือกแกน X", all_columns)
    with graph_col2:
        y_axis = st.selectbox("เลือกแกน Y (หรือเลือก None)", ["None"] + numeric_cols)
    with graph_col3:
        graph_type = st.selectbox("เลือกประเภทกราฟ (หรือ Auto)", ["Auto", "Scatter Plot", "Line Plot", "Bar Plot"])

    # --- Logic แนะนำประเภทกราฟ
    auto_selected_graph = None

    if graph_type == "Auto":
        if (x_axis in numeric_cols) and (y_axis != "None" and y_axis in numeric_cols):
            if x_axis == y_axis:
                auto_selected_graph = "Histogram"
                st.info("ℹ️ เลือก X และ Y ซ้ำกัน: เปลี่ยนเป็น Histogram ให้อัตโนมัติ")
            else:
                auto_selected_graph = "Scatter Plot"
        elif (x_axis in text_cols) and (y_axis != "None" and y_axis in numeric_cols):
            auto_selected_graph = "Bar Plot"
        elif (x_axis in numeric_cols) and (y_axis == "None"):
            auto_selected_graph = "Histogram"
        else:
            st.warning("🛑 กราฟอัตโนมัติยังไม่รองรับการจับคู่คอลัมน์นี้ กรุณาเลือกเอง")
    else:
        auto_selected_graph = graph_type  # ถ้าไม่ Auto, ใช้ตามที่เลือก

    # --- วาดกราฟ
    if auto_selected_graph:

        if auto_selected_graph == "Scatter Plot":
            if (x_axis in numeric_cols) and (y_axis != "None" and y_axis in numeric_cols):
                if x_axis != y_axis:
                    fig = px.scatter(
                        filtered_df,
                        x=x_axis,
                        y=y_axis,
                        trendline="ols",
                        title=f"🔵 Scatter Plot: {x_axis} vs {y_axis}",
                        color_discrete_sequence=["#00BFFF"]
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("❌ Scatter Plot ไม่สามารถใช้ X และ Y เป็นคอลัมน์เดียวกันได้")
            else:
                st.error("❌ Scatter Plot ต้องเลือก X และ Y เป็นตัวเลข")

        elif auto_selected_graph == "Line Plot":
            if (x_axis in numeric_cols) and (y_axis != "None" and y_axis in numeric_cols):
                if x_axis != y_axis:
                    fig = px.line(
                        filtered_df,
                        x=x_axis,
                        y=y_axis,
                        title=f"🟠 Line Plot: {x_axis} vs {y_axis}",
                        markers=True,
                        color_discrete_sequence=["#FF7F50"]
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("❌ Line Plot ไม่สามารถใช้ X และ Y เป็นคอลัมน์เดียวกันได้")
            else:
                st.error("❌ Line Plot ต้องเลือก X และ Y เป็นตัวเลข")

        elif auto_selected_graph == "Bar Plot":
            if (y_axis != "None" and y_axis in numeric_cols):
                fig = px.bar(
                    filtered_df,
                    x=x_axis,
                    y=y_axis,
                    title=f"🟢 Bar Plot: {x_axis} vs {y_axis}",
                    color_discrete_sequence=["#32CD32"]
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("❌ Bar Plot ต้องเลือก Y เป็นตัวเลข")

        elif auto_selected_graph == "Histogram":
            fig = px.histogram(
                filtered_df,
                x=x_axis,
                title=f"🟣 Histogram: Distribution of {x_axis}",
                color_discrete_sequence=["#800080"]
            )
            st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("🚨 กรุณาอัปโหลดไฟล์ Excel หรือ CSV ก่อนเริ่มวิเคราะห์ข้อมูล")

