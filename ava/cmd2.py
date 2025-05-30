import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="SCADA Command Dashboard", layout="wide")

st.title("📊 SCADA Device Command Summary Dashboard")

# --- Upload Excel ---
uploaded_file = st.file_uploader("📥 Upload Excel File", type=["xlsx"])
if uploaded_file:
    sheet_names = pd.ExcelFile(uploaded_file).sheet_names
    sheet = st.selectbox("เลือก Sheet", sheet_names)
    df = pd.read_excel(uploaded_file, sheet_name=sheet)

    # --- User selects columns ---
    col_device = st.selectbox("เลือกคอลัมน์อุปกรณ์ (Device)", df.columns)
    col_total = st.selectbox("เลือกคอลัมน์ 'สั่งการทั้งหมด'", df.columns)
    col_success = st.selectbox("เลือกคอลัมน์ 'สั่งการสำเร็จ'", df.columns)

    # --- Rename & clean ---
    df = df[[col_device, col_total, col_success]].copy()
    df.columns = ["Device", "สั่งการทั้งหมด", "สั่งการสำเร็จ"]

    # --- คำนวณ % สำเร็จ และอันดับ ---
    df_summary = df.groupby("Device").agg({
        "สั่งการทั้งหมด": "sum",
        "สั่งการสำเร็จ": "sum"
    }).reset_index()

    df_summary["% การสั่งการสำเร็จ"] = (df_summary["สั่งการสำเร็จ"] / df_summary["สั่งการทั้งหมด"]) * 100
    df_summary["อันดับสั่งการทั้งหมด"] = df_summary["สั่งการทั้งหมด"].rank(ascending=False, method='min')
    df_summary["อันดับ % สำเร็จ"] = df_summary["% การสั่งการสำเร็จ"].rank(ascending=False, method='min')

    df_summary["สั่งการทั้งหมด"] = df_summary["สั่งการทั้งหมด"].astype(int)
    df_summary["สั่งการสำเร็จ"] = df_summary["สั่งการสำเร็จ"].astype(int)
    df_summary["% การสั่งการสำเร็จ"] = df_summary["% การสั่งการสำเร็จ"].round(2)

    # --- แสดงตารางจัดอันดับ ---
    st.markdown("## 🏆 จัดอันดับอุปกรณ์ตามการสั่งการ")

    df_sorted_total = df_summary.sort_values(by="สั่งการทั้งหมด", ascending=False)
    st.markdown("### 🔢 จัดอันดับตามจำนวนสั่งการทั้งหมด")
    st.dataframe(df_sorted_total, use_container_width=True)

    df_sorted_success = df_summary.sort_values(by="% การสั่งการสำเร็จ", ascending=False)
    st.markdown("### ✅ จัดอันดับตาม % การสั่งการสำเร็จ")
    st.dataframe(df_sorted_success, use_container_width=True)

    # Checkbox สำหรับเลือก "แสดงทั้งหมด"
    show_all = st.checkbox("✅ แสดงอุปกรณ์ทั้งหมด", value=False)

    if show_all:
        # ถ้าเลือกแสดงทั้งหมด ไม่ต้องจำกัดจำนวน
        top_total = df_sorted_total
        top_success = df_sorted_success
    else:
        # ถ้าไม่เลือกแสดงทั้งหมด ให้ใช้ slider เลือก Top N
        top_n = st.slider("เลือกจำนวนอันดับสูงสุดที่จะแสดงในกราฟ", min_value=5, max_value=min(len(df_summary), 50), value=10)
        top_total = df_sorted_total.head(top_n)
        top_success = df_sorted_success.head(top_n)

    # กราฟรวมการสั่งการทั้งหมด
    fig_total = px.bar(top_total, x="Device", y="สั่งการทั้งหมด", text="สั่งการทั้งหมด",
                    title="🏅 อุปกรณ์ที่มีการสั่งการมากที่สุด")
    st.plotly_chart(fig_total, use_container_width=True)

    # กราฟ % การสั่งการสำเร็จ
    fig_success = px.bar(top_success, x="Device", y="% การสั่งการสำเร็จ", text="% การสั่งการสำเร็จ",
                        title="🏅 อุปกรณ์ที่สั่งการสำเร็จสูงสุด (%)")
    st.plotly_chart(fig_success, use_container_width=True)

    # --- Download CSV ---
    csv = df_summary.to_csv(index=False).encode('utf-8-sig')
    st.download_button("⬇️ ดาวน์โหลดสรุปอันดับ (CSV)", csv, "command_summary.csv", "text/csv")
