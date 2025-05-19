import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

def plot_avg(df):
    # --- เตรียมข้อมูล ---
    df_avg = df_combined.copy()

    # แปลง "Availability (%)" เป็น float
    df_avg["Availability (%)"] = df_avg["Availability (%)"].replace({",": "", "%": ""}, regex=True)
    df_avg["Availability (%)"] = pd.to_numeric(df_avg["Availability (%)"], errors="coerce")

    # แปลง "Availability Period" เป็น datetime แล้วสร้าง "Month"
    df_avg["Month"] = pd.to_datetime(df_avg["Availability Period"], format="%Y-%m", errors="coerce")
    df_avg["Month_str"] = df_avg["Month"].dt.to_period("M").astype(str)

    # ลบค่าที่ไม่สมบูรณ์
    df_avg = df_avg.dropna(subset=["Availability (%)", "Device", "Month_str"])

    # --- ตัวเลือกเดือน (Filter) ---
    all_months = sorted(df_avg["Month_str"].unique())
    selected_months = st.multiselect("📆 เลือกเดือนที่ต้องการวิเคราะห์", all_months, default=all_months)

    # กรองข้อมูลตามเดือนที่เลือก
    df_avg = df_avg[df_avg["Month_str"].isin(selected_months)]

    # --- ตัวเลือก Device (Filter) ---
    all_devices = sorted(df_avg["Device"].unique())
    selected_devices = st.multiselect("🖥️ เลือก Device ที่ต้องการวิเคราะห์", all_devices, default=all_devices)

    # กรองข้อมูลตาม Device ที่เลือก
    df_avg = df_avg[df_avg["Device"].isin(selected_devices)]

    # --- 🔹 กราฟที่ 1: ค่าเฉลี่ยรวมทุก Device รายเดือน ---
    monthly_avg = df_avg.groupby("Month_str")["Availability (%)"].mean().reset_index()
    monthly_avg["Availability (%)"] = monthly_avg["Availability (%)"].round(2)

    fig_total_avg = px.line(
        monthly_avg,
        x="Month_str",
        y="Availability (%)",
        markers=True,
        title="📈 ค่าเฉลี่ย Availability (%) ของทุก Device รายเดือน",
        )
    fig_total_avg.update_layout(
        xaxis_title="เดือน",
        yaxis_title="Average Availability (%)",
        yaxis=dict(range=[0, 105]),
        hovermode="x unified"
        )

    # --- 🔹 กราฟที่ 2: Availability (%) รายเดือนแยกตาม Device ---
    device_monthly = df_avg.groupby(["Month_str", "Device"])["Availability (%)"].mean().reset_index()
    device_monthly["Availability (%)"] = device_monthly["Availability (%)"].round(2)

    fig_by_device = px.line(
        device_monthly,
        x="Month_str",
        y="Availability (%)",
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

    # --- แสดงผล ---
    #st.plotly_chart(fig_total_avg, use_container_width=True)
    #st.plotly_chart(fig_by_device, use_container_width=True)

    fig_scatter = px.scatter(
        df_avg,
        x="Device",
        y="Availability (%)",
        color="Month_str",  # เพื่อแยกสีตามเดือน
        title="📍 Availability (%) ของแต่ละ Device (Scatter)",
        hover_data=["Month_str"],  # แสดงเดือนใน hover
        )

    fig_scatter.update_layout(
        xaxis_title="Device",
        yaxis_title="Availability (%)",
        yaxis=dict(range=[0, 105]),
        xaxis_tickangle=-45,
        height=600
        )

    st.plotly_chart(fig_scatter, use_container_width=True)
    
def plot(df,type):
    # เตรียมข้อมูล
    df_line = df_combined.copy()

    # แปลง Availability เป็นตัวเลข
    df_line["Availability (%)"] = df_line["Availability (%)"].replace({",": "", "%": ""}, regex=True)
    df_line["Availability (%)"] = pd.to_numeric(df_line["Availability (%)"], errors="coerce")

    # แปลงคอลัมน์เป็น datetime และแยกเป็นเดือน
    df_line["Month"] = pd.to_datetime(df_line["Availability Period"], format="%Y-%m", errors="coerce")
    df_line["Month_str"] = df_line["Month"].dt.to_period("M").astype(str)

    # รายชื่อเดือนทั้งหมด
    all_months = sorted(df_line["Month_str"].dropna().unique())

    # 🧭 ตัวเลือก: กรองเดือน
    selected_months = st.multiselect("📆 เลือกเดือนที่ต้องการแสดง (หลายเดือน)", all_months, default=all_months)

    # กรองข้อมูลตามเดือนที่เลือก
    filtered_df = df_line[df_line["Month_str"].isin(selected_months)]

    # วาด Line Plot: Availability ของแต่ละ Device ตามเดือน
    fig = px.line(
        filtered_df,
        x="Month_str",
        y="Availability (%)",
        color="Device",
        markers=True,
        title="📈 Availability (%) ของแต่ละ Device ตามเดือน"
    )

    fig.update_layout(
        xaxis_title="เดือน",
        yaxis_title="Availability (%)",
        yaxis=dict(range=[0, 105]),
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

def Plot_summary(df):
    # เตรียม DataFrame แบบ Long format สำหรับ plot
    plot_df = df.copy()
    plot_df["Month"] = pd.to_datetime(plot_df["Availability Period"], format="%Y-%m", errors="coerce")
    plot_df["Month_num"] = plot_df["Month"].dt.month
    month_names = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
                'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']
    plot_df["Month_name"] = plot_df["Month_num"].apply(lambda x: month_names[x - 1] if pd.notnull(x) else "")

    # กรองเฉพาะแถวที่ Month_name มีค่า (ไม่เป็นค่าว่าง)
    plot_df = plot_df[plot_df["Month_name"] != ""]

    # สร้างกราฟเส้น
    fig = px.line(
        plot_df,
        x="Month_name",
        y="Availability (%)",
        color="Device",
        markers=True,
        title="📈 Availability (%) รายเดือนของแต่ละ Device",
    )

    # ปรับแกนและรูปแบบ
    fig.update_layout(
        xaxis_title="เดือน",
        yaxis_title="Availability (%)",
        yaxis=dict(range=[0, 100]),
        legend_title="Device",
        margin=dict(t=60, b=40)
    )

    # แสดงใน Streamlit
    st.plotly_chart(fig, use_container_width=True)

def df_addColMonth(df):
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
        values="Availability (%)",
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
    
    return pivot_df

def evaluate(df,bins,labels,flag):
    #เพิ่ม Month
    df["Month"] = pd.to_datetime(df["Availability Period"], format="%Y-%m", errors="coerce")
    df["Month_str"] = df["Month"].dt.strftime("%Y-%m")
    # เพิ่มคอลัมน์ "เกณฑ์การประเมิน"
    df["เกณฑ์การประเมิน"] = pd.cut(df["Availability (%)"], bins=bins, labels=labels, right=True)
    # กำหนดเงื่อนไขสำหรับผลการประเมิน
    def evaluate_result(row):
        if row["เกณฑ์การประเมิน"] == "90 < Availability (%) <= 100":
            return "✅"
        elif row["เกณฑ์การประเมิน"] == "80 < Availability (%) <= 90":
            return "⚠️"
        else:
            return "❌"
    # เพิ่มคอลัมน์ "ผลการประเมิน"
    df["ผลการประเมิน"] = df.apply(evaluate_result, axis=1)

    # สรุปเฉลี่ยรายเดือน
    month_summary = df.groupby("Month_str")["Availability (%)"].mean().reset_index()
    month_summary["เกณฑ์การประเมิน"] = pd.cut(month_summary["Availability (%)"], bins=bins, labels=labels)
    month_summary["ผลการประเมิน"] = month_summary["เกณฑ์การประเมิน"].apply(
        lambda x: "✅" if x == "90 < Availability (%) <= 100" else ("⚠️" if x == "80 < Availability (%) <= 90" else "❌")
    )
    month_summary["จำนวน Device"] = df.groupby("Month_str")["Device"].nunique().values
    month_summary["เปอร์เซ็นต์ (%)"] = 100.0

    ### ✅
    st.info(f"✅ สรุป Avg. Availability (%) รวมของ {flag} แยกตามเดือน")
    st.write(month_summary)      

    # คำนวณค่าเฉลี่ยของ Availability (%) แยกตาม Device โดยเฉลี่ยจากหลายเดือน
    device_avg = df.groupby("Device")["Availability (%)"].mean().reset_index()
    device_avg.columns = ["Device", "Avg Availability (%)"]
        # เพิ่มการประเมินผลแบบสัญลักษณ์
    def evaluate_status(avg):
        if avg > 90:
            return "✅"
        elif avg > 80:
            return "⚠️"
        else:
            return "❌"

    device_avg["Evaluation"] = device_avg["Avg Availability (%)"].apply(evaluate_status)

    device_months = df.groupby("Device")["Month"].nunique().reset_index()
    device_months.columns = ["Device", "Active Months"]

    # รวมเข้ากับตาราง avg
    device_avg = device_avg.merge(device_months, on="Device")
    
    ### ✅
    st.info(f"✅ สรุป Avg. Availability (%) แยกตาม{flag}")
    st.dataframe(device_avg)

    # สรุปรวมทั้งหมด
    overall_avg = df["Availability (%)"].mean()
    total_row = pd.DataFrame({
        "Month_str": ["รวมทั้งหมด"],
        "Availability (%)": [overall_avg],
        "เกณฑ์การประเมิน": [pd.cut([overall_avg], bins=bins, labels=labels)[0]],
        "ผลการประเมิน": [evaluate_result({"เกณฑ์การประเมิน": pd.cut([overall_avg], bins=bins, labels=labels)[0]})],
        "จำนวน Device": [df["Device"].nunique()],
        "เปอร์เซ็นต์ (%)": [100.0]
    })
    summary_df = pd.concat([month_summary, total_row], ignore_index=True)
    
    summary_df["Device+Percent"] = summary_df.apply(
        lambda row: f"{int(row['จำนวน Device']):,} ({row['เปอร์เซ็นต์ (%)']:.2f}%)", axis=1
    )
    pivot_df = df_addColMonth(df)

    ### ✅
    st.info(f"✅ สรุป Availability (%) แต่ละ{flag}แยกตามเดือน")
    st.write(pivot_df)


    def test():
        """
        # สรุปจำนวน Device ในแต่ละเกณฑ์
        summary_df = df["ผลการประเมิน"].value_counts().reset_index()
        summary_df.columns = ["ผลการประเมิน", "จำนวน Device"]
        # สรุปจำนวน Device ในแต่ละ "เกณฑ์การประเมิน" และ "ผลการประเมิน"
        summary_df = df.groupby(["เกณฑ์การประเมิน", "ผลการประเมิน"]).size().reset_index(name="จำนวน Device")
        # ลบแถวที่ "จำนวน Device" เป็น 0 ออก
        summary_df = summary_df[summary_df["จำนวน Device"] > 0]
        # ลบ index ออกจาก summary_df
        summary_df = summary_df.reset_index(drop=True)
        # จัดกลุ่มข้อมูล Availability (%) ตามช่วงที่กำหนด
        df["Availability Range"] = pd.cut(
            df["Availability (%)"], bins=bins, labels=labels, right=True
        )
        # คำนวณจำนวนทั้งหมดของ Device
        total_devices = summary_df["จำนวน Device"].sum()
        # คำนวณ % ของแต่ละช่วง
        summary_df["เปอร์เซ็นต์ (%)"] = (summary_df["จำนวน Device"] / total_devices) * 100
        # จัดรูปแบบค่าเปอร์เซ็นต์ให้เป็นทศนิยม 2 ตำแหน่ง
        #summary_df["เปอร์เซ็นต์ (%)"] = summary_df["เปอร์เซ็นต์ (%)"].map("{:.2f}%".format)
        summary_df["เปอร์เซ็นต์ (%)"] = summary_df["เปอร์เซ็นต์ (%)"].round(2)

        cols = ['เกณฑ์การประเมิน','ผลการประเมิน'] + [col for col in df.columns if col != 'เกณฑ์การประเมิน' and 
                                                    col != 'ผลการประเมิน']
        cols_show = ["ผลการประเมิน", "เกณฑ์การประเมิน", "Device+Percent"]
        #df = df[[
        #    "เกณฑ์การประเมิน", "Device", "description", "Availability (%)",
        #    "Initializing Count", "Initializing Duration (seconds)",
        #    "Telemetry Failure Count", "Telemetry Failure Duration (seconds)",
        #    "Connecting Count", "Connecting Duration (seconds)", "Month", "ผลการประเมิน", "Availability Range"
        #]]
        # ✨ เพิ่มแถวผลรวมของจำนวน Device
        total_row = pd.DataFrame({
            "ผลการประเมิน": ["รวมทั้งหมด"],
            "เกณฑ์การประเมิน": [""],
            "จำนวน Device": [summary_df["จำนวน Device"].sum()],
            "เปอร์เซ็นต์ (%)": [100.0]  # เพราะรวมคือ 100%
        })

        # ✨ เอามาต่อกับ summary_df
        summary_df = pd.concat([summary_df, total_row], ignore_index=True)
        summary_df = summary_df[["ผลการประเมิน", 
                                "เกณฑ์การประเมิน",
                                "จำนวน Device",
                                "เปอร์เซ็นต์ (%)"]]
        # ✅ Format ตัวเลขสวยๆ
        summary_df["จำนวน Device"] = summary_df["จำนวน Device"].apply(lambda x: f"{x:,}")
        summary_df["เปอร์เซ็นต์ (%)"] = summary_df["เปอร์เซ็นต์ (%)"].apply(lambda x: f"{x:.2f}%")
        summary_df["Device+Percent"] = summary_df.apply(
            lambda row: f"{row['จำนวน Device']} ({row['เปอร์เซ็นต์ (%)']})", axis=1
            )
        summary_df = summary_df[["ผลการประเมิน", 
                                "เกณฑ์การประเมิน",
                                "จำนวน Device",
                                "เปอร์เซ็นต์ (%)",
                                "Device+Percent"]]
        show_df = summary_df.copy()[cols_show]
        fig1 = px.bar(
            #summary_df[summary_df["เกณฑ์การประเมิน"] != "รวมทั้งหมด"],  # ไม่เอาแถวรวมทั้งหมดไป plot,
            summary_df,
            x="เกณฑ์การประเมิน",
            y="จำนวน Device",
            color="ผลการประเมิน",
            text="จำนวน Device",
            barmode="group",
            title="จำนวน Device ตามเกณฑ์การประเมิน",
        )
        # ✅ Pie Chart สัดส่วนผลการประเมิน
        fig2 = px.pie(
            summary_df[summary_df["เกณฑ์การประเมิน"] != "รวมทั้งหมด"],
            names="ผลการประเมิน",
            values="จำนวน Device",
            title="ประเมิน",
            hole=0.4
        )
        fig2.update_traces(textinfo='percent+label')
        """
    
    # Bar Chart
    fig1 = px.bar(
        summary_df[summary_df["Month_str"] != "รวมทั้งหมด"],
        x="Month_str",
        y="จำนวน Device",
        color="ผลการประเมิน",
        text="Device+Percent",
        barmode="group",
        title="จำนวน Device ตามเกณฑ์การประเมิน (รายเดือน)"
    )

    # Pie Chart
    fig2 = px.pie(
        summary_df[summary_df["Month_str"] == "รวมทั้งหมด"],
        names="ผลการประเมิน",
        values="จำนวน Device",
        title="สรุปผลรวมการประเมินทั้งหมด",
        hole=0.4
    )
    fig2.update_traces(textinfo="percent+label")

    show_df = summary_df[["Month_str", "Availability (%)", "เกณฑ์การประเมิน", "ผลการประเมิน", "Device+Percent"]]
    return df, summary_df, fig1, fig2, show_df

def range_ava(df,bins,labels):
    filtered_df["Availability Group"] = pd.cut(filtered_df["Availability (%)"], bins=bins_bar, labels=labels_bar, right=True)
    filtered_by_group = filtered_df[filtered_df["Availability Group"].isin(selected_group)]
    grouped_counts = filtered_by_group["Availability Group"].value_counts().sort_index().reset_index()
    grouped_counts.rename(columns={"Availability Group": "ช่วง % Availability","count": "จำนวนอุปกรณ์"}, inplace=True)
    fig3 = px.bar(
                grouped_counts,
                x="ช่วง % Availability",
                y="จำนวนอุปกรณ์",
                color="ช่วง % Availability",
                text="จำนวนอุปกรณ์",
                title="📊 จำนวนอุปกรณ์ในแต่ละช่วง % Availability",
            )
    fig3.update_layout(
            xaxis_title="ช่วง % Availability",
            yaxis_title="จำนวนอุปกรณ์",
            showlegend=False,
            )
    st.plotly_chart(fig3, use_container_width=True)

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

def convert_date(df):
    #df['Availability Period'] = df['Availability Period'].astype(str).apply(convert_thai_date)
    df['Availability Period'] = pd.to_datetime(df['Availability Period'], format='%Y-%m')
    df['Month'] = df['Availability Period'].dt.to_period('M')
    months = sorted(df['Month'].dropna().unique().astype(str))
    return df, months

# ฟังก์ชันเลือกสีตามเงื่อนไขของ label
def get_color(label):
    try:
        # ดึงค่าตัวเลขจากช่วง เช่น "0-10 %" → 10
        upper = int(label.split("-")[1].strip().replace("%", ""))
        if upper <= 80:
            return "red"
        elif upper <= 90:
            return "yellow"
        else:
            return "green"
    except:
        return "gray"


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
        df["Availability (%)"] = df["Availability (%)"].replace({",": "", "%": ""}, regex=True)
        df["Availability (%)"] = pd.to_numeric(df["Availability (%)"], errors="coerce")

        all_data.append(df)

    df_combined = pd.concat(all_data, ignore_index=True)
    option_func = ['สถานะ', 'ประเมินผล', 'Histogram', 'เปรียบเทียบทุกเดือน']
    option_submenu = ['ระบบจำหน่ายสายส่ง','สถานีไฟฟ้า']
    submenu_select = st.sidebar.radio(label="ระบบ: ", options = option_submenu)
    if submenu_select == 'ระบบจำหน่ายสายส่ง':
        title = 'อุปกรณ์ FRTU'
    else:
        title = 'สถานีไฟฟ้า'

    func_select = st.sidebar.radio(label="function: ", options = option_func)   
    if func_select == 'ประเมินผล':
        bins_eva = [0, 80, 90, 100]
        labels_eva = ["0 <= Availability (%) <= 80", "80 < Availability (%) <= 90", "90 < Availability (%) <= 100"]
        cols = "จำนวน " + title
        df_evaluate = df_combined.copy()

        df_eva, summary_df, fig1, fig2, show_df = evaluate(df_evaluate,bins_eva,labels_eva,title)
        #st.plotly_chart(fig1)
        #st.plotly_chart(fig2)
        #st.dataframe(show_df)
        show_df.rename(columns={"Device+Percent": cols}, inplace=True)
        #st.markdown("### 🔹 ผลการประเมิน Availability (%) ของอุปกรณ์ในสถานีไฟฟ้า")
        #st.dataframe(show_df)
        header_colors = ['#003366', '#006699', '#0099CC']   # สีหัวตาราง
        cell_colors = ['#E6F2FF', '#D9F2D9', '#FFF2CC']     # สีพื้นหลังเซลล์แต่ละคอลัมน์

        fig3 = go.Figure(data=[go.Table(
            header=dict(
                values=[
                    "<b>ผลการประเมิน</b>",
                    "<b>เกณฑ์การ<br>ประเมิน</b>",
                    f"<b>{cols}</b>"
                ],
                fill_color=header_colors,
                align=["center", "center", "center"],
                font=dict(color='white', size=14)
            ),
            cells=dict(
                values=[
                    summary_df["ผลการประเมิน"],
                    summary_df["เกณฑ์การประเมิน"],
                    summary_df["Device+Percent"]
                ],
                fill_color=[cell_colors[0]] * len(summary_df.columns),
                align='center',
                font=dict(color='black', size=13)
            )
        )])

        fig3.update_layout(
            title=dict(
                text=f"🔹 ผลการประเมิน Availability (%) ของ {cols.replace('<br>', ' ')}",
                x=0.5,  # ตรงกลาง
                xanchor='center',
                font=dict(size=20)
                ),
                margin=dict(t=60, b=20)
        )
        st.plotly_chart(fig3, use_container_width=True)

    elif func_select == 'Histogram':
        
        df_histogram = df_combined.copy()  # ป้องกัน SettingWithCopyWarning
        # ลบ % และ comma ออกก่อน แล้วแปลงเป็น float
        df_histogram["Availability (%)"] = df_histogram["Availability (%)"].replace({",": "", "%": ""}, regex=True)
        df_histogram["Availability (%)"] = pd.to_numeric(df_histogram["Availability (%)"], errors="coerce")
        #add แปลงเป็นเดือน (ชื่อไทย)
        df_histogram["Month"] = pd.to_datetime(df_histogram["Availability Period"], format="%Y-%m", errors="coerce")
        df_histogram["Month_num"] = df_histogram["Month"].dt.month
        df_histogram["Month_year"] = df_histogram["Month"].dt.to_period("M").astype(str)  # รูปแบบ: 2025-03
        #thai_months = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
                    #'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']
        #df_histogram["Month_name"] = df_histogram["Month_num"].apply(lambda x: thai_months[x - 1] if pd.notnull(x) else "")

        # กำหนดช่วงกลุ่ม Availability
        bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        labels = [f"{bins[i]}-{bins[i+1]} %" for i in range(len(bins)-1)]
        df_histogram["Availability Group"] = pd.cut(df_histogram["Availability (%)"], bins=bins, labels=labels, right=True)

        # --- สร้าง Selectbox สำหรับเลือกเดือน ---
        available_months = sorted(df_histogram["Month_year"].dropna().unique())
        selected_month = st.selectbox("📅 เลือกเดือนที่ต้องการดู Histogram", available_months)

        # --- กรองข้อมูลเฉพาะเดือนที่เลือก ---
        filtered_df = df_histogram[df_histogram["Month_year"] == selected_month]

        # Group ข้อมูล
        #grouped_counts = df_histogram.groupby(["Month_name", "Availability Group"]).size().reset_index(name="จำนวน Device")
        #grouped_counts = df_histogram["Availability Group"].value_counts().sort_index().reset_index() ###ของเดิม

        # --- สร้าง Histogram ---
        grouped_counts = filtered_df["Availability Group"].value_counts().sort_index().reset_index()
        grouped_counts.columns = ["ช่วง % Availability", "จำนวน Device"]

        """
        # Plot เป็นกราฟแยกตามเดือน
        fig_old = px.bar(
            grouped_counts,
            x="Availability Group",
            y="จำนวน Device",
            color="Month_name",
            barmode="group",  # หรือ "stack" ก็ได้
            text="จำนวน Device",
            title="📊 จำนวน Device ในแต่ละช่วง % Availability แยกตามเดือน",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_old.update_layout(
            xaxis_title="ช่วง % Availability",
            yaxis_title="จำนวน Device",
            yaxis_type="log"
        )
        """
            # วาดกราฟ
        fig = px.bar(
            grouped_counts,
            x="ช่วง % Availability",
            y="จำนวน Device",
            color="ช่วง % Availability",
            text="จำนวน Device",
            title=f"📊 จำนวน Device ในแต่ละช่วง % Availability (เดือน {selected_month})",
            color_discrete_sequence=[
                "#FF0000", "#FF4000", "#FF8000", "#FFBF00", "#FFFF00",
                "#BFFF00", "#80FF00", "#40FF00", "#00FF00", "#00CC00"
            ]
        )
        fig.update_layout(
            xaxis_title="ช่วง % Availability",
            yaxis_title="จำนวน Device",
            showlegend=False,
        )

        fig.update_traces(texttemplate="%{text:,}", textposition="outside")

        st.plotly_chart(fig, use_container_width=True)

        typeplot = "Line"
        plot(df_combined,typeplot)
        plot_avg(df_combined)

        fig2 = px.bar(
            grouped_counts,
            x="Availability Group",
            y="จำนวน Device",
            facet_col="Month_name",
            color="Availability Group",
            text="จำนวน Device",
            title="📊 Availability Distribution รายเดือน (แยกกราฟต่อเดือน)",
            category_orders={"Availability Group": labels},
            color_discrete_sequence=px.colors.sequential.YlGn
        )

        fig2.update_layout(
            height=500,
            showlegend=False,
            yaxis_type="log"
        )
        fig2.update_traces(texttemplate="%{text:,}", textposition="outside")

        st.plotly_chart(fig2, use_container_width=True)
        cols = "จำนวน " + title
        grouped_counts.rename(columns={"Availability Group": "ช่วง % Availability","count": cols}, inplace=True)
        fig = px.bar(
                    grouped_counts,
                    x="ช่วง % Availability",
                    y=cols,
                    color="ช่วง % Availability",
                    text=cols,
                    title=f"📊 {cols}ในแต่ละช่วง % Availability",
                    color_discrete_sequence=[
                        "#FF0000", "#FF4000", "#FF8000", "#FFBF00", "#FFFF00",
                        "#BFFF00", "#80FF00", "#40FF00", "#00FF00", "#00CC00"
                        ]  # ตัวอย่างสีไล่จากแดงไปเขียว
                        )
        fig.update_layout(
                xaxis_title="ช่วง % Availability",
                yaxis_title=cols,
                showlegend=False,
                )
        fig.update_traces(
                texttemplate="%{text:,}",  # ใส่ comma
                textposition="outside"
                )
        st.plotly_chart(fig, use_container_width=True)

        # เตรียมข้อมูล
        x_vals = grouped_counts["ช่วง % Availability"]
        y_vals = grouped_counts[cols]
        colors = [get_color(x) for x in x_vals]

        # สร้างกราฟ
        fig11 = go.Figure(data=[go.Bar(
            x=x_vals,
            y=y_vals,
            text=[f"{int(v):,}" for v in y_vals],  # ใส่ comma
            textposition="outside",
            marker_color=colors
        )])
        # ปรับ layout
        fig11.update_layout(
            title=f"📊 {cols}ในแต่ละช่วง % Availability (log scale)",
            xaxis_title="ช่วง % Availability",
            yaxis_type="log",  # ใช้ log scale
            yaxis_title=cols,
            showlegend=False,
            margin=dict(t=60, b=40)
        )

        st.plotly_chart(fig11, use_container_width=True)
    elif func_select == 'สถานะ':
        st.write("n/a")
    elif func_select == 'เปรียบเทียบทุกเดือน':
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
                df["Availability (%)"] = df["Availability (%)"].replace({",": "", "%": ""}, regex=True)
                df["Availability (%)"] = pd.to_numeric(df["Availability (%)"], errors="coerce")

                all_data.append(df)

            df_combined = pd.concat(all_data, ignore_index=True)

            # ---- Monthly Summary ----
            df_combined["Year"] = df_combined["Month"].dt.year
            selected_year = df_combined["Year"].mode()[0]  # ปีที่พบมากที่สุด

            # จำกัดแค่ปีเดียว เช่น 2025
            df_combined = df_combined[df_combined["Year"] == selected_year]

            monthly_avg = df_combined.groupby(df_combined["Month"].dt.month)["Availability (%)"].mean().reset_index()
            monthly_avg.columns = ["MonthNumber", "Availability (%)"]

            # เติมเดือนที่หายไป (ให้มีครบ 1-12)
            all_months_df = pd.DataFrame({"MonthNumber": list(range(1, 13))})
            monthly_avg = all_months_df.merge(monthly_avg, on="MonthNumber", how="left")
            #monthly_avg["Availability (%)"] = monthly_avg["Availability (%)"].fillna(0)

            # แปลงเลขเดือนเป็นชื่อ (ภาษาไทย/อังกฤษ)
            month_names = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
                        'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']
            monthly_avg["Month"] = monthly_avg["MonthNumber"].apply(lambda x: month_names[x-1])

            # ---- Bar Chart ----
            fig_bar = px.bar(
                monthly_avg,
                x="Month",
                y="Availability (%)",
                text=monthly_avg["Availability (%)"].round(1),
                color="Availability (%)",
                title=f"📊 Availability (%) เฉลี่ยรายเดือน (Bar Chart) - ปี {selected_year}"
            )
            fig_bar.update_layout(
                xaxis_title="เดือน",
                yaxis_title="Availability (%)",
                yaxis=dict(range=[0, 100]),
                showlegend=False,
                margin=dict(t=60, b=40)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            # ---- Line Chart ----
            fig_line = px.line(
                monthly_avg,
                x="MonthNumber",
                y="Availability (%)",
                markers=True,
                text=monthly_avg["Availability (%)"].round(1),
                title=f"📈 Availability (%) เฉลี่ยรายเดือน (Line Chart) - ปี {selected_year}"
            )

            fig_line.update_traces(
                textposition="bottom center",  # 👈 อยู่ใต้ marker เพื่อลดปัญหาล้น
                connectgaps=False
            )

            fig_line.update_layout(
                xaxis=dict(
                    title="เดือน",
                    tickmode="array",
                    tickvals=list(range(1, 13)),
                    ticktext=month_names
                ),
                yaxis=dict(
                    title="Availability (%)",
                    range=[0, 105]  # 👈 เพิ่มเพดานนิดหน่อยกันล้น
                ),
                showlegend=False,
                margin=dict(t=80, b=40)  # 👈 เพิ่ม margin ด้านบน
            )

            st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning("🚨 ไม่ได้เลือก function")

"""   
uploaded_file = st.file_uploader("📥 อัปโหลดไฟล์ Excel หรือ CSV", type=["xlsx", "csv"])
if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
        st.success(f"✅ โหลดไฟล์ {uploaded_file.name} เรียบร้อย")
    else:
        df = pd.read_excel(uploaded_file)
        st.success(f"✅ โหลดไฟล์ {uploaded_file.name} ไม่เรียบร้อย")
        
    df_filtered, months = convert_date(df)
"""  

    