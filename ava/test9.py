import pandas as pd
import re
import streamlit as st

def calculate_state_durations(df, start_time, end_time):
    # Convert timestamps
    df["Field change time"] = pd.to_datetime(df["Field change time"])
    start_time = pd.to_datetime(start_time)
    end_time = pd.to_datetime(end_time)
    
    # Sort data by time
    df = df.sort_values("Field change time").reset_index(drop=True)
    
    # Extract previous and new states
    def extract_states(message):
        match = re.search(r"Remote unit state changed from (.+?) to (.+)", str(message))
        return match.groups() if match else (None, None)
    
    df[["Previous State", "New State"]] = df["Message"].apply(lambda x: pd.Series(extract_states(x)))
    df = df.dropna(subset=["Previous State", "New State"])
    
    # Add start_time as the first event if necessary
    first_event_time = df["Field change time"].iloc[0]
    if first_event_time > start_time:
        #df.loc[-1] = [start_time, None, df["Previous State"].iloc[0], None, None]
        new_row = pd.DataFrame([{
            "Field change time": start_time,
            "Message": None,
            "Previous State": df["Previous State"].iloc[0],
            "New State": None,
            "Next Change Time": None
        }])
        df = pd.concat([new_row, df], ignore_index=True)
        st.write(df)
        df.index = df.index + 1
        df = df.sort_values("Field change time").reset_index(drop=True)
    
    # Calculate time difference
    df["Next Change Time"] = df["Field change time"].shift(-1)
    df.loc[df.index[-1], "Next Change Time"] = end_time  # Ensure last event stops at end_time
    df["Time Difference (seconds)"] = (df["Next Change Time"] - df["Field change time"]).dt.total_seconds()
    
    # Adjust time range
    df["Adjusted Start"] = df["Field change time"].clip(lower=start_time)
    df["Adjusted End"] = df["Next Change Time"].clip(upper=end_time)
    df["Adjusted Duration"] = (df["Adjusted End"] - df["Adjusted Start"]).dt.total_seconds()
    
    # Sum up duration per state
    state_durations = df.groupby("Previous State")["Adjusted Duration"].sum().reset_index()
    state_durations["Duration"] = pd.to_timedelta(state_durations["Adjusted Duration"], unit="s")
    
    return state_durations

# โหลดข้อมูลจากไฟล์
df = pd.read_excel("ava_test.xlsx", sheet_name="Sheet5")

# กำหนดช่วงเวลา
start_time = "2025-02-16 00:00:00"
end_time = "2025-02-17 00:00:00"

# คำนวณระยะเวลาของแต่ละ State
result = calculate_state_durations(df, start_time, end_time)

# แสดงผล
st.write(result)
