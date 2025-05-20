import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

def show_month(df):
    df_pivot = df.copy()

    # แปลงคอลัมน์เดือน
    df_pivot["Month"] = pd.to_datetime(df_pivot["Availability Period"], format="%Y-%m", errors="coerce")
    df_pivot["Month_num"] = df_pivot["Month"].dt.month

    month_names = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
                   'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']
    df_pivot["Month_name"] = df_pivot["Month_num"].apply(lambda x: month_names[int(x) - 1] if pd.notnull(x) else "")

    st.write("ค่าไม่ใช่ตัวเลข (จะถูกแปลงเป็น NaN):")
    st.write(df_pivot[df_pivot["สั่งการสำเร็จ (%)"].isnull()])

    # Pivot: row = Device, col = month, val = success %
    pivot_df = df_pivot.pivot_table(
        index="Device",
        columns="Month_name",
        values="สั่งการสำเร็จ (%)",
        aggfunc="mean"
    )

    st.write("Pivot แล้ว:")
    st.dataframe(pivot_df)

    st.write("ตรวจอุปกรณ์ที่ไม่มีข้อมูลทุกเดือน:")
    st.write(pivot_df[pivot_df.drop(columns="Avg สั่งการสำเร็จ (%)").isnull().all(axis=1)])

    # ตรวจอุปกรณ์ที่ไม่มีข้อมูลเลย
    null_mask = pivot_df.drop(columns="Avg สั่งการสำเร็จ (%)").isnull().all(axis=1)
    devices_all_null = pivot_df[null_mask].index.tolist()

    # เรียงเดือน
    pivot_df = pivot_df.reindex(columns=month_names)

    # ค่าเฉลี่ย (ยังเป็น float ตอนนี้)
    pivot_df["Avg สั่งการสำเร็จ (%)"] = pivot_df.mean(axis=1, skipna=True)

    # คัดลอกเพื่อเช็คอุปกรณ์ที่ไม่มีข้อมูลเลย
    null_mask = pivot_df.drop(columns="Avg สั่งการสำเร็จ (%)").isnull().all(axis=1)
    devices_all_null = pivot_df[null_mask].index.tolist()
    st.write(devices_all_null)
    # จัดรูปแบบเปอร์เซ็นต์ (xx.xx%) ถ้าไม่ใช่ NaN
    def format_percent(val):
        return f"{val:.2f}%" if pd.notnull(val) else ""

    for col in month_names + ["Avg สั่งการสำเร็จ (%)"]:
        if col in pivot_df.columns:
            pivot_df[col] = pivot_df[col].apply(format_percent)

    # Reset index
    pivot_df = pivot_df.reset_index()

    return pivot_df, devices_all_null

# ---- Upload and Merge ----
uploaded_files = st.file_uploader("📁 อัปโหลดไฟล์ Excel (หลายไฟล์)", type=["xlsx", "xls"], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    
    for uploaded_file in uploaded_files:
        df = pd.read_excel(uploaded_file)

        if "Availability Period" not in df.columns:
            st.warning(f"❌ ไม่มีคอลัมน์ 'Availability Period' ในไฟล์ {uploaded_file.name}")
            
        #df["สั่งการสำเร็จ (%)"] = df["สั่งการสำเร็จ (%)"].replace({",": "", "%": "", "": None}, regex=True)
        #df["สั่งการสำเร็จ (%)"] = pd.to_numeric(df["สั่งการสำเร็จ (%)"], errors="coerce")

        df["Month"] = pd.to_datetime(df["Availability Period"], format="%Y-%m", errors="coerce")
        df["สั่งการสำเร็จ (%)"] = df["สั่งการสำเร็จ (%)"].replace({",": "", "%": ""}, regex=True)

        #df["สั่งการสำเร็จ (%)"] = df["สั่งการสำเร็จ (%)"].astype(str).str.replace(",", "").str.replace("%", "").str.strip()
        df["สั่งการสำเร็จ (%)"] = pd.to_numeric(df["สั่งการสำเร็จ (%)"], errors="coerce")
        
        all_data.append(df)

    df_combined = pd.concat(all_data, ignore_index=True)

    format_dict = {
        "สั่งการทั้งหมด": "{:,.0f}",       # จำนวนเต็ม มี comma
        "สั่งการสำเร็จ": "{:,.0f}",        # จำนวนเต็ม มี comma
        "สั่งการสำเร็จ (%)": "{:.2f}"     # ทศนิยม 2 ตำแหน่ง
    }

    option_func = ['สถานะ', 'ประเมินผล', 'Histogram', 'เปรียบเทียบทุกเดือน']
    option_submenu = ['ระบบจำหน่ายสายส่ง','สถานีไฟฟ้า']
    submenu_select = st.sidebar.radio(label="ระบบ: ", options = option_submenu)

    if submenu_select == 'ระบบจำหน่ายสายส่ง':
        title = 'อุปกรณ์ FRTU'
    else:
        title = 'สถานีไฟฟ้า'
    
    #st.dataframe(df_combined)

    ### ✅
    st.info(f"✅ สรุป สั่งการสำเร็จ (%) แต่ละ {title} แยกตามเดือน")
    #pivot_df = pivot_df.style.format(format_dict)
    pivot_df, devices_all_null = show_month(df_combined)
    #st.dataframe(pivot_df)
    #st.write(devices_all_null)

        

    device_options = pivot_df_["Device"].unique()
    selected_devices = st.multiselect("เลือก Device ที่ต้องการแสดง", device_options, default=device_options)

    pivot_df_filtered = pivot_df[pivot_df["Device"].isin(selected_devices)]

    df_plot = pivot_df_filtered.melt(id_vars=["Device"], 
                        value_vars=[col for col in pivot_df.columns if col not in ["Device", "Avg สั่งการสำเร็จ (%)"]],
                        var_name="เดือน", 
                        value_name="สั่งการสำเร็จ (%)")

    # plot line chart
    fig_line = px.line(df_plot, 
                x="เดือน", 
                y="สั่งการสำเร็จ (%)", 
                color="Device", 
                markers=True,
                title="📈 สั่งการสำเร็จ (%) รายเดือนแยกตาม Device")

    fig_line.update_layout(xaxis_title="เดือน", yaxis_title="สั่งการสำเร็จ (%)", yaxis=dict(range=[0, 105]))
    

    fig_bar = px.bar(pivot_df_filtered, 
              x="Device", 
              y="Avg สั่งการสำเร็จ (%)", 
              text="Avg สั่งการสำเร็จ (%)", 
              title="📊 ค่าเฉลี่ยสั่งการสำเร็จ (%) ของแต่ละ Device")

    fig_bar.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig_bar.update_layout(xaxis_tickangle=-45, yaxis_range=[0, 105], yaxis_title="Avg สั่งการสำเร็จ (%)")
    
    # ✅ Scatter plot: แสดง Avg ของแต่ละ Device
    fig3 = px.scatter(
        pivot_df,
        x="Device",
        y="Avg สั่งการสำเร็จ (%)",
        text="Avg สั่งการสำเร็จ (%)",
        color="Avg สั่งการสำเร็จ (%)",
        color_continuous_scale="Viridis",
        title="🔵 Scatter: ค่าเฉลี่ยสั่งการสำเร็จ (%) ของแต่ละ Device"
    )
    fig3.update_traces(textposition="top center")
    fig3.update_layout(xaxis_tickangle=-45, yaxis_range=[0, 105])
    

    # แปลง wide → long เพื่อดู scatter รายเดือน
    df_scatter = pivot_df.melt(
        id_vars=["Device"], 
        value_vars=[col for col in pivot_df.columns if col not in ["Device", "Avg สั่งการสำเร็จ (%)"]],
        var_name="เดือน", 
        value_name="สั่งการสำเร็จ (%)"
    )

    fig3_month = px.scatter(
        df_scatter,
        x="Device",
        y="สั่งการสำเร็จ (%)",
        color="เดือน",
        title="🔵 Scatter: สั่งการสำเร็จ (%) รายเดือนตาม Device"
    )
    fig3_month.update_layout(xaxis_tickangle=-45, yaxis_range=[0, 105])
    

    # Histogram จากค่าเฉลี่ยของแต่ละ Device
    fig4 = px.histogram(
        pivot_df,
        x="Avg สั่งการสำเร็จ (%)",
        nbins=10,
        title="📊 Histogram: ความถี่ของค่าเฉลี่ยสั่งการสำเร็จ (%)",
        color_discrete_sequence=["#0072B2"]
    )
    fig4.update_layout(xaxis_title="Avg สั่งการสำเร็จ (%)", yaxis_title="จำนวน Device")
    

    # melt ก่อน
    df_hist = df_scatter.copy()

    fig4_month = px.histogram(
        df_hist,
        x="สั่งการสำเร็จ (%)",
        color="เดือน",
        nbins=10,
        barmode="overlay",  # หรือ "group"
        title="📊 Histogram: สั่งการสำเร็จ (%) แยกตามเดือน"
    )
    fig4_month.update_layout(xaxis_title="สั่งการสำเร็จ (%)", yaxis_title="จำนวน")
    

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Line Chart", 
    "📊 Bar Chart", 
    "🔵 Scatter (Avg)", 
    "🔵 Scatter (รายเดือน)", 
    "📊 Histogram (Avg)", 
    "📊 Histogram (รายเดือน)"
])

    """
    with tab1:
        st.plotly_chart(fig_line, use_container_width=True)

    with tab2:
        st.plotly_chart(fig_bar, use_container_width=True)

    with tab3:
        st.plotly_chart(fig3, use_container_width=True)

    with tab4:
        st.plotly_chart(fig3_month, use_container_width=True)

    with tab5:
        st.plotly_chart(fig4, use_container_width=True)

    with tab6:
        st.plotly_chart(fig4_month, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Line Chart")
        st.plotly_chart(fig_line, use_container_width=True, key="line_chart")

    with col2:
        st.subheader("🔵 Scatter (Avg)")
        st.plotly_chart(fig3, use_container_width=True, key="scatter_avg")

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("📊 Histogram (Avg)")
        st.plotly_chart(fig4, use_container_width=True, key="histogram_avg")

    with col4:
        st.subheader("📊 Histogram (รายเดือน)")
        st.plotly_chart(fig4_month, use_container_width=True, key="histogram_month")
    
    # Tabs แยกประเภทกราฟ
    tab1, tab2 = st.tabs(["📊 กราฟรวม", "🧪 เปรียบเทียบ"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📈 Line Chart")
            st.plotly_chart(fig_line, use_container_width=True, key="line_chart_tab1")
        with col2:
            st.subheader("🔵 Scatter (Avg)")
            st.plotly_chart(fig3, use_container_width=True, key="scatter_avg_tab1")

    with tab2:
        col3, col4 = st.columns(2)
        with col3:
            st.subheader("🔵 Scatter รายเดือน")
            st.plotly_chart(fig3_month, use_container_width=True, key="scatter_month_tab2")
        with col4:
            st.subheader("📊 Bar Chart: ค่าเฉลี่ยแต่ละ Device")
            st.plotly_chart(fig_bar, use_container_width=True, key="bar_chart_tab2")
"""

