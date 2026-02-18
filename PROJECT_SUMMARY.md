# Tóm Tắt Dự Án: Store Sales Forecasting - Corporación Favorita

> **Phiên bản:** 1.0 | **Ngày tạo:** 2026-02-18 | **Nhóm:** Topic 13

---

## 1. Tổng Quan Bài Toán

### 1.1 Bối Cảnh Doanh Nghiệp

**Corporación Favorita** là chuỗi siêu thị lớn tại Ecuador, vận hành **54 cửa hàng** trải rộng khắp **22 thành phố** trong **16 tỉnh/thành**. Doanh nghiệp này đang đối mặt với bài toán cốt lõi của bán lẻ hiện đại: **dự báo doanh số chính xác ở cấp độ cửa hàng - nhóm sản phẩm - ngày**, nhằm tối ưu hoá vận hành và lợi nhuận.

Ecuador là nền kinh tế phụ thuộc nặng vào dầu mỏ (dầu chiếm ~40% thu nhập xuất khẩu), khiến sức mua người tiêu dùng bị ảnh hưởng trực tiếp bởi biến động giá dầu toàn cầu. Giai đoạn 2015–2016 chứng kiến cuộc khủng hoảng giá dầu nghiêm trọng (giảm 76% từ $110 xuống $26/thùng), gây tác động mạnh đến hành vi mua sắm và doanh thu bán lẻ.

### 1.2 Mục Tiêu Dự Án

Xây dựng mô hình dự báo doanh số **15 ngày tới** cho mỗi tổ hợp `(cửa hàng × nhóm sản phẩm)`, với:
- **Metric chính:** RMSLE (Root Mean Squared Logarithmic Error) — phạt đồng đều sai số tương đối ở mọi mức doanh số
- **Quy mô dự báo:** 54 stores × 33 product families = 1,782 chuỗi thời gian song song
- **Thời gian dự báo:** Tháng 8–9/2017 (dựa trên dữ liệu đến 15/8/2017)

### 1.3 Tầm Quan Trọng Kinh Doanh

| Ứng dụng | Tác động |
|----------|---------|
| Quản lý tồn kho | Giảm hết hàng (stockout) và tồn kho dư thừa |
| Lên kế hoạch khuyến mãi | Đo ROI của từng chiến dịch giảm giá |
| Phân bổ nguồn lực | Lập lịch nhân sự theo traffic dự báo |
| Mở rộng thị trường | Xác định khu vực còn tiềm năng phát triển |

---

## 2. Dữ Liệu và Cấu Trúc Dataset

### 2.1 Tổng Quan Các File Dữ Liệu

| File | Số dòng | Số cột | Khoảng thời gian | Kích thước |
|------|---------|--------|-------------------|-----------|
| `train.csv` | 3,000,888 | 6 | 2013-01-01 → 2017-08-15 | 137.4 MB |
| `test.csv` | ~28,512 | 5 | 2017-08-16 → 2017-08-31 | ~2 MB |
| `oil.csv` | 1,218 | 2 | 2013-01-01 → 2017-08-31 | ~19 KB |
| `stores.csv` | 54 | 6 | (tĩnh, không có thời gian) | ~3 KB |
| `transactions.csv` | 83,488 | 3 | 2013-01-01 → 2017-08-15 | ~2 MB |
| `holidays_events.csv` | 350 | 6 | 2012-03-02 → 2017-12-26 | ~14 KB |

### 2.2 Schema Chi Tiết

#### train.csv — Dữ liệu huấn luyện chính
```
Cấu trúc: Panel 3 chiều = Cửa hàng (54) × Nhóm hàng (33) × Ngày (~1,685)
```

| Cột | Kiểu | Mô tả | Phạm vi |
|-----|------|--------|---------|
| `id` | int64 | Định danh dòng | 0 – 3,000,887 |
| `date` | datetime | Ngày giao dịch | 2013-01-01 → 2017-08-15 |
| `store_nbr` | int64 | Mã cửa hàng | 1 – 54 |
| `family` | object | Nhóm sản phẩm | 33 categories |
| `sales` | float64 | Doanh số (đơn vị/giá trị) | 0 – 124,717 |
| `onpromotion` | int64 | Số SKU đang khuyến mãi | 0 – 741 |

#### stores.csv — Metadata cửa hàng
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| `store_nbr` | int64 | Mã cửa hàng (primary key) |
| `city` | object | Thành phố (22 thành phố) |
| `state` | object | Tỉnh/thành (16 tỉnh) |
| `type` | object | Loại cửa hàng: A, B, C, D, E |
| `cluster` | int64 | Nhóm phân đoạn (1–17) |

#### oil.csv — Giá dầu thô WTI
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| `date` | datetime | Ngày giao dịch |
| `dcoilwtico` | float64 | Giá dầu WTI (USD/thùng) |

#### holidays_events.csv — Ngày lễ và sự kiện Ecuador
| Cột | Kiểu | Mô tả |
|-----|------|--------|
| `date` | datetime | Ngày diễn ra |
| `type` | object | Loại: Holiday, Event, Bridge, Transfer, Work Day |
| `locale` | object | Phạm vi: National, Regional, Local |
| `locale_name` | object | Tên địa điểm (24 vị trí) |
| `description` | object | Tên sự kiện (103 mô tả) |
| `transferred` | bool | Nghỉ bù sang ngày khác |

### 2.3 Thống Kê Cơ Bản

| Chỉ số | Giá trị |
|--------|---------|
| Tổng doanh số (2013–2017) | ~$1.07 tỷ |
| CAGR doanh số | 8.45%/năm |
| Trung bình doanh số/record | $357.78 |
| Trung vị doanh số/record | $11.00 |
| Tỷ lệ doanh số = 0 | 31.30% (939,130 records) |
| Doanh số ngày cao nhất (trung bình) | $808,565 (tháng 12) |
| Doanh số ngày thấp nhất (trung bình) | $571,895 (tháng 2) |

---

## 3. Phát Hiện Chính Từ Phân Tích Khám Phá (EDA)

### 3.1 Xu Hướng Tổng Thể

#### Tăng Trưởng Doanh Số Theo Năm

| Năm | Tổng Doanh Số | Tăng Trưởng YoY |
|-----|--------------|-----------------|
| 2013 | $140.4M | — |
| 2014 | $209.5M | **+49.2%** |
| 2015 | $240.9M | +15.0% |
| 2016 | $288.7M | +19.8% |
| 2017 | $194.2M | (8 tháng) |

> **Lưu ý:** Tốc độ tăng 49.2% năm 2014 có thể phản ánh mở rộng mạng lưới cửa hàng, không phải tăng trưởng hữu cơ thuần túy.

#### Mùa Vụ Theo Thời Gian

- **Tháng đỉnh cao:** Tháng 12 (avg $808,565/ngày) — Giáng sinh và Năm mới
- **Tháng thấp điểm:** Tháng 2 (avg $571,895/ngày) — sau Tết Dương lịch
- **Quý tốt nhất:** Q4 (mùa lễ hội)
- **Ngày tốt nhất trong tuần:** Chủ nhật ($825,218/ngày trung bình)
- **Ngày thấp nhất:** Thứ Năm ($505,269/ngày trung bình)
- **Chênh lệch Thứ 7 vs Thứ 5:** +26% (1,953 vs 1,550 giao dịch/cửa hàng)

#### Phân Rã Chuỗi Thời Gian (STL Decomposition)

Áp dụng STL với `period=365`, kết quả:
- **Trend:** Đường đi lên đều đặn → doanh nghiệp tăng trưởng ổn định
- **Seasonality:** Dao động sin đều theo tuần rất mạnh → xác nhận weekly seasonality
- **ACF peaks:** Lag 7, 14, 21 — doanh số có "trí nhớ" tuần
- **PACF:** Lag 1 và Lag 7 là 2 yếu tố trực tiếp mạnh nhất
- **Yếu tố dự báo mạnh nhất:** `sales_lag_365` (doanh số cùng kỳ năm ngoái)

#### Sự Kiện Bất Thường (Outliers)

| Ngày | Sự kiện | Tác động |
|------|---------|---------|
| 2013-01-01 | Tết Dương lịch | Doanh số chỉ $2,512 (giảm 99%) |
| 2016-04-16 | **Động đất Ecuador** | Spike panic buying, kéo dài ~2 tuần |
| 2015-12-24 | Giáng sinh 2015 | 171,169 giao dịch (gấp 2.03× bình thường) |

---

### 3.2 Yếu Tố Bên Ngoài (Giá Dầu, Ngày Lễ, Sự Kiện)

#### Giá Dầu WTI

| Chỉ số | Giá trị |
|--------|---------|
| Phạm vi giá | $26.19 – $110.62/thùng |
| Trung bình | $67.71/thùng |
| Trung vị | $53.19/thùng |
| Volatility (Std/Mean) | 38% — cực kỳ cao |
| Dữ liệu thiếu | 43 ngày (3.5%) — cuối tuần/ngày lễ thị trường |

**Các giai đoạn dầu:**

| Giai đoạn | Mức giá | Bối cảnh |
|-----------|---------|---------|
| 2013–2014 | $90–$110/thùng | Boom khai thác |
| 2015–2016 | $26–$50/thùng | **Khủng hoảng** (giảm 76%) |
| 2017 | $45–$55/thùng | Phục hồi một phần |

**Kết luận về tương quan dầu–doanh số:**
- Tương quan thô: ~-0.5 (âm) — nhưng đây là **tương quan giả** (spurious) do xu hướng dài hạn đối nghịch
- Lag 7/30 ngày: tương quan yếu, không có giá trị dự báo đáng kể
- **Khuyến nghị:** Dùng rolling mean 30 ngày như biến phụ trợ, không đặt trọng số cao

#### Ngày Lễ và Sự Kiện

**Tổng quan:**
- **350 sự kiện** trên 312 ngày duy nhất (5 năm)
- Trung bình **70 sự kiện/năm** → khoảng **17% số ngày** trong năm có sự kiện
- **49.7% quốc gia** (ảnh hưởng tất cả 54 cửa hàng)
- **50.3% khu vực/địa phương** (chỉ ảnh hưởng một số cửa hàng)

**Phân loại tác động:**

| Loại ngày lễ | Tác động doanh số | Ghi chú |
|-------------|------------------|---------|
| Bridge (Ngày cầu) | **Cao nhất** | Ngày kẹp giữa lễ và cuối tuần |
| Transfer (Nghỉ bù) | Cao | Chỉ 12 ngày (3.4%) |
| Pre-holiday (Trước 1-2 ngày) | Cao — **stockpiling effect** | Người dân mua trước khi đóng cửa |
| Holiday day | Thấp — gần bằng 0 | Cửa hàng đóng hoặc giảm giờ |
| Post-holiday (Sau 1-2 ngày) | Thấp — hồi phục chậm | Tiêu thụ hàng đã tích |

**Sự kiện nổi bật:**
- **Carnaval:** Xuất hiện 10 lần (nhiều nhất) — lễ hội đa ngày, cần feature riêng
- **Giáng sinh 23-24/12:** Đỉnh traffic mọi năm (2× bình thường)
- **25/12:** Tất cả cửa hàng đóng cửa hoàn toàn (không có record)

---

### 3.3 Phân Tích Theo Sản Phẩm (Product Family)

#### Phân Phối Doanh Thu Theo Nhóm Hàng (Top 10)

| Nhóm hàng | Tổng Doanh Số | % Tổng | % Khuyến Mãi |
|-----------|--------------|--------|-------------|
| GROCERY I | $343.5M | **32.0%** | 24.5% |
| BEVERAGES | $217.0M | **20.2%** | 11.6% |
| PRODUCE | $122.7M | **11.4%** | 14.3% |
| CLEANING | $97.5M | 9.1% | 8.5% |
| DAIRY | $64.5M | 6.0% | 9.3% |
| BREAD/BAKERY | $42.1M | 3.9% | — |
| POULTRY | $31.9M | 3.0% | — |
| MEATS | $31.1M | 2.9% | — |
| PERSONAL CARE | $24.6M | 2.3% | — |
| DELI | $24.1M | 2.2% | — |

> **Quy luật Pareto:** Top 3 nhóm (GROCERY I, BEVERAGES, PRODUCE) chiếm **63.6%** tổng doanh thu.

#### Đặc Điểm Từng Nhóm Hàng

| Nhóm | Đặc tính | Chiến lược mô hình |
|------|---------|-------------------|
| GROCERY I, BEVERAGES | Ổn định, daily necessity, nhạy với promo | Ưu tiên tối ưu hóa |
| PRODUCE, MEATS | Biến động cao, phụ thuộc ngày nhập hàng | Cần lag features mạnh |
| SCHOOL & OFFICE SUPPLIES | **Spike tháng 8–9** (mùa tựu trường Sierra) | Feature `is_school_season` |
| BREAD/BAKERY | Ổn định, ít biến động | Mô hình đơn giản |
| AUTOMOTIVE, BOOKS | Thưa thớt, zero-rate cao (>50%) | Mô hình Tweedie/zero-inflated |
| LIQUOR | Đỉnh tháng 12 (Giáng sinh/Năm mới) | Seasonal feature |

#### Hiệu Quả Khuyến Mãi Theo Nhóm

- **Nhạy cảm cao** (promo lift 2-3×): GROCERY I, CLEANING, PERSONAL CARE — khách chờ giảm giá mới mua
- **Thờ ơ** (promo lift nhỏ): BREAD, AUTOMOTIVE, LIQUOR — nhu cầu không đổi khi có khuyến mãi

---

### 3.4 Phân Tích Theo Cửa Hàng

#### Phân Phối Doanh Thu Theo Cửa Hàng (Top 10)

| Cửa hàng # | Tổng Doanh Số | % Tổng | Giao Dịch TB/Ngày |
|------------|--------------|--------|------------------|
| 44 | $62.1M | 5.8% | **4,337** |
| 45 | $54.5M | 5.1% | 3,891 |
| 47 | $50.9M | 4.7% | 3,542 |
| 3 | $50.5M | 4.7% | 3,201 |
| 49 | $43.4M | 4.0% | 2,847 |
| 46 | $41.9M | 3.9% | — |
| 48 | $35.9M | 3.3% | — |
| 51 | $32.9M | 3.1% | — |
| 8 | $30.5M | 2.8% | — |
| 50 | $28.7M | 2.7% | — |

> Top 10 cửa hàng (18.5% số lượng) = **40% tổng doanh thu**

**Chênh lệch cực đoan:** Store 44 (4,337 giao dịch/ngày) so Store 26 (635 giao dịch/ngày) = **6.8× lần**

#### Phân Loại Cửa Hàng

| Tiêu chí | Phân phối |
|---------|-----------|
| **Loại (Type):** D (33.3%), E (20.4%), A (16.7%), B (14.8%), C (14.8%) | 5 loại, phân bố tương đối đều |
| **Cluster:** 17 nhóm, trung bình 3.2 cửa hàng/nhóm | Phân đoạn tinh (fine-grained) |
| **Địa lý:** Quito 22 cửa hàng (40.7%), Guayaquil 4 (7.4%) | Tập trung cao ở thủ đô |

#### Phân Tích Địa Lý

| Vùng | Đặc điểm | Ghi chú |
|------|----------|---------|
| Highland (Pichincha, Azuay...) | 60%+ số cửa hàng, nhiều Quito | Mùa tựu trường theo lịch Sierra |
| Coastal (Guayas, Manabi...) | Ít cửa hàng hơn, sales/cửa hàng cao | Lịch học khác (Costa) |

#### Cửa Hàng Mở Muộn (Dữ Liệu Thưa)

| Store | Ngày dữ liệu bắt đầu | % Dữ liệu thiếu |
|-------|---------------------|----------------|
| 52 | 2017-04-20 | 93% |
| 22 | ~2013-06 | 60% |
| 42 | ~2013-07 | 57% |
| 21 | ~2013-07 | 56% |

---

## 4. Quy Tắc Nghiệp Vụ Quan Trọng

### 4.1 Diễn Giải Doanh Số = 0

| Tình huống | Ý nghĩa | Cách xử lý |
|-----------|---------|-----------|
| Cửa hàng đóng cửa ngày lễ | Zero thật (không có khách) | Giữ nguyên + flag `is_holiday` |
| Cửa hàng chưa mở (Store 52...) | Không có dữ liệu | Mask/exclude khỏi training |
| Nhóm hàng thưa thớt (BOOKS, AUTO) | Không có giao dịch ngày đó | Giữ nguyên, dùng mô hình phù hợp |
| Hết hàng (stockout) | Nhu cầu thật nhưng không có hàng | Không thể phân biệt từ dữ liệu |

> **31.3% doanh số = 0** — không phải lỗi dữ liệu mà là đặc tính của bán lẻ thưa thớt

### 4.2 Quy Tắc Ngày Lễ Ecuador

```
Cấp quốc gia (National):  Ảnh hưởng TẤT CẢ 54 cửa hàng
Cấp tỉnh (Regional):      Ảnh hưởng cửa hàng trong tỉnh đó
Cấp thành phố (Local):    Ảnh hưởng cửa hàng trong thành phố đó
```

- **Transferred holidays:** Chỉ 12 ngày (3.4%) — đơn giản, không cần logic phức tạp
- **Pre-holiday stockpiling:** Doanh số tăng 1–2 ngày trước ngày lễ (không phải ngày lễ bản thân)
- **Bridge days (ngày cầu):** Có tác động lên doanh số MẠNH NHẤT trong tất cả loại lễ

### 4.3 Ngày Lương Ecuador (Payday Effect)

Người lao động Ecuador nhận lương vào **ngày 15** và **ngày cuối tháng** — tạo ra spike mua sắm có thể dự báo được:
```python
df['is_payday'] = df['date'].dt.day.isin([15, 30, 31]).astype(int)
# Hoặc chi tiết hơn:
df['is_mid_payday'] = (df['date'].dt.day == 15).astype(int)
df['is_end_payday'] = (df['date'].dt.is_month_end).astype(int)
```

### 4.4 Sự Kiện Động Đất 2016

- **Ngày:** 16/04/2016
- **Tác động:** Spike panic buying kéo dài ~2 tuần
- **Xử lý:** Tạo biến `is_earthquake` hoặc smooth dữ liệu đoạn này để tránh mô hình học sai quy luật bình thường

### 4.5 Mùa Tựu Trường Ecuador

- **Vùng Sierra (Highland):** Tháng 8–9 là mùa tựu trường → SCHOOL & OFFICE SUPPLIES tăng đột biến
- **Vùng Costa (Coastal):** Mùa học khác (tháng 4–5) → cần điều chỉnh riêng theo vùng

### 4.6 Xử Lý Giá Dầu Thiếu

```python
# Forward fill cho ngày cuối tuần/ngày lễ thị trường
df_oil['dcoilwtico'] = df_oil['dcoilwtico'].ffill().bfill()
# Không dùng interpolation — giá dầu có momentum, giữ nguyên giá cuối cùng là hợp lý
```

### 4.7 Merge Ngày Lễ Vào Dữ Liệu Cửa Hàng

```python
# Bắt buộc phải map địa điểm cửa hàng với locale của ngày lễ
store_locale_map = {
    'Quito': 'Pichincha',
    'Guayaquil': 'Guayas',
    'Cuenca': 'Azuay',
    # ... (hoàn thiện map cho 22 thành phố)
}
# 50.3% sự kiện là local/regional → bỏ qua sẽ gây sai số hệ thống
```

---

## 5. Kế Hoạch Feature Engineering

### 5.1 Nhóm Feature Ưu Tiên Cao (Phải Có)

#### A. Temporal Features (Thời Gian)

```python
# Trích xuất từ cột 'date'
df['day_of_week'] = df['date'].dt.dayofweek          # 0=Mon, 6=Sun
df['day_of_month'] = df['date'].dt.day               # 1-31
df['month'] = df['date'].dt.month                    # 1-12
df['year'] = df['date'].dt.year                      # 2013-2017
df['week_of_year'] = df['date'].dt.isocalendar().week
df['quarter'] = df['date'].dt.quarter                # 1-4
df['is_weekend'] = (df['date'].dt.dayofweek >= 5).astype(int)
df['is_month_start'] = df['date'].dt.is_month_start.astype(int)
df['is_month_end'] = df['date'].dt.is_month_end.astype(int)
df['is_quarter_end'] = df['date'].dt.is_quarter_end.astype(int)

# Payday effect (ngày lương Ecuador)
df['is_payday'] = df['date'].dt.day.isin([15, 30, 31]).astype(int)
df['days_to_payday'] = df['date'].dt.day.apply(
    lambda d: min(abs(d - 15), abs(d - 30)) if d <= 30 else abs(d - 30)
)
```

#### B. Lag Features (Trễ Doanh Số)

```python
# Theo nhóm store × family để tránh data leakage
lags = [1, 7, 14, 28, 365]

for lag in lags:
    df[f'sales_lag_{lag}'] = (
        df.groupby(['store_nbr', 'family'])['sales']
        .shift(lag)   # Đơn vị: ngày
    )

# sales_lag_365 là FEATURE MẠNH NHẤT (từ phân tích ACF/tương quan)
```

#### C. Rolling Window Features

```python
windows = [7, 14, 28]
for w in windows:
    grouped = df.groupby(['store_nbr', 'family'])['sales']
    df[f'sales_roll_mean_{w}'] = grouped.shift(1).rolling(w).mean()
    df[f'sales_roll_std_{w}'] = grouped.shift(1).rolling(w).std()
    df[f'sales_roll_max_{w}'] = grouped.shift(1).rolling(w).max()

# QUAN TRỌNG: luôn shift(1) trước rolling để tránh data leakage
```

#### D. Holiday Features

```python
# Binary flags
df['is_holiday'] = df['holiday_type'].notna().astype(int)
df['is_national_holiday'] = (df['locale'] == 'National').astype(int)
df['is_regional_holiday'] = (df['locale'] == 'Regional').astype(int)
df['is_transferred'] = df['transferred'].astype(int)

# One-hot encode holiday type
holiday_dummies = pd.get_dummies(df['holiday_type'], prefix='htype')
df = pd.concat([df, holiday_dummies], axis=1)

# Halo effect — quan trọng nhất
df['days_to_next_holiday'] = ...   # Đếm ngược đến ngày lễ tiếp theo
df['days_after_last_holiday'] = ...  # Đếm từ ngày lễ gần nhất
df['is_1day_before_holiday'] = (df['days_to_next_holiday'] == 1).astype(int)
df['is_2day_before_holiday'] = (df['days_to_next_holiday'] == 2).astype(int)
```

### 5.2 Nhóm Feature Ưu Tiên Trung Bình

#### E. Sự Kiện Đặc Biệt

```python
# Động đất 2016
df['is_earthquake'] = (
    (df['date'] >= '2016-04-16') & (df['date'] <= '2016-04-30')
).astype(int)

# Mùa tựu trường (Sierra)
df['is_school_season'] = df['month'].isin([8, 9]).astype(int)

# Carnaval (tra cứu từ holidays_events.csv)
carnaval_dates = df_holidays[df_holidays['description'] == 'Carnaval']['date']
df['is_carnaval'] = df['date'].isin(carnaval_dates).astype(int)

# Christmas Eve / Giáng sinh
df['is_christmas_eve'] = (
    (df['date'].dt.month == 12) & (df['date'].dt.day == 24)
).astype(int)
```

#### F. Oil Price Features

```python
# Giá dầu cơ bản (sau imputation)
df['oil_price'] = df['dcoilwtico']

# Rolling averages (smooth volatility)
df['oil_ma_7'] = df['dcoilwtico'].rolling(7).mean()
df['oil_ma_30'] = df['dcoilwtico'].rolling(30).mean()  # Khuyến nghị dùng cái này

# Regime flags
df['is_oil_crash'] = (df['dcoilwtico'] < 40).astype(int)   # 2015-2016
df['is_oil_boom'] = (df['dcoilwtico'] > 90).astype(int)    # 2013-2014
```

#### G. Transaction Features

```python
# Lag từ transactions.csv (store traffic)
df['trans_lag_1'] = df.groupby('store_nbr')['transactions'].shift(1)
df['trans_lag_7'] = df.groupby('store_nbr')['transactions'].shift(7)
df['trans_roll_7'] = (
    df.groupby('store_nbr')['transactions']
    .shift(1).rolling(7).mean()
)

# Chuẩn hóa theo cửa hàng (z-score per store)
store_stats = df.groupby('store_nbr')['transactions'].agg(['mean', 'std'])
df = df.merge(store_stats, on='store_nbr')
df['trans_zscore'] = (df['transactions'] - df['mean']) / df['std']
```

### 5.3 Nhóm Feature Ưu Tiên Thấp

#### H. Store & Product Categorical Features

```python
# Store metadata (join từ stores.csv)
# One-hot encoding cho tree-based models
store_dummies = pd.get_dummies(df['type'], prefix='store_type')
df = pd.concat([df, store_dummies], axis=1)

# Cluster encoding
df['cluster'] = df['cluster'].astype('category')

# Geographic features
df['is_quito'] = (df['city'] == 'Quito').astype(int)
df['is_coastal'] = df['state'].isin([
    'Guayas', 'Manabí', 'El Oro', 'Esmeraldas', 'Santa Elena'
]).astype(int)

# Target encoding cho family (dùng cross-validation để tránh leakage)
# TE = mean(sales) của family trong training fold
```

#### I. Interaction Features

```python
# Promotion × Weekend (khuếch đại hiệu ứng)
df['promo_weekend'] = df['onpromotion'] * df['is_weekend']

# Holiday × Region (local holiday chỉ ảnh hưởng vùng đó)
df['local_holiday_coastal'] = df['is_regional_holiday'] * df['is_coastal']

# Store type × Season
df['typeA_december'] = df['store_type_A'] * (df['month'] == 12).astype(int)
```

### 5.4 Lưu Ý Kỹ Thuật Quan Trọng

| Vấn đề | Nguy cơ | Giải pháp |
|--------|---------|-----------|
| **Data leakage** | Dùng dữ liệu tương lai trong training | Luôn `shift(1)` trước khi rolling/lag |
| **Sparsity 31%** | Mô hình bias về 0 | Dùng RMSLE (log transform tự động xử lý) |
| **Store 52 mở muộn** | Chuỗi toàn 0 dài gây nhiễu | Mask pre-opening period |
| **Time-based split** | Không được random shuffle | Split: Train đến 2016-12, Valid 2017-01 đến 2017-07 |
| **Moving Average cho SCHOOL** | Sẽ san phẳng spike tháng 8-9 | Không dùng MA cho nhóm này |
| **Oil lag tối ưu** | Chưa xác định | Test lag 0, 7, 14, 30; kinh nghiệm: 30 ngày |

---

## 6. Kế Hoạch Xây Dựng Mô Hình

### 6.1 Chiến Lược Tổng Thể

```
Approach: Global Panel Model (một mô hình cho tất cả store-family)
          + Store-level embeddings/fixed effects
          + Time-based cross-validation
```

**Lý do chọn global model:**
- 1,782 chuỗi thời gian riêng lẻ → không đủ data cho mô hình riêng từng chuỗi
- LightGBM xử lý tốt dữ liệu panel với store_nbr/family làm categorical features
- Sharing information giữa stores/families giúp học patterns tốt hơn

**Validation Strategy:**
```
Train:      2013-01-01 → 2016-12-31 (4 năm)
Validation: 2017-01-01 → 2017-07-31 (7 tháng)
Test:       2017-08-16 → 2017-08-31 (test set Kaggle)

Không được dùng random split — bắt buộc time-based split!
```

### 6.2 Phase A — Baseline Models (Ngày 1–2)

**Mục tiêu:** Đặt mức baseline RMSLE để tất cả mô hình sau phải vượt qua.

| Model | Mô tả | Implementation |
|-------|--------|---------------|
| Naive Seasonal | Sales hôm nay = Sales cùng ngày tuần trước | `pred = sales_lag_7` |
| Historical Mean | Trung bình lịch sử theo store×family×dow | `groupby mean` |
| Exponential Smoothing | Trọng số giảm dần cho dữ liệu cũ | `statsmodels.tsa.holtwinters` |

```python
# Naive Baseline
def naive_forecast(df):
    df['pred'] = df.groupby(['store_nbr', 'family'])['sales'].shift(7)
    return df

# Tính RMSLE baseline
from sklearn.metrics import mean_squared_log_error
rmsle = np.sqrt(mean_squared_log_error(y_true, y_pred))
print(f"Baseline RMSLE: {rmsle:.4f}")
```

**Mục tiêu:** Hiểu baseline để target cải thiện ít nhất 20-30%.

### 6.3 Phase B — Classical Time Series (Ngày 2–3)

**Chọn chuỗi để test ARIMA/SARIMA:**
- Store 44 × GROCERY I (high volume, regular pattern)
- Store 44 × BEVERAGES (high volume, seasonal)
- Store 26 × PRODUCE (low volume, noisy)

**Lý do giới hạn:** SARIMA không scale được với 1,782 chuỗi → chỉ dùng để học và benchmark.

```python
from statsmodels.tsa.statespace.sarimax import SARIMAX

# SARIMA(p,d,q)(P,D,Q,s) với s=7 (weekly seasonality)
model = SARIMAX(series, order=(1,1,1), seasonal_order=(1,1,1,7))
result = model.fit()
forecast = result.forecast(steps=15)
```

### 6.4 Phase C — LightGBM (Trục Chính, Ngày 3–6)

**Thiết lập training:**

```python
import lightgbm as lgb

# Cấu hình cơ bản
params = {
    'objective': 'regression',          # hoặc 'tweedie' cho zero-inflation
    'metric': 'rmse',
    'num_leaves': 127,
    'learning_rate': 0.05,
    'feature_fraction': 0.8,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'min_child_samples': 50,
    'n_estimators': 1000,
    'early_stopping_rounds': 50,
    'verbose': -1
}

# Features
feature_cols = [
    # Temporal
    'day_of_week', 'day_of_month', 'month', 'year', 'is_weekend',
    'is_payday', 'days_to_payday',
    # Lags
    'sales_lag_1', 'sales_lag_7', 'sales_lag_14', 'sales_lag_28', 'sales_lag_365',
    # Rolling
    'sales_roll_mean_7', 'sales_roll_std_7', 'sales_roll_mean_28',
    # Holiday
    'is_holiday', 'is_national_holiday', 'days_to_next_holiday',
    'is_1day_before_holiday', 'is_2day_before_holiday',
    'htype_Bridge', 'htype_Transfer', 'htype_Holiday',
    # Events
    'is_earthquake', 'is_school_season', 'is_carnaval',
    # Oil
    'oil_ma_30', 'is_oil_crash',
    # Store features
    'store_nbr', 'cluster', 'store_type_A', 'store_type_B', 'store_type_C',
    'store_type_D', 'store_type_E', 'is_quito', 'is_coastal',
    # Product
    'family_encoded',   # Label/target encoding
    'onpromotion',
    # Transactions
    'trans_lag_7', 'trans_roll_7'
]

# Training
train_data = lgb.Dataset(X_train[feature_cols], label=np.log1p(y_train))
valid_data = lgb.Dataset(X_valid[feature_cols], label=np.log1p(y_valid))

model = lgb.train(params, train_data, valid_sets=[valid_data])
y_pred = np.expm1(model.predict(X_test[feature_cols]))
```

**Hyperparameter Tuning:**

```python
# Optuna cho auto-tuning (ưu tiên hơn grid search)
import optuna

def objective(trial):
    params = {
        'num_leaves': trial.suggest_int('num_leaves', 31, 255),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
        'feature_fraction': trial.suggest_float('feature_fraction', 0.5, 1.0),
        'min_child_samples': trial.suggest_int('min_child_samples', 20, 100),
    }
    # cross-val và trả về RMSLE
    ...

study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=50)
```

### 6.5 Phase D — XGBoost & Ensemble (Ngày 6–7)

```python
import xgboost as xgb

# XGBoost với cùng features
xgb_model = xgb.XGBRegressor(
    objective='reg:squarederror',
    n_estimators=1000,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    early_stopping_rounds=50
)

# Train với log1p target
xgb_model.fit(X_train, np.log1p(y_train),
              eval_set=[(X_valid, np.log1p(y_valid))])
xgb_pred = np.expm1(xgb_model.predict(X_test))

# Ensemble: Weighted Average
lgb_weight = 0.6
xgb_weight = 0.4
final_pred = lgb_weight * lgb_pred + xgb_weight * xgb_pred
```

### 6.6 Phân Chia Công Việc Nhóm

| Thành viên | Nhiệm vụ chính | Deliverable |
|-----------|----------------|-------------|
| **Thanh** | EDA tổng thể + Feature Engineering temporal/lag | `feature_engineering.py` |
| **Hai** | Phân tích oil & holidays + External features | `external_features.py` |
| **Lan** | Transactions analysis + Store traffic features | `transaction_features.py` |
| **Han** | Store analysis + Categorical encoding | `store_features.py` |
| **Trung** | Holiday mapping + Model building LightGBM | `lgbm_model.py` |
| **All** | Review baseline, tuning, ensemble | `final_submission.csv` |

---

## 7. Timeline Thực Hiện

| Ngày | Phase | Công việc | Người phụ trách | Deliverable |
|------|-------|-----------|----------------|-------------|
| **Ngày 1** | Feature Prep | Merge tất cả datasets, xử lý missing | All | `merged_train.parquet` |
| **Ngày 1** | Feature Prep | Tạo temporal features | Thanh | `temporal_features.py` |
| **Ngày 2** | Baseline | Naive + Historical Mean | Hai | Baseline RMSLE score |
| **Ngày 2** | Feature Eng | Lag/Rolling features | Thanh | `lag_features.py` |
| **Ngày 3** | Feature Eng | Holiday & event features | Trung + Lan | `holiday_features.py` |
| **Ngày 3** | Classical TS | SARIMA trên 3 chuỗi chọn | Hai | SARIMA benchmark |
| **Ngày 4** | ML Model | LightGBM v1 + validation | Trung | RMSLE v1 |
| **Ngày 5** | ML Model | Feature importance + tuning | Thanh + Trung | RMSLE v2 |
| **Ngày 6** | ML Model | XGBoost training | Han | XGB RMSLE |
| **Ngày 6** | Ensemble | Weighted average | All | Ensemble RMSLE |
| **Ngày 7** | Submission | Final predictions + submit | All | `submission.csv` |

---

## 8. Metric Đánh Giá và Mục Tiêu

### 8.1 RMSLE — Root Mean Squared Logarithmic Error

$$\text{RMSLE} = \sqrt{\frac{1}{n} \sum_{i=1}^{n} \left(\log(1 + \hat{y}_i) - \log(1 + y_i)\right)^2}$$

**Ưu điểm của RMSLE:**
- Phạt sai số **tương đối** đồng đều — sai 50% ở $100 bị phạt tương đương sai 50% ở $100,000
- Phù hợp với dữ liệu bán lẻ có phân phối skewed lớn
- Xử lý doanh số = 0 thông qua log(1+x) → không bị undefined

```python
from sklearn.metrics import mean_squared_log_error

def rmsle(y_true, y_pred):
    # Clip predictions tại 0 (không dự báo âm)
    y_pred = np.clip(y_pred, 0, None)
    return np.sqrt(mean_squared_log_error(y_true, y_pred))
```

### 8.2 Mục Tiêu Score

| Level | RMSLE | Ý nghĩa |
|-------|-------|---------|
| Baseline (Naive) | ~0.50–0.60 | Chỉ dùng sales_lag_7 |
| Target nhóm | **≤ 0.40** | LightGBM với đầy đủ features |
| Stretch goal | ≤ 0.35 | Ensemble + tuning tốt |
| Top Kaggle (lịch sử) | ~0.15–0.20 | Rất phức tạp, không thực tế |

### 8.3 Sub-metrics theo Nhóm

```python
# Đánh giá riêng cho nhóm doanh số cao (quan trọng hơn)
top_families = ['GROCERY I', 'BEVERAGES', 'PRODUCE']
top_stores = [44, 45, 47, 3, 49]

rmsle_top_fam = rmsle(y_true[mask_top_fam], y_pred[mask_top_fam])
rmsle_top_store = rmsle(y_true[mask_top_store], y_pred[mask_top_store])
# Mục tiêu: RMSLE top families < 0.30
```

---

## 9. Rủi Ro và Cách Giảm Thiểu

| Rủi ro | Mức độ | Cách giảm thiểu |
|--------|--------|----------------|
| **Data leakage từ lag features** | Cao | Luôn shift(1) trước rolling; kiểm tra feature importance |
| **Overfitting trên chuỗi dài** | Trung | Early stopping; time-based CV thay random CV |
| **Scope creep** | Trung | Focus LightGBM trước, thêm model sau |
| **Dữ liệu ngày lễ bỏ sót (local)** | Trung | Kiểm tra locale mapping đầy đủ trước khi train |
| **Store 52 mới mở** | Thấp | Mask pre-opening period; add `is_new_store` flag |
| **Tương quan giả dầu-doanh số** | Thấp | Dùng rolling mean, không raw price; kiểm tra SHAP |
| **SCHOOL spike bị san phẳng** | Thấp | Không dùng MA; kiểm tra feature importance |
| **Zero-inflation bias** | Trung | Thử `tweedie` objective trong LightGBM |

---

## 10. Kết Luận

### Điểm Mạnh Dự Án

1. **Dữ liệu chất lượng cao:** Zero missing values ở train/stores/holidays — foundation tốt
2. **Phân tích EDA sâu:** 5 notebooks chi tiết từ 5 thành viên, phủ tất cả datasets
3. **Insights rõ ràng:** Xác định được yếu tố dự báo chính (lag_365, day_of_week, holiday_halo)
4. **Business context phong phú:** Hiểu Ecuador-specific patterns (payday, earthquake, school season)

### Ưu Tiên Nhóm Cho Tuần Tới

1. **Ưu tiên #1 — Feature Engineering:** Tạo lag, rolling, holiday halo features đúng cách (không leakage)
2. **Ưu tiên #2 — Holiday Mapping:** Hoàn thiện bảng map locale cửa hàng → địa điểm ngày lễ
3. **Ưu tiên #3 — Baseline nhanh:** Chạy LightGBM v1 trong ngày 3–4 để có điểm tham chiếu
4. **Ưu tiên #4 — Validate kỹ:** Luôn check RMSLE trên validation set trước khi submit

### Yếu Tố Thành Công

- **Không rush vào model khi feature chưa tốt** — feature engineering chiếm 70% kết quả
- **sales_lag_365 là vũ khí chính** — theo phân tích ACF, dữ liệu cùng kỳ năm ngoái mạnh nhất
- **Top 3 families cần RMSLE tốt nhất** — GROCERY I, BEVERAGES, PRODUCE chiếm 64% doanh thu
- **Holiday halo effect** — dự báo 2 ngày trước ngày lễ quan trọng hơn chính ngày lễ

---

*Tài liệu này được tổng hợp từ phân tích của cả nhóm. Cập nhật lần cuối: 2026-02-18.*
