import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from io import StringIO
import numpy as np
import io
from plotly.express.colors import qualitative


color_map = {
    "ม.ค. 2025": "#1f77b4",  # ฟ้า
    "ก.พ. 2025": "#ff7f0e",  # ส้ม
    "มี.ค. 2025": "#2ca02c",  # เขียว
    "เม.ย. 2025": "#d62728",  # แดง
    "พ.ค. 2025": "#9467bd",  # ม่วง
    "มิ.ย. 2025": "#8c564b",  # น้ำตาล
    "ก.ค. 2025": "#e377c2",  # ชมพู
    "ส.ค. 2025": "#7f7f7f",  # เทา
    "ก.ย. 2025": "#bcbd22",  # เขียวมะนาว
    "ต.ค. 2025": "#17becf",  # ฟ้าน้ำทะเล
    "พ.ย. 2025": "#aec7e8",  # ฟ้าอ่อน
    "ธ.ค. 2025": "#ffbb78",  # ส้มอ่อน
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
    device_meta = df_pivot[["Device", "ผู้ดูแล"]].drop_duplicates()
    pivot_df = pivot_df.reset_index().merge(device_meta, on="Device", how="left").set_index("Device")
    st.dataframe(pivot_df)
    # เรียงเดือน
    pivot_df = pivot_df.reindex(columns=month_names)

    # ค่าเฉลี่ย (ยังเป็น float ตอนนี้)
    pivot_df["Avg.สั่งการสำเร็จ (%)"] = pivot_df.mean(axis=1, skipna=True)
    
    # คัดลอกเพื่อเช็คอุปกรณ์ที่ไม่มีข้อมูลเลย
    null_mask = pivot_df.drop(columns="Avg.สั่งการสำเร็จ (%)").isnull().all(axis=1)
    devices_all_null = pivot_df[null_mask].index.tolist()

    if devices_all_null:
        st.warning(f"🔍 พบ {len(devices_all_null)} อุปกรณ์ที่ไม่มีข้อมูลเลยทั้งปี:")
        st.write(devices_all_null)
    
    pivot_df_numeric = pivot_df.copy()  # ก่อน format

    # จัดรูปแบบเปอร์เซ็นต์ (xx.xx%) ถ้าไม่ใช่ NaN
    def format_percent(val):
        return f"{val:.2f}%" if pd.notnull(val) else "-"
    
    for col in month_names + ["Avg.สั่งการสำเร็จ (%)"]:
        if col in pivot_df.columns:
            pivot_df[col] = pivot_df[col].apply(format_percent)
    
    pivot_df_display = pivot_df.reset_index()
    
    pivot_df_rename = pivot_df_display.copy()
    #pivot_df_rename = pivot_df_rename.rename(columns={"Device": flag})
    pivot_df_rename.rename(columns={"Device": flag}, inplace=True)
    #pivot_df_rename.insert(0, "ลำดับ", range(1, len(pivot_df_rename) + 1))
    
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

    st.info("จัดอันดับ Avg.สั่งการสำเร็จ (%)")
    pivot_df_numeric["อันดับ"] = pivot_df_numeric["Avg.สั่งการสำเร็จ (%)"].rank(method='min', ascending=False).astype("Int64")
    pivot_df_rename.insert(1, "อันดับ", pivot_df_numeric["อันดับ"])
    st.dataframe(pivot_df_rename, use_container_width=True)
    st.info("rrr")
    st.dataframe(pivot_df_numeric, use_container_width=True)
    #wide format (แต่ละเดือนเป็นคอลัมน์)
    #long format (เดือนอยู่ในแถว)
    # ✅ แปลงตารางจาก wide เป็น long format เพื่อแสดง "เดือน", "Device", "Avg.สั่งการสำเร็จ (%)"
    df_long = pivot_df_numeric.reset_index().melt(
        id_vars="Device",
        value_vars=month_names,
        var_name="เดือน",
        value_name="Success Rate (%)"
    )

    # ✅ ลบค่า NaN (อุปกรณ์ที่ไม่มีข้อมูลในบางเดือน)
    df_long = df_long.dropna(subset=["Success Rate (%)"])

    # ✅ แปลงค่าให้เป็นเปอร์เซ็นต์ 2 ตำแหน่ง
    df_long["Success Rate (%)"] = df_long["Success Rate (%)"].map(lambda x: f"{x:.2f}%" if pd.notnull(x) else "-")

    df_long.rename(columns={"Success Rate (%)": "Avg.สั่งการสำเร็จ (%)"}, inplace=True)

    # ✅ แสดงผล
    #st.subheader("📊 ตาราง \"เดือน - Device - Avg.สั่งการสำเร็จ (%)\"")
    #st.dataframe(df_long, use_container_width=True, hide_index=True)

    # กรองเฉพาะคอลัมน์เดือนเท่านั้น (จาก pivot_df_numeric ที่ยังเป็น float)
    df_avg_month = pivot_df_numeric[month_names].mean(axis=0, skipna=True).reset_index()

    # เปลี่ยนชื่อคอลัมน์
    df_avg_month.columns = ["เดือน", "Avg.สั่งการสำเร็จ (%)"]

    # จัดรูปแบบค่าเป็นเปอร์เซ็นต์
    df_avg_month["Avg.สั่งการสำเร็จ (%)"] = df_avg_month["Avg.สั่งการสำเร็จ (%)"].map(lambda x: f"{x:.2f}%" if pd.notnull(x) else "-")

    # แสดงผล
    st.subheader("📋 ค่าเฉลี่ยการสั่งการสำเร็จ (%) รายเดือน (รวมทุก Device)")
    st.dataframe(df_avg_month, use_container_width=True, hide_index=True)

    # เฉลี่ยข้ามทุกอุปกรณ์ในแต่ละเดือน
    monthly_avg = pivot_df_numeric[month_names].mean(skipna=True).reset_index()
    monthly_avg.columns = ["เดือน", "Avg.สั่งการสำเร็จ (%)"]

    # จัดรูปแบบ %
    monthly_avg["Avg.สั่งการสำเร็จ (%)"] = monthly_avg["Avg.สั่งการสำเร็จ (%)"].map(lambda x: f"{x:.2f}%")

    #st.subheader("📊 ค่าเฉลี่ยสั่งการสำเร็จ (%) รายเดือน (รวมทุกอุปกรณ์)")
    #st.dataframe(monthly_avg, use_container_width=True, hide_index=True)

    # ✅ ตรวจสอบ Device ที่ไม่มีข้อมูลเลยในแต่ละเดือน
    missing_by_month = {}
    for month in month_names:
        if month in pivot_df.columns:
            missing_devices = pivot_df[pd.isna(pivot_df[month])].index.tolist()
            if missing_devices:
                missing_by_month[month] = missing_devices

    # ✅ แสดงผลลัพธ์
    if missing_by_month:
        with st.expander("📌 รายการ Device ที่ไม่มีข้อมูลสั่งการในแต่ละเดือน"):
            for month, devices in missing_by_month.items():
                st.markdown(f"**{month}**: พบ {len(devices)} อุปกรณ์")
                st.write(devices)

    # แปลง dict เป็น DataFrame
    missing_df = pd.DataFrame([
        {"Month": month, "Device": device}
        for month, devices in missing_by_month.items()
        for device in devices
    ])

    st.subheader("📋 ตาราง Device ที่ไม่มีการสั่งการในแต่ละเดือน")
    st.dataframe(missing_df)
    return pivot_df_display, devices_all_null, pivot_df_numeric

def lineplot(df):
    df_plot = df.melt(id_vars=["Device"], 
                      value_vars=[col for col in df_display.columns if col not in ["Device", "Avg.สั่งการสำเร็จ (%)"]],
                      var_name="เดือน", 
                      value_name="สั่งการสำเร็จ (%)")

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
        y="Avg.สั่งการสำเร็จ (%)", 
        text="Avg.สั่งการสำเร็จ (%)", 
        title=f"📊 % สั่งการสำเร็จเฉลี่ย {countMonth} เดือน ของแต่ละ {flag}")

    fig_bar.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig_bar.update_layout(xaxis_tickangle=-45, yaxis_range=[0, 120], xaxis_title=flag,yaxis_title="Avg.สั่งการสำเร็จ (%)")
    st.plotly_chart(fig_bar, use_container_width=True)

def scatterplot(df_num,df_dis,flag,countMonth):
    # ✅ Scatter plot: แสดง Avg ของแต่ละ Device
    #df_num["Avg_Success_Text"] = df_num["Avg.สั่งการสำเร็จ (%)"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "")

    fig3 = px.scatter(
        df_num.reset_index(),
        x="Device",
        y="Avg.สั่งการสำเร็จ (%)",
        text="Avg.สั่งการสำเร็จ (%)",
        color="Avg.สั่งการสำเร็จ (%)",
        color_continuous_scale="Viridis",
        title=f"🔵 Scatter : % สั่งการสำเร็จเฉลี่ย {countMonth} เดือน ของแต่ละ {flag}"
        )
    
    fig3.update_traces(texttemplate="%{text:.2f}", textposition="top center")
    fig3.update_layout(
        xaxis_tickangle=-45,
        xaxis_title=flag,
        yaxis_range=[0, 120],
        yaxis_title="Avg.สั่งการสำเร็จ (%)"
        )
    st.plotly_chart(fig3, use_container_width=True)

    # ✅ แปลงค่าทั้งหมดที่เป็น '%' เป็น float
    df_display_clean = df_dis.copy()
    month_cols = [col for col in df_dis.columns if col not in ["Device", "Avg.สั่งการสำเร็จ (%)"]]
    
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

    # ✅ ปรับแต่ง layout
    fig3_month.update_layout(
        xaxis_tickangle=-45,
        xaxis_title=flag,
        yaxis_range=[0, 120],
        yaxis_title="% การสั่งการสำเร็จ" #รวม % สั่งการสำเร็จ (Stacked)
        )

    fig3_month.update_traces(
        marker=dict(size=12, symbol="circle", line=dict(width=1, color="DarkSlateGrey")),
        texttemplate="%{text:.2f}",  # ✅ กำหนดรูปแบบแสดงค่า
        textposition="top center", #"top center", #outside    # ✅ ตำแหน่งข้อความ
        textfont_size=10,
        )

    st.plotly_chart(fig3_month, use_container_width=True)
    
def histogram(df_num,df_dis,flag,countMonth):
    # กำหนดช่วง bin เอง เช่น 0-10, 10-20, ..., 90-100
    bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    labels = [f"{i}-{i+10}%" for i in bins[:-1]]
    #bins = list(range(0, 110, 10))  # [0, 10, ..., 100]

    # ✅ แปลงค่าทั้งหมดที่เป็น '%' เป็น float
    df_display_clean = df_dis.copy()
    st.dataframe(df_display_clean)
    month_cols = [col for col in df_dis.columns if col not in ["Device", "Avg.สั่งการสำเร็จ (%)"]]

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
    # value_vars=[col for col in df_dis.columns if col not in ["Device", "Avg.สั่งการสำเร็จ (%)", "Avg_Success_Text"]],
    # var_name="เดือน",value_name="สั่งการสำเร็จ (%)")
    
    # 2. สร้าง df ที่มีทุกช่วง (เพื่อให้ plotly แสดงทุก bin แม้ไม่มีข้อมูล)
    dummy_bins = pd.DataFrame({
        "ช่วง % สั่งการ": labels,
        "จำนวน": [0]*len(labels),
        "เดือน": ["dummy"]*len(labels)
    })

    # แปลงค่าว่าง/None เป็น NaN และแปลงเป็น float
    df_melt["สั่งการสำเร็จ (%)"] = (df_melt["สั่งการสำเร็จ (%)"].replace("None", np.nan).replace({",": "", "%": ""}, regex=True))
    df_melt["สั่งการสำเร็จ (%)"] = pd.to_numeric(df_melt["สั่งการสำเร็จ (%)"], errors="coerce")
    
    # สร้าง column ช่วงการสั่งการ
    df_melt["ช่วง % สั่งการ"] = pd.cut(
        df_melt["สั่งการสำเร็จ (%)"], 
        bins=bins, 
        labels=labels, 
        include_lowest=True,
        right=False
        )

    # ลบ NaN
    df_clean = df_melt.dropna(subset=["ช่วง % สั่งการ", "เดือน"])

    # 4. นับจำนวนจริง
    df_hist = df_clean.groupby(["ช่วง % สั่งการ", "เดือน"]).size().reset_index(name="จำนวน")

    # 5. รวม dummy เข้ากับข้อมูลจริง (ใช้ concat)
    df_combined = pd.concat([df_hist, dummy_bins], ignore_index=True)
    # กรองค่าที่เป็น NaN และไม่เอาค่า 0
    #df_melt_filtered = df_melt[
    #    (df_melt["สั่งการสำเร็จ (%)"].notnull()) & 
    #    (df_melt["สั่งการสำเร็จ (%)"] > 0)
    #]

    # 6. ตรวจสอบ color map สำหรับเดือนจริง
    months_with_data = df_clean["เดือน"].unique()
    filtered_color_map = {m: color_map[m] for m in months_with_data if m in color_map}
    
    # 7. Plot
    fig = px.bar(
        df_combined[df_combined["เดือน"] != "dummy"],  # ตัด dummy ออกจากกราฟจริง
        x="ช่วง % สั่งการ",
        y="จำนวน",
        color="เดือน",
        category_orders={"ช่วง % สั่งการ": labels},
        color_discrete_map=filtered_color_map,
        barmode="group",
        title=f"📊 Histogram: จำนวน {flag} แต่ละช่วง % สั่งการสำเร็จเฉลี่ย {countMonth} เดือน"
        )

    fig.update_layout(
        xaxis_title="ช่วง % สั่งการสำเร็จ",
        yaxis_title=f"จำนวน {flag}",
        bargap=0.0
    )

    fig.update_traces(texttemplate="%{y}", textposition="outside")

    st.plotly_chart(fig, use_container_width=True)
    
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
        xbins=dict(start=0, end=100, size=10),
        texttemplate="%{y}", textposition="outside"
        )

    fig4_month.update_layout(
        xaxis_title="Avg.สั่งการสำเร็จ (%)",
        yaxis_title=f"จำนวน {title}",
        xaxis=dict(tickmode="linear", tick0=0, dtick=10),
        xaxis_categoryarray=labels,  # บังคับให้แสดงทุก bin
        #bargap=0.1,  # ปรับช่องว่างระหว่างแท่ง
        #barmode='overlay'
        )

    st.plotly_chart(fig4_month, use_container_width=True)

def stacked(df_num,df_dis,flag,countMonth):
    # ✅ ตัวเลือกให้ผู้ใช้เลือกประเภทของ Bar Chart
    chart_mode = st.selectbox("🛠️ เลือกรูปแบบกราฟ", ["Grouped", "Stacked"])

    # ✅ เตรียมข้อมูล (เหมือนเดิม)
    df_display_clean = df_dis.copy()
    month_cols = [col for col in df_dis.columns if col not in ["Device", "Avg.สั่งการสำเร็จ (%)"]]

    for col in month_cols:
        df_display_clean[col] = (
            df_display_clean[col]
            .replace("-", None)
            .str.replace("%", "", regex=False)
        )
        df_display_clean[col] = pd.to_numeric(df_display_clean[col], errors="coerce")

    df_bar = df_display_clean.melt(
        id_vars=["Device"],
        value_vars=month_cols,
        var_name="เดือน",
        value_name="สั่งการสำเร็จ (%)"
    ).dropna(subset=["สั่งการสำเร็จ (%)"])

    # ✅ เลือก barmode ตาม toggle
    barmode = "group" if chart_mode == "Grouped" else "stack"

    # ✅ ชื่อกราฟให้เปลี่ยนตามประเภท
    title = (
        f"📊 Grouped Bar Chart: % สั่งการสำเร็จรายเดือนของแต่ละ {flag}"
        if barmode == "group"
        else f"📊 Stacked Bar Chart: % สั่งการสำเร็จรายเดือนของแต่ละ {flag}"
    )

    # ✅ ดึงชื่อเดือนทั้งหมดจาก df_bar หรือ df ที่ใช้ plot
    unique_months = df_bar["เดือน"].unique()

    # ✅ ใช้ชุดสีจาก Plotly
    color_palette = px.colors.qualitative.Plotly  # มี 10 สีหลัก

    # ✅ สร้าง color_map โดยวนสีหากเดือนมากกว่า 10 เดือน
    color_map = {
        month: color_palette[i % len(color_palette)] for i, month in enumerate(sorted(unique_months))
    }

    # ✅ วาดกราฟ
    fig_bar = px.bar(
        df_bar,
        x="Device",
        y="สั่งการสำเร็จ (%)",
        color="เดือน",
        color_discrete_map=color_map,
        barmode=barmode,
        text="สั่งการสำเร็จ (%)",
        title=title
    )

    fig_bar.update_layout(
        xaxis_tickangle=-45,
        xaxis_title=flag,
        yaxis_range=[0, 400],
        uniformtext_minsize=8,
        uniformtext_mode='show'  # หรือ 'show
    )

    fig_bar.update_traces(
        texttemplate="%{text:.2f}",
        textposition="inside", #if barmode == "stack" else "outside",
        marker=dict(line=dict(width=0.5, color="DarkSlateGrey")),
        insidetextfont=dict(color="white")  # หรือ "black" ตามสี bar
    )

    # ✅ แสดงผล
    st.plotly_chart(fig_bar, use_container_width=True)
def ranking(df):
    # รวมข้อมูลตาม Device
    df_summary = df.groupby("Device").agg({
        "สั่งการทั้งหมด": "sum",
        "สั่งการสำเร็จ": "sum"
        }).reset_index()

    # คำนวณเปอร์เซ็นต์
    df_summary["% การสั่งการสำเร็จ"] = (df_summary["สั่งการสำเร็จ"] / df_summary["สั่งการทั้งหมด"]) * 100
    
    # จัดอันดับ
    df_summary["อันดับสั่งการทั้งหมด"] = df_summary["สั่งการทั้งหมด"].rank(ascending=False, method='min') #ascending=False (เรียงจากมากไปน้อย) method='min' ถ้าอุปกรณ์ 2 ตัวมีค่า สั่งการทั้งหมด เท่ากัน → ทั้งคู่จะได้ "อันดับต่ำสุดในกลุ่มนั้น
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

    # Top 10 by total
    top10_total = df_sorted_total.head(10)
    fig_top_total = px.bar(top10_total, x="Device", y="สั่งการทั้งหมด", text="สั่งการทั้งหมด",
                        title="🏅 Top 10 อุปกรณ์ที่มีการสั่งการมากที่สุด")
    st.plotly_chart(fig_top_total, use_container_width=True)

    # Top 10 by % success
    top10_success = df_sorted_success.head(10)
    fig_top_success = px.bar(top10_success, x="Device", y="% การสั่งการสำเร็จ", text="% การสั่งการสำเร็จ",
                            title="🏅 Top 10 อุปกรณ์ที่สั่งการสำเร็จสูงสุด (%)")
    st.plotly_chart(fig_top_success, use_container_width=True)

def ranking_by_month(df):
    # รวมข้อมูลตามเดือน + อุปกรณ์
    df_summary = df.groupby(["Availability Period", "Device"]).agg({
        "สั่งการทั้งหมด": "sum",
        "สั่งการสำเร็จ": "sum"
    }).reset_index()

    # คำนวณเปอร์เซ็นต์สำเร็จ
    df_summary["% การสั่งการสำเร็จ"] = (df_summary["สั่งการสำเร็จ"] / df_summary["สั่งการทั้งหมด"]) * 100

    # จัดอันดับในแต่ละเดือน
    df_summary["อันดับสั่งการทั้งหมด"] = df_summary.groupby("Availability Period")["สั่งการทั้งหมด"].rank(ascending=False, method="min")
    df_summary["อันดับ % สำเร็จ"] = df_summary.groupby("Availability Period")["% การสั่งการสำเร็จ"].rank(ascending=False, method="min")

    # จัดรูปแบบ
    df_summary["สั่งการทั้งหมด"] = df_summary["สั่งการทั้งหมด"].astype(int)
    df_summary["สั่งการสำเร็จ"] = df_summary["สั่งการสำเร็จ"].astype(int)
    df_summary["% การสั่งการสำเร็จ"] = df_summary["% การสั่งการสำเร็จ"].round(2)

    st.markdown("## 📅 จัดอันดับอุปกรณ์แยกตามเดือน")

    # แสดงตารางรวม
    st.dataframe(df_summary, use_container_width=True)

    # เลือกดูเฉพาะเดือน
    selected_month = st.selectbox("เลือกเดือนเพื่อดู Top 10", df_summary["Availability Period"].unique())
    top10 = df_summary[df_summary["Availability Period"] == selected_month].sort_values(by="สั่งการทั้งหมด", ascending=False).head(10)

    fig = px.bar(
        top10,
        x="Device",
        y="สั่งการทั้งหมด",
        text="สั่งการทั้งหมด",
        title=f"🏅 Top 10 อุปกรณ์ที่มีการสั่งการมากที่สุดในเดือน {selected_month}"
    )
    st.plotly_chart(fig, use_container_width=True)

    buffer = io.BytesIO()
    df_summary.to_excel(buffer, index=False)
    st.download_button("📥 ดาวน์โหลดตารางจัดอันดับรายเดือน", buffer.getvalue(), file_name="ranking_by_month.xlsx")

    # ==== เพิ่ม: อุปกรณ์ที่ไม่มีการสั่งการเลย ====

    st.markdown("## ❌ รายชื่ออุปกรณ์ที่ไม่มีการสั่งการเลยในแต่ละเดือน")

    # แปลง None ใน 'สั่งการทั้งหมด' เป็น 0
    df["สั่งการทั้งหมด"] = df["สั่งการทั้งหมด"].fillna(0).astype(int)

    # ตรวจสอบว่ามีคอลัมน์เดือนหรือยัง
    if "Availability Period" not in df.columns:
        df["Availability Period"] = pd.to_datetime(df["Field change time"]).dt.to_period("M").astype(str)

    # กรองอุปกรณ์ที่ไม่มีการสั่งการ
    df_no_cmd = df[df["สั่งการทั้งหมด"] == 0]
    df_result = df_no_cmd[["Availability Period", "Device"]].drop_duplicates().sort_values(
        by=["Availability Period", "Device"]
    ).reset_index(drop=True)

    st.dataframe(df_result, use_container_width=True)

    buffer = io.BytesIO()
    df_result.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    st.download_button(
        label="📥 ดาวน์โหลดรายชื่ออุปกรณ์ที่ไม่มีการสั่งการ",
        data=buffer,
        file_name="devices_no_command.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def devices_with_no_commands(df_all):
    # แปลงค่า None/NaN เป็น 0
    df_all["สั่งการทั้งหมด"] = df_all["สั่งการทั้งหมด"].fillna(0).astype(int)

    # ตรวจสอบว่ามีคอลัมน์ "Availability Period" หรือยัง
    if "Availability Period" not in df_all.columns:
        df_all["Availability Period"] = pd.to_datetime(df_all["Field change time"]).dt.to_period("M").astype(str)

    # กรองเฉพาะอุปกรณ์ที่ไม่มีการสั่งการเลย
    df_no_cmd = df_all[df_all["สั่งการทั้งหมด"] == 0]

    # ตัดซ้ำ เหลือเฉพาะ Device และเดือน
    df_result = df_no_cmd[["Availability Period", "Device"]].drop_duplicates().sort_values(
        by=["Availability Period", "Device"]
    ).reset_index(drop=True)

    # แสดงผล
    st.markdown("## ❌ อุปกรณ์ที่ไม่มีการสั่งการเลยในแต่ละเดือน")
    st.dataframe(df_result, use_container_width=True)

    # ปุ่มดาวน์โหลด
    buffer = io.BytesIO()
    df_result.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    st.download_button(
        label="📥 ดาวน์โหลดรายชื่ออุปกรณ์ที่ไม่มีการสั่งการ",
        data=buffer,
        file_name="devices_no_command.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    return df_result

def device_command_summary_table(df, flag):
    st.markdown("## 📊 สรุปอุปกรณ์ที่ไม่ได้สั่งการในแต่ละเดือน")

    # เติม missing เป็น 0 และจัดรูปแบบ
    df["สั่งการทั้งหมด"] = df["สั่งการทั้งหมด"].fillna(0).astype(int)

    # ดึงเดือนและปี
    if "Availability Period" not in df.columns:
        df["Availability Period"] = pd.to_datetime(df["Field change time"]).dt.to_period("M").astype(str)
    
    df["มีการสั่งการ"] = df["สั่งการทั้งหมด"].apply(lambda x: 1 if x > 0 else 0)

    # แปลงเป็น datetime แล้วเปลี่ยนชื่อเดือน → ม.ค. 2025
    df["เดือนแสดงผล"] = pd.to_datetime(df["Availability Period"], format="%Y-%m")
    df["เดือนแสดงผล"] = df["เดือนแสดงผล"].dt.strftime("%b %Y")  # เช่น Jan 2025
    month_map = {
        "Jan": "ม.ค.", "Feb": "ก.พ.", "Mar": "มี.ค.", "Apr": "เม.ย.",
        "May": "พ.ค.", "Jun": "มิ.ย.", "Jul": "ก.ค.", "Aug": "ส.ค.",
        "Sep": "ก.ย.", "Oct": "ต.ค.", "Nov": "พ.ย.", "Dec": "ธ.ค."
    }
    df["เดือนแสดงผล"] = df["เดือนแสดงผล"].apply(lambda x: f"{month_map.get(x[:3], x[:3])} {x[4:]}")

    # เปลี่ยนชื่อ Device ตาม flag
    if flag == "สถานีไฟฟ้า":
        df["Device"] = df["Device"].apply(lambda x: x.split("_")[0])  # หรือชื่อสถานีที่คุณต้องการ

    # Pivot Table
    pivot = df.pivot_table(index="Device", columns="เดือนแสดงผล", values="มีการสั่งการ", aggfunc="max", fill_value=0)
    pivot = pivot.applymap(lambda x: "✅" if x == 1 else "❌")

    # เปลี่ยนชื่อคอลัมน์ Device ตาม flag
    new_device_column_name = "อุปกรณ์ FRTU" if flag == "อุปกรณ์ FRTU" else "สถานีไฟฟ้า"
    pivot.index.name = new_device_column_name

    # อุปกรณ์ที่ไม่มีการสั่งการเลย
    never_commanded = pivot[(pivot == "❌").all(axis=1)].copy()
    never_commanded.index.name = new_device_column_name

    # แสดงตาราง
    st.markdown("### 📌 ตารางสรุป (✅ = มีสั่งการ, ❌ = ไม่มีสั่งการ)")
    st.dataframe(pivot, use_container_width=True)

    st.markdown("### 🚫 อุปกรณ์ที่ไม่มีการสั่งการเลยทุกเดือน")
    st.dataframe(never_commanded, use_container_width=True)

    # ปุ่มดาวน์โหลด
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pivot.to_excel(writer, sheet_name="Summary")
        never_commanded.to_excel(writer, sheet_name="Never Commanded")
    buffer.seek(0)

    st.download_button(
        label="📥 ดาวน์โหลดตารางสรุปอุปกรณ์",
        data=buffer,
        file_name="device_no_command_summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    return df

def compare(df):
    
    # เติมค่า NaN ด้วย 0 แล้วแปลงชนิดข้อมูลให้เหมาะสม
    df[["สั่งการทั้งหมด", "สั่งการสำเร็จ", "สั่งการสำเร็จ (%)"]] = df[["สั่งการทั้งหมด", "สั่งการสำเร็จ", "สั่งการสำเร็จ (%)"]].fillna(0).astype(int)
    df["สั่งการสำเร็จ (%)"] = df["สั่งการสำเร็จ (%)"].fillna(0).round(2)
    
    # เลือก Device ที่ต้องการเจาะลึก
    device_select = st.selectbox("🔍 เลือกอุปกรณ์เพื่อดูแนวโน้ม % การสั่งการ", df["Device"].unique())

    # ข้อมูลของอุปกรณ์นั้น
    device_df = df[df["Device"] == device_select]

    fig_line = px.line(
        df,
        x="Device",
        y="สั่งการสำเร็จ (%)",
        title=f"📈 แนวโน้ม % การสั่งการสำเร็จของอุปกรณ์ {device_select}",
        markers=True
    )
    fig_line.update_traces(texttemplate="%{y:.1f}%", textposition="top center")
    st.plotly_chart(fig_line, use_container_width=True)

# ---- Upload and Merge ----
uploaded_files = st.file_uploader("📁 อัปโหลดไฟล์ Excel (หลายไฟล์)", type=["xlsx", "xls"], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    
    for uploaded_file in uploaded_files:
        xls = pd.ExcelFile(uploaded_file)
        sheetnames = xls.sheet_names
        # ให้ผู้ใช้เลือกชื่อชีต
        selected_sheet = st.selectbox(f"📑 เลือก Sheet สำหรับไฟล์ {uploaded_file.name}", sheetnames, key=uploaded_file.name)

        df = pd.read_excel(uploaded_file,sheet_name=selected_sheet)

        if "Availability Period" not in df.columns:
            st.warning(f"❌ ไม่มีคอลัมน์ 'Availability Period' ในไฟล์ {uploaded_file.name}")
            continue
        df["Month"] = pd.to_datetime(df["Availability Period"], format="%Y-%m", errors="coerce")
        df["สั่งการสำเร็จ (%)"] = df["สั่งการสำเร็จ (%)"].replace({",": "", "%": ""}, regex=True)

        #df["สั่งการสำเร็จ (%)"] = df["สั่งการสำเร็จ (%)"].astype(str).str.replace(",", "").str.replace("%", "").str.strip()
        df["สั่งการสำเร็จ (%)"] = pd.to_numeric(df["สั่งการสำเร็จ (%)"], errors="coerce")
        
        all_data.append(df)

        df["สั่งการสำเร็จ (%)"] = df["สั่งการสำเร็จ (%)"] * 100

     # รวมข้อมูลทั้งหมดจากหลายไฟล์
    df_merged = pd.concat(all_data, ignore_index=True)
    #df_combined = pd.concat(all_data, ignore_index=True)
    st.success(f"✅ รวมข้อมูลจาก {len(uploaded_files)} ไฟล์ สำเร็จแล้ว!")

    # ---- Select Flag (ระดับการแสดงผล: Zone/Province/Feeder) ----
    flag = st.selectbox("🔍 เลือกระดับการวิเคราะห์", ["อุปกรณ์ FRTU", "สถานีไฟฟ้า"])

    #if flag not in df_merged.columns:
    #    st.error(f"❌ ไม่พบคอลัมน์ '{flag}' ในข้อมูล กรุณาตรวจสอบว่าไฟล์มีคอลัมน์นี้")
    #    st.stop()

    # ---- เรียกฟังก์ชัน Pivot เพื่อแสดงตาราง ----
    title = flag  # เก็บไว้ใช้ในชื่อกราฟ
    df_display, devices_all_null, df_numeric = pivot(df_merged, flag)
    #st.info("aaa")
    #st.dataframe(df_numeric)
    #ranking(df_merged)
    #ranking_by_month(df_merged)
    #missing_devices_df = devices_with_no_commands(df_merged)
    #df_summary = device_command_summary_table(df_merged, flag)
    #compare(df_summary)

    # ---- นับจำนวนเดือนที่มีการแสดงผล ----
    #countMonth = df_merged.drop(columns=["Avg.สั่งการสำเร็จ (%)"]).count(axis=1).max()
    countMonth = len(df_merged["Availability Period"].unique())

    # ---- เรียกฟังก์ชัน Visualization ----
    with st.expander("📈 Line Chart", expanded=True):
        #lineplot(df_display)
        st.info('test')
    with st.expander("📊 Bar Chart", expanded=True):
        barplot(df_numeric, flag, countMonth)
        st.info('test')
    with st.expander("🔵 Scatter Plot", expanded=True):
        scatterplot(df_numeric, df_display, flag, countMonth)
        st.info('test')
    with st.expander("📊 Histogram", expanded=True):
        histogram(df_numeric, df_display, flag, countMonth)
        st.info('test')
    with st.expander("📊 Stacked", expanded=True):
        stacked(df_numeric, df_display, flag, countMonth)
        st.info('test')

    

    # แปลง Timestamp เป็น datetime (ถ้ายังไม่ได้แปลง)
#df["Timestamp"] = pd.to_datetime(df["Timestamp"])

# เพิ่มคอลัมน์เดือนในรูปแบบ 'YYYY-MM'
#df["Month"] = df["Timestamp"].dt.to_period("M").astype(str)

# นับจำนวนคำสั่งต่อ Device ต่อเดือน
    command_counts = df_merged.groupby(["Month", "Device"]).size().reset_index(name="Command Count")

    """   
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
    

    lineplot(df_display)
    barplot(df_numeric,title,countMonth)
    scatterplot(df_numeric,df_display,title,countMonth)
    histogram(df_numeric,df_display,title,countMonth)
    """