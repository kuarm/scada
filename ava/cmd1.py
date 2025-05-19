import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

def show_month(df):
    # แปลงคอลัมน์เดือน
    df["Month"] = pd.to_datetime(df["Availability Period"], format="%Y-%m", errors="coerce")
    df["Month_num"] = df["Month"].dt.month
    month_names = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
                'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']
    df["Month_name"] = df["Month_num"].apply(lambda x: month_names[x - 1] if pd.notnull(x) else "")

    # Pivot table: row = Device, column = Month_name, values = Availability (%)
    pivot_df = df.pivot_table(
        index="Device",
        columns="Month_name",
        values="สั่งการสำเร็จ (%)",
        aggfunc="mean"
    )

    # เรียงลำดับคอลัมน์ตามเดือน
    pivot_df = pivot_df.reindex(columns=month_names)

    # เพิ่มคอลัมน์ค่าเฉลี่ยของแต่ละ Device
    pivot_df["Avg Availability (%)"] = pivot_df.mean(axis=1)

    # Reset index เพื่อให้ Device เป็นคอลัมน์
    pivot_df = pivot_df.reset_index()

    # จัดรูปแบบตัวเลขให้สวยงาม
    pivot_df = pivot_df.round(2)

    st.dataframe(pivot_df)
    
    return pivot_df

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
        df["สั่งการสำเร็จ (%)"] = df["สั่งการสำเร็จ (%)"].replace({",": "", "%": ""}, regex=True)
        df["สั่งการสำเร็จ (%)"] = pd.to_numeric(df["สั่งการสำเร็จ (%)"], errors="coerce")

        all_data.append(df)

    df_combined = pd.concat(all_data, ignore_index=True)

    option_func = ['สถานะ', 'ประเมินผล', 'Histogram', 'เปรียบเทียบทุกเดือน']
    option_submenu = ['ระบบจำหน่ายสายส่ง','สถานีไฟฟ้า']
    submenu_select = st.sidebar.radio(label="ระบบ: ", options = option_submenu)

    if submenu_select == 'ระบบจำหน่ายสายส่ง':
        title = 'อุปกรณ์ FRTU'
    else:
        title = 'สถานีไฟฟ้า'
    
    st.dataframe(df_combined)
    pivot_df = show_month(df_combined)

    fig_by_device = px.line(
        pivot_df,
        x="Device",
        y="สั่งการสำเร็จ (%)",
        color="Device",
        markers=True,
        title="📊 Availability (%) รายเดือนแยกตาม Device"
        )
    fig_by_device.update_layout(
        xaxis_title="เดือน",
        yaxis_title="Availability (%)",
        yaxis=dict(range=[0, 105]),
        hovermode="x unified"
        )
    st.plotly_chart(fig_by_device, use_container_width=True)