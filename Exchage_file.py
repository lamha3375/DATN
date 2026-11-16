
import pandas as pd
import os

# Đường dẫn file Excel
file_excel = r"D:\DATN\He_Thong_Tri_Thuc_Lich_Su_Tay_Son.xlsx"

# Thư mục lưu các file CSV
thu_muc_luu = r"D:\DATN\CSV"

# Tạo thư mục nếu chưa tồn tại
os.makedirs(thu_muc_luu, exist_ok=True)

# Đọc toàn bộ sheet trong Excel
sheets = pd.read_excel(file_excel, sheet_name=None)

# Chuyển từng sheet thành một file CSV
for ten_sheet, df in sheets.items():
    ten_file = os.path.join(thu_muc_luu, f"{ten_sheet}.csv")

    df.to_csv(
        ten_file,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"Đã xuất: {ten_file}")

print("HOÀN TẤT CHUYỂN ĐỔI!")
