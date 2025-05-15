import pandas as pd
import streamlit as st
import test17
import importlib

<<<<<<< HEAD

=======
>>>>>>> 158bcb5485711eca8e477698eb7a97672f72b8e2
# ✅ **โหลดข้อมูล Remote**
df_remote = pd.read_excel("RemoteUnit.xlsx", sheet_name="RemoteUnitReport_Friday, March ", skiprows=4)

# กรองเฉพาะแถวที่คอลัมน์ "Substation" มีค่า "S1 FRTU"
df_remote = df_remote[df_remote["Substation"] == "S1 FRTU"]

new_columns = [
    "Availability (%)",
    "จำนวนครั้ง Initializing",
    "ระยะเวลา Initializing (seconds)",
    "จำนวนครั้ง Telemetry Failure",
    "ระยะเวลา Telemetry Failure (seconds)",
    "จำนวนครั้ง Connecting",
    "ระยะเวลา Connecting (seconds)"
]

new_col = ["New State", "Adjusted Duration (seconds)", "device_availability"]

for col in new_columns:
    df_remote[col] = 0  # กำหนดค่าเริ่มต้นเป็น 0 หรือ NaN ตามต้องการ

for col in new_col:
    df_remote[col] = ""
# เลือกเฉพาะคอลัมน์ที่สนใจ
columns_to_keep_remote = ["Name", "State", "Description"] + new_columns + new_col
df_remote = df_remote[columns_to_keep_remote]

<<<<<<< HEAD
#df_availability = test17.get_device_availability()
=======
st.write(df_remote)
df_remote.rename(columns={"Name": "Device"}, inplace=True)

# ✅ **คำนวณ Availability (%) จาก test17.py**
device_availability = test17.calculate_device_count(df_remote)

# ✅ **คำนวณ Availability (%) และรวมกับ Device Count Duration**
device_availability = test17.get_device_availability(df_remote)

# ✅ **อัพเดตค่า Availability (%) และ Device Count ใน df_remote**
df_remote = df_remote.merge(device_availability[["Device", "Availability (%)", "Device Count"]], on="Device", how="left")

st.write(df_remote)
>>>>>>> 158bcb5485711eca8e477698eb7a97672f72b8e2

# ✅ รวมค่า Availability (%) จาก test17.py
#df_remote = df_remote.merge(test17.device_availability[["Name", "Availability (%)"]], on="Name", how="left")
#df_remote["Availability (%)"] = df_remote["Name"].map(test17.device_availability)
# แสดง DataFrame ใน Streamlit
<<<<<<< HEAD
#st.dataframe(df_availability)
=======
>>>>>>> 158bcb5485711eca8e477698eb7a97672f72b8e2

# ✅ กำหนดค่าเริ่มต้นของ "Availability (%)" เป็น 100%
#df_remote["Availability (%)"] = 100  

#st.dataframe(test17.device_availability[["Total Duration (seconds)", "Online Duration (seconds)"]])

if __name__ == "__main__":
    st.write(df_remote)  # แสดงค่าใน Streamlit
