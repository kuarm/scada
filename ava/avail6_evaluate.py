import pandas as pd
import streamlit as st
import plotly.express as px





uploaded_file = st.file_uploader("📥 อัปโหลดไฟล์ Excel หรือ CSV", type=["xlsx", "csv"])

def evaluate(df,bins,labels):
    # เพิ่มคอลัมน์ "เกณฑ์การประเมิน"
    df["เกณฑ์การประเมิน"] = pd.cut(df["Availability (%)"], bins=bins, labels=labels, right=True)
    # กำหนดเงื่อนไขสำหรับผลการประเมิน
    def evaluate_result(row):
        if row["เกณฑ์การประเมิน"] == "90 < Availability (%) <= 100":
            return "✅ ไม่แฮงค์"
        elif row["เกณฑ์การประเมิน"] == "80 < Availability (%) <= 90":
            return "⚠️ ทรงๆ"
        else:
            return "❌ ต้องนอน"
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
    return df, summary_df, fig1, fig2

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

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
    else:
        df = pd.read_excel(uploaded_file)
     
    df_filtered, months = convert_date(df)
    st.success(f"✅ โหลดไฟล์ {uploaded_file.name} เรียบร้อย")
    
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
        df_eva, summary_df, fig1, fig2 = evaluate(df_evaluate,bins_eva,labels_eva)
        summary_df.rename(columns={"จำนวน Device": cols}, inplace=True)
        st.write(summary_df)
    elif func_select == 'Histogram':
        bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        labels = [f"{bins[i]}-{bins[i+1]} %" for i in range(len(bins)-1)]  # ["0-10", "10-20", ..., "90-100"]
        df_histogram = df_filtered.copy()  # ป้องกัน SettingWithCopyWarning
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
        
        # คำนวณค่ากลุ่มรายเดือน
        monthly_summary = df_compare.groupby('Month')['Availability (%)'].mean().reset_index()
        
        #all_months = pd.date_range(start=min_month, end=max_month, freq='MS')  # MS = Month Start
        # สร้างช่วงเดือนครบ 12 เดือนในปี 2025
        all_months = pd.date_range(start="2025-01-01", end="2025-12-01", freq='MS')  # Month Start
        # สร้าง DataFrame เดือนครบทุกเดือน
        all_months_df = pd.DataFrame({'Month': all_months})
        all_months_df['Month_str'] = all_months_df['Month'].dt.strftime('%b %Y')
        
        # แปลง monthly_summary ให้มี Month (datetime) และ Month_str
        monthly_summary['Month'] = pd.to_datetime(monthly_summary['Month'], format="%b %Y")
        monthly_summary['Month_str'] = monthly_summary['Month'].dt.strftime('%b %Y')

        # Merge ข้อมูลจริงเข้ากับเดือนทั้งหมด
        monthly_summary_full = pd.merge(all_months_df, monthly_summary, on='Month_str', how='left')

        # แทนค่าที่ไม่มีเป็น 0 (หรือใช้ NaN ก็ได้แล้วแต่กราฟ)
        monthly_summary_full['Availability (%)'] = monthly_summary_full['Availability (%)'].fillna(0)

        # เรียงตามลำดับเวลา
        monthly_summary_full = monthly_summary_full.sort_values('Month_str')
        
        # ตาราง
        st.dataframe(monthly_summary_full[['Month_str', 'Availability (%)']], use_container_width=True)

        # เรียงลำดับตาม Month ที่เป็น datetime
        #monthly_summary_full = monthly_summary_full.sort_values('Month')
        
        st.write(monthly_summary_full[['Month', 'Month_str']])
        
         # Line Chart
        st.subheader("📊 Availability (%) รายเดือน (เส้น)")
        # วาดกราฟจาก monthly_summary_full
        fig_line = px.line(
            monthly_summary_full,
            x="Month_str",
            y="Availability (%)",
            text="Availability (%)",
            color="Availability (%)",
            title="📊 Availability (%) รายเดือน (ครบ 12 เดือน)"
        )
        fig_line.update_layout(
            xaxis_title="เดือน",
            yaxis_title="Availability (%)",
            yaxis=dict(range=[0, 100]),
            xaxis_tickmode='array',
            xaxis_tickvals=monthly_summary_full['Month_str'],
            showlegend=False,
        )
        st.plotly_chart(fig_line, use_container_width=True)

        # Bar Chart
        st.subheader("📊 Availability (%) รายเดือน (แท่ง)")
        fig_bar = px.bar(
            monthly_summary,
            x="Month_str",
            y="Availability (%)",
            color="Availability (%)",
            text="Availability (%)"
        )
        fig_bar.update_layout(
            xaxis_title="เดือน",
            yaxis_title="Availability (%)",
            yaxis=dict(range=[0, 100]),  # บังคับแกน Y 0-100
            showlegend=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("🚨 ไม่ได้เลือก function")


    