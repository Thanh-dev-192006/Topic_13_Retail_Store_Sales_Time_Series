# Giải thích chi tiết: `feature_external.py`

> **Tuần 3 — Topic 13: Retail Store Sales Time Series**  
> File: `notebooks/04_feature_engineering/features/feature_external.py`

---

## 1. File này có nhiệm vụ gì?

File `feature_external.py` có nhiệm vụ **tạo ra các features (đặc trưng) từ dữ liệu bên ngoài** để cung cấp cho model machine learning (LightGBM). Cụ thể là từ hai nguồn:

- **`oil.csv`** — Giá dầu thô WTI hàng ngày
- **`stores.csv`** — Thông tin metadata của 54 cửa hàng

File này là một mắt xích trong pipeline feature engineering của dự án, nằm cùng thư mục với hai file đã có:

```
notebooks/04_feature_engineering/features/
├── feature_temporal.py   ← Tuần trước: features về thời gian (tháng, ngày, tuần...)
├── feature_holiday.py    ← Tuần trước: features về ngày lễ
└── feature_external.py   ← Tuần này: features từ giá dầu & thông tin cửa hàng
```

---

## 2. Tại sao cần file này?

### 2.1 Tại sao cần giá dầu?

Ecuador là quốc gia **phụ thuộc nặng vào xuất khẩu dầu mỏ**. Ngân sách chính phủ, việc làm và thu nhập người dân đều gắn chặt với giá dầu thế giới. Khi giá dầu giảm:

```
Giá dầu giảm
    → Ngân sách chính phủ thiếu hụt
    → Cắt giảm chi tiêu công, mất việc làm
    → Thu nhập người dân giảm
    → Người dân mua sắm ít hơn
    → Doanh số bán lẻ giảm
```

EDA ở Tuần 2 đã **đo được correlation = -0.63** giữa giá dầu và doanh số — đây là mức tương quan âm rất mạnh. Nếu bỏ qua thông tin này, model sẽ bị thiếu một yếu tố giải thích cực kỳ quan trọng và dự báo kém chính xác.

### 2.2 Tại sao cần thông tin cửa hàng?

Model cần phân biệt **54 cửa hàng khác nhau** để học đúng pattern của từng cửa hàng. Một cửa hàng loại A ở Quito hoạt động rất khác một cửa hàng loại D ở tỉnh lẻ. Nếu không encode thông tin này, model sẽ xử lý tất cả các cửa hàng như nhau — dẫn đến dự báo không chính xác.

---

## 3. Hướng đi và cách thức xây dựng

### 3.1 Hướng đi tổng thể

File được xây dựng theo hướng **modular** (từng module độc lập), gồm 3 tầng:

```
Tầng 1: add_oil_features()      ← Xử lý giá dầu
Tầng 2: add_store_encoding()    ← Xử lý thông tin cửa hàng
Tầng 3: build_external_features() ← Pipeline gọi cả hai tầng trên
```

Người dùng chỉ cần gọi hàm ở **Tầng 3** là đủ — không cần quan tâm bên trong làm gì.

### 3.2 Nguyên tắc thiết kế

Có 3 nguyên tắc được tuân theo khi xây dựng:

**Nguyên tắc 1 — Không làm rò rỉ dữ liệu tương lai (No Data Leakage)**  
Tất cả lag features đều dùng thông tin từ *quá khứ*, không bao giờ dùng thông tin từ ngày hiện tại hay tương lai. Model phải học từ dữ liệu thực tế, không được "nhìn trộm" vào tương lai.

**Nguyên tắc 2 — Phù hợp với LightGBM**  
LightGBM cần dữ liệu dạng số. Mọi cột dạng text (loại cửa hàng, thành phố...) đều phải được chuyển sang số trước khi đưa vào model.

**Nguyên tắc 3 — Dễ tái sử dụng**  
Hàm nhận DataFrame vào và trả DataFrame ra — có thể dùng cho cả tập train lẫn tập test mà không cần chỉnh sửa.

---

## 4. Giải thích chi tiết từng phần code

### 4.1 Hàm `add_oil_features()` — Tạo features từ giá dầu

```python
def add_oil_features(df, oil_df, date_col="date"):
```

Hàm này nhận vào DataFrame chính và DataFrame giá dầu, trả về DataFrame chính đã được thêm các cột oil features.

---

#### Bước 1: Chuẩn bị bảng giá dầu liên tục theo ngày

```python
full_date_range = pd.DataFrame({
    "date": pd.date_range(start=oil["date"].min(), end=oil["date"].max(), freq="D")
})
oil = full_date_range.merge(oil, on="date", how="left")
```

**Vấn đề:** File `oil.csv` chỉ chứa các ngày có giao dịch (thứ 2 - thứ 6). Cuối tuần và ngày lễ không có giá → tạo ra "lỗ hổng" trong dữ liệu.

**Giải pháp:** Tạo ra một bảng ngày đầy đủ từ đầu đến cuối (kể cả thứ 7, chủ nhật), rồi merge với bảng giá dầu. Các ngày không có giá sẽ tự động điền NaN — chuẩn bị cho bước ffill tiếp theo.

**Tại sao cần làm vậy?** Vì DataFrame chính (train.csv) có đủ 7 ngày trong tuần. Nếu bảng oil thiếu ngày cuối tuần, khi merge sẽ bị mất thông tin hoặc tạo ra NaN không cần thiết.

---

#### Bước 2: Xử lý Missing Values bằng Forward Fill

```python
oil["oil_price"] = oil["oil_price"].ffill()
oil["oil_price"] = oil["oil_price"].bfill()
```

**`ffill()` là gì?** Forward Fill — mang giá trị của ngày *liền trước* điền vào ngày đang bị thiếu.

**Ví dụ trực quan:**
```
Thứ 5  (01/03): $50.20  ← có giá
Thứ 6  (02/03): $50.80  ← có giá
Thứ 7  (03/03): NaN     ← sau ffill → $50.80
Chủ nhật(04/03): NaN    ← sau ffill → $50.80
Thứ 2  (05/03): $49.50  ← có giá mới
```

**Tại sao dùng ffill mà không dùng cách khác?**
- Giá dầu cuối tuần không có, nhưng giá dầu ngày thứ 6 *vẫn còn hiệu lực* cho đến khi có giá mới vào thứ 2.
- Dùng interpolation (nội suy) sẽ "bịa ra" giá dầu tương lai giả — không hợp lý.
- Dùng mean (trung bình) sẽ xóa đi thông tin về xu hướng ngắn hạn.

**`bfill()`** (Backward Fill) chỉ dùng để backup cho trường hợp NaN xuất hiện ngay ở đầu chuỗi (rất hiếm) — khi đó không có ngày trước để ffill.

---

#### Bước 3: Tạo Lag Features

```python
oil["oil_price_lag_7"]  = oil["oil_price"].shift(7)
oil["oil_price_lag_14"] = oil["oil_price"].shift(14)
```

**`shift(n)` là gì?** Dịch chuyển toàn bộ cột xuống n hàng — tức là giá trị ở hàng hiện tại sẽ là giá trị của n ngày trước đó.

**Ví dụ trực quan với `shift(7)`:**
```
Ngày        oil_price    oil_price_lag_7
01/01        $50           NaN
08/01        $52           $50  ← giá của 7 ngày trước (01/01)
15/01        $48           $52  ← giá của 7 ngày trước (08/01)
```

**Tại sao lag 7 và lag 14, không phải lag 1 hay lag 30?**
- **Lag 1 (ngày hôm qua)**: Tác động kinh tế không xảy ra chỉ sau 1 ngày.
- **Lag 7 (1 tuần)**: Capture chu kỳ hành vi mua sắm theo tuần.
- **Lag 14 (2 tuần)**: EDA Tuần 2 đã đo và xác nhận đây là lag có correlation âm mạnh nhất với doanh số.
- **Lag 30+**: Quá xa, tác động đã bị pha loãng bởi nhiều yếu tố khác.

**Tại sao đây KHÔNG phải data leakage?** Vì khi dự báo ngày hôm nay (t), chúng ta hoàn toàn *đã biết* giá dầu của 7 hay 14 ngày trước đó — đó là dữ liệu lịch sử thực tế.

---

#### Bước 4: Rolling Mean 28 ngày

```python
oil["oil_price_rolling_mean_28"] = (
    oil["oil_price"].rolling(window=28, min_periods=1).mean()
)
```

**`rolling(window=28).mean()` là gì?** Với mỗi ngày, tính trung bình của 28 ngày *liền trước* (bao gồm ngày đó).

**Ví dụ trực quan:**
```
Ngày 28: trung bình của ngày 1 đến ngày 28
Ngày 29: trung bình của ngày 2 đến ngày 29
Ngày 30: trung bình của ngày 3 đến ngày 30
```

**Tại sao cần rolling mean?**
- Giá dầu hàng ngày có nhiều biến động "nhiễu" ngắn hạn.
- Rolling mean 28 ngày "làm mịn" nhiễu và phản ánh **xu hướng thực sự** của giá dầu trong 1 tháng qua.
- Model học được: "giá dầu đang trong giai đoạn cao hay thấp" — quan trọng hơn là "hôm qua giá dầu tăng hay giảm".

**`min_periods=1`**: Cho phép tính trung bình dù chưa đủ 28 ngày (ví dụ ngày thứ 3 chỉ có 3 điểm dữ liệu). Nếu không có tham số này, 27 ngày đầu sẽ bị NaN.

---

#### Bước 5: Percentage Change

```python
oil["oil_price_change_pct"] = oil["oil_price"].pct_change(periods=7)
```

**`pct_change(periods=7)` là gì?** Tính % thay đổi so với 7 ngày trước.

**Công thức:** `(giá_hôm_nay - giá_7_ngày_trước) / giá_7_ngày_trước`

**Ví dụ:**
```
Ngày 1:  $100
Ngày 8:  $85  → change_pct = (85-100)/100 = -0.15 = -15%
```

**Tại sao cần feature này?**  
Nó capture được **"cú sốc"** (shock) — điều mà giá tuyệt đối không thể hiện. Giá dầu giảm từ $100 xuống $85 trong 1 tuần (-15%) tạo ra phản ứng tâm lý và kinh tế rất khác so với cùng mức giá $85 nhưng đã ổn định 3 tháng.

---

#### Bước 6: Merge vào DataFrame chính

```python
df = df.merge(oil[oil_cols], on="date", how="left")
```

**`left merge` là gì?** Giữ nguyên tất cả hàng của DataFrame chính (df), tìm và ghép thông tin oil tương ứng theo ngày. Nếu không có ngày khớp, điền NaN.

**Tại sao dùng left thay vì inner?** Để đảm bảo không mất dữ liệu train — mỗi dòng trong train.csv đều được giữ lại.

---

### 4.2 Hàm `add_store_encoding()` — Encode thông tin cửa hàng

```python
def add_store_encoding(df, stores_df):
```

---

#### Label Encoding cho `store_type`

```python
type_mapping = {t: i for i, t in enumerate(sorted(stores["type"].unique()))}
stores["store_type_encoded"] = stores["type"].map(type_mapping)
```

**Label Encoding là gì?** Chuyển mỗi giá trị text thành một số nguyên.

**Kết quả:**
```
A → 0
B → 1
C → 2
D → 3
E → 4
```

**Tại sao dùng `sorted()`?** Để mapping luôn nhất quán: A=0, B=1... bất kể thứ tự xuất hiện trong dữ liệu.

**Tại sao Label Encoding đủ cho `store_type`?** Vì chỉ có 5 loại (A-E). LightGBM xử lý tốt biến số với ít giá trị duy nhất. Nếu có 100+ loại thì cần cân nhắc cách khác.

---

#### Frequency Encoding cho `city` và `state`

```python
city_freq  = stores["city"].value_counts(normalize=True).to_dict()
state_freq = stores["state"].value_counts(normalize=True).to_dict()

stores["city_freq"]  = stores["city"].map(city_freq)
stores["state_freq"] = stores["state"].map(state_freq)
```

**Frequency Encoding là gì?** Thay mỗi giá trị text bằng **tần suất xuất hiện** của nó trong tập dữ liệu (số từ 0 đến 1).

**Ví dụ với 54 cửa hàng:**
```
Quito có 12/54 cửa hàng → city_freq = 12/54 ≈ 0.222
Guayaquil có 8/54 cửa hàng → city_freq = 8/54 ≈ 0.148
Manta có 2/54 cửa hàng → city_freq = 2/54 ≈ 0.037
```

**Tại sao không dùng Label Encoding cho city?** City có 18 giá trị — nếu encode thành 0-17, model có thể hiểu nhầm "thành phố số 10 > thành phố số 5" (thứ tự số) trong khi thực tế không có ý nghĩa đó.

**Tại sao không dùng One-Hot Encoding?** One-hot sẽ tạo ra 18 cột mới cho city và nhiều cột cho state — với 3 triệu dòng dữ liệu, điều này rất tốn bộ nhớ và không cần thiết.

**Frequency Encoding giải quyết cả hai vấn đề:** Chỉ 1 cột số, không có thứ tự giả, và còn mang thêm thông tin "thành phố này lớn hay nhỏ".

**`normalize=True`**: Trả về tỷ lệ phần trăm (0-1) thay vì số đếm tuyệt đối — giúp model dễ học hơn.

---

#### Giữ nguyên `cluster`

```python
# cluster đã là số (1-17) → giữ nguyên, không encode thêm
```

`cluster` trong stores.csv đã là số nguyên từ 1-17. LightGBM đọc và xử lý trực tiếp được, không cần biến đổi thêm.

---

#### Merge vào DataFrame chính

```python
df = df.merge(stores[store_cols], on="store_nbr", how="left")
```

Tương tự như merge oil, nhưng merge theo `store_nbr` thay vì `date` — mỗi cửa hàng có thông tin riêng cố định theo thời gian.

---

### 4.3 Hàm `build_external_features()` — Pipeline tổng hợp

```python
def build_external_features(df, oil_df, stores_df, date_col="date"):
    df = add_oil_features(df, oil_df, date_col=date_col)
    df = add_store_encoding(df, stores_df)
    return df
```

Hàm này đơn giản là **gọi tuần tự** hai hàm ở trên. Đây là hàm người dùng sẽ dùng trong thực tế — chỉ cần gọi 1 lần, nhận về DataFrame đầy đủ features.

---

### 4.4 Danh sách tên features (Constants)

```python
OIL_FEATURE_NAMES   = ["oil_price", "oil_price_lag_7", ...]
STORE_FEATURE_NAMES = ["cluster", "store_type_encoded", ...]
ALL_EXTERNAL_FEATURE_NAMES = OIL_FEATURE_NAMES + STORE_FEATURE_NAMES
```

Các hằng số này được định nghĩa để các file khác trong project (ví dụ file modeling) có thể **import và dùng trực tiếp** — không cần gõ lại tên từng cột, tránh lỗi typo.

**Cách dùng ở bước modeling sau:**
```python
from features.feature_external import ALL_EXTERNAL_FEATURE_NAMES
X = train[ALL_EXTERNAL_FEATURE_NAMES]
```

---

## 5. Tóm tắt toàn bộ features được tạo ra

### Oil Features (5 features)

| Tên Feature | Ý nghĩa | Lý do cần |
|---|---|---|
| `oil_price` | Giá dầu gốc (đã ffill) | Thông tin cơ bản nhất |
| `oil_price_lag_7` | Giá dầu 1 tuần trước | Tác động ngắn hạn có độ trễ |
| `oil_price_lag_14` | Giá dầu 2 tuần trước | Lag tốt nhất theo EDA |
| `oil_price_rolling_mean_28` | Trung bình 28 ngày | Xu hướng dài hạn, giảm nhiễu |
| `oil_price_change_pct` | % thay đổi so với tuần trước | Capture cú sốc bất ngờ |

### Store Features (4 features)

| Tên Feature | Cột gốc | Phương pháp | Ý nghĩa |
|---|---|---|---|
| `store_type_encoded` | `type` (A-E) | Label Encoding | Phân loại cửa hàng |
| `cluster` | `cluster` (1-17) | Giữ nguyên | Nhóm cửa hàng theo chiến lược |
| `city_freq` | `city` | Frequency Encoding | Quy mô thành phố |
| `state_freq` | `state` | Frequency Encoding | Quy mô tỉnh/bang |

---

## 6. Cách dùng file này trong project

```python
import pandas as pd
from features.feature_external import build_external_features, ALL_EXTERNAL_FEATURE_NAMES

# Đọc dữ liệu
train  = pd.read_csv("data/train.csv")
oil    = pd.read_csv("data/oil.csv")
stores = pd.read_csv("data/stores.csv")

# Tạo features — chỉ 1 dòng
train = build_external_features(train, oil, stores)

# Xem kết quả
print(train[ALL_EXTERNAL_FEATURE_NAMES].head())
print(f"Số features ngoại cảnh: {len(ALL_EXTERNAL_FEATURE_NAMES)}")
# Output: Số features ngoại cảnh: 9
```

---

## 7. Vị trí trong pipeline tổng thể

```
train.csv
    │
    ▼
[feature_temporal.py]  →  thêm: year, month, day_of_week, lag_7, rolling_mean...
    │
    ▼
[feature_holiday.py]   →  thêm: is_national_holiday, holiday_type, days_to_next_holiday...
    │
    ▼
[feature_external.py]  →  thêm: oil_price_lag_14, store_type_encoded, city_freq...  ← TUẦN NÀY
    │
    ▼
[LightGBM Model]       →  học từ tất cả features → dự báo doanh số
```

File của tuần này là **mắt xích cuối cùng** của giai đoạn Feature Engineering trước khi đưa vào model.