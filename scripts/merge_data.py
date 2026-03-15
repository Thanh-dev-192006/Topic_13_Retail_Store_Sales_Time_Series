import pandas as pd
from pathlib import Path

# Đường dẫn đúng tới thư mục data
data_folder = Path("src/data")

# File gốc
base_file = data_folder / "train.csv"

# Lấy tất cả file feature train_*.csv, bỏ train.csv
feature_files = [
    f for f in data_folder.glob("train_*.csv")
    if f.name != "train.csv"
]

# Đọc file train gốc
base_df = pd.read_csv(base_file)

# Ghép từng file feature
for file in feature_files:
    feature_df = pd.read_csv(file)

    # Bỏ cột trùng để tránh duplicate columns
    feature_df = feature_df[[col for col in feature_df.columns if col not in base_df.columns]]

    # Ghép ngang theo cột
    base_df = pd.concat([base_df, feature_df], axis=1)

# Lưu file kết quả
output_file = data_folder / "train_full.csv"
base_df.to_csv(output_file, index=False)

print(f"Đã tạo file: {output_file}")