import re
import pandas as pd
import streamlit as st

# โหลดข้อมูลจากไฟล์ Excel
file_path = "ava_test.xlsx"  # เปลี่ยนเป็น path ของไฟล์คุณ
df = pd.read_excel(file_path, sheet_name="Sheet5",header=0)

# แปลงคอลัมน์ Field change time เป็น datetime
df["Field change time"] = pd.to_datetime(df["Field change time"], errors="coerce")

# Sort by time to ensure correct sequence
df = df.sort_values("Field change time").reset_index(drop=True)

# Calculate time differences
df["Time Difference (seconds)"] = df["Field change time"].diff().dt.total_seconds()

# Function to extract previous and new state from message
def extract_states(message):
    match = re.search(r"Remote unit state changed from (.+?) to (.+)", message)
    if match:
        return match.group(1), match.group(2)
    return None, None

# Apply function to extract states
df[["Previous State", "New State"]] = df["Message"].apply(lambda x: pd.Series(extract_states(x)))

# ใช้ regex แยก State ก่อนหน้า และหลังการเปลี่ยนแปลง
df[["Previous State", "Next State"]] = df["Message"].str.extract(r'from (.+) to (.+)')
st.write(df)

# Remove rows with missing states (if any)
df = df.dropna(subset=["Previous State", "Next State"])

# Calculate total duration each state was active
state_durations = df.groupby("Previous State")["Time Difference (seconds)"].sum().reset_index()

# Convert total seconds to timedelta format for better readability
state_durations["Duration"] = pd.to_timedelta(state_durations["Time Difference (seconds)"], unit="s")

# คำนวณ Duration
#df["Duration (second)"] = df.groupby(["Previous State", "Next State"])["Field change time"].diff().dt.total_seconds()



# Aggregate total time for each state
#state_durations = df.groupby("Previous State")["Previous State Duration"].sum().reset_index()

# Show results
st.write(state_durations)
