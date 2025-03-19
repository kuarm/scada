import pandas as pd
import streamlit as st
import test17

# ✅ **โหลดข้อมูล Remote**
df_remote = pd.read_excel("RemoteUnit.xlsx", sheet_name="RemoteUnitReport_Friday, March ", skiprows=4)

# กรองเฉพาะแถวที่คอลัมน์ "Substation" มีค่า "S1 FRTU"
df_remote = df_remote[df_remote["Substation"] == "S1 FRTU"]

# เลือกเฉพาะคอลัมน์ที่สนใจ
columns_to_keep_remote = ["Name", "State", "Description"]
df_remote = df_remote[columns_to_keep_remote]

# ✅ กำหนดค่าเริ่มต้นของ "Availability (%)" เป็น 100%
df_remote["Availability (%)"] = 100  

#st.dataframe(test17.device_availability[["Total Duration (seconds)", "Online Duration (seconds)"]])

if __name__ == "__main__":
    st.write(test17.device_availability)  # หรือโค้ดอื่นที่ต้องการให้รันเฉพาะเมื่อเรียกตรงๆ
