import pandas as pd
import streamlit as st
import test17

st.write(test17)
# ✅ **โหลดข้อมูล Remote**
df_remote = pd.read_excel("RemoteUnit.xlsx", sheet_name="RemoteUnitReport_Friday, March ", skiprows=4)

# กรองเฉพาะแถวที่คอลัมน์ "Substation" มีค่า "S1 FRTU"
df_remote = df_remote[df_remote["Substation"] == "S1 FRTU"]

# เลือกเฉพาะคอลัมน์ที่สนใจ
columns_to_keep_remote = ["Name", "State", "Description"]
df_remote = df_remote[columns_to_keep_remote]

df_availability = test17.get_device_availability()

# ✅ รวมค่า Availability (%) จาก test17.py
#df_remote = df_remote.merge(test17.device_availability[["Name", "Availability (%)"]], on="Name", how="left")
#df_remote["Availability (%)"] = df_remote["Name"].map(test17.device_availability)
# แสดง DataFrame ใน Streamlit
st.dataframe(df_availability)

# ✅ กำหนดค่าเริ่มต้นของ "Availability (%)" เป็น 100%
#df_remote["Availability (%)"] = 100  

#st.dataframe(test17.device_availability[["Total Duration (seconds)", "Online Duration (seconds)"]])

if __name__ == "__main__":
    st.write(df_remote)  # แสดงค่าใน Streamlit
