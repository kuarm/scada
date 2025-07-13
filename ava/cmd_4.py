import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from io import StringIO


"""
# 📁 อัปโหลดไฟล์ Excel
uploaded_file = st.file_uploader("📁 กรุณาอัปโหลดไฟล์ Excel", type=["xlsx"])

if uploaded_file:
    # อ่านไฟล์ทั้งหมดจาก 3 sheet
    sheet_names = ["RTU", "SUBSTATION", "FRTU"]
    dfs = []

    for sheet in sheet_names:
        try:
            df = pd.read_excel(uploaded_file, sheet_name=sheet)
            df["Sheet"] = sheet  # เพิ่มแหล่งที่มาของข้อมูล
            dfs.append(df)
        except:
            st.warning(f"❗ ไม่พบ Sheet: {sheet}")

    if not dfs:
        st.error("📄 ไม่พบข้อมูลใน Sheets ที่กำหนด")
    else:
        # รวมข้อมูลทุก sheet
        df_all = pd.concat(dfs, ignore_index=True)

        # ตรวจสอบคอลัมน์ที่จำเป็น
        if "Device" not in df_all.columns or "Availability Period" not in df_all.columns or "สั่งการสำเร็จ (%)" not in df_all.columns:
            st.error("❌ ไฟล์ Excel ต้องมีคอลัมน์: 'Device', 'Availability Period', 'สั่งการสำเร็จ (%)'")
        else:
            # แปลงคอลัมน์เวลาเป็นเดือน
            df_all["Month"] = pd.to_datetime(df_all["Availability Period"], format="%Y-%m", errors="coerce")
            df_all["Month_str"] = df_all["Month"].dt.strftime("%Y-%m")

            # สร้าง index ของทุก combination ที่เป็นไปได้
            all_devices = df_all["Device"].dropna().unique()
            all_months = df_all["Month_str"].dropna().unique()
            index = pd.MultiIndex.from_product([all_devices, all_months], names=["Device", "Month_str"])

            # ค่าเฉลี่ยการสั่งการ
            df_summary = df_all.groupby(["Device", "Month_str"])["สั่งการสำเร็จ (%)"].mean().reset_index()

            # เติมช่องว่าง
            df_full = df_summary.set_index(["Device", "Month_str"]).reindex(index).reset_index()

            # ค้นหา Device ที่ไม่มีข้อมูลในเดือนนั้น
            df_missing = df_full[df_full["สั่งการสำเร็จ (%)"].isna()].copy()

            st.success("✅ พบข้อมูล Device ที่ไม่มีการสั่งการในบางเดือน")
            st.dataframe(df_missing, use_container_width=True)

            # แสดงสรุปจำนวน Device ที่ไม่มีข้อมูลในแต่ละเดือน
            missing_summary = df_missing.groupby("Month_str")["Device"].count().reset_index()
            missing_summary.columns = ["เดือน", "จำนวนอุปกรณ์ที่ไม่มีข้อมูล"]
            st.bar_chart(missing_summary.set_index("เดือน"))
"""




#df_rtu = pd.read_excel(xls, sheet_name="RTU")
#df_sub = pd.read_excel(xls, sheet_name="SUBSTATION")
#df_frtu = pd.read_excel(xls, sheet_name="FRTU")

# 2. รวมทั้งสาม sheet เข้าด้วยกัน
#df_all = pd.concat([df_rtu, df_sub, df_frtu], ignore_index=True)

# 📥 โหลดข้อมูลจาก Sheet "Sum"
uploaded_file = st.file_uploader("📁 อัปโหลดไฟล์ที่มี Sheet 'Sum'", type=["xlsx"])

month_names = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
                   'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']
if uploaded_file:
    try:
        df_sum = pd.read_excel(uploaded_file, sheet_name="Sum")
        df_rtu = pd.read_excel(uploaded_file , sheet_name="RTU")
        df_substation = pd.read_excel(uploaded_file , sheet_name="SUBSTATION")
        df_frtu = pd.read_excel(uploaded_file , sheet_name="FRTU")
        df_rtu["ประเภท"] = "RTU"
        df_substation["ประเภท"] = "SUBSTATION"
        df_frtu["ประเภท"] = "FRTU"

        # รวมทั้งหมด
        df_all = pd.concat([df_rtu, df_substation, df_frtu], ignore_index=True)

        df_merged = df_sum.merge(df_all[["Device", "ประเภท"]], on="Device", how="left")
        st.dataframe(df_merged)

    except:
        st.error("❌ ไม่พบ Sheet ชื่อ 'Sum'")
    else:
        # 2. คัด column เดือนที่มีข้อมูลอย่างน้อย 1 ช่อง
        valid_months = [col for col in month_names if col in df.columns and df[col].notna().any()]
        # สมมติว่า df เป็น wide format
        df = df.melt(
            id_vars=["Device"], 
            value_vars=valid_months, 
            var_name="เดือน", 
            value_name="สั่งการสำเร็จ (%)")
        # แปลงเป็น float ป้องกันกรณีเป็น string
        df["สั่งการสำเร็จ (%)"] = pd.to_numeric(df["สั่งการสำเร็จ (%)"], errors="coerce")
        df["สั่งการสำเร็จ (%)"] = df["สั่งการสำเร็จ (%)"] * 100

        # ✅ แปลงค่าให้เป็นเปอร์เซ็นต์ 2 ตำแหน่ง
        df["สั่งการสำเร็จ (%)"] = df["สั่งการสำเร็จ (%)"].map(lambda x: f"{x:.2f}%" if pd.notnull(x) else "-")
        st.dataframe(df)
        # ✅ ตรวจสอบว่ามีคอลัมน์ที่จำเป็น
        required_cols = ["Device", "เดือน", "สั่งการสำเร็จ (%)"]

        if not all(col in df.columns for col in required_cols):
            st.error(f"❌ ต้องมีคอลัมน์: {required_cols}")
        else:
            # ✅ ตรวจหาว่าในแต่ละเดือนมี Device ใดที่ไม่ได้สั่งการเลย
            #df["สั่งการสำเร็จ (%)"] = pd.to_numeric(df["สั่งการสำเร็จ (%)"], errors="coerce")

            # คัด Device ที่ "สั่งการสำเร็จ (%)" เป็น - 
            #df_missing = df[df["สั่งการสำเร็จ (%)"].isna()]
            df_missing = df[df["สั่งการสำเร็จ (%)"].astype(str).str.strip() == "-"]
            
            st.dataframe(df_missing)
            # นับจำนวน Device ต่อเดือน
            summary = df_missing.groupby("เดือน")["Device"].nunique().reset_index()
            summary.columns = ["เดือน", "จำนวน Device ที่ไม่มีการสั่งการ"]

            st.info("📊 จำนวน Device ที่ไม่มีการสั่งการเลยในแต่ละเดือน")
            st.dataframe(summary)

            # แสดง Device รายเดือนที่ไม่มีการสั่งการ
            st.info("🧾 รายชื่อ Device ที่ไม่มีการสั่งการในแต่ละเดือน")

            missing_summary_list = []  # สำหรับ export

            for month, group in df_missing.groupby("เดือน"):
                device_list = group["Device"].dropna().unique().tolist()
                st.markdown(f"### 📅 เดือน: {month}")
                st.write(f"🔸 จำนวน: {len(device_list)} อุปกรณ์")
                st.write(device_list)

                # เก็บเข้า list สำหรับ export
                for device in device_list:
                    missing_summary_list.append({"เดือน": month, "Device": device})

            #✅ เตรียมไฟล์สำหรับดาวน์โหลด (รวมทุกเดือน)
            df_missing_export = pd.DataFrame(missing_summary_list)
            st.dataframe(df_missing_export)

            def to_excel(df):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Missing Devices')
                processed_data = output.getvalue()
                return processed_data

            excel_data = to_excel(df_missing_export)

            st.download_button(
                label="📥 ดาวน์โหลดรายชื่อ Device ที่ไม่มีการสั่งการ (รวมทุกเดือน)",
                data=excel_data,
                file_name="missing_devices_by_month.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # ✅ เตรียมไฟล์ Excel

            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                for month, group in df_missing.groupby("เดือน"):
                    df_month = group[["Device"]].dropna().drop_duplicates().reset_index(drop=True)
                    sheet_name = str(month)[:31]  # Excel จำกัดชื่อชีตไม่เกิน 31 ตัวอักษร
                    df_month.to_excel(writer, sheet_name=sheet_name, index=False)

            # ✅ สร้างปุ่มดาวน์โหลด
            st.download_button(
                label="📥 ดาวน์โหลดรายชื่อ Device ที่ไม่มีการสั่งการ (แยกตามเดือน)",
                data=output.getvalue(),
                file_name="missing_devices_by_month_sheets.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            #✅ เตรียมข้อมูลเปรียบเทียบก่อน plot:

            # 🔹 นับจำนวนทั้งหมดต่อเดือน
            total_devices_by_month = df.groupby("เดือน")["Device"].nunique()

            # 🔹 นับจำนวนที่ไม่มีการสั่งการ
            missing_devices_by_month = df_missing.groupby("เดือน")["Device"].nunique()

            # 🔹 สร้าง DataFrame เปรียบเทียบ
            comparison_df = pd.DataFrame({
                "ไม่มีการสั่งการ": missing_devices_by_month,
                "มีการสั่งการ": total_devices_by_month - missing_devices_by_month
            }).fillna(0).astype(int).reset_index()

            #📊 Plot กราฟแท่งเปรียบเทียบ:
            # 🔸 Melt เพื่อให้ Plotly เข้าใจว่าเราต้องการ grouped bar
            comparison_melted = comparison_df.melt(id_vars="เดือน", 
                                                value_vars=["มีการสั่งการ", "ไม่มีการสั่งการ"],
                                                var_name="สถานะการสั่งการ", 
                                                value_name="จำนวน Device")

            # รายชื่อเดือนเรียงตามปฏิทิน
            thai_month_order = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
                                'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']

            fig = px.bar(
                comparison_melted,
                x="เดือน",
                y="จำนวน Device",
                color="สถานะการสั่งการ",
                barmode="group",
                text="จำนวน Device",
                title="📊 เปรียบเทียบจำนวน Device ที่มี / ไม่มีการสั่งการในแต่ละเดือน",
                color_discrete_map={
                    "มีการสั่งการ": "#00CC66",
                    "ไม่มีการสั่งการ": "#FF4444"
                }
            )
            # 🔸 สร้างกราฟ
            fig2 = px.bar(
                comparison_df,
                x="เดือน",
                y=["มีการสั่งการ", "ไม่มีการสั่งการ"],
                barmode="group",
                title="📊 เปรียบเทียบจำนวน Device ที่มี/ไม่มีการสั่งการในแต่ละเดือน",
                category_orders={"เดือน": thai_month_order},  # ✅ เรียงลำดับเดือน
                labels={"value": "จำนวน Device", "variable": "สถานะการสั่งการ"},
                color_discrete_map={
                    "ไม่มีการสั่งการ": "#FF5733",  # สีส้มแดง
                    "มีการสั่งการ": "#2ECC71"     # สีเขียว
                },
                text_auto=True
            )
            fig2.update_traces(
                texttemplate="%{y:,}",  # ใส่ comma คั่นหลักพัน เช่น 1,000
                textposition="outside"  # หรือ "auto", "inside", "outside", "top center"
            )
            fig2.update_layout(
                xaxis_title="เดือน",
                yaxis_title="จำนวน Device",
                legend_title="สถานะ",
                bargap=0.2
            )
            st.plotly_chart(fig2, use_container_width=True)

            # 🔸 สร้างไฟล์ Excel จาก comparison_df
            def to_excel_download(df):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='เปรียบเทียบสั่งการ')
                return output.getvalue()

            # 🔹 เตรียมข้อมูล (จากก่อนหน้านี้)
            export_df = comparison_df[["เดือน", "ไม่มีการสั่งการ", "มีการสั่งการ"]]
            
            # 🔸 แปลงเป็นไฟล์ Excel
            excel_data = to_excel_download(export_df)

            # 🔸 ปุ่มดาวน์โหลด
            st.download_button(
                label="📥 ดาวน์โหลดสรุปการสั่งการรายเดือน (Excel)",
                data=excel_data,
                file_name="Device_Command_Summary.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

