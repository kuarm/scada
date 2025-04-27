import pandas as pd
import streamlit as st
import plotly.express as px

source_csv_feeder = "D:/ML/scada/ava/source_csv/availability_data.csv"
source_csv_sub = ""

# แผนที่ชื่อเดือนย่อภาษาไทย -> เลขเดือน
thai_months = {
    'ม.ค.': '01', 'ก.พ.': '02', 'มี.ค.': '03', 'เม.ย.': '04',
    'พ.ค.': '05', 'มิ.ย.': '06', 'ก.ค.': '07', 'ส.ค.': '08',
    'ก.ย.': '09', 'ต.ค.': '10', 'พ.ย.': '11', 'ธ.ค.': '12'
}

@st.cache_data
def load_data_csv(file_path):
    df = pd.read_csv(file_path)
    # แปลงวันที่ไทยเป็นรูปแบบสากล
    df['Availability Period'] = df['Availability Period'].astype(str).apply(convert_thai_date)
    df['Availability Period'] = pd.to_datetime(df['Availability Period'], format='%m %Y')
    df['Month'] = df['Availability Period'].dt.to_period('M')
    
    return df

# แปลงชื่อเดือนในคอลัมน์ Availability Period เป็นรูปแบบที่ pandas เข้าใจ
def convert_thai_date(date_str):
    for th_month, num_month in thai_months.items():
        if th_month in date_str:
            return date_str.replace(th_month, num_month)
    return date_str

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
        "เกณฑ์การประเมิน": ["รวมทั้งหมด"],
        "ผลการประเมิน": [""],
        "จำนวน Device": [summary_df["จำนวน Device"].sum()],
        "เปอร์เซ็นต์ (%)": [100.0]  # เพราะรวมคือ 100%
    })

    # ✨ เอามาต่อกับ summary_df
    summary_df = pd.concat([summary_df, total_row], ignore_index=True)
    # ✅ Format ตัวเลขสวยๆ
    summary_df["จำนวน Device"] = summary_df["จำนวน Device"].apply(lambda x: f"{x:,}")
    summary_df["เปอร์เซ็นต์ (%)"] = summary_df["เปอร์เซ็นต์ (%)"].apply(lambda x: f"{x:.2f}%")
    fig1 = px.bar(
        summary_df[summary_df["เกณฑ์การประเมิน"] != "รวมทั้งหมด"],  # ไม่เอาแถวรวมทั้งหมดไป plot,
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

option_menu = ['สถานะอุปกรณ์','% ความพร้อมใช้งาน', '% การสั่งการ', 'ข้อมูลการสั่งการ']
option_func = ['ข้อมูล & ประเมินผล % Availability', 'ข้อมูลอุปกรณ์ตาม % Availability', 'ดู % Availability vs ']
option_submenu = ['ระบบจำหน่ายสายส่ง','สถานีไฟฟ้า']

def main():
    menu_select = st.sidebar.radio(label="Menu: ", options = option_menu)
    
    if menu_select == '% ความพร้อมใช้งาน':
        #st.header("📊 %ความพร้อมใช้งานของอุปกรณ์")
        
        submenu_select = st.sidebar.radio(label="ระบบ: ", options = option_submenu)
        
        if submenu_select == 'ระบบจำหน่ายสายส่ง':
            df = load_data_csv(source_csv_feeder)
            # --- 🎯 Filter เดือน ---
            months = sorted(df['Month'].dropna().unique().astype(str))
            selected_month = st.sidebar.selectbox("เลือกเดือน", months)
            # กรองข้อมูลตามเดือน
            filtered_df = df[df['Month'].astype(str) == selected_month]
            filtered_df = filtered_df.drop(columns=['Availability Period','Source File'],axis=0)
            
            func_select = st.sidebar.radio(label="function: ", options = option_func)
            
            if func_select == 'ข้อมูล & ประเมินผล % Availability':
                st.info(f"📊 % ความพร้อมใช้งานอุปกรณ์ Frtu เดือน {selected_month} จำนวน {len(filtered_df['Device'])} ชุด ")
                col1, col2, col3, col4 = st.columns(4)
                st.markdown("---------")
                bins_bar = [0, 20, 40, 60, 80, 90, 95, 100]
                labels_bar = ["0-20%", "21-40%", "41-60%", "61-80%", "81-90%", "91-95%", "96-100%"]
                
                with col1:
                    st.metric(label="📈 Avg. Availability (%)", value=f"{filtered_df['Availability (%)'].mean():.2f} %")
                with col2:
                    st.metric(label="🔢 Avg. จำนวนครั้ง Initializing", value=f"{filtered_df['จำนวนครั้ง Initializing'].mean():.2f}")
                with col3:
                    st.metric(label="🔢 Avg. จำนวนครั้ง Connecting", value=f"{filtered_df['จำนวนครั้ง Connecting'].mean():.2f}")
                with col4:
                    st.metric(label="🔢 Avg. จำนวนครั้ง Telemetry Failure", value=f"{filtered_df['จำนวนครั้ง Telemetry Failure'].mean():.2f}")
                #selected_group = st.multiselect("เลือกช่วง % Availability:", options=labels_bar, default=labels_bar)
                select_all = st.checkbox("📌 เลือกช่วง % Availability ทั้งหมด", value=True)

                if select_all:
                    selected_group = st.multiselect("เลือกช่วง % Availability:", options=labels_bar, default=labels_bar)
                else:
                    selected_group = st.multiselect("เลือกช่วง % Availability:", options=labels_bar)
                # ตรวจสอบว่าผู้ใช้ไม่ได้เลือกอะไรเลย
                if not selected_group:
                    st.warning("⚠️ กรุณาเลือกอย่างน้อยหนึ่งช่วง % Availability")
                    st.stop()
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
                st.markdown("---------")
            
                bins_eva = [0, 80, 90, 100]
                labels_eva = ["0 <= Availability (%) <= 80", "80 < Availability (%) <= 90", "90 < Availability (%) <= 100"]
                df_eva, summary_df, fig1, fig2 = evaluate(filtered_df,bins_eva,labels_eva)
                st.plotly_chart(fig1, use_container_width=True)
                st.dataframe(summary_df)
                #st.write(df_eva.columns.to_list())
                #st.dataframe(df_eva)
                filter_detail_select = st.checkbox("Filter Device ตามเกณฑ์ประเมิณ: ")         
                if filter_detail_select:
                    select_all = st.checkbox("📌 เลือกช่วง % Availability ทั้งหมด", value=True)
                    rangeava_options = df_eva["Availability Range"].unique()
                    if select_all:
                        rangeava_select = st.multiselect("เลือกช่วง % Availability:", options=rangeava_options, default=rangeava_options)
                        df_ava = df_eva.copy()
                    else:
                        rangeava_select = st.multiselect("เลือกช่วง % Availability:", options=rangeava_options)
                        df_ava = df_eva[df_eva["Availability Range"].isin(rangeava_select)]
                        
                    #rangeava_options = ["ทั้งหมด"] + list(df_eva["Availability Range"].unique())
                    #rangeava_select = st.multiselect("เลือกช่วง Availability", rangeava_options, default=["ทั้งหมด"])
                    #if not rangeava_select or "ทั้งหมด" in rangeava_select:
                        #df_ava = df_eva.copy()  # แสดงข้อมูลทั้งหมด
                    #else:
                        #df_ava = df_eva[df_eva["Availability Range"].isin(rangeava_select)]  # กรองเฉพาะที่เลือก
                    #device_list = ["ทั้งหมด"] + list(df_ava["Device"].unique())
                    #selected_devices = st.multiselect("เลือกอุปกรณ์", device_list, default=["ทั้งหมด"])  
                    #if not selected_devices or "ทั้งหมด" in selected_devices:
                    #    df_ava = df_ava.copy()  # แสดงข้อมูลทั้งหมด
                    #else:
                    #    df_ava = df_ava[df_ava["Device"].isin(selected_devices)]  # กรองเฉพาะที่เลือก
                    st.dataframe(df_ava)
                    
                    filter_describe_select = st.checkbox("ดูค่าต่างๆ เชิงสถิติ : ")
                    if filter_describe_select:  
                        st.write(df_ava.describe())
                st.markdown("---------")
            elif func_select == 'ข้อมูลอุปกรณ์ตาม % Availability':
                min_avail, max_avail = st.slider("เลือกช่วง Availability (%)", 0, 100, (70, 90), step=1)
                filtered_df = filtered_df[(filtered_df["Availability (%)"] >= min_avail) & (filtered_df["Availability (%)"] <= max_avail)]
                
                # 🔥 เพิ่มตัวเลือก Filter แบบ multiselect ต่อคอลัมน์
                device_options = filtered_df["Device"].unique().tolist()
                selected_devices = st.multiselect("เลือกอุปกรณ์ (Device):", options=device_options, default=device_options)

                description_options = filtered_df["จำนวนครั้ง Initializing"].unique().tolist()
                selected_descriptions = st.multiselect("เลือก Description:", options=description_options, default=description_options)

                # ✅ เพิ่มตัวกรองช่วงจำนวนครั้ง Initializing
                if "จำนวนครั้ง Initializing" in filtered_df.columns:
                    min_init, max_init = int(filtered_df["จำนวนครั้ง Initializing"].min()), int(filtered_df["จำนวนครั้ง Initializing"].max())
                    selected_init_range = st.slider(
                        "เลือกช่วง จำนวนครั้ง Initializing:",
                        min_value=min_init,
                        max_value=max_init,
                        value=(min_init, max_init),
                        step=1
                    )
                    filtered_df = filtered_df[
                        (filtered_df["จำนวนครั้ง Initializing"] >= selected_init_range[0]) &
                        (filtered_df["จำนวนครั้ง Initializing"] <= selected_init_range[1])
                    ]
        
                # กรองข้อมูลตามที่เลือก
                filtered_df = filtered_df[
                    (filtered_df["Device"].isin(selected_devices)) & 
                    (filtered_df["Description"].isin(selected_descriptions))
                ]
                
                st.info(f"จำนวน Frtu : {len(filtered_df['Device'])} ชุด")
                st.write(filtered_df)
                #filtered_by_group = filtered_df[filtered_df["Availability Group"].isin(selected_group)]
                #devices_counts = filtered_df["Device"].sum()

                #st.dataframe(filtered_df[['Device', 'Availability (%)']].sort_values(by='Availability (%)', ascending=False))
                #st.dataframe(filtered_df.sort_values(by='Availability (%)', ascending=False))
                
                # --- 📈 กราฟ ---
                fig_bar = px.bar(
                    filtered_df,
                    x='Device',
                    y='Availability (%)',
                    color='Availability (%)',
                    title=f"Availability (%) ต่อ Device - {selected_month}",
                    color_continuous_scale='Greens'
                )
                #st.plotly_chart(fig_bar, use_container_width=True)

                # แปลง Period เป็น string
                #df['Month'] = df['Month'].astype(str)
                fig_scatter = px.scatter(
                    filtered_df,
                    x='Device',  # แกน X = เดือน
                    y='Availability (%)',  # แกน Y = Availability
                    color='Device',  # แยกสีตาม Device
                    hover_data=['Device', 'Availability (%)'],  # ข้อมูลเมื่อ hover
                    title='Availability (%) รายเดือนของแต่ละ Device'
                )
                fig_scatter.update_traces(mode='markers+lines')  # แสดงทั้งจุดและเส้นเชื่อม
                fig_scatter.update_layout(xaxis_title='Device', yaxis_title='Availability (%)')
                st.plotly_chart(fig_scatter, use_container_width=True)
                st.markdown("---------")
        else:
            df = load_data_csv(source_csv_sub)
            
if __name__ == "__main__":
    main()


