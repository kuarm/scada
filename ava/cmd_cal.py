import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from io import StringIO
import numpy as np

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

def pivot(df,flag):
    df_pivot = df.copy()

    # แปลงคอลัมน์เดือน
    df_pivot["Month"] = pd.to_datetime(df_pivot["Availability Period"], format="%Y-%m", errors="coerce")
    df_pivot["Month_num"] = df_pivot["Month"].dt.month

    month_names = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
                   'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']
    df_pivot["Month_name"] = df_pivot["Month_num"].apply(lambda x: month_names[int(x) - 1] if pd.notnull(x) else "")

    pivot_df = df_pivot.pivot_table(
        index="Device",
        columns="Month_name",
        values="สั่งการสำเร็จ (%)",
        aggfunc="mean"
    )

    # เรียงเดือน
    pivot_df = pivot_df.reindex(columns=month_names)

    # ค่าเฉลี่ย (ยังเป็น float ตอนนี้)
    pivot_df["Avg สั่งการสำเร็จ (%)"] = pivot_df.mean(axis=1, skipna=True)

    # คัดลอกเพื่อเช็คอุปกรณ์ที่ไม่มีข้อมูลเลย
    null_mask = pivot_df.drop(columns="Avg สั่งการสำเร็จ (%)").isnull().all(axis=1)
    devices_all_null = pivot_df[null_mask].index.tolist()

    if devices_all_null:
        st.warning(f"🔍 พบ {len(devices_all_null)} อุปกรณ์ที่ไม่มีข้อมูลเลยทั้งปี:")
        st.write(devices_all_null)
    
    pivot_df_numeric = pivot_df.copy()  # ก่อน format
    st.write(pivot_df_numeric.columns)
    # จัดรูปแบบเปอร์เซ็นต์ (xx.xx%) ถ้าไม่ใช่ NaN
    def format_percent(val):
        return f"{val:.2f}%" if pd.notnull(val) else "-"
    
    for col in month_names + ["Avg สั่งการสำเร็จ (%)"]:
        if col in pivot_df.columns:
            pivot_df[col] = pivot_df[col].apply(format_percent)
    
    pivot_df_display = pivot_df.reset_index()
    pivot_df_rename = pivot_df_display.copy()
    pivot_df_rename = pivot_df_rename.rename(columns={
        "Device": flag})
    
    st.info(f"✅ สรุป สั่งการสำเร็จ (%) แต่ละ {title} แยกตามเดือน")
    st.dataframe(pivot_df_rename, use_container_width=True)

    def to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            processed_data = output.getvalue()
            return processed_data
    excel_data = to_excel(pivot_df_rename)
    xlsx_filename = 'command_data' + '_' + flag + ".xlsx"
    st.download_button(
            label=f"📥 ดาวน์โหลดข้อมูลการสั่งการ {flag}",
            data=excel_data,
            file_name=xlsx_filename,
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
    
    return pivot_df_display, devices_all_null, pivot_df_numeric

def lineplot(df):
    df_plot = df.melt(id_vars=["Device"], 
                      value_vars=[col for col in df_display.columns if col not in ["Device", "Avg สั่งการสำเร็จ (%)"]],
                      var_name="เดือน", 
                      value_name="สั่งการสำเร็จ (%)")
    st.dataframe(df_plot)

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

def barplot(df,flag,countMonth):
    fig_bar = px.bar(
        df.reset_index(), 
        x="Device",
        y="Avg สั่งการสำเร็จ (%)", 
        text="Avg สั่งการสำเร็จ (%)", 
        title=f"📊 % สั่งการสำเร็จเฉลี่ย {countMonth} เดือน ของแต่ละ {flag}")

    fig_bar.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig_bar.update_layout(xaxis_tickangle=-45, yaxis_range=[0, 120], xaxis_title=flag,yaxis_title="Avg สั่งการสำเร็จ (%)")
    st.plotly_chart(fig_bar, use_container_width=True)

def scatterplot(df_num,df_dis,flag,countMonth):
    # ✅ Scatter plot: แสดง Avg ของแต่ละ Device
    #df_num["Avg_Success_Text"] = df_num["Avg สั่งการสำเร็จ (%)"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "")

    fig3 = px.scatter(
        df_num.reset_index(),
        x="Device",
        y="Avg สั่งการสำเร็จ (%)",
        text="Avg สั่งการสำเร็จ (%)",
        color="Avg สั่งการสำเร็จ (%)",
        color_continuous_scale="Viridis",
        title=f"🔵 Scatter : % สั่งการสำเร็จเฉลี่ย {countMonth} เดือน ของแต่ละ {flag}"
    )
    
    fig3.update_traces(texttemplate="%{text:.2f}", textposition="top center")
    fig3.update_layout(
        xaxis_tickangle=-45,
        xaxis_title=flag,
        yaxis_range=[0, 120],
        yaxis_title="Avg สั่งการสำเร็จ (%)"
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ✅ แปลงค่าทั้งหมดที่เป็น '%' เป็น float
    df_display_clean = df_dis.copy()
    month_cols = [col for col in df_dis.columns if col not in ["Device", "Avg สั่งการสำเร็จ (%)"]]
    
    for col in month_cols:
        df_display_clean[col] = (
            df_display_clean[col]
            .replace("-", None)
            .str.replace("%", "", regex=False)
        )
        df_display_clean[col] = pd.to_numeric(df_display_clean[col], errors="coerce")
    
    df_scatter = df_display_clean.melt(
        id_vars=["Device"],
        value_vars=month_cols,
        var_name="เดือน",
        value_name="สั่งการสำเร็จ (%)"
    )
    df_scatter = df_scatter.dropna(subset=["สั่งการสำเร็จ (%)"])
    
    fig3_month = px.scatter(
    df_scatter,
    x="Device",
    y="สั่งการสำเร็จ (%)",
    color="เดือน",
    color_discrete_map=color_map,
    size=[10]*len(df_scatter),
    size_max=12,
    text="สั่งการสำเร็จ (%)",  # ✅ เพิ่มเพื่อให้แสดงข้อความ
    title=f"🔵 Scatter : % สั่งการสำเร็จรายเดือน ของแต่ละ {flag}"
)
    fig3_month.update_layout(xaxis_tickangle=-45, yaxis_range=[0, 105], xaxis_title=flag)
    fig3_month.update_traces(
    marker=dict(size=12, symbol="circle", line=dict(width=1, color="DarkSlateGrey")),
    texttemplate="%{text:.2f}",  # ✅ กำหนดรูปแบบแสดงค่า
    textposition="top center",     # ✅ ตำแหน่งข้อความ
    textfont_size=10,
    )

    st.plotly_chart(fig3_month, use_container_width=True)

def histogram(df_num,df_dis,flag,countMonth):
    # กำหนดช่วง bin เอง เช่น 0-10, 10-20, ..., 90-100
    bins = list(range(0, 110, 10))  # [0, 10, 20, ..., 100]
    labels = [f"{i}-{i+10}%" for i in bins[:-1]]  # ['0-10%', '10-20%', ..., '90-100%']
    st.write(labels)
    # ✅ แปลงค่าทั้งหมดที่เป็น '%' เป็น float
    df_display_clean = df_dis.copy()
    month_cols = [col for col in df_dis.columns if col not in ["Device", "Avg สั่งการสำเร็จ (%)"]]

    for col in month_cols:
        df_display_clean[col] = (
            df_display_clean[col]
            .replace("-", None)
            .str.replace("%", "", regex=False)
        )
        df_display_clean[col] = pd.to_numeric(df_display_clean[col], errors="coerce")

    df_melt = df_display_clean.melt(
        id_vars=["Device"],
        value_vars=month_cols,
        var_name="เดือน",
        value_name="สั่งการสำเร็จ (%)"
    )

    #df_melt = df_melt.dropna(subset=["สั่งการสำเร็จ (%)"])


    # เตรียม DataFrame แบบ melt
    #df_melt = df_dis.melt(
    #    id_vars=["Device"],
    # value_vars=[col for col in df_dis.columns if col not in ["Device", "Avg สั่งการสำเร็จ (%)", "Avg_Success_Text"]],
    # var_name="เดือน",value_name="สั่งการสำเร็จ (%)")
    
    # แปลงค่าว่าง/None เป็น NaN และแปลงเป็น float
    df_melt["สั่งการสำเร็จ (%)"] = (df_melt["สั่งการสำเร็จ (%)"].replace("None", np.nan).replace({",": "", "%": ""}, regex=True))
    df_melt["สั่งการสำเร็จ (%)"] = pd.to_numeric(df_melt["สั่งการสำเร็จ (%)"], errors="coerce")
    
    # สร้างคอลัมน์ bin ใหม่
    df_melt["ช่วง % สำเร็จ"] = pd.cut(df_melt["สั่งการสำเร็จ (%)"], bins=bins, labels=labels, include_lowest=True, right=False)

    st.write(df_melt["ช่วง % สำเร็จ"])
    # กรองค่าที่เป็น NaN และไม่เอาค่า 0
    #df_melt_filtered = df_melt[
    #    (df_melt["สั่งการสำเร็จ (%)"].notnull()) & 
    #    (df_melt["สั่งการสำเร็จ (%)"] > 0)
    #]
    # 1. กรองเฉพาะแถวที่มีค่าตัวเลขจริงใน "สั่งการสำเร็จ (%)"
    df_scatter_clean = df_melt[pd.to_numeric(df_melt["สั่งการสำเร็จ (%)"], errors="coerce").notna()]

    # 2. ดึงชื่อเดือนที่มีข้อมูลจริง
    used_months = df_scatter_clean["เดือน"].unique()

    # 3. สร้าง color_map เฉพาะเดือนที่มีข้อมูล
    filtered_color_map = {month: color_map[month] for month in used_months if month in color_map}

    fig4_month = px.histogram(
        df_melt,
        x="สั่งการสำเร็จ (%)",
        color="เดือน",
        nbins=10,
        barmode="overlay", #"overlay",  # หรือ "group"
        color_discrete_map=filtered_color_map,
        #text_auto=True,     # 👈 แสดงตัวเลขบนแท่ง
        #histfunc="count",   # 👈 นับจำนวนรายการ (ค่าปริยาย)
        title=f"📊 Histogram : จำนวน {flag} แต่ละช่วง % สั่งการสำเร็จเฉลี่ย {countMonth} เดือน"
    ) 

    fig4_month.update_traces(
        xbins=dict(start=10, end=100, size=10),
        texttemplate="%{y}", textposition="outside"
        )

    fig4_month.update_layout(
        xaxis_title="Avg สั่งการสำเร็จ (%)",
        yaxis_title=f"จำนวน {title}",
        xaxis=dict(tickmode="linear", tick0=0, dtick=10),
        xaxis_categoryarray=labels,  # บังคับให้แสดงทุก bin
        #bargap=0.1,  # ปรับช่องว่างระหว่างแท่ง
        #barmode='overlay'
        )
    
    st.plotly_chart(fig4_month, use_container_width=True)

# ---- Upload and Merge ----
uploaded_files = st.file_uploader("📁 อัปโหลดไฟล์ Excel (หลายไฟล์)", type=["xlsx", "xls"], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    
    for uploaded_file in uploaded_files:
        df = pd.read_excel(uploaded_file)

        if "Availability Period" not in df.columns:
            st.warning(f"❌ ไม่มีคอลัมน์ 'Availability Period' ในไฟล์ {uploaded_file.name}")
        
        df["Month"] = pd.to_datetime(df["Availability Period"], format="%Y-%m", errors="coerce")
        df["สั่งการสำเร็จ (%)"] = df["สั่งการสำเร็จ (%)"].replace({",": "", "%": ""}, regex=True)

        #df["สั่งการสำเร็จ (%)"] = df["สั่งการสำเร็จ (%)"].astype(str).str.replace(",", "").str.replace("%", "").str.strip()
        df["สั่งการสำเร็จ (%)"] = pd.to_numeric(df["สั่งการสำเร็จ (%)"], errors="coerce")
        
        all_data.append(df)

    df_combined = pd.concat(all_data, ignore_index=True)
    countMonth = len(df_combined["Availability Period"].unique())
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

    df_display, devices_all_null, df_numeric = pivot(df_combined,title)
    #lineplot(df_display)
    barplot(df_numeric,title,countMonth)
    scatterplot(df_numeric,df_display,title,countMonth)
    histogram(df_numeric,df_display,title,countMonth)