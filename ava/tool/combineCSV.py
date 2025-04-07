import os
import pandas as pd

def combine_csv(input_folder, output_file):
    try:
        # ตรวจสอบว่าโฟลเดอร์มีอยู่จริง
        if not os.path.exists(input_folder):
            print(f"❌ โฟลเดอร์ {input_folder} ไม่พบ")
            return
        
        # หาไฟล์ CSV ด้วย os.scandir()
        csv_files = [entry.path for entry in os.scandir(input_folder) if entry.is_file() and entry.name.endswith(".csv")]

        if not csv_files:
            print("❌ ไม่มีไฟล์ CSV ในโฟลเดอร์ที่ระบุ")
            return

        df_list = []

        for file_path in csv_files:
            try:
                df = pd.read_csv(file_path, skiprows=6)  # ปรับ skiprows ตามต้องการ
                if df.empty:
                    print(f"⚠️ ไฟล์ {file_path} ว่างเปล่า!")
                else:
                    df_list.append(df)
            except Exception as e:
                print(f"❌ ไม่สามารถอ่านไฟล์ {file_path}: {e}")

        if df_list:
            df_combined = pd.concat(df_list, ignore_index=True)
            df_combined.to_csv(output_file, index=False)
            print(f"✅ รวมไฟล์สำเร็จ! บันทึกที่ {output_file}")
        else:
            print("❌ ไม่มีข้อมูลที่สามารถรวมได้")

    except Exception as e:
        print(f"เกิดข้อผิดพลาด: {e}")

# 🔹 กำหนดพาธ
input_folder = r"D:\Develop\scada\ava\source_csv"
output_file = r"D:\Develop\scada\ava\source_csv\combined_output.csv"

combine_csv(input_folder, output_file)
