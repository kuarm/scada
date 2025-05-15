# availability_data.py
import pandas as pd

# สร้าง DataFrame ที่มีข้อมูล Availability (%)
df_availability = pd.DataFrame({
    "Name": ["Unit A", "Unit B", "Unit C"],
    "Availability (%)": [95.5, 98.2, 87.3]
})
