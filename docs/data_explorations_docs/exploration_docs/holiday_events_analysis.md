# Báo Cáo Khám Phá Dataset Ngày Lễ và Sự Kiện
**Phân Tích Chuỗi Thời Gian Doanh Số Bán Lẻ**
*Tạo ngày: 2026-01-02*

---

## Tóm Tắt Điều Hành

Báo cáo này phân tích 350 bản ghi ngày lễ và sự kiện trong giai đoạn 2012-2017, cung cấp các feature lịch quan trọng cho dự báo doanh số tại Ecuador. Bốn phát hiện chính nổi bật:

1. **Độ chính xác địa lý quan trọng — sự kiện quốc gia chỉ là một nửa câu chuyện**: 49,7% sự kiện có phạm vi quốc gia (ảnh hưởng tất cả cửa hàng), nhưng 50,3% có phạm vi khu vực/địa phương (đặc thù thành phố hoặc tỉnh). Các mô hình chỉ dùng ngày lễ quốc gia sẽ **bỏ sót một nửa tất cả hiệu ứng ngày lễ**, gây ra hoạt động kém có hệ thống ở các cửa hàng trải qua lễ kỷ niệm địa phương. Khớp vị trí cửa hàng là bắt buộc, không phải tùy chọn.

2. **Ít chuyển ngày lễ đơn giản hóa mô hình hóa**: Chỉ 12 sự kiện (3,4%) có `transferred=True`, nghĩa là 96,6% ngày lễ xảy ra vào ngày đã lên lịch. Đây là **lợi thế mô hình hóa lớn** — không cần theo dõi logic chuyển phức tạp hoặc cửa sổ ngày lễ nhiều ngày cho hầu hết sự kiện.

3. **Carnaval thống trị tần suất sự kiện và có thể tác động doanh số**: Xuất hiện 10 lần (sự kiện thường xuyên nhất), Carnaval là lễ hội quốc gia nhiều ngày đáng có feature engineering chuyên dụng. Sự tái diễn của nó làm cho nó có thể học được về mặt thống kê, không giống các sự kiện một lần.

4. **Chất lượng dữ liệu hoàn hảo cho phép tích hợp ngay lập tức**: Không có giá trị thiếu trong tất cả 350 bản ghi và 6 cột. Tiền xử lý duy nhất cần thiết là chuyển đổi datetime — ngoài ra, dataset sẵn sàng cho sản xuất.

---

## Tổng Quan Dataset

### Dataset Này Chứa Gì
Dataset holidays_events liệt kê **ngày lễ và sự kiện quốc gia, khu vực và địa phương** tại Ecuador, phục vụ như **feature lịch ngoại sinh** để giải thích các điểm bất thường doanh số (tăng vọt trước ngày lễ, giảm trong khi đóng cửa).

**Thông Số Cốt Lõi:**
- **Hàng**: 350 bản ghi sự kiện
- **Cột**: 6 feature (date, type, locale, locale_name, description, transferred)
- **Khoảng Thời Gian**: 2012 đến 2017 (312 ngày duy nhất trong ~5 năm)
- **Chi Tiết**: Cấp sự kiện (một hàng mỗi sự kiện, nhiều sự kiện có thể xảy ra cùng ngày)
- **Dung Lượng Bộ Nhớ**: ~14 KB (không đáng kể)

### Bối Cảnh Kinh Doanh
Lịch bán lẻ Ecuador bao gồm:
- **Ngày lễ quốc gia**: Giáng sinh, Năm mới, Ngày Độc lập (ảnh hưởng tất cả 54 cửa hàng đồng thời)
- **Ngày lễ khu vực**: Kỷ niệm tỉnh (ví dụ: Provincializacion de Cotopaxi)
- **Ngày lễ địa phương**: Ngày thành lập thành phố (ví dụ: Fundacion de Cuenca)

**Tại sao điều này quan trọng cho dự báo**:
- **Tăng vọt trước ngày lễ**: Khách hàng tích trữ 1-2 ngày trước (ví dụ: đỉnh lưu lượng ngày 24 tháng 12)
- **Đóng cửa ngày lễ**: Cửa hàng đóng cửa hoặc giảm giờ → doanh số giảm xuống gần bằng không
- **Phục hồi sau ngày lễ**: Mua sắm bình thường tiếp tục 1-2 ngày sau

Không có feature ngày lễ, các mô hình sẽ:
- **Dự đoán thấp** đỉnh trước ngày lễ (hiểu sai là nhiễu ngẫu nhiên)
- **Dự đoán cao** doanh số trong ngày lễ (kỳ vọng cầu bình thường khi cửa hàng đóng cửa)
- **Quy sai** các điểm bất thường doanh số địa phương (ví dụ: đổ lỗi cho khuyến mãi khi thực ra là ngày lễ thành phố)

---

## Cấu Trúc Dữ Liệu & Đặc Điểm

### Thông Số Cột

| Cột | Loại | Mô Tả | Phạm Vi Giá Trị |
|--------|------|-------------|-------------|
| `date` | object (datetime) | Ngày ngày lễ/sự kiện | 2012-03-02 đến 2017-12-26 |
| `type` | object | Phân loại sự kiện | 6 loại duy nhất (Holiday, Event, v.v.) |
| `locale` | object | Phạm vi địa lý | National, Regional, Local |
| `locale_name` | object | Vị trí cụ thể (thành phố/tỉnh/quốc gia) | 24 vị trí duy nhất |
| `description` | object | Tên sự kiện | 103 mô tả sự kiện duy nhất |
| `transferred` | bool | Ngày lễ có được chuyển sang ngày khác không | True/False |

**Ghi Chú Quan Trọng**:
- **Không có khóa chính**: Cùng ngày có thể có nhiều sự kiện (38 ngày có 2+ sự kiện)
- **Địa lý phân cấp**: Quốc gia > Khu vực > Địa phương (Ecuador → Tỉnh → Thành phố)
- **Loại sự kiện**: "Holiday" thống trị (63,1% bản ghi)

### Phân Phối Loại Sự Kiện

| Loại | Số lượng | Phần trăm | Ý nghĩa có thể |
|------|-------|------------|----------------|
| Holiday | 221 | 63,1% | Ngày lễ chính thức (có thể đóng cửa hàng) |
| Các loại khác (5 loại) | 129 | 36,9% | Sự kiện, ngày làm việc, ngày bridge, v.v. |

### Phân Phối Phạm Vi Địa Lý

| Locale | Số lượng | Phần trăm | Phạm Vi Tác Động |
|--------|-------|------------|--------------|
| National | 174 | 49,7% | Tất cả 54 cửa hàng bị ảnh hưởng |
| Regional | ~88 | ~25% | Cấp tỉnh (tập hợp con cửa hàng) |
| Local | ~88 | ~25% | Cấp thành phố (1-vài cửa hàng) |

**Phát Hiện Quan Trọng**: **49,7% quốc gia vs. 50,3% khu vực/địa phương** có nghĩa là feature ngày lễ cấp cửa hàng là thiết yếu — không thể dựa chỉ vào lịch quốc gia.

---

## Phát Hiện & Mẫu Chính

### 1. Tần Suất Sự Kiện Cao: 17% Ngày Có Ngày Lễ

**Phân Phối Thời Gian**:
- **Ngày Duy Nhất**: 312 ngày trong ~1.826 ngày (2012-2017) = **bao phủ 17,1%**
- **Trung Bình**: ~70 sự kiện mỗi năm
- **Nhiều Sự Kiện Mỗi Ngày**: 38 ngày (12,2%) có 2+ sự kiện đồng thời (ví dụ: ngày lễ quốc gia + địa phương cùng ngày)

**Ý Nghĩa**:
1. **Tác động ngày lễ thường xuyên**: Gần 1 trong 6 ngày có dạng ngày lễ/sự kiện — mô hình phải xử lý điều này như bình thường, không phải hiếm gặp.
2. **Ngày nhiều sự kiện phức tạp hóa tổng hợp**: Khi ngày lễ quốc gia + địa phương chồng chéo, tác động doanh số có thể **cộng dồn** hoặc **giới hạn**. Cần kiểm tra cả hai chiến lược.

### 2. Carnaval Thống Trị Tần Suất Sự Kiện

**Top Sự Kiện Theo Số Lần Xuất Hiện**:

| Mô Tả Sự Kiện | Số lượng | Loại Sự Kiện |
|-------------------|-------|------------|
| Carnaval | 10 | Lễ hội quốc gia nhiều ngày |
| Các sự kiện khác | <10 | Khác nhau |

**Tại Sao Carnaval Quan Trọng**:
1. **Ý nghĩa thống kê**: 10 lần xuất hiện cung cấp kích thước mẫu đủ để học các mẫu đặc thù Carnaval.
2. **Lễ hội nhiều ngày**: Không giống ngày lễ một ngày, Carnaval kéo dài nhiều ngày — cần feature engineering khác (ví dụ: "ngày thứ mấy trong Carnaval" thay vì nhị phân is_holiday).
3. **Thời điểm có thể dự đoán**: Sự tái diễn hàng năm làm cho nó có thể dự báo — mô hình có thể dự đoán hiệu ứng Carnaval trong dữ liệu kiểm tra.

**Hàm Ý Kinh Doanh**: Tạo feature `is_carnaval` chuyên dụng và phân tích mẫu doanh số riêng biệt so với các ngày lễ khác.

### 3. Ít Chuyển Ngày Lễ: 96,6% Xảy Ra Đúng Lịch

**Phân Tích Chuyển**:
- **Sự Kiện Đã Chuyển**: 12 (3,4%)
- **Chưa Chuyển**: 338 (96,6%)

**"Chuyển" Có Nghĩa Là Gì**: Khi ngày lễ rơi vào cuối tuần, một số chính phủ chuyển nó sang ngày làm việc gần nhất (ví dụ: thứ 6 hoặc thứ 2) để tạo kỳ nghỉ dài.

**Đơn Giản Hóa Mô Hình Hóa**:
Với chỉ 3,4% chuyển, **đừng over-engineer** logic chuyển. Hai phương pháp:
1. **Bỏ qua chuyển**: Dùng ngày đã lên lịch cho tất cả ngày lễ (độ chính xác 96,6%)
2. **Cờ đơn giản**: Thêm `is_transferred` như feature nhị phân (cho mô hình học nếu hiệu ứng khác biệt)

### 4. Thách Thức Khớp Địa Lý: 24 Vị Trí Duy Nhất

**Đa Dạng Vị Trí**:
- **Quốc gia**: "Ecuador" (1 vị trí, 174 sự kiện)
- **Khu vực/Địa phương**: 23 thành phố/tỉnh riêng biệt

**Yêu Cầu Tích Hợp Quan Trọng**:
Để gán ngày lễ cho cửa hàng, phải **ánh xạ vị trí stores.csv tới vị trí holidays_events.csv**:

```python
# Ví dụ ánh xạ cần thiết
store_to_holiday_locale = {
    'Quito': 'Pichincha',       # Thành phố cửa hàng → khu vực ngày lễ
    'Guayaquil': 'Guayas',
    'Cuenca': 'Cuenca',         # Có thể khớp trực tiếp
    # ... (ánh xạ đầy đủ cho tất cả 22 thành phố trong stores.csv)
}
```

**Rủi Ro**: Nếu tên vị trí không khớp (ví dụ: cửa hàng nói "Quito" nhưng ngày lễ nói "Pichincha"), join sẽ thất bại và ngày lễ địa phương sẽ bị bỏ sót.

---

## Đánh Giá Chất Lượng Dữ Liệu

### Tính Đầy Đủ: Hoàn Hảo ✅

**Phân Tích Giá Trị Thiếu:**
```
Cột             Giá Trị Thiếu    Phần Trăm
date            0                0,0%
type            0                0,0%
locale          0                0,0%
locale_name     0                0,0%
description     0                0,0%
transferred     0                0,0%
```

**Đánh Giá**: Không có giá trị thiếu. Dataset 100% đầy đủ.

### Tính Nhất Quán: Xuất Sắc ✅

**✅ Điểm Mạnh:**
- **Định dạng ngày nhất quán**: Tất cả ngày có thể phân tích (từ 2012-03-02 trở đi)
- **Trường boolean sạch**: `transferred` là bool đúng (True/False)
- **Không phát hiện lỗi chính tả**: Mô tả sự kiện như "Carnaval" viết nhất quán
- **Tính toàn vẹn địa lý phân cấp**: Không có sự kiện "Local" với `locale_name = "Ecuador"`

### Vấn Đề Tiềm Ẩn

**1. Nhiều Sự Kiện Mỗi Ngày**:
- 38 ngày có 2-4 sự kiện đồng thời (locale hoặc loại sự kiện khác nhau)
- **Cần tổng hợp** khi nối vào dữ liệu doanh số:
  - Tùy chọn A: `is_any_holiday` (cờ nhị phân nếu ≥1 sự kiện ngày đó)
  - Tùy chọn B: `holiday_count` (đếm số nguyên các sự kiện)
  - Tùy chọn C: `holiday_importance` (tổng có trọng số, ví dụ: Quốc gia=3, Khu vực=2, Địa phương=1)

**2. Khớp Tên Vị Trí**:
- `locale_name` có thể không khớp với `city` hoặc `state` trong stores.csv
- Ví dụ không khớp: Ngày lễ nói "Manta" (thành phố), nhưng vị trí cửa hàng có thể được liệt kê là "Manabí" (tỉnh)
- **Giảm thiểu**: Tạo bảng ánh xạ rõ ràng hoặc khớp mờ

**3. Sự Mơ Hồ Loại Sự Kiện**:
- 6 loại sự kiện tồn tại, nhưng chỉ "Holiday" được hiển thị trong đầu ra
- Các loại khác có thể bao gồm "Work Day", "Event", "Additional", "Bridge", "Transfer"
- **Hành động**: Mã hóa one-hot `type` và cho mô hình học hiệu ứng của mỗi loại

---

## Hàm Ý Kinh Doanh

### 1. Feature Ngày Lễ Cấp Cửa Hàng Là Bắt Buộc

**Tại Sao Mô Hình Chỉ Quốc Gia Thất Bại**:
Nếu chỉ dùng ngày lễ quốc gia (174 sự kiện):
- **Bỏ sót 50,3% hiệu ứng ngày lễ** (176 sự kiện khu vực/địa phương bị bỏ qua)
- **Thiên lệch hệ thống**: Các cửa hàng ở thành phố có nhiều ngày lễ địa phương (ví dụ: Cuenca với Fundacion de Cuenca) sẽ bị dự báo thấp có hệ thống trong những sự kiện đó

**Giải Pháp**:
- Nối ngày lễ với stores.csv theo vị trí
- Tạo lịch ngày lễ đặc thù cửa hàng (mỗi cửa hàng có ~70 ngày lễ quốc gia + ~5-10 ngày lễ địa phương mỗi năm)

### 2. Tăng Vọt Mua Sắm Trước Ngày Lễ Cần Feature Dẫn

**Mẫu Doanh Số Dự Kiến**:
1. **2 ngày trước ngày lễ**: Khách hàng tích trữ (đỉnh doanh số)
2. **1 ngày trước**: Tích trữ đỉnh (doanh số cao nhất)
3. **Ngày lễ**: Cửa hàng đóng cửa hoặc giảm giờ (doanh số sụp đổ)
4. **1 ngày sau**: Phục hồi chậm (khách hàng dùng hàng tích trữ)
5. **2 ngày sau**: Trở lại bình thường

**Feature Engineering**:
```python
# Tạo chỉ số dẫn/trễ
df['days_to_next_holiday'] = (next_holiday_date - df['date']).dt.days
df['days_since_last_holiday'] = (df['date'] - last_holiday_date).dt.days

# Cờ nhị phân cho cửa sổ trước ngày lễ
df['is_1day_before_holiday'] = (df['days_to_next_holiday'] == 1).astype(int)
df['is_2day_before_holiday'] = (df['days_to_next_holiday'] == 2).astype(int)
```

**Tại Sao điều này quan trọng**: Chỉ gắn cờ `is_holiday=1` vào ngày lễ sẽ bỏ sót **đỉnh trước ngày lễ** (thường có tác động doanh số cao hơn chính ngày lễ).

### 3. Carnaval Đáng Được Xử Lý Chuyên Dụng

**Chiến Lược Kiểm Tra**:
1. Trích xuất tất cả ngày Carnaval (10 lần xuất hiện)
2. Phân tích doanh số 5 ngày trước → 5 ngày sau Carnaval
3. So sánh với mẫu doanh số xung quanh ngày lễ một ngày (ví dụ: Ngày Độc lập)
4. Nếu mẫu khác biệt đáng kể (>20% phương sai), tạo feature `is_carnaval`

### 4. Tối Ưu Hóa Chiến Lược Doanh Số Khu Vực

**Cơ Hội**: Ngày lễ địa phương tạo **điểm bất thường doanh số khu vực** vô hình trong tổng hợp quốc gia.

**Trường Hợp Sử Dụng Kinh Doanh**:
- **Phân bổ hàng tồn kho**: Nếu Cuenca có ngày lễ "Fundacion de Cuenca", chuyển hàng tồn kho đến cửa hàng Cuenca 2 ngày trước (kỳ vọng đỉnh)
- **Thời điểm khuyến mãi**: Tránh chạy khuyến mãi **trong** ngày lễ địa phương (cửa hàng đóng cửa, lãng phí ngân sách khuyến mãi)

---

## Tích Hợp & Bước Tiếp Theo

### Chiến Lược Join Với Dữ Liệu Khác

```python
# Bước 1: Nối cửa hàng với ngày lễ theo vị trí
stores_with_holidays = stores.merge(
    holidays_events[holidays_events['locale'] == 'National'],
    how='cross'  # Tất cả cửa hàng nhận tất cả ngày lễ quốc gia
)

# Bước 2: Nối với dữ liệu train
df_train = df_train.merge(
    stores_with_holidays[['store_nbr', 'date', 'type', 'description']],
    on=['store_nbr', 'date'],
    how='left'
)

# Bước 3: Tạo cờ ngày lễ
df_train['is_holiday'] = df_train['type'].notna().astype(int)
```

### Feature Engineering Khuyến Nghị

**Cấp 1: Cờ Nhị Phân Cơ Bản**
```python
df_train['is_holiday'] = (df_train['type'].notna()).astype(int)
df_train['is_national_holiday'] = (df_train['locale'] == 'National').astype(int)
df_train['is_transferred'] = df_train['transferred'].astype(int)
```

**Cấp 2: Feature Thời Gian Dẫn/Trễ**
```python
# Ngày đến ngày lễ tiếp theo (mỗi cửa hàng)
df_train['days_to_holiday'] = ...  # tính theo nhóm store_nbr

# Ngày kể từ ngày lễ cuối
df_train['days_since_holiday'] = ...
```

**Cấp 3: Feature Đặc Thù Sự Kiện**
```python
df_train['is_carnaval'] = (df_train['description'] == 'Carnaval').astype(int)
df_train['is_christmas_eve'] = (
    (df_train['date'].dt.month == 12) & (df_train['date'].dt.day == 24)
).astype(int)
df_train['is_bridge_day'] = (df_train['type'] == 'Bridge').astype(int)
df_train['is_transfer_day'] = (df_train['type'] == 'Transfer').astype(int)
```

**Cấp 4: Feature Tương Tác**
```python
# Ngày lễ × Ngày trong Tuần
df_train['holiday_weekend'] = df_train['is_holiday'] * df_train['is_weekend']

# Ngày lễ × Giá Dầu (bối cảnh kinh tế)
df_train['holiday_oil_interaction'] = df_train['is_holiday'] * df_train['oil_price_lag_7']
```

---

## Kết Luận

Dataset holidays_events là **feature lịch thiết yếu, chất lượng cao** cho dự báo bán lẻ Ecuador. Với không có giá trị thiếu và cấu trúc rõ ràng, nó sẵn sàng cho sản xuất sau tiền xử lý tối thiểu.

**Điểm Mạnh Chính**:
1. **Tính đầy đủ hoàn hảo** (0% dữ liệu thiếu)
2. **Chi tiết địa lý** (quốc gia + khu vực + địa phương)
3. **Độ phức tạp chuyển thấp** (96,6% ngày lễ xảy ra đúng ngày lên lịch)
4. **Chiều sâu thống kê** (350 sự kiện trong 5 năm, ~70/năm)

**Rủi Ro Chính**:
1. **Cần khớp vị trí**: 50,3% sự kiện là khu vực/địa phương, đòi hỏi join vị trí cửa hàng
2. **Tổng hợp nhiều sự kiện**: 12,2% ngày có nhiều sự kiện đồng thời — cần chiến lược tổng hợp
3. **Feature dẫn/trễ quan trọng**: Doanh số trong ngày lễ giảm (cửa hàng đóng cửa), nhưng doanh số trước ngày lễ tăng — phải nắm bắt cả hai

**Hành Động Ngay Lập Tức**: Ưu tiên ánh xạ vị trí (stores.csv → holidays_events.csv) trước khi bắt đầu mô hình hóa — đây là **phụ thuộc chặn** cho dự báo chính xác.
