import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go



def evaluate(df,bins,labels):
    # ลบ % และ comma ออกก่อน แล้วแปลงเป็น float
    df["Availability (%)"] = df["Availability (%)"].replace({",": "", "%": ""}, regex=True)
    df["Availability (%)"] = pd.to_numeric(df["Availability (%)"], errors="coerce")

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

uploaded_file = st.file_uploader("📥 อัปโหลดไฟล์ Excel หรือ CSV", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
        st.success(f"✅ โหลดไฟล์ {uploaded_file.name} เรียบร้อย")
    else:
        df = pd.read_excel(uploaded_file)
        st.success(f"✅ โหลดไฟล์ {uploaded_file.name} ไม่เรียบร้อย")
        
    df_filtered, months = convert_date(df)
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
        df_evaluate = df_filtered.copy()
        df_eva, summary_df, fig1, fig2, show_df = evaluate(df_evaluate,bins_eva,labels_eva)
        st.write(fig2)
        show_df.rename(columns={"Device+Percent": cols}, inplace=True)
        #st.markdown("### 🔹 ผลการประเมิน Availability (%) ของอุปกรณ์ในสถานีไฟฟ้า")
        #st.dataframe(show_df)
        header_colors = ['#003366', '#006699', '#0099CC']   # สีหัวตาราง
        cell_colors = ['#E6F2FF', '#D9F2D9', '#FFF2CC']     # สีพื้นหลังเซลล์แต่ละคอลัมน์

        fig2 = go.Figure(data=[go.Table(
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

        fig2.update_layout(
            title=dict(
                text=f"🔹 ผลการประเมิน Availability (%) ของ {cols.replace('<br>', ' ')}",
                x=0.5,  # ตรงกลาง
                xanchor='center',
                font=dict(size=20)
                ),
                margin=dict(t=60, b=20)
        )
        #st.plotly_chart(fig2, use_container_width=True)

    elif func_select == 'Histogram':
        bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        labels = [f"{bins[i]}-{bins[i+1]} %" for i in range(len(bins)-1)]  # ["0-10", "10-20", ..., "90-100"]
        df_histogram = df_filtered.copy()  # ป้องกัน SettingWithCopyWarning
        # ลบ % และ comma ออกก่อน แล้วแปลงเป็น float
        df["Availability (%)"] = df["Availability (%)"].replace({",": "", "%": ""}, regex=True)
        df["Availability (%)"] = pd.to_numeric(df["Availability (%)"], errors="coerce")
        df_histogram["Availability Group"] = pd.cut(df_histogram["Availability (%)"], bins=bins, labels=labels, right=True)
        grouped_counts = df_histogram["Availability Group"].value_counts().sort_index().reset_index()
        cols = "จำนวน " + title
        grouped_counts.rename(columns={"Availability Group": "ช่วง % Availability","count": cols}, inplace=True)
        fig = px.bar(
                    grouped_counts,
                    x="ช่วง % Availability",
                    y=cols,
                    color="ช่วง % Availability",
                    text=cols,
                    title=f"📊 {cols}ในแต่ละช่วง % Availability",
                )
        fig.update_layout(
                xaxis_title="ช่วง % Availability",
                yaxis_title=cols,
                showlegend=False,
                )
        st.plotly_chart(fig, use_container_width=True)
    elif func_select == 'สถานะ':
        st.write("n/a")
    elif func_select == 'เปรียบเทียบทุกเดือน':
        df_compare = df_filtered.copy()
        #st.write(df_compare.columns.to_list())

        # ล้างช่องว่าง + ลบ NaN
        df_compare = df_compare[df_compare['Month'].notna()]
        df_compare['Month'] = df_compare['Month'].astype(str).str.strip()

        # แปลงเป็น datetime แล้วเหลือแค่เดือน
        df_compare['Month'] = pd.to_datetime(df_compare['Month'], format="%Y-%m", errors='coerce')
        df_compare['Month'] = df_compare['Month'].dt.to_period('M').dt.to_timestamp()

        # สร้างช่วงเดือนครบ 12 เดือน (ตามปีที่เจอในข้อมูล)
        min_month = df_compare['Month'].min()
        max_month = df_compare['Month'].max()
        
                # สมมุติว่า df_compare['Month'] ถูกแปลงแล้ว และคำนวณ mean ตามเดือน
        monthly_summary = df_compare.groupby('Month')['Availability (%)'].mean().reset_index()

        # เติมเดือนที่หายไป (ถ้าต้องการให้มีครบ 12 เดือน)
        all_months = pd.date_range(start="2025-01-01", end="2025-12-01", freq='MS')
        monthly_summary_full = pd.DataFrame({'Month': all_months})
        # รวมกับค่าจริงที่ได้จากข้อมูล
        monthly_summary = df_compare.groupby('Month')['Availability (%)'].mean().reset_index()
        monthly_summary_full = monthly_summary_full.merge(monthly_summary, on='Month', how='left')
        #แปลงค่า NaN เป็น 0 หรือใช้วิธี interpolation (เลือกอย่างใดอย่างหนึ่ง)
        # ทางเลือก 1: เติม 0 แทน NaN
        monthly_summary_full['Availability (%)'] = monthly_summary_full['Availability (%)'].fillna(0)
        # สร้างชื่อเดือนแบบสวยงาม
        #monthly_summary_full['Month_str'] = monthly_summary_full['Month'].dt.strftime('%b %Y')

        # เรียงลำดับให้แน่นอน
        #monthly_summary_full = monthly_summary_full.sort_values('Month')

        # Plot bar chart
        fig = px.bar(
            monthly_summary_full,
            x="Month",
            y="Availability (%)",
            #text="Availability (%)",
            text=monthly_summary_full["Availability (%)"].round(1),  # แสดงค่า % บนแท่ง
            color="Availability (%)",
            title="📊 Availability (%) รายเดือน (ครบ 12 เดือน)"
        )

        # จัดรูปแบบแกน X ให้แสดงชื่อเดือน (เช่น Apr 2025)
        fig.update_layout(
            xaxis_title="เดือน",
            yaxis_title="Availability (%)",
            yaxis=dict(range=[0, 100]),
            xaxis=dict(
                tickformat="%b %Y",  # แสดง Apr 2025
                tickmode='linear'
            ),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
        # plot line graph
        fig_monthly = px.line(
            monthly_summary_full,
            x="Month",
            y="Availability (%)",
            markers=True,
            title="📈 Availability (%) รายเดือน (Line Graph)"
        )

        # ปรับแกน X ให้อ่านง่ายและครบ 12 เดือน
        fig_monthly.update_layout(
            xaxis=dict(
                tickformat="%b %Y",  # Apr 2025
                tickmode="linear",
                tickangle=-45        # หมุน label แกน X ป้องกันซ้อน
            ),
            yaxis=dict(range=[0, 100]),  # สเกล 0-100
            showlegend=False,
        )
        st.plotly_chart(fig_monthly, use_container_width=True)
    else:
        st.warning("🚨 ไม่ได้เลือก function")


    