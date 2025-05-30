import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from io import StringIO
import numpy as np

def group(df):
    # รวมข้อมูลตาม Device
    df_summary = df.groupby("Device").agg({
        "สั่งการทั้งหมด": "sum",
        "สั่งการสำเร็จ": "sum"
    }).reset_index()

    # คำนวณเปอร์เซ็นต์
    df_summary["% การสั่งการสำเร็จ"] = (df_summary["สั่งการสำเร็จ"] / df_summary["สั่งการทั้งหมด"]) * 100

    # จัดอันดับ
    df_summary["อันดับสั่งการทั้งหมด"] = df_summary["สั่งการทั้งหมด"].rank(ascending=False, method='min')
    df_summary["อันดับ % สำเร็จ"] = df_summary["% การสั่งการสำเร็จ"].rank(ascending=False, method='min')

    # จัดรูปแบบตัวเลข
    df_summary["สั่งการทั้งหมด"] = df_summary["สั่งการทั้งหมด"].astype(int)
    df_summary["สั่งการสำเร็จ"] = df_summary["สั่งการสำเร็จ"].astype(int)
    df_summary["% การสั่งการสำเร็จ"] = df_summary["% การสั่งการสำเร็จ"].round(2)

    st.markdown("## 🏆 จัดอันดับอุปกรณ์ตามการสั่งการ")

    # ตารางเรียงตามสั่งการทั้งหมด
    st.markdown("### 🔢 จัดอันดับตามจำนวนสั่งการทั้งหมด")
    df_sorted_total = df_summary.sort_values(by="สั่งการทั้งหมด", ascending=False)
    st.dataframe(df_sorted_total, use_container_width=True)

    # ตารางเรียงตาม % สำเร็จ
    st.markdown("### ✅ จัดอันดับตาม % การสั่งการสำเร็จ")
    df_sorted_success = df_summary.sort_values(by="% การสั่งการสำเร็จ", ascending=False)
    st.dataframe(df_sorted_success, use_container_width=True)

def show_month(df,flag):
    df_pivot = df.copy()

    # แปลงคอลัมน์เดือน
    df_pivot["Month"] = pd.to_datetime(df_pivot["Availability Period"], format="%Y-%m", errors="coerce")
    df_pivot["Month_num"] = df_pivot["Month"].dt.month

    month_names = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
                   'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']
    df_pivot["Month_name"] = df_pivot["Month_num"].apply(lambda x: month_names[int(x) - 1] if pd.notnull(x) else "")

    #st.write("ค่าไม่ใช่ตัวเลข (จะถูกแปลงเป็น NaN):")
    #st.write(df_pivot[df_pivot["สั่งการสำเร็จ (%)"].isnull()])

    # Pivot: row = Device, col = month, val = success %
    pivot_df = df_pivot.pivot_table(
        index="Device",
        columns="Month_name",
        values="สั่งการสำเร็จ (%)",
        aggfunc="mean"
    )

    #st.write("Pivot แล้ว:")
    #st.dataframe(pivot_df)


    # เรียงเดือน
    pivot_df = pivot_df.reindex(columns=month_names)

    # ค่าเฉลี่ย (ยังเป็น float ตอนนี้)
    pivot_df["Avg สั่งการสำเร็จ (%)"] = pivot_df.mean(axis=1, skipna=True)

    # คัดลอกเพื่อเช็คอุปกรณ์ที่ไม่มีข้อมูลเลย
    null_mask = pivot_df.drop(columns="Avg สั่งการสำเร็จ (%)").isnull().all(axis=1)
    devices_all_null = pivot_df[null_mask].index.tolist()
    #st.info("check null")
    #st.write(devices_all_null)

    if devices_all_null:
        st.warning(f"🔍 พบ {len(devices_all_null)} อุปกรณ์ที่ไม่มีข้อมูลเลยทั้งปี:")
        st.write(devices_all_null)

    pivot_df_numeric = pivot_df.copy()  # ก่อน format

    # จัดรูปแบบเปอร์เซ็นต์ (xx.xx%) ถ้าไม่ใช่ NaN
    def format_percent(val):
        return f"{val:.2f}%" if pd.notnull(val) else "-"

    for col in month_names + ["Avg สั่งการสำเร็จ (%)"]:
        if col in pivot_df.columns:
            pivot_df[col] = pivot_df[col].apply(format_percent)

    pivot_df_display = pivot_df.reset_index()
    
    st.info(f"✅ สรุป สั่งการสำเร็จ (%) แต่ละ {title} แยกตามเดือน")
    st.dataframe(pivot_df_display, use_container_width=True)

    def to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            processed_data = output.getvalue()
            return processed_data
    excel_data = to_excel(pivot_df_display)
    xlsx_filename = 'command_data' + '_' + flag + ".xlsx"
    st.download_button(
            label=f"📥 ดาวน์โหลดข้อมูลการสั่งการ {flag}",
            data=excel_data,
            file_name=xlsx_filename,
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
    
    return pivot_df_display, devices_all_null, pivot_df_numeric

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
    #st.info(f"✅ สรุป สั่งการสำเร็จ (%) แต่ละ {title} แยกตามเดือน")
    #pivot_df = pivot_df.style.format(format_dict)
    df_display, devices_all_null, df_numeric = show_month(df_combined,title)
    
    device_options = df_display["Device"].unique()
    selected_devices = st.multiselect("เลือก Device ที่ต้องการแสดง", device_options, default=device_options)

    pivot_df_filtered = df_display[df_display["Device"].isin(selected_devices)] #ตารางค่า %cmd แต่ละเดือน แยกตาม Device

    df_plot = pivot_df_filtered.melt(id_vars=["Device"], 
                        value_vars=[col for col in df_display.columns if col not in ["Device", "Avg สั่งการสำเร็จ (%)"]],
                        var_name="เดือน", 
                        value_name="สั่งการสำเร็จ (%)")
    #
    #st.dataframe(df_plot)

    # plot line chart
    fig_line = px.line(
        df_plot, 
        x="เดือน", 
        y="สั่งการสำเร็จ (%)", 
        color="Device", 
        markers=True,
        title="📈 สั่งการสำเร็จ (%) รายเดือนแยกตาม Device")

    fig_line.update_layout(xaxis_title="เดือน", yaxis_title="สั่งการสำเร็จ (%)", yaxis=dict(range=[0, 105]))
    st.plotly_chart(fig_line, use_container_width=True)

    fig_bar = px.bar(
        df_numeric.reset_index(), 
        x="Device",
        y="Avg สั่งการสำเร็จ (%)", 
        text="Avg สั่งการสำเร็จ (%)", 
        title="📊 ค่าเฉลี่ยสั่งการสำเร็จ (% Avg) ของแต่ละ Device")

    fig_bar.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig_bar.update_layout(xaxis_tickangle=-45, yaxis_range=[0, 120], yaxis_title="Avg สั่งการสำเร็จ (%)")
    st.plotly_chart(fig_bar, use_container_width=True)

    # ✅ Scatter plot: แสดง Avg ของแต่ละ Device
    df_numeric["Avg_Success_Text"] = df_numeric["Avg สั่งการสำเร็จ (%)"].apply(
        lambda x: f"{x:.2f}" if pd.notnull(x) else ""
        )
    fig3 = px.scatter(
        df_numeric.reset_index(),
        x="Device",
        y="Avg สั่งการสำเร็จ (%)",
        text="Avg สั่งการสำเร็จ (%)",
        color="Avg สั่งการสำเร็จ (%)",
        color_continuous_scale="Viridis",
        title="🔵 Scatter: ค่าเฉลี่ยสั่งการสำเร็จ (%) ของแต่ละ Device"
    )
    
    fig3.update_traces(texttemplate="%{text:.2f}", textposition="top center")
    fig3.update_layout(
        xaxis_tickangle=-45,
        yaxis_range=[0, 120],
        yaxis_title="Avg สั่งการสำเร็จ (%)"
    )
    st.plotly_chart(fig3, use_container_width=True)

    # แปลง wide → long เพื่อดู scatter รายเดือน
    df_scatter = pivot_df_filtered.melt(
        id_vars=["Device"], 
        value_vars=[col for col in df_display.columns if col not in ["Device", "Avg สั่งการสำเร็จ (%)"]],
        var_name="เดือน", 
        value_name="สั่งการสำเร็จ (%)"
    )
    color_map = {
        "ม.ค.": "#1f77b4",
        "ก.พ.": "#ff7f0e",
        "มี.ค.": "#2ca02c",
        "เม.ย.": "#d62728",
        "พ.ค.": "#9467bd",
        "มิ.ย.": "#8c564b",
        "ก.ค.": "#e377c2",
        "ส.ค.": "#7f7f7f",
        "ก.ย.": "#bcbd22",
        "ต.ค.": "#17becf",
        "พ.ย.": "#aec7e8",
        "ธ.ค.": "#ffbb78"
        }
    
    fig3_month = px.scatter(
    df_scatter,
    x="Device",
    y="สั่งการสำเร็จ (%)",
    color="เดือน",
    color_discrete_map=color_map,
    size=[10]*len(df_scatter),
    size_max=12,
    title="🔵 Scatter: สั่งการสำเร็จ (%) รายเดือนตาม Device"
)
    fig3_month.update_layout(xaxis_tickangle=-45, yaxis_range=[0, 105])
    fig3_month.update_traces(marker=dict(size=12, symbol="circle", line=dict(width=1, color="DarkSlateGrey")))
    st.plotly_chart(fig3_month, use_container_width=True)

    # melt ก่อน
    df_hist = df_numeric.copy()
    #df_hist["สั่งการสำเร็จ (%)"] = df_hist["สั่งการสำเร็จ (%)"].replace({",": "", "%": ""}, regex=True)
    #df_hist["สั่งการสำเร็จ (%)"] = pd.to_numeric(df_hist["สั่งการสำเร็จ (%)"], errors="coerce")
    
    fig4 = px.histogram(
        df_hist,
        x="Avg สั่งการสำเร็จ (%)",
        #color="เดือน",         # หรือไม่ใช้ก็ได้
        barmode="group",        # หรือ "overlay"
        title="📊 Histogram: ความถี่ของค่าเฉลี่ยสั่งการสำเร็จ (%)",
        color_discrete_sequence=["#0072B2"]
    )
    # กำหนดช่วงแกน X ทีละ 10 หน่วย
    fig4.update_traces(
        xbins=dict(
            start=0,      # เริ่มที่ 0
            end=100,      # จบที่ 100
            size=10       # ความกว้างของแต่ละ bin
        ),
        texttemplate="%{y}", textposition="outside"
    )
    fig4.update_layout(
        xaxis_title="Avg สั่งการสำเร็จ (%)",
        yaxis_title="จำนวน Device",
        xaxis=dict(
            tickmode="linear",
            tick0=0,
            dtick=10  # ให้แสดง label ทุก ๆ 10 หน่วย
        )
    )

    st.plotly_chart(fig4, use_container_width=True)

    ###--------------------------------------------###
    # เตรียม DataFrame แบบ melt
    df_melt = df_display.melt(
        id_vars=["Device"],
        value_vars=[col for col in df_display.columns if col not in ["Device", "Avg สั่งการสำเร็จ (%)", "Avg_Success_Text"]],
        var_name="เดือน",
        value_name="สั่งการสำเร็จ (%)"
    )
    
    # แปลงค่าว่าง/None เป็น NaN และแปลงเป็น float
    df_melt["สั่งการสำเร็จ (%)"] = (df_melt["สั่งการสำเร็จ (%)"].replace("None", np.nan).replace({",": "", "%": ""}, regex=True))
    df_melt["สั่งการสำเร็จ (%)"] = pd.to_numeric(df_melt["สั่งการสำเร็จ (%)"], errors="coerce")
    
    # กรองค่าที่เป็น NaN และไม่เอาค่า 0
    df_melt_filtered = df_melt[
        (df_melt["สั่งการสำเร็จ (%)"].notnull()) & 
        (df_melt["สั่งการสำเร็จ (%)"] > 0)
    ]

    fig4_month = px.histogram(
        df_melt,
        x="สั่งการสำเร็จ (%)",
        color="เดือน",
        nbins=10,
        barmode="overlay", #"overlay",  # หรือ "group"
        color_discrete_map=color_map,
        #text_auto=True,     # 👈 แสดงตัวเลขบนแท่ง
        #histfunc="count",   # 👈 นับจำนวนรายการ (ค่าปริยาย)
        title="📊 Histogram: สั่งการสำเร็จ (%) แยกตามเดือน"
    ) 

    fig4_month.update_traces(
        xbins=dict(start=10, end=100, size=10),
        texttemplate="%{y}", textposition="outside"
        )

    fig4_month.update_layout(
        xaxis_title="Avg สั่งการสำเร็จ (%)",
        yaxis_title=f"จำนวน {title}",
        xaxis=dict(tickmode="linear", tick0=0, dtick=10),
        #bargap=0.1,  # ปรับช่องว่างระหว่างแท่ง
        #barmode='overlay'
        )
    st.info("info")
    st.plotly_chart(fig4_month, use_container_width=True)

    ###--------------------------------------------###

    fig_group = px.histogram(
        df_hist,
        x="สั่งการสำเร็จ (%)",
        color="เดือน",
        #nbins=10,
        barmode="group",             # ⬅ แยกแท่งตามเดือน
        color_discrete_map=color_map,
        text_auto=True,
        histfunc="count",
        title="📊 Histogram (Grouped): สั่งการสำเร็จ (%) แยกตามเดือน"
        )

    fig_group.update_layout(
        xaxis_range=[0, 100],
        xaxis_title="สั่งการสำเร็จ (%)",
        yaxis_title="จำนวน",
        bargap=0.1
        )
    st.plotly_chart(fig_group, use_container_width=True)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Line Chart", 
    "📊 Bar Chart", 
    "🔵 Scatter (Avg)", 
    "🔵 Scatter (รายเดือน)", 
    "📊 Histogram (Avg)", 
    "📊 Histogram (รายเดือน)"
])

    
    with tab1:
        #st.plotly_chart(fig_line, use_container_width=True)
        st.write("test")

    with tab2:
        #st.plotly_chart(fig_bar, use_container_width=True)
        st.write("test")

    with tab3:
        #st.plotly_chart(fig3, use_container_width=True)
        st.write("test")

    with tab4:
        #st.plotly_chart(fig3_month, use_container_width=True)
        st.write("test")

    with tab5:
        #st.plotly_chart(fig4, use_container_width=True)
        st.write("test")

    with tab6:
        #st.plotly_chart(fig4_month, use_container_width=True)
        st.write("test")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Line Chart")
        #st.plotly_chart(fig_line, use_container_width=True, key="line_chart")

    with col2:
        st.subheader("🔵 Scatter (Avg)")
        #st.plotly_chart(fig3, use_container_width=True, key="scatter_avg")

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("📊 Histogram (Avg)")
        #st.plotly_chart(fig4, use_container_width=True, key="histogram_avg")

    with col4:
        st.subheader("📊 Histogram (รายเดือน)")
        #st.plotly_chart(fig4_month, use_container_width=True, key="histogram_month")
    
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


    group(df_combined)