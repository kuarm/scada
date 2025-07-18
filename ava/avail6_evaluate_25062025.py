import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from io import BytesIO

# --- ตัวเลือกเดือน (Filter) ---
month_names_th = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
                'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']

def plot_avg(df,flag):
    # --- เตรียมข้อมูล ---
    df_avg = df.copy()

    # แปลง "Availability (%)" เป็น float
    df_avg["Availability (%)"] = df_avg["Availability (%)"].replace({",": "", "%": ""}, regex=True)
    df_avg["Availability (%)"] = pd.to_numeric(df_avg["Availability (%)"], errors="coerce")

    # แปลง "Availability Period" เป็น datetime แล้วสร้าง "Month"
    df_avg["Month"] = pd.to_datetime(df_avg["Availability Period"], format="%Y-%m", errors="coerce")
    df_avg["Month_str"] = df_avg["Month"].dt.to_period("M").astype(str)

    # ลบค่าที่ไม่สมบูรณ์
    df_avg = df_avg.dropna(subset=["Availability (%)", "Device", "Month_str"])


    df_avg["ปี"] = pd.to_datetime(df_avg["Month_str"], format="%Y-%m", errors="coerce").dt.year
    #df_avg["เดือน"] = pd.to_datetime(df_avg["Month_str"], format="%Y-%m", errors="coerce").dt.month
    
    
    all_months = sorted(df_avg["Month_str"].unique())
    selected_months = st.multiselect("📆 เลือกเดือนที่ต้องการวิเคราะห์", all_months, default=all_months)

    # กรองข้อมูลตามเดือนที่เลือก
    df_avg = df_avg[df_avg["Month_str"].isin(selected_months)]
    years = sorted(df_avg["ปี"].unique())
    year_str = ", ".join(str(y) for y in years)
    
    # --- ตัวเลือก Device (Filter) ---
    all_devices = sorted(df_avg["Device"].unique())
    selected_devices = st.multiselect("🖥️ เลือก Device ที่ต้องการวิเคราะห์", all_devices, default=all_devices)

    # กรองข้อมูลตาม Device ที่เลือก
    df_avg = df_avg[df_avg["Device"].isin(selected_devices)]
    
    # --- 🔹 กราฟที่ 1: ค่าเฉลี่ยรวมทุก Device รายเดือน ---
    monthly_avg = df_avg.groupby("Month_str")["Availability (%)"].mean().reset_index()
    monthly_avg["Availability (%)"] = monthly_avg["Availability (%)"].round(2)
    
    ###✅✅✅ Avg. ✅✅✅
    # แปลง Month_str เป็น datetime ก่อน
    monthly_avg["Month_dt"] = pd.to_datetime(monthly_avg["Month_str"], format="%Y-%m", errors="coerce")
    monthly_avg["เดือน"] = monthly_avg["Month_dt"].dt.month.apply(lambda x: month_names_th[x - 1])
    fig_total_avg = px.line(
        monthly_avg,
        x="เดือน",
        y="Availability (%)",
        markers=True,
        title=f"📈 ค่า Availability (%) เฉลี่ยรายเดือนในปี {year_str} ของ {flag} ",
        text="Availability (%)"
        )
    fig_total_avg.update_traces(
        texttemplate="%{text:.2f}%",  # format ตัวเลข
        textposition="top center"
        )
    fig_total_avg.update_layout(
        xaxis=dict(categoryorder="array", categoryarray=month_names_th),
        xaxis_title="เดือน",
        yaxis_title="Availability (%) เฉลี่ย",
        yaxis=dict(range=[0, 105]),
        hovermode="x unified"
        )
    st.plotly_chart(fig_total_avg, use_container_width=True)

    # --- 🔹 กราฟที่ 2: Availability (%) รายเดือนแยกตาม Device ---
    device_monthly = df_avg.groupby(["Month_str", "Device"])["Availability (%)"].mean().reset_index()
    device_monthly["Availability (%)"] = device_monthly["Availability (%)"].round(2)

    ###✅✅✅ LINE ✅✅✅
    fig_by_device = px.line(
        device_monthly,
        x="Month_str",
        y="Availability (%)",
        color="Device",
        markers=True,
        title=f"📊 Availability (%) รายเดือนแยกตาม {flag}"
        )
    fig_by_device.update_layout(
        xaxis_title="เดือน",
        yaxis_title="Availability (%)",
        yaxis=dict(range=[0, 105]),
        hovermode="x unified"
        )
    #st.plotly_chart(fig_by_device, use_container_width=True)

    ###✅✅✅ Scatter ✅✅✅
    #df_avg.rename(columns={"Month_str": "เดือน"}, inplace=True)
    df_avg["Month_dt"] = pd.to_datetime(df_avg["Month_str"], format="%Y-%m", errors="coerce")
    df_avg["เดือน"] = df_avg["Month_dt"].dt.month.apply(lambda x: month_names_th[x - 1])
    fig_scatter = px.scatter(
        df_avg,
        x="Device",
        y="Availability (%)",
        color="เดือน",  # เพื่อแยกสีตามเดือน
        title = f"📍 ค่า Availability (%) รายเดือนในปี {year_str} ของ {flag}",
        hover_data=["เดือน"],  # แสดงเดือนใน hover
        )

    fig_scatter.update_layout(
        xaxis_title=flag,
        yaxis_title="Availability (%)",
        yaxis=dict(range=[-5, 105]),
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
    df["Availability (%)"] = pd.to_numeric(df["Availability (%)"], errors="coerce")
    df["Availability (%)"] = df["Availability (%)"] * 100
    #df["Availability (%)"] = df["Availability (%)"].map(lambda x: f"{x:.2f} %")
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
    pivot_df["Avg.Availability (%)"] = pivot_df.mean(axis=1)

    # Reset index เพื่อให้ Device เป็นคอลัมน์
    pivot_df = pivot_df.reset_index()

    pivot_df.rename(columns={"Device": flag}, inplace=True)

    # จัดรูปแบบตัวเลข: แสดงเป็นทศนิยม 2 ตำแหน่ง และใส่ % เฉพาะคอลัมน์ที่เป็นเดือน + ค่าเฉลี่ย
    value_cols = month_names + ["Avg.Availability (%)"]
    pivot_df[value_cols] = pivot_df[value_cols].applymap(
        lambda x: f"{x:.2f} %" if pd.notnull(x) else "-"
    )
    ### ✅✅✅
    st.info(f"📊 สรุป Availability (%) รายเดือนของ {flag}")
    st.dataframe(pivot_df)
    
    # --- แปลงเป็น Excel สำหรับดาวน์โหลด ---
    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Availability (%)_month")
        processed_data = output.getvalue()
        return processed_data

    excel_file = to_excel(pivot_df)
    # --- ปุ่มดาวน์โหลดใน Streamlit ---
    st.download_button(
        label="📥 ดาวน์โหลด Availability (%)_month",
        data=excel_file,
        file_name="Availability (%)_month.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    return pivot_df

def evaluate(df,bins,labels,flag):
    #เพิ่ม Month
    df["Month"] = pd.to_datetime(df["Availability Period"], format="%Y-%m", errors="coerce")
    df["Month_str"] = df["Month"].dt.strftime("%Y-%m")
    df["Availability (%)"] = df["Availability (%)"] * 100
    df["ปี"] = pd.to_datetime(df["Month_str"], format="%Y-%m", errors="coerce").dt.year
    years = sorted(df["ปี"].unique())
    year_str = ", ".join(str(y) for y in years)
    # หาค่าเดือนแรก และเดือนสุดท้าย
    min_month = df["Month"].min()
    max_month = df["Month"].max()
    # แสดงชื่อเดือนแบบไทย
    thai_start = f"{month_names_th[min_month.month - 1]} {min_month.year}"
    thai_end = f"{month_names_th[max_month.month - 1]} {max_month.year}"

    thai_start_month = month_names_th[min_month.month - 1]
    thai_end_month = month_names_th[max_month.month - 1]

    # แสดงผล
    st.success(f"📆 เดือนแรก: {thai_start} | เดือนสุดท้าย: {thai_end}")

    all_month_summaries = []  # 🔹 รวมไว้ทีหลัง
    all_device_summaries = []

    # กำหนดเงื่อนไขสำหรับผลการประเมิน
    def evaluate_result(row):
        if row == "90 < Availability (%) <= 100": #label == "90 < Availability (%) <= 100": รับ String
            return "✅ ดีเยี่ยม"
        elif row == "80 < Availability (%) <= 90":
            return "⚠️ ควรปรับปรุง"
        else:
            return "❌ ต่ำกว่าเกณฑ์"
        
    # 🔹 ฟังก์ชันประเมินผลในแต่ละกลุ่ม (PEA หรือ Producer)
    def evaluate_group(df_group, owner_label):
        # เพิ่มคอลัมน์ "เกณฑ์การประเมิน"
        df_group["เกณฑ์การประเมิน"] = pd.cut(df_group["Availability (%)"], bins=bins, labels=labels, right=True)
        #df_pea = df[df["ผู้ดูแล"] == "PEA ดูแล"] #df_Producer = df[df["ผู้ดูแล"] == "Producer ดูแล"]

        # เพิ่มคอลัมน์ "ผลการประเมิน"
        df_group["ผลการประเมิน"] = df_group["เกณฑ์การประเมิน"].apply(evaluate_result)

        # ✅ รายเดือนเฉลี่ย
        month_summary = df_group.groupby("Month_str")["Availability (%)"].mean().reset_index()
        month_summary["เกณฑ์การประเมิน"] = pd.cut(month_summary["Availability (%)"], bins=bins, labels=labels)
        month_summary["ผลการประเมิน"] = month_summary["เกณฑ์การประเมิน"].apply(evaluate_result)
        month_summary["จำนวน Device"] = df_group.groupby("Month_str")["Device"].nunique().values
        month_summary["ผู้ดูแล"] = owner_label  # 🔹 เพิ่มคอลัมน์ระบุเจ้าของ
        #month_summary["ผลการประเมิน"] = month_summary["เกณฑ์การประเมิน"].apply(
        #    lambda x: "✅" if x == "90 < Availability (%) <= 100" else ("⚠️" if x == "80 < Availability (%) <= 90" else "❌")
        #)

        # ✅ รายอุปกรณ์เฉลี่ย
        # คำนวณค่าเฉลี่ยของ Availability (%) แยกตาม Device โดยเฉลี่ยจากหลายเดือน
        device_avg = df_group.groupby("Device")["Availability (%)"].mean().reset_index()
        #device_avg.columns = ["Device", "Avg. Availability (%)"]
        device_avg["เกณฑ์การประเมิน"] = pd.cut(device_avg["Availability (%)"], bins=bins, labels=labels)
        device_avg["ผลการประเมิน"] = device_avg["เกณฑ์การประเมิน"].apply(evaluate_result)
        device_avg["ผู้ดูแล"] = owner_label  # 🔹 เพิ่มคอลัมน์ระบุเจ้าของ

        month_summary_re = month_summary.rename(columns={
                "Month_str": "ปี-เดือน",
                "จำนวน Device": "จำนวน",
                "Availability (%)": "Avg.Availability (%)"
            })
        
        device_avg_re = device_avg.rename(columns={
                "Availability (%)": "Avg.Availability (%)",
                "Device": flag
            })
        return month_summary_re, device_avg_re
         
    # 🔸 เรียกประเมินแต่ละกลุ่ม
    for owner_label in ["PEA ดูแล", "Producer ดูแล"]:
        df_group = df[df["ผู้ดูแล"] == owner_label].copy()
        if not df_group.empty:
            summary, summary_device = evaluate_group(df_group, owner_label)
            all_month_summaries.append(summary)
            all_device_summaries.append(summary_device)

    # ✅ รวมผลลัพธ์ทุกกลุ่ม
    final_month_summary = pd.concat(all_month_summaries, ignore_index=True)
    final_device_summary = pd.concat(all_device_summaries, ignore_index=True)
    # แปลงปี-เดือนกลับเป็น datetime เพื่อง่ายต่อการ sort
    final_month_summary["ปี-เดือน-dt"] = pd.to_datetime(final_month_summary["ปี-เดือน"], format="%Y-%m", errors="coerce")
    # เรียงตามเวลา
    final_month_summary = final_month_summary.sort_values(by="ปี-เดือน-dt")
    # เพิ่มคอลัมน์ลำดับ
    final_month_summary.insert(0, "ลำดับ", range(1, len(final_month_summary) + 1))
    # ลบคอลัมน์ช่วยถ้าไม่ต้องการแสดง
    final_month_summary = final_month_summary.drop(columns=["ปี-เดือน-dt"])
    # ✅ แปลง "Avg Availability (%)" ให้มี 3 ตำแหน่ง และเพิ่ม "%"
    final_month_summary["Avg.Availability (%)"] = final_month_summary["Avg.Availability (%)"].map(lambda x: f"{x:.3f} %")
    final_device_summary["Avg.Availability (%)"] = final_device_summary["Avg.Availability (%)"].map(lambda x: f"{x:.3f} %")
    ### ✅ แสดงรวมในตารางเดียว
    st.info(f"📊 ประเมินผลค่า Availability (%) รวมเฉลี่ย {thai_start_month} - {thai_end_month} {max_month.year} ของ{flag} (แยกตามผู้ดูแล)")
    
    # ✅ แสดงผลโดยซ่อน index ด้านซ้าย
    st.dataframe(final_month_summary, use_container_width=True, hide_index=True)
    
    #fig_bar1 = px.bar(final_month_summary, x="ปี-เดือน", y="Avg.Availability (%)", color="ผู้ดูแล", barmode="group")
    #st.plotly_chart(fig_bar1, use_container_width=True)
    
    
    #สรุปจำนวนเดือนทั้งหมด (ไม่แสดงในตาราง device_avg)
    total_months = df_group["Month"].nunique()

    
    #device_avg1 = df.groupby("Device")["Availability (%)"].mean().reset_index()
    #device_avg1["Availability (%)"] = device_avg1["Availability (%)"].round(2)
    #device_avg1 = device_avg1.sort_values("Availability (%)", ascending=False)
    #t.dataframe(device_avg1)

    ### ✅✅✅
    st.info(f"📊 ประเมินผลค่า Availability (%) แต่ละ {flag} เฉลี่ย {total_months} เดือน ({thai_start_month} - {thai_end_month} {max_month.year})")
    st.dataframe(final_device_summary)
    
    # --- แปลงเป็น Excel สำหรับดาวน์โหลด ---
    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="ประเมินผลค่า Ava")
        processed_data = output.getvalue()
        return processed_data

    excel_file1 = to_excel(final_month_summary)
    excel_file2 = to_excel(final_device_summary)

    # --- ปุ่มดาวน์โหลดใน Streamlit ---
    st.download_button(
        label="📥 ดาวน์โหลด evaluate_month_avg",
        data=excel_file1,
        file_name="evaluate_month_avg.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.download_button(
        label="📥 ดาวน์โหลด evaluate_device_avg",
        data=excel_file2,
        file_name="evaluate_device_avg.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    #----------------------------------------------------#
    # สรุปรวมทั้งหมด
    overall_avg = df["Availability (%)"].mean()
    overall_label = pd.cut([overall_avg], bins=bins, labels=labels)[0]
    total_row = pd.DataFrame({
        "Month_str": ["รวมทั้งหมด"],
        "Availability (%)": [overall_avg],
        "เกณฑ์การประเมิน": [pd.cut([overall_avg], bins=bins, labels=labels)[0]],
        "ผลการประเมิน": [evaluate_result(overall_label)],
        "จำนวน Device": [df["Device"].nunique()]
    })
    #summary_df = pd.concat([final_month_summary, total_row], ignore_index=True)
    #summary_df["Device+Percent"] = summary_df.apply(lambda row: f"{int(row['จำนวน Device']):,}", axis=1)
    
    # 🔹 ประเมินผลแยกตามผู้ดูแล
    for owner in final_month_summary["ผู้ดูแล"].unique():
        df_owner = final_month_summary[final_month_summary["ผู้ดูแล"] == owner].copy()

        # แปลง % กลับเป็นตัวเลข
        monthly_avg = df_owner["Avg.Availability (%)"].str.replace("%", "").astype(float)

        # คำนวณค่าเฉลี่ยของค่าเฉลี่ยรายเดือน
        avg_of_monthly_avg = monthly_avg.mean()

        # ประเมินผล
        eval_label = pd.cut([avg_of_monthly_avg], bins=bins, labels=labels)[0]
        eval_symbol = evaluate_result(eval_label)

        # แสดงผล
        st.success(f"🎯 ค่าเฉลี่ยของค่าเฉลี่ยรายเดือนสำหรับ {owner}: **{avg_of_monthly_avg:.3f}%** {eval_symbol}")

    return final_month_summary, final_device_summary

    
    
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
        """

def range_ava(df,bins,labels,flag):
    filtered_df["Availability Group"] = pd.cut(filtered_df["Availability (%)"], bins=bins, labels=labels, right=True)
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

def ranking(df):
    # ตัวอย่าง: Ranking แยกตาม "ผู้ดูแล"
    df_group = df[df["ผู้ดูแล"] == "PEA ดูแล"]  # หรือ "Producer ดูแล"

    device_avg = df_group.groupby("Device")["Availability (%)"].mean().reset_index()
    device_avg.columns = ["Device", "Avg Availability (%)"]
    device_avg["Rank"] = device_avg["Avg Availability (%)"].rank(ascending=False, method="min").astype(int)
    device_avg = device_avg.sort_values(by="Rank").reset_index(drop=True)

    st.info("📈 จัดอันดับ Availability (%) ของ PEA ดูแล")
    st.dataframe(device_avg)

    # คำนวณค่าเฉลี่ยของ Availability (%) แยกตาม Device
    device_avg = df.groupby("Device")["Availability (%)"].mean().reset_index()
    device_avg.columns = ["Device", "Avg Availability (%)"]

    # จัดอันดับ (อันดับ 1 คือค่ามากสุด)
    device_avg["Rank"] = device_avg["Avg Availability (%)"].rank(ascending=False, method="min").astype(int)

    # เรียงลำดับใหม่เพื่อแสดงจากอันดับ 1 ลงมา
    device_avg = device_avg.sort_values(by="Rank").reset_index(drop=True)

    device_avg["Avg Availability (%)"] = device_avg["Avg Availability (%)"] * 100

    # แสดงตาราง Ranking
    st.info("📈 ตารางจัดอันดับ Availability (%) เฉลี่ย รายอุปกรณ์")
    st.dataframe(device_avg)

def rank_availability(df):
    st.subheader("📊 การจัดอันดับ Availability (%) เฉลี่ย (แยกตามผู้ดูแล)")

    # ✅ เตรียมกลุ่ม
    for owner in ["PEA ดูแล", "Producer ดูแล"]:
        df_group = df[df["ผู้ดูแล"] == owner].copy()

        if df_group.empty:
            st.warning(f"⚠️ ไม่พบข้อมูลของกลุ่ม '{owner}'")
            continue

        # ✅ คำนวณ Avg. Availability (%) ต่อ Device
        device_avg = df_group.groupby("Device")["Availability (%)"].mean().reset_index()
        device_avg.columns = ["Device", "Avg Availability (%)"]

        # ✅ จัดอันดับ
        device_avg["Rank"] = device_avg["Avg Availability (%)"].rank(method="min", ascending=False).astype(int)

        # ✅ เรียงตามอันดับ
        device_avg = device_avg.sort_values(by="Rank").reset_index(drop=True)

        # ✅ แสดงตาราง
        st.markdown(f"### 🏆 อันดับ Availability (%) เฉลี่ย ของกลุ่ม {owner}")
        st.dataframe(device_avg)

def rank_and_plot_top10(df):
    st.subheader("🏆 อันดับ Top 10 Availability (%) เฉลี่ย แยกตามผู้ดูแล")

    for owner in ["PEA ดูแล", "Producer ดูแล"]:
        df_group = df[df["ผู้ดูแล"] == owner].copy()

        if df_group.empty:
            st.warning(f"⚠️ ไม่พบข้อมูลของกลุ่ม '{owner}'")
            continue

        # ✅ คำนวณค่าเฉลี่ย
        device_avg = df_group.groupby("Device")["Availability (%)"].mean().reset_index()
        device_avg.columns = ["Device", "Avg Availability (%)"]

        # ✅ จัดอันดับ
        device_avg["Rank"] = device_avg["Avg Availability (%)"].rank(method="min", ascending=False).astype(int)

        # ✅ Top 10
        top10 = device_avg.sort_values(by="Rank").head(10)

        # ✅ วาดกราฟ Plotly
        fig = px.bar(
            top10.sort_values(by="Avg Availability (%)"),  # เรียงจากล่างขึ้นบน
            x="Avg Availability (%)",
            y="Device",
            orientation="h",
            text="Avg Availability (%)",
            title=f"📊 Top 10 Availability (%) เฉลี่ย ({owner})",
            color="Avg Availability (%)",
            color_continuous_scale="Greens" if "PEA" in owner else "Blues"
        )

        fig.update_layout(
            xaxis_title="Availability (%)",
            yaxis_title="Device",
            yaxis=dict(autorange="reversed"),  # ให้ Rank 1 อยู่บนสุด
            height=500,
            margin=dict(t=50, b=50)
        )

        fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

def rank_plot_top10_combined(df):
    st.subheader("🏆 อันดับ Top 10 Availability (%) เฉลี่ย (รวมทุกผู้ดูแล)")

    # ✅ คำนวณค่าเฉลี่ยรายอุปกรณ์
    device_avg = df.groupby(["Device", "ผู้ดูแล"])["Availability (%)"].mean().reset_index()
    device_avg.columns = ["Device", "ผู้ดูแล", "Avg Availability (%)"]

    # ✅ จัดอันดับรวม
    device_avg["Rank"] = device_avg["Avg Availability (%)"].rank(method="min", ascending=False).astype(int)

    # ✅ เลือก Top 10
    top10_combined = device_avg.sort_values(by="Rank").head(10)

    # ✅ วาดกราฟ
    fig = px.bar(
        top10_combined.sort_values(by="Avg Availability (%)"),
        x="Avg Availability (%)",
        y="Device",
        color="ผู้ดูแล",
        orientation="h",
        text="Avg Availability (%)",
        title="📊 Top 10 Availability (%) เฉลี่ย (รวมทุกผู้ดูแล)",
        color_discrete_map={
            "PEA ดูแล": "#2ECC71",      # เขียว
            "Producer ดูแล": "#3498DB"  # น้ำเงิน
        }
    )

    fig.update_layout(
        xaxis_title="Availability (%)",
        yaxis_title="Device",
        yaxis=dict(autorange="reversed"),
        height=500,
        margin=dict(t=50, b=50)
    )

    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")

    st.plotly_chart(fig, use_container_width=True)

def bar_compare_caretakers(df):
    st.subheader("📊 เปรียบเทียบ Availability (%) แยกตามผู้ดูแล")

    # ✅ คำนวณค่าเฉลี่ยรายอุปกรณ์ + ผู้ดูแล
    device_avg = df.groupby(["Device", "ผู้ดูแล"])["Availability (%)"].mean().reset_index()
    device_avg.columns = ["Device", "ผู้ดูแล", "Avg Availability (%)"]

    # ✅ วาดกราฟ Bar เปรียบเทียบ
    fig = px.bar(
        device_avg,
        x="Device",
        y="Avg Availability (%)",
        color="ผู้ดูแล",
        barmode="group",  # แสดงเป็นคู่แท่ง
        text="Avg Availability (%)",
        title="📊 เปรียบเทียบ Availability (%) แยกตามผู้ดูแล (Grouped Bar)",
        color_discrete_map={
            "PEA ดูแล": "#2ECC71",
            "Producer ดูแล": "#3498DB"
        }
    )

    fig.update_layout(
        xaxis_title="Device",
        yaxis_title="Availability (%)",
        xaxis_tickangle=-45,
        height=600,
        margin=dict(t=60, b=80)
    )

    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")

    st.plotly_chart(fig, use_container_width=True)

def bar_stacked_top10(df):
    st.subheader("📊 Top 10 Availability (%) เฉลี่ยสูงสุด (Stacked Bar เปรียบเทียบผู้ดูแล)")
    
    # ✅ คำนวณค่าเฉลี่ย Availability (%) ต่ออุปกรณ์ + ผู้ดูแล
    device_avg = df.groupby(["Device", "ผู้ดูแล"])["Availability (%)"].mean().reset_index()
    device_avg.columns = ["Device", "ผู้ดูแล", "Avg Availability (%)"]

    # ✅ รวมเป็นค่าเฉลี่ยรวม per Device (เพื่อจัดอันดับ Top 10)
    top_devices = device_avg.groupby("Device")["Avg Availability (%)"].mean().nlargest(10).index

    # ✅ กรองเฉพาะ Top 10
    df_top10 = device_avg[device_avg["Device"].isin(top_devices)]
    df_top10["Avg Availability (%)"] = df_top10["Avg Availability (%)"] * 100
    # ✅ วาดกราฟ Stacked Bar
    fig = px.bar(
        df_top10,
        x="Device",
        y="Avg Availability (%)",
        color="ผู้ดูแล",
        barmode="stack",
        text="Avg Availability (%)",
        title="📊 Top 10 Availability (%) สูงสุด แยกตามผู้ดูแล (Stacked Bar)",
        color_discrete_map={
            "PEA ดูแล": "#2ECC71",
            "Producer ดูแล": "#3498DB"
        }
    )

    fig.update_layout(
        xaxis_title="Device",
        yaxis_title="Availability (%)",
        xaxis_tickangle=-45,
        height=600,
        margin=dict(t=60, b=80)
    )

    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")

    st.plotly_chart(fig, use_container_width=True)

def bar_grouped_top10(df):
    st.subheader("📊 Top 10 Availability (%) เฉลี่ยสูงสุด (Grouped Bar เปรียบเทียบผู้ดูแล)")

    # ✅ 1. คำนวณค่าเฉลี่ย Availability (%) แยกตาม Device + ผู้ดูแล
    device_avg = df.groupby(["Device", "ผู้ดูแล"])["Availability (%)"].mean().reset_index()
    device_avg.columns = ["Device", "ผู้ดูแล", "Avg Availability (%)"]

    # ✅ 2. หา Top 10 Device ที่มีค่าเฉลี่ยรวมสูงสุด
    top_devices = device_avg.groupby("Device")["Avg Availability (%)"].mean().nlargest(10).index

    # ✅ 3. กรองเฉพาะ Device เหล่านั้น
    df_top10 = device_avg[device_avg["Device"].isin(top_devices)]

    # ✅ 4. วาด Grouped Bar
    fig = px.bar(
        df_top10,
        x="Device",
        y="Avg Availability (%)",
        color="ผู้ดูแล",
        barmode="group",
        text="Avg Availability (%)",
        title="📊 Top 10 Availability (%) สูงสุด แยกตามผู้ดูแล (Grouped Bar)",
        color_discrete_map={
            "PEA ดูแล": "#2ECC71",
            "Producer ดูแล": "#3498DB"
        }
    )

    fig.update_layout(
        xaxis_title="Device",
        yaxis_title="Availability (%)",
        xaxis_tickangle=-45,
        height=600,
        margin=dict(t=60, b=80)
    )

    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")

    st.plotly_chart(fig, use_container_width=True)

def show_top10_table(df):
    st.subheader("📋 ตารางอันดับ Availability (%) เฉลี่ยสูงสุดและต่ำสุด")

    # ✅ คำนวณค่าเฉลี่ย Availability (%) แยกตาม Device
    device_avg = df.groupby(["Device", "ผู้ดูแล"])["Availability (%)"].mean().reset_index()
    device_avg.columns = ["Device", "ผู้ดูแล", "Avg Availability (%)"]

    # ✅ จัดอันดับ
    device_avg_sorted = device_avg.sort_values(by="Avg Availability (%)", ascending=False).reset_index(drop=True)
    device_avg_sorted["อันดับ"] = device_avg_sorted.index + 1

    # ✅ แสดง Top 10 สูงสุด
    st.markdown("### 🟢 Top 10 อันดับสูงสุด")
    st.dataframe(device_avg_sorted.head(10).style.format({"Avg Availability (%)": "{:.2f}"}), use_container_width=True)

    # ✅ แสดง Top 10 ต่ำสุด
    st.markdown("### 🔴 Top 10 อันดับต่ำสุด")
    st.dataframe(device_avg_sorted.tail(10).sort_values("Avg Availability (%)").style.format({"Avg Availability (%)": "{:.2f}"}), use_container_width=True)

def show_top10_combined_table(df):
    st.subheader("📋 ตารางรวมอันดับ Availability (%) เฉลี่ยสูงสุดและต่ำสุด")

    # ✅ คำนวณค่าเฉลี่ย Availability (%) แยกตาม Device
    device_avg = df.groupby(["Device", "ผู้ดูแล"])["Availability (%)"].mean().reset_index()
    device_avg.columns = ["Device", "ผู้ดูแล", "Avg Availability (%)"]

    # ✅ จัดอันดับ
    device_avg_sorted = device_avg.sort_values(by="Avg Availability (%)", ascending=False).reset_index(drop=True)
    device_avg_sorted["อันดับ (รวมทั้งหมด)"] = device_avg_sorted.index + 1

    # ✅ แยก Top 10 สูงสุด
    top10 = device_avg_sorted.head(10).copy()
    top10["ประเภท"] = "🔼 Top 10 สูงสุด"

    # ✅ แยก Top 10 ต่ำสุด
    bottom10 = device_avg_sorted.tail(10).copy()
    bottom10["ประเภท"] = "🔽 Bottom 10 ต่ำสุด"

    # ✅ รวมตาราง
    combined_df = pd.concat([top10, bottom10], ignore_index=True)

    # ✅ เรียงลำดับใหม่โดยเอา Top 10 อยู่ด้านบน
    combined_df = combined_df.sort_values(by=["ประเภท", "Avg Availability (%)"], ascending=[True, False])

    # ✅ แสดงตาราง
    st.dataframe(combined_df[["อันดับ (รวมทั้งหมด)", "Device", "ผู้ดูแล", "Avg Availability (%)", "ประเภท"]].style.format({
        "Avg Availability (%)": "{:.2f}"
    }), use_container_width=True)

def show_top10_combined_table_(df):
    st.subheader("📋 ตารางรวมอันดับ Availability (%) เฉลี่ยสูงสุดและต่ำสุด")

    # ✅ คำนวณค่าเฉลี่ย Availability (%) แยกตาม Device
    device_avg = df.groupby(["Device", "ผู้ดูแล"])["Availability (%)"].mean().reset_index()
    device_avg.columns = ["Device", "ผู้ดูแล", "Avg Availability (%)"]

    # ✅ แยก Device ที่ Avg = 0 ออก
    excluded_zero_df = device_avg[device_avg["Avg Availability (%)"] == 0]
    device_avg = device_avg[device_avg["Avg Availability (%)"] > 0]

    device_avg["Avg Availability (%)"] = device_avg["Avg Availability (%)"] * 100

    # ✅ จัดอันดับ
    device_avg_sorted = device_avg.sort_values(by="Avg Availability (%)", ascending=False).reset_index(drop=True)
    device_avg_sorted["อันดับ (รวมทั้งหมด)"] = device_avg_sorted.index + 1

    # ✅ แยก Top 10 สูงสุด
    top10 = device_avg_sorted.head(10).copy()
    top10["ประเภท"] = "🔼 Top 10 สูงสุด"

    # ✅ แยก Bottom 10 ต่ำสุด
    bottom10 = device_avg_sorted.tail(10).copy()
    bottom10["ประเภท"] = "🔽 Bottom 10 ต่ำสุด"

    # ✅ รวมตาราง
    combined_df = pd.concat([top10, bottom10], ignore_index=True)
    combined_df = combined_df.sort_values(by=["ประเภท", "Avg Availability (%)"], ascending=[True, False])

    # ✅ แสดงตาราง
    st.dataframe(
        combined_df[["อันดับ (รวมทั้งหมด)", "Device", "ผู้ดูแล", "Avg Availability (%)", "ประเภท"]]
        .style.format({"Avg Availability (%)": "{:.10f}"}),
        use_container_width=True
    )

    # ✅ แสดงหมายเหตุ
    num_excluded = len(excluded_zero_df)
    if num_excluded > 0:
        st.markdown(f"> ℹ️ **หมายเหตุ**: ตัดอุปกรณ์ที่มี Avg Availability = 0 ออกจากการจัดอันดับจำนวน **{num_excluded} รายการ**")

def plot_top_bottom_chart(df):
    # คำนวณค่าเฉลี่ย Availability
    device_avg = df.groupby(["Device", "ผู้ดูแล"])["Availability (%)"].mean().reset_index()
    device_avg.columns = ["Device", "ผู้ดูแล", "Avg Availability (%)"]

    # แยก Device ที่ Avg = 0 ออก
    device_avg = device_avg[device_avg["Avg Availability (%)"] > 0]

    # จัดอันดับ
    device_avg_sorted = device_avg.sort_values(by="Avg Availability (%)", ascending=False).reset_index(drop=True)
    device_avg_sorted["อันดับ"] = device_avg_sorted.index + 1

    # Top และ Bottom
    top10 = device_avg_sorted.head(10).copy()
    top10["ประเภท"] = "🔼 Top 10 สูงสุด"
    
    bottom10 = device_avg_sorted.tail(10).copy()
    bottom10["ประเภท"] = "🔽 Bottom 10 ต่ำสุด"

    # รวม
    combined_df = pd.concat([top10, bottom10], ignore_index=True)

    # สร้างกราฟแนวนอน เปรียบเทียบ
    fig = px.bar(
        combined_df,
        x="Avg Availability (%)",
        y="Device",
        color="ผู้ดูแล",
        facet_row="ประเภท",  # แยกกราฟบนล่าง
        orientation="h",
        text="Avg Availability (%)",
        title="📊 เปรียบเทียบ Top 10 และ Bottom 10 ของ Availability (%) เฉลี่ย (แยกตามผู้ดูแล)",
        color_discrete_map={
            "PEA ดูแล": "#1f77b4",
            "Producer ดูแล": "#ff7f0e"
        }
    )

    fig.update_layout(
        height=700,
        showlegend=True,
        yaxis=dict(categoryorder='total ascending'),
        margin=dict(t=60, b=40)
    )
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")

    st.plotly_chart(fig, use_container_width=True)

def plot_top_bottom_by_owner(df):
    # เตรียมข้อมูลพื้นฐาน
    df["Availability (%)"] = pd.to_numeric(df["Availability (%)"], errors="coerce")
    df = df[df["Availability (%)"] > 0]  # ตัดค่า 0 ออก
    df["Availability (%)"] = df["Availability (%)"] * 100
    owners = df["ผู้ดูแล"].dropna().unique()

    for owner in owners:
        df_owner = df[df["ผู้ดูแล"] == owner]
        device_avg = df_owner.groupby("Device")["Availability (%)"].mean().reset_index()
        device_avg.columns = ["Device", "Avg Availability (%)"]
        device_avg = device_avg.sort_values(by="Avg Availability (%)", ascending=False).reset_index(drop=True)

        # แยก Top / Bottom
        top10 = device_avg.head(10).copy()
        top10["ประเภท"] = "🔼 Top 10 สูงสุด"
        bottom10 = device_avg.tail(10).copy()
        bottom10["ประเภท"] = "🔽 Bottom 10 ต่ำสุด"
        df_plot = pd.concat([top10, bottom10])

        # วาดกราฟแนวนอน
        fig = px.bar(
            df_plot,
            x="Avg Availability (%)",
            y="Device",
            color="ประเภท",
            orientation="h",
            text="Avg Availability (%)",
            title=f"📊 อันดับ Availability (%) เฉลี่ยของอุปกรณ์ ({owner})",
            color_discrete_map={
                "🔼 Top 10 สูงสุด": "#2ecc71",
                "🔽 Bottom 10 ต่ำสุด": "#e74c3c"
            }
        )

        fig.update_layout(
            height=600,
            yaxis=dict(categoryorder='total ascending'),
            showlegend=True
        )
        fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")

        st.plotly_chart(fig, use_container_width=True)

def plot_top_bottom_faceted(df):
    # แปลงให้เป็นตัวเลข และตัดอุปกรณ์ที่ค่า Availability = 0
    df["Availability (%)"] = pd.to_numeric(df["Availability (%)"], errors="coerce")
    df = df[df["Availability (%)"] > 0]

    df_result = []

    for owner in df["ผู้ดูแล"].dropna().unique():
        df_owner = df[df["ผู้ดูแล"] == owner]
        device_avg = df_owner.groupby("Device")["Availability (%)"].mean().reset_index()
        device_avg.columns = ["Device", "Avg Availability (%)"]
        device_avg["ผู้ดูแล"] = owner

        top10 = device_avg.nlargest(10, "Avg Availability (%)").copy()
        top10["ประเภท"] = "🔼 Top 10 สูงสุด"

        bottom10 = device_avg.nsmallest(10, "Avg Availability (%)").copy()
        bottom10["ประเภท"] = "🔽 Bottom 10 ต่ำสุด"

        df_result.append(pd.concat([top10, bottom10]))

    df_plot = pd.concat(df_result)

    # วาดกราฟรวมโดยใช้ facet_col
    fig = px.bar(
        df_plot,
        x="Avg Availability (%)",
        y="Device",
        color="ประเภท",
        facet_col="ผู้ดูแล",
        orientation="h",
        text="Avg Availability (%)",
        title="📊 เปรียบเทียบ Top/Bottom 10 Availability (%) ระหว่างผู้ดูแล",
        color_discrete_map={
            "🔼 Top 10 สูงสุด": "#27ae60",
            "🔽 Bottom 10 ต่ำสุด": "#c0392b"
        },
        height=700
    )

    fig.update_layout(
        showlegend=True,
        yaxis=dict(categoryorder='total ascending')
    )
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")

    st.plotly_chart(fig, use_container_width=True)
  
def summarize_top_bottom_table(df):
    df["Availability (%)"] = pd.to_numeric(df["Availability (%)"], errors="coerce")

    # กรองข้อมูลที่ Availability > 0
    df_valid = df[df["Availability (%)"] > 0].copy()
    df_zero = df[df["Availability (%)"] == 0].copy()

    summary_tables = []

    for owner in df_valid["ผู้ดูแล"].dropna().unique():
        df_owner = df_valid[df_valid["ผู้ดูแล"] == owner]
        device_avg = df_owner.groupby("Device")["Availability (%)"].mean().reset_index()
        device_avg.columns = ["Device", "Avg Availability (%)"]
        device_avg["ผู้ดูแล"] = owner

        # Top 10
        top10 = device_avg.nlargest(10, "Avg Availability (%)").copy()
        top10["ประเภท"] = "🔼 Top 10 สูงสุด"

        # Bottom 10
        bottom10 = device_avg.nsmallest(10, "Avg Availability (%)").copy()
        bottom10["ประเภท"] = "🔽 Bottom 10 ต่ำสุด"

        summary_tables.append(pd.concat([top10, bottom10]))

    df_summary = pd.concat(summary_tables, ignore_index=True)
    
    # เรียงให้อ่านง่าย
    df_summary = df_summary.sort_values(by=["ผู้ดูแล", "ประเภท", "Avg Availability (%)"], ascending=[True, False, False])

    # แสดงผลใน Streamlit
    st.info("📋 ตารางสรุป Top/Bottom 10 ของแต่ละผู้ดูแล")
    st.dataframe(df_summary.style.format({"Avg Availability (%)": "{:.2f}"}), use_container_width=True)

    if not df_zero.empty:
        st.warning(f"⚠️ พบ Device จำนวน {df_zero['Device'].nunique()} รายการ ที่มีค่า Avg Availability = 0 และไม่ถูกนำมาจัดอันดับ")
        
    # แปลงให้เป็นตัวเลข และกรองข้อมูล Availability = 0
    df["Availability (%)"] = pd.to_numeric(df["Availability (%)"], errors="coerce")
    df = df[df["Availability (%)"] > 0]

    df_result = []

    for owner in df["ผู้ดูแล"].dropna().unique():
        df_owner = df[df["ผู้ดูแล"] == owner]
        device_avg = df_owner.groupby("Device")["Availability (%)"].mean().reset_index()
        device_avg.columns = ["Device", "Avg Availability (%)"]
        device_avg["ผู้ดูแล"] = owner

        top10 = device_avg.nlargest(10, "Avg Availability (%)").copy()
        top10["ประเภท"] = "🔼 Top 10 สูงสุด"

        bottom10 = device_avg.nsmallest(10, "Avg Availability (%)").copy()
        bottom10["ประเภท"] = "🔽 Bottom 10 ต่ำสุด"

        df_result.append(pd.concat([top10, bottom10]))

    df_plot = pd.concat(df_result)

    # วาดกราฟแบบ facet_row
    fig = px.bar(
        df_plot,
        x="Avg Availability (%)",
        y="Device",
        color="ประเภท",
        facet_row="ผู้ดูแล",  # 🔸 เปลี่ยนจาก facet_col → facet_row
        orientation="h",
        text="Avg Availability (%)",
        title="📊 เปรียบเทียบ Top/Bottom 10 Availability (%) แยกตามผู้ดูแล (แนวตั้ง)",
        color_discrete_map={
            "🔼 Top 10 สูงสุด": "#27ae60",
            "🔽 Bottom 10 ต่ำสุด": "#c0392b"
        },
        height=900
    )

    fig.update_layout(
        showlegend=True,
        yaxis=dict(categoryorder='total ascending'),
        margin=dict(t=60, b=40)
    )
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")

    st.plotly_chart(fig, use_container_width=True)

def summarize_top_bottom_table_(df):
    df["Availability (%)"] = pd.to_numeric(df["Availability (%)"], errors="coerce")
    df["Availability (%)"] = df["Availability (%)"] * 100
    # กรองข้อมูลที่ Availability > 0
    df_valid = df[df["Availability (%)"] > 0].copy()
    df_zero = df[df["Availability (%)"] == 0].copy()

    summary_tables = []

    for owner in df_valid["ผู้ดูแล"].dropna().unique():
        df_owner = df_valid[df_valid["ผู้ดูแล"] == owner]
        device_avg = df_owner.groupby("Device")["Availability (%)"].mean().reset_index()
        device_avg.columns = ["Device", "Avg Availability (%)"]
        device_avg["ผู้ดูแล"] = owner

        # Top 10
        top10 = device_avg.nlargest(10, "Avg Availability (%)").copy()
        top10["ประเภท"] = "🔼 Top 10 สูงสุด"

        # Bottom 10
        bottom10 = device_avg.nsmallest(10, "Avg Availability (%)").copy()
        bottom10["ประเภท"] = "🔽 Bottom 10 ต่ำสุด"

        summary_tables.append(pd.concat([top10, bottom10]))

    df_summary = pd.concat(summary_tables, ignore_index=True)
    
    # เรียงให้อ่านง่าย
    df_summary = df_summary.sort_values(by=["ผู้ดูแล", "ประเภท", "Avg Availability (%)"], ascending=[True, False, False])

    # แสดงผลใน Streamlit
    st.info("📋 ตารางสรุป Top/Bottom 10 ของแต่ละผู้ดูแล")
    st.dataframe(df_summary.style.format({"Avg Availability (%)": "{:.5f}%"}), use_container_width=True)

    if not df_zero.empty:
        st.warning(f"⚠️ พบ Device จำนวน {df_zero['Device'].nunique()} รายการ ที่มีค่า Avg Availability = 0 และไม่ถูกนำมาจัดอันดับ")

    
def summarize_top_bottom_overall(df,flag):
    df["Availability (%)"] = pd.to_numeric(df["Availability (%)"], errors="coerce")
    df["Availability (%)"] = df["Availability (%)"] * 100
    
    # กรองข้อมูลที่ Availability > 0
    df_valid = df[df["Availability (%)"] > 0].copy()
    df_zero = df[df["Availability (%)"] == 0].copy()
    
    # คำนวณค่าเฉลี่ยตาม Device
    device_avg = df_valid.groupby("Device")["Availability (%)"].mean().reset_index()
    device_avg.columns = ["Device", "Avg. Availability (%)"]

     # รวมข้อมูลอื่น ๆ ที่ต้องการ (ใช้ข้อมูลล่าสุดของแต่ละ Device)
    latest_info = df_valid.sort_values("Month").drop_duplicates(subset="Device", keep="last")[
        ["Device", "Description", "สถานที่", "การไฟฟ้า", "ผู้ดูแล"]
    ]

    device_avg = device_avg.merge(latest_info, on="Device", how="left")

    device_avg = device_avg.sort_values("Avg. Availability (%)", ascending=False).reset_index(drop=True)
    #device_avg.insert(0, "อันดับ", range(1, len(device_avg) + 1))

    # สรุป Top 10 และ Bottom 10
    top10 = device_avg.head(10).copy()
    top10["ประเภท"] = "🔼 Top 10 สูงสุด"
    bottom10 = device_avg.tail(10).copy()
    bottom10["ประเภท"] = "🔽 Bottom 10 ต่ำสุด"

    df_summary = pd.concat([top10, bottom10], ignore_index=True)

    # จัดเรียงจากมากไปน้อย
    #df_summary = df_summary.sort_values(by="Avg. Availability (%)", ascending=False)
    #df_summary = df_summary.sort_values("Avg. Availability (%)", ascending=False).reset_index(drop=True)
    df_summary.insert(0, "อันดับ", range(1, len(df_summary) + 1))
    # จัดเรียงใหม่ให้ Top และ Bottom แยกกลุ่ม และเรียงตามอันดับ
    #df_summary = df_summary.sort_values(by=["ประเภท", "อันดับ"])


    # แสดงผลใน Streamlit
    st.info("📋 ตารางสรุป Top 10 และ Bottom 10 ของทุกอุปกรณ์ (รวมทุกผู้ดูแล)")
    #st.dataframe(df_summary.style.format({"Avg Availability (%)": "{:.5f}%"}), use_container_width=True)
    #st.dataframe(
    #    df_summary[[
    #        "อันดับ", "Avg. Availability (%)", "Device", "Description", "สถานที่", "การไฟฟ้า", "ผู้ดูแล", "ประเภท"
    #    ]].style.format({"Avg. Availability (%)": "{:.2f}"}),
    #    use_container_width=True, hide_index=True
    #)
    df_summary = df_summary[[
        "อันดับ", "Avg. Availability (%)", "Device", 
        "Description", "สถานที่", "การไฟฟ้า", "ผู้ดูแล", "ประเภท"
        ]]

    # แสดงหมายเหตุถ้ามี Device ที่มีค่า 0%
    if not df_zero.empty:
        st.warning(f"⚠️ มี Device จำนวน {df_zero['Device'].nunique()} รายการที่มี Avg. Availability = 0 ซึ่งไม่ถูกจัดอันดับ")

    # ✅ แปลง "Avg Availability (%)" ให้มี 3 ตำแหน่ง และเพิ่ม "%"
    df_summary["Avg. Availability (%)"] = df_summary["Avg. Availability (%)"].map(lambda x: f"{x:.3f} %")
    st.dataframe(df_summary)
    
    
    # --- แปลงเป็น Excel สำหรับดาวน์โหลด ---
    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Top Bottom Availability")
        processed_data = output.getvalue()
        return processed_data

    excel_file = to_excel(df_summary)

    # --- ปุ่มดาวน์โหลดใน Streamlit ---
    st.download_button(
        label="📥 ดาวน์โหลดตารางอันดับ Availability (Top/Bottom)",
        data=excel_file,
        file_name="availability_ranking_top_bottom.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

        # 🔽 แปลง df_zero["Device"] เป็น DataFrame สำหรับ export
    df_zero_export = df_zero[["Device"]].drop_duplicates().reset_index(drop=True)
    df_zero_export.columns = ["Device (Availability = 0)"]

    st.info(f"{flag} จำนวน {df_zero['Device'].nunique()} {flag} ที่ Avg. Availability = 0")
    st.dataframe(df_zero_export)
    def to_excel_zero(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Zero Availability")
        return output.getvalue()

    excel_file_zero = to_excel_zero(df_zero_export)

    st.download_button(
        label="📥 ดาวน์โหลดรายการอุปกรณ์ที่ Availability = 0",
        data=excel_file_zero,
        file_name="devices_with_zero_availability.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# ---- Upload and Merge ----
uploaded_files = st.file_uploader("📁 อัปโหลดไฟล์ Excel (หลายไฟล์)", type=["xlsx", "xls"], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    
    for uploaded_file in uploaded_files:
        # อ่านชื่อชีตทั้งหมดในไฟล์
        xls = pd.ExcelFile(uploaded_file)
        sheetnames = xls.sheet_names
        # ให้ผู้ใช้เลือกชื่อชีต
        selected_sheet = st.selectbox(f"📑 เลือก Sheet สำหรับไฟล์ {uploaded_file.name}", sheetnames, key=uploaded_file.name)

        df = pd.read_excel(uploaded_file,sheet_name=selected_sheet)
        
        if "Month" not in df.columns:
            st.warning(f"❌ ไม่มีคอลัมน์ 'Availability Period' ในไฟล์ {uploaded_file.name}")
            continue
        df["Month"] = pd.to_datetime(df["Availability Period"], format="%Y-%m", errors="coerce")
        df["Availability (%)"] = df["Availability (%)"].replace({",": "", "%": ""}, regex=True)
        df["Availability (%)"] = pd.to_numeric(df["Availability (%)"], errors="coerce")
        df = df[df["ใช้งาน/ไม่ใช้งาน"] == "ใช้งาน"]
        all_data.append(df)

    df_combined = pd.concat(all_data, ignore_index=True)
    option_func = ['ค่า Ava', 'Ranking', 'ประเมินผล', 'Histogram', 'เปรียบเทียบทุกเดือน']
    option_submenu = ['ระบบจำหน่ายสายส่ง','สถานีไฟฟ้า']
    flag = st.selectbox("🔍 เลือกระดับการวิเคราะห์", ["อุปกรณ์ FRTU", "สถานีไฟฟ้า"])
    title = flag  # เก็บไว้ใช้ในชื่อกราฟ
    
    #owner = st.selectbox("🔍 เลือกผู้ดูแล", ["PEA ดูแล", "Producer ดูแล"])
    # เปลี่ยนชื่อคอลัมน์ Device ตาม flag
    
    #new_device_column_name = "PEA ดูแล" if owner == "PEA ดูแล" else "Producer ดูแล"
    #pivot.index.name = new_device_column_name

    

    func_select = st.sidebar.radio(label="function: ", options = option_func)  
    if  func_select == 'ค่า Ava':
        # ✅ Pivot แสดง Availability รายเดือนทุกอุปกรณ์
        pivot_df = df_addColMonth(df_combined)
 

    elif func_select == 'ประเมินผล':
        bins_eva = [0, 80, 90, 100]
        labels_eva = ["0 <= Availability (%) <= 80", "80 < Availability (%) <= 90", "90 < Availability (%) <= 100"]
        cols = "จำนวน " + title
        df_evaluate = df_combined.copy()

        monthly_avg, device_avg = evaluate(df_evaluate,bins_eva,labels_eva,title)

        
        #st.plotly_chart(fig1)#st.plotly_chart(fig2)#st.dataframe(show_df)
        #show_df.rename(columns={"Device+Percent": cols}, inplace=True)
        #st.markdown("### 🔹 ผลการประเมิน Availability (%) ของอุปกรณ์ในสถานีไฟฟ้า")#st.dataframe(show_df)
        header_colors = ['#003366', '#006699', '#0099CC']   # สีหัวตาราง
        cell_colors = ['#E6F2FF', '#D9F2D9', '#FFF2CC']     # สีพื้นหลังเซลล์แต่ละคอลัมน์
        """
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
        #st.plotly_chart(fig3, use_container_width=True)
        """
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
        # คำนวณค่าเฉลี่ย Availability (%) ต่ออุปกรณ์ พร้อมแนบชื่อผู้ดูแล
        df_avg_device = df_histogram.groupby(["Device", "ผู้ดูแล"])["Availability (%)"].mean().reset_index()
        # กำหนดช่วงกลุ่ม Availability
        bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        labels = [f"{bins[i]}-{bins[i+1]} %" for i in range(len(bins)-1)]
        #df_histogram["Availability (%)"] = df_histogram["Availability (%)"] * 100
        df_avg_device["Availability (%)"] = df_avg_device["Availability (%)"] * 100
        df_histogram["Availability Group"] = pd.cut(df_histogram["Availability (%)"], bins=bins, labels=labels, right=True)
        df_avg_device["Availability Group"] = pd.cut(df_avg_device["Availability (%)"], bins=bins, labels=labels, right=True)

        total_months = df_histogram["Month"].nunique()
        # --- สร้าง Selectbox สำหรับเลือกเดือน ---
        available_months = sorted(df_histogram["Month_year"].dropna().unique())
        selected_month = st.selectbox("📅 เลือกเดือนที่ต้องการดู Histogram", available_months)
        
        # --- กรองข้อมูลเฉพาะเดือนที่เลือก ---
        #filtered_df = df_histogram[df_histogram["Month_year"] == selected_month]
        
        # Group ข้อมูล
        #grouped_counts = df_histogram.groupby(["Month_name", "Availability Group"]).size().reset_index(name="จำนวน Device")
        #grouped_counts = df_histogram["Availability Group"].value_counts().sort_index().reset_index() ###ของเดิม
        
        # --- สร้าง Histogram ---
        grouped_counts = df_histogram["Availability Group"].value_counts().sort_index().reset_index()
        grouped_counts.columns = ["ช่วง % Availability", "จำนวน Device"]
        #grouped_counts_avg = df_avg_device["Availability Group"].value_counts().sort_index().reset_index()
        #grouped_counts_avg.columns = ["ช่วง % Availability", "จำนวน Device"]
        # นับจำนวน Device ในแต่ละช่วง % แยกตามผู้ดูแล
        grouped_counts_avg = df_avg_device.groupby(["ผู้ดูแล", "Availability Group"]).size().reset_index(name="จำนวน Device")

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
            yaxis_title="จำนวน{title}",
            showlegend=True,                 # ✅ เปิดการแสดง Legend
            legend_title="ผู้ดูแล"         # ✅ ชื่อของ Legend
        )

        fig.update_traces(texttemplate="%{text:,}", textposition="outside")
        #st.plotly_chart(fig, use_container_width=True)

        ###✅✅✅ Bar_avg ✅✅✅
        fig_bar_avg = px.bar(
            grouped_counts_avg,
            x="Availability Group",
            y="จำนวน Device",
            color="ผู้ดูแล",
            barmode="group",  # แยกกราฟแท่งแบบข้างกัน # หรือ "stack" ก็ได้
            text="จำนวน Device",
            title=f"📊 จำนวน{title} ในแต่ละช่วง % Availability เฉลี่ย {total_months} เดือน",
            category_orders={"Availability Group": labels},  # เรียงช่วงจากน้อยไปมาก
            color_discrete_sequence=px.colors.qualitative.Set2
            #color_discrete_sequence=[
            #    "#FF0000", "#FF4000", "#FF8000", "#FFBF00", "#FFFF00",
            #    "#BFFF00", "#80FF00", "#40FF00", "#00FF00", "#00CC00"
            #]
        )
        fig_bar_avg.update_layout(
            xaxis_title="ช่วง % Availability",
            yaxis_title=f"จำนวน{title}",
            showlegend=True,
            legend_title="ผู้ดูแล" # ✅ ชื่อของ Legend
        )
        fig_bar_avg.update_traces(texttemplate="%{text:,}", textposition="outside")

        st.plotly_chart(fig_bar_avg, use_container_width=True)
        def download_plotly_figure(fig, filename="chart.png"):
            buffer = BytesIO()
            # บันทึกเป็น PNG (หรือ pdf, svg ก็ได้)
            pio.write_image(fig, buffer, format="png", scale=2)  # scale ปรับความละเอียด
            return buffer.getvalue()
        
        # --- ดาวน์โหลด fig_bar_avg ---
        png_data = download_plotly_figure(fig_bar_avg, filename="histogram_bar_avg.png")

        st.download_button(
            label="📥 ดาวน์โหลดกราฟ Histogram เฉลี่ย (PNG)",
            data=png_data,
            file_name="histogram_bar_avg.png",
            mime="image/png"
        )
        #-----------------------------------------------------------

        typeplot = "Line"
        #plot(df_combined,typeplot)
        plot_avg(df_combined,title)

        #st.dataframe(grouped_counts)
        """
        fig2 = px.bar(
            grouped_counts,
            x="ช่วง % Availability",
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
        #st.plotly_chart(fig2, use_container_width=True)

        """
        cols = "จำนวน " + title
        
        fig = px.bar(
                    grouped_counts,
                    x="ช่วง % Availability",
                    y="จำนวน Device",
                    color="ช่วง % Availability",
                    text="จำนวน Device",
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
        #st.plotly_chart(fig, use_container_width=True)

        # เตรียมข้อมูล
        x_vals = grouped_counts["ช่วง % Availability"]
        y_vals = grouped_counts["จำนวน Device"]
        colors = [get_color(x) for x in x_vals]

        # สร้างกราฟ
        fig_log = go.Figure(data=[go.Bar(
            x=x_vals,
            y=y_vals,
            text=[f"{int(v):,}" for v in y_vals],  # ใส่ comma
            textposition="outside",
            marker_color=colors
        )])
        # ปรับ layout
        fig_log.update_layout(
            title=f"📊 {cols}ในแต่ละช่วง % Availability (log scale)",
            xaxis_title="ช่วง % Availability",
            yaxis_type="log",  # ใช้ log scale
            yaxis_title=cols,
            showlegend=False,
            margin=dict(t=60, b=40)
        )

        #st.plotly_chart(fig_log, use_container_width=True)
    elif func_select == 'Ranking':
        summarize_top_bottom_overall(df_combined,title)
        
    elif func_select == 'เปรียบเทียบทุกเดือน':
        """
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
        df_histogram = df_combined.copy()
    
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

    