# ปรับปรุงการดึงสถานะ Online
df_subset['Current State'] = df_subset['Message'].apply(
    lambda x: "Online" if "to Online" in str(x) else (
        "Initializing" if "Initializing" in str(x) else (
            "Telemetry Failure" if "Telemetry Failure" in str(x) else (
                "Connecting" if "Connecting" in str(x) else (
                    "Offline" if "Offline" in str(x) else None
                )
            )
        )
    )
)

# กรองเฉพาะข้อมูลที่มี State
df_filtered = df_subset.dropna(subset=['Current State'])

# คำนวณระยะเวลาของแต่ละ State
df_filtered['Next Time'] = df_filtered.groupby('Device')['Field change time'].shift(-1)
df_filtered['Duration'] = (df_filtered['Next Time'] - df_filtered['Field change time']).dt.total_seconds()

# ลบค่า NaN
df_filtered = df_filtered.dropna()

# คำนวณ Availability ใหม่
availability_df = df_filtered.groupby(['Device', 'Current State'])['Duration'].sum().unstack(fill_value=0)
availability_df['Total Time'] = availability_df.sum(axis=1)
availability_df['Online Time'] = availability_df.get('Online', 0)
availability_df['Availability (%)'] = (availability_df['Online Time'] / availability_df['Total Time']) * 100

# แสดงผลลัพธ์ Availability ของแต่ละอุปกรณ์
availability_df[['Availability (%)']].sort_values(by='Availability (%)', ascending=False).head(10)
