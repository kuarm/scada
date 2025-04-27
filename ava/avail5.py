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
    fig1 = px.bar(
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
        summary_df,
        names="ผลการประเมิน",
        values="จำนวน Device",
        title="ประเมิน",
        hole=0.4
    )
    fig2.update_traces(textinfo='percent+label')
    #st.plotly_chart(fig2, use_container_width=True)
    return df, summary_df, fig1, fig2











option_menu = ['สถานะอุปกรณ์','% ความพร้อมใช้งาน', '% การสั่งการ', 'ข้อมูลการสั่งการ']
option_func = ['ประเมินผล % Availability', 'ข้อมูลอุปกรณ์ตาม % Availability', 'เลือกช่วง % Availability']
option_submenu = ['ระบบจำหน่ายสายส่ง','สถานีไฟฟ้า']

def main():
    menu_select = st.sidebar.radio(label="Menu: ", options = option_menu)
    
    if menu_select == '% ความพร้อมใช้งาน':
        st.header("📊 %ความพร้อมใช้งานของอุปกรณ์")
        
        submenu_select = st.sidebar.radio(label="ระบบ: ", options = option_submenu)
        
        if submenu_select == 'ระบบจำหน่ายสายส่ง':
            df = load_data_csv(source_csv_feeder)
            # --- 🎯 Filter เดือน ---
            months = sorted(df['Month'].dropna().unique().astype(str))
            selected_month = st.selectbox("เลือกเดือน", months)
            # กรองข้อมูลตามเดือน
            filtered_df = df[df['Month'].astype(str) == selected_month]
            filtered_df = filtered_df.drop(columns=['Availability Period','Source File'],axis=0)
            
            func_select = st.sidebar.radio(label="function: ", options = option_func)
            
            if func_select == 'ประเมินผล % Availability':
                bins_eva = [0, 80, 90, 100]
                labels_eva = ["0 <= Availability (%) <= 80", "80 < Availability (%) <= 90", "90 < Availability (%) <= 100"]
                df_eva, summary_df, fig1, fig2 = evaluate(filtered_df,bins_eva,labels_eva)
                st.plotly_chart(fig1, use_container_width=True)
            elif func_select == 'ข้อมูลอุปกรณ์ตาม % Availability':
                min_avail, max_avail = st.slider("เลือกช่วง Availability (%)", 0, 100, (70, 90), step=1)
                filtered_df = filtered_df[(filtered_df["Availability (%)"] >= min_avail) & (filtered_df["Availability (%)"] <= max_avail)]
                st.dataframe(filtered_df)
                #filtered_by_group = filtered_df[filtered_df["Availability Group"].isin(selected_group)]
                devices_counts = filtered_df["Device"].sum()
                #devices_counts = filtered_df["Device"].sum()
                st.write(devices_counts)


            

                # --- 📊 แสดงผล Availability (%) เฉพาะเดือนที่เลือก ---
                st.subheader(f"Availability (%) ในเดือน {selected_month}")
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
                #st.plotly_chart(fig, use_container_width=True)

                # แปลง Period เป็น string
                df['Month'] = df['Month'].astype(str)
                fig_scatter = px.scatter(
                    filtered_df,
                    x='Device',  # แกน X = เดือน
                    y='Availability (%)',  # แกน Y = Availability
                    color='Device',  # แยกสีตาม Device
                    hover_data=['Device', 'Availability (%)'],  # ข้อมูลเมื่อ hover
                    title='Availability (%) รายเดือนของแต่ละ Device'
                )

                fig_scatter.update_traces(mode='markers+lines')  # แสดงทั้งจุดและเส้นเชื่อม
                fig_scatter.update_layout(xaxis_title='เดือน', yaxis_title='Availability (%)')

                st.plotly_chart(fig_scatter, use_container_width=True)

        else:
            df = load_data_csv(source_csv_sub)
            
if __name__ == "__main__":
    main()


