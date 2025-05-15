import pandas as pd
import streamlit as st
import plotly.express as px
from io import StringIO
from datetime import datetime

st.set_page_config(page_title="Ultra Device Dashboard", layout="wide", page_icon="⚡")

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
            # สร้างสำเนาข้อมูลก่อนกรอง
            df_selection = filtered_df.copy()
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
                #min_avail, max_avail = st.slider("เลือกช่วง Availability (%)", 0, 100, (0, 100), step=1)
                #filtered_df = filtered_df[(filtered_df["Availability (%)"] >= min_avail) & (filtered_df["Availability (%)"] <= max_avail)]
                
                

                st.title("📈 Ultra Dashboard - Dynamic Filtering + Export + Save Preset")

                # -----------------------------------
                # 🔥 เตรียม SessionState
                # -----------------------------------
                if "saved_presets" not in st.session_state:
                    st.session_state.saved_presets = {}

                # สำเนาข้อมูลหลัก
                df_selection = filtered_df.copy()

                # --------------------------
                # 🔥 ฟิลเตอร์ Dynamic
                # --------------------------
                st.sidebar.header("🎛️ ตัวกรองข้อมูล (Filters)")

                filters = {}

                use_inputbox = st.sidebar.checkbox("✅ ใช้การพิมพ์ตัวเลขแทน Slider", value=False)

                for col in df_selection.columns:
                    if pd.api.types.is_numeric_dtype(df_selection[col]):
                        min_val = int(df_selection[col].min())
                        max_val = int(df_selection[col].max())
                        if use_inputbox:
                            min_input = st.sidebar.number_input(f"ใส่ค่าต่ำสุด {col}:", value=min_val, key=f"{col}_min")
                            max_input = st.sidebar.number_input(f"ใส่ค่าสูงสุด {col}:", value=max_val, key=f"{col}_max")
                            filters[col] = (min_input, max_input)
                        else:
                            selected_range = st.sidebar.slider(
                                f"เลือกช่วง {col}:", 
                                min_value=min_val, 
                                max_value=max_val,
                                value=(min_val, max_val),
                                step=1,
                                key=col
                            )
                            filters[col] = selected_range
                    elif pd.api.types.is_object_dtype(df_selection[col]) or pd.api.types.is_categorical_dtype(df_selection[col]):
                        options = df_selection[col].dropna().unique().tolist()
                        selected_options = st.sidebar.multiselect(
                            f"เลือก {col}:", 
                            options=options, 
                            default=options,
                            key=col
                        )
                        filters[col] = selected_options

                # --------------------------
                # 🔥 Apply Filter
                # --------------------------
                for col, condition in filters.items():
                    if isinstance(condition, tuple):
                        df_selection = df_selection[
                            (df_selection[col] >= condition[0]) & (df_selection[col] <= condition[1])
                        ]
                    else:
                        df_selection = df_selection[df_selection[col].isin(condition)]

                st.success(f"🎯 พบ {len(df_selection)} รายการ หลังกรองข้อมูล")

                # --------------------------
                # 💾 Save Filter Preset
                # --------------------------
                preset_name = st.sidebar.text_input("ตั้งชื่อ Preset", "")
                if st.sidebar.button("💾 Save Preset"):
                    if preset_name:
                        st.session_state.saved_presets[preset_name] = filters.copy()
                        st.sidebar.success(f"✅ บันทึก Preset '{preset_name}' เรียบร้อยแล้ว!")
                    else:
                        st.sidebar.warning("⚠️ กรุณาตั้งชื่อก่อนบันทึก Preset")

                # --------------------------
                # 📂 Load Filter Preset
                # --------------------------
                if st.session_state.saved_presets:
                    selected_preset = st.sidebar.selectbox("📂 โหลด Preset ที่มี", options=["-"] + list(st.session_state.saved_presets.keys()))
                    if selected_preset != "-" and st.sidebar.button("🔄 Load Preset"):
                        loaded_filters = st.session_state.saved_presets[selected_preset]
                        st.experimental_rerun()

                # --------------------------
                # 📋 เลือกซ่อน/แสดงคอลัมน์
                # --------------------------
                with st.expander("🧹 จัดการคอลัมน์ที่ต้องการแสดง/ซ่อน"):
                    selected_cols = st.multiselect(
                        "เลือกคอลัมน์ที่ต้องการแสดง:", 
                        options=list(df_selection.columns), 
                        default=list(df_selection.columns)
                    )
                    df_selection = df_selection[selected_cols]

                st.dataframe(df_selection, use_container_width=True)

                # --------------------------
                # 📈 กราฟ
                # --------------------------
                if not df_selection.empty:
                    st.subheader("📊 การแสดงผลกราฟ")

                    # --- เลือก Theme
                    themes = {
                        "Basic": px.colors.qualitative.Plotly,
                        "Pastel": px.colors.qualitative.Pastel,
                        "Bold": px.colors.qualitative.Bold,
                        "Dark": px.colors.qualitative.Dark2,
                    }
                    selected_theme = st.selectbox("🎨 เลือก Theme กราฟ:", list(themes.keys()))

                    y_col = st.selectbox("เลือกคอลัมน์ที่ Plot (Y-axis):", df_selection.select_dtypes(include=['number']).columns)
                    fig = px.bar(
                        df_selection,
                        x="Device",
                        y=y_col,
                        text=y_col,
                        color_discrete_sequence=themes[selected_theme]
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # ดาวน์โหลดกราฟ
                    img_bytes = fig.to_image(format="png")
                    st.download_button(
                        label="📥 ดาวน์โหลดกราฟ (PNG)",
                        data=img_bytes,
                        file_name=f"chart_{datetime.now().strftime('%Y%m%d-%H%M%S')}.png",
                        mime="image/png"
                    )

                else:
                    st.warning("❗ ไม่มีข้อมูลสำหรับสร้างกราฟ โปรดปรับฟิลเตอร์ใหม่")

                # --------------------------
                # 📥 Download Data as Excel (.xlsx)
                # --------------------------
                def to_excel(df):
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                        df.to_excel(writer, index=False, sheet_name="Filtered Data")
                        workbook = writer.book
                        worksheet = writer.sheets["Filtered Data"]
                        for idx, col in enumerate(df.columns):
                            column_len = max(df[col].astype(str).map(len).max(), len(col))
                            worksheet.set_column(idx, idx, column_len + 2)
                    processed_data = output.getvalue()
                    return processed_data

                excel_data = to_excel(df_selection)

                st.download_button(
                    label="📥 ดาวน์โหลดข้อมูลเป็น Excel (.xlsx)",
                    data=excel_data,
                    file_name=f"filtered_devices_{datetime.now().strftime('%Y%m%d-%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                # -----------------------------------
                # 📈📉 Section: Plot ความสัมพันธ์ระหว่าง 2 คอลัมน์
                # -----------------------------------
                st.subheader("🔗 วิเคราะห์ความสัมพันธ์ระหว่างคอลัมน์")

                num_cols = df_selection.select_dtypes(include=['number']).columns.tolist()

                if len(num_cols) >= 2:
                    col1, col2 = st.columns(2)
                    with col1:
                        selected_x = st.selectbox("เลือกแกน X-axis:", options=num_cols, key="x_axis_relation")
                    with col2:
                        selected_y = st.selectbox("เลือกแกน Y-axis:", options=num_cols, key="y_axis_relation")

                    plot_type = st.radio(
                        "เลือกประเภทกราฟ:", 
                        options=["Scatter Plot", "Line Plot", "Bar Plot"], 
                        horizontal=True,
                        key="relation_plot_type"
                    )

                    if selected_x and selected_y:
                        if plot_type == "Scatter Plot":
                            fig_relation = px.scatter(
                                df_selection,
                                x=selected_x,
                                y=selected_y,
                                color_discrete_sequence=["#636EFA"],
                                trendline="ols", # เพิ่มเส้นเทรนด์ให้ด้วย!
                                title=f"Scatter Plot ระหว่าง {selected_x} และ {selected_y}"
                            )
                        elif plot_type == "Line Plot":
                            fig_relation = px.line(
                                df_selection,
                                x=selected_x,
                                y=selected_y,
                                markers=True,
                                title=f"Line Plot ระหว่าง {selected_x} และ {selected_y}"
                            )
                        elif plot_type == "Bar Plot":
                            fig_relation = px.bar(
                                df_selection,
                                x=selected_x,
                                y=selected_y,
                                title=f"Bar Plot ระหว่าง {selected_x} และ {selected_y}"
                            )

                        st.plotly_chart(fig_relation, use_container_width=True)
                else:
                    st.warning("⚠️ ต้องมีอย่างน้อย 2 คอลัมน์ตัวเลขเพื่อสร้างกราฟความสัมพันธ์")

        else:
            df = load_data_csv(source_csv_sub)
            
if __name__ == "__main__":
    main()