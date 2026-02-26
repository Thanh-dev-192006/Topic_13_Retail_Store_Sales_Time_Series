# Báo Cáo Khám Phá Dataset Giá Dầu
**Phân Tích Chuỗi Thời Gian Doanh Số Bán Lẻ**
*Tạo ngày: 2026-01-02*

---

## Tóm Tắt Điều Hành

Báo cáo này phân tích 1.218 bản ghi giá dầu thô hàng ngày (WTI) trong 4,6 năm, phục vụ như chỉ số kinh tế vĩ mô quan trọng cho dự báo bán lẻ. Ba phát hiện chính nổi bật:

1. **Biến động cao với sự thay đổi chế độ**: Giá dầu dao động từ 26,19 USD đến 110,62 USD mỗi thùng (biên độ 323%), với mean ở 67,71 USD nhưng median ở 53,19 USD — chỉ ra phân phối lệch phải do giai đoạn giá cao 2013-2014 trước vụ sụp đổ dầu 2015-2016.

2. **Dữ liệu thiếu tối thiểu, khoảng trống có cấu trúc**: Chỉ 43 giá trị thiếu (3,5%), xảy ra vào cuối tuần và ngày nghỉ thị trường khi giao dịch dầu dừng. Điền tiếp (forward-fill) duy trì tính liên tục chuỗi thời gian mà không tạo ra thiên lệch.

3. **Sự liên quan đặc thù Ecuador được khuếch đại**: Là nền kinh tế xuất khẩu dầu, lĩnh vực bán lẻ Ecuador cực kỳ nhạy cảm với biến động giá dầu — ảnh hưởng đến chi phí vận chuyển, sức mua tiêu dùng và chi tiêu chính phủ cho trợ cấp. Vụ sụp đổ 2015-2016 (giá giảm 76% từ đỉnh) có thể đã kích hoạt những thay đổi cấu trúc trong hành vi tiêu dùng.

---

## Tổng Quan Dataset

### Dataset Này Chứa Gì
Dataset dầu cung cấp giá dầu thô WTI (West Texas Intermediate) hàng ngày, phục vụ như **feature kinh tế vĩ mô ngoại sinh** để giải thích xu hướng doanh số bán lẻ ngoài các yếu tố cấp cửa hàng.

**Thông Số Cốt Lõi:**
- **Hàng**: 1.218 bản ghi hàng ngày
- **Cột**: 2 feature (date, dcoilwtico)
- **Khoảng Thời Gian**: 1 tháng 1 năm 2013 đến 31 tháng 8 năm 2017 (4,6 năm)
- **Chi Tiết**: Giá hàng ngày (ngày lịch, không chỉ ngày giao dịch)
- **Dung Lượng Bộ Nhớ**: ~19 KB (không đáng kể)

### Bối Cảnh Kinh Doanh
Nền kinh tế Ecuador phụ thuộc nặng vào dầu (xuất khẩu dầu chiếm ~40% thu nhập xuất khẩu). Biến động giá dầu trực tiếp ảnh hưởng đến:
- **Doanh thu chính phủ** → ảnh hưởng tiền lương và trợ cấp khu vực công
- **Tỷ lệ lạm phát** → ảnh hưởng sức mua tiêu dùng
- **Chi phí vận chuyển** → ảnh hưởng logistics bán lẻ và giá sản phẩm
- **Ổn định tiền tệ** → Ecuador dùng USD nhưng niềm tin kinh tế tương quan với dầu

Đối với dự báo bán lẻ, giá dầu hoạt động như **chỉ số dẫn** nắm bắt các cú sốc kinh tế vĩ mô không thấy trong dữ liệu cấp cửa hàng.

---

## Cấu Trúc Dữ Liệu & Đặc Điểm

### Thông Số Cột

| Cột | Loại | Mô Tả | Phạm Vi Giá Trị |
|--------|------|-------------|-------------|
| `date` | object (datetime) | Ngày lịch | 2013-01-01 đến 2017-08-31 |
| `dcoilwtico` | float64 | Giá dầu thô hàng ngày (USD/thùng) | 26,19 USD - 110,62 USD |

---

## Phát Hiện & Mẫu Chính

### 1. Phân Phối & Biến Động Giá Dầu

**Hồ Sơ Thống Kê:**
- **Giá Trung Bình**: 67,71 USD mỗi thùng
- **Giá Trung Vị**: 53,19 USD mỗi thùng
- **Độ Lệch Chuẩn**: 25,63 (38% mean — biến động cực cao)
- **Phạm Vi**: 26,19 USD đến 110,62 USD (chênh lệch 323% giữa min và max)

**Ý Nghĩa**:
Khoảng cách 21% giữa mean và median tiết lộ **độ lệch phải** — vài giai đoạn giá cao (2013-2014) làm tăng trung bình. Phân phối cho thấy:
- Đuôi dài của giá thấp trong vụ sụp đổ dầu 2015-2016
- Tập trung xung quanh mức 45-55 USD trong giai đoạn phục hồi (2016-2017)
- Không có giá nào theo phân phối chuẩn — kỳ vọng phá vỡ cấu trúc trong chuỗi thời gian

**Hàm Ý Mô Hình Hóa**:
1. Không giả định giá dầu dừng — dùng sai phân hoặc biến đổi log
2. Xem xét mô hình chuyển chế độ để nắm bắt các kỷ nguyên giá cao/thấp khác biệt
3. Hiệu ứng trễ có thể xảy ra (ví dụ: cú sốc giá dầu hôm nay ảnh hưởng doanh số 7-30 ngày sau)

### 2. Mẫu Giá Trị Thiếu: Cuối Tuần & Ngày Nghỉ

**Quy Mô Vấn Đề:**
- **Giá Trị Thiếu**: 43 bản ghi (3,5% dataset)
- **Nguyên Nhân**: Thị trường hợp đồng tương lai dầu đóng cửa vào cuối tuần và ngày nghỉ liên bang Mỹ

**Chiến Lược Xử Lý:**
- **Điền tiếp (ffill)**: Mang giá biết cuối cùng tiếp tục (giả định giá tồn tại cho đến khi thị trường mở lại)
- **Điền ngược (bfill)**: Cho bất kỳ NaN đầu nào

**Tại Sao Điều Này Hoạt Động:**
- Giá dầu có **động lượng** — giá mở cửa thứ 2 thường gần với giá đóng cửa thứ 6
- Phương án thay thế (nội suy) sẽ làm mịn nhân tạo biến động
- Xóa hàng sẽ gây lệch ngày với dữ liệu doanh số

**Sau Khi Điền**: Không còn giá trị thiếu.

### 3. Xu Hướng Dài Hạn: Vụ Sụp Đổ Dầu 2015-2016

**Các Giai Đoạn Chế Độ Quan Sát:**

| Giai Đoạn | Phạm Vi Giá | Bối Cảnh Kinh Tế |
|--------|-------------|------------------|
| 2013-2014 | 90-110 USD/thùng | Giai đoạn bùng nổ trước sụp đổ (sản xuất OPEC cao, cầu mạnh) |
| 2015-2016 | 26-50 USD/thùng | **Giai đoạn sụp đổ** (cung dư thừa, cầu toàn cầu yếu), 96 ngày sụp đổ (<40 USD) |
| 2017 | 45-55 USD/thùng | Phục hồi một phần (cắt giảm sản xuất OPEC) |

**Hàm Ý Kinh Doanh Cho Ecuador**:
Trong **vụ sụp đổ 2015-2016** (giá giảm 76% từ 110 USD xuống 26 USD):
- **Khủng hoảng ngân sách chính phủ**: Ecuador mất hàng tỷ trong doanh thu xuất khẩu dầu
- **Biện pháp thắt lưng buộc bụng**: Cắt giảm chi tiêu công làm giảm thu nhập khả dụng
- **Tác động bán lẻ**: Người tiêu dùng trì hoãn mua hàng lớn, chuyển sang thương hiệu giá trị

**Tại Sao Điều Này Quan Trọng Cho Dự Báo**:
- Mô hình doanh số được huấn luyện trên dữ liệu 2013-2014 sẽ thất bại trong 2015-2016 mà không có feature giá dầu
- Khuyến mãi có thể kém hiệu quả hơn trong vụ sụp đổ (người tiêu dùng thắt chặt ngân sách bất kể giảm giá)
- Sự khác biệt cấp cửa hàng có thể mở rộng (thành thị vs. nông thôn, sang trọng vs. giảm giá)

---

## Đánh Giá Chất Lượng Dữ Liệu

### Tính Đầy Đủ: Xuất Sắc ✅

**Phân Tích Giá Trị Thiếu:**
```
Cột             Giá Trị Thiếu    Phần Trăm
date            0                0,0%
dcoilwtico      43               3,5%
```

**Đánh Giá**: Chỉ 43 giá trị thiếu, tất cả được giải thích có cấu trúc (ngày không giao dịch). Sau khi điền, dataset 100% đầy đủ.

### Tính Nhất Quán: Cao ✅

**✅ Điểm Mạnh:**
- Định dạng ngày nhất quán (YYYY-MM-DD)
- Không có giá âm (min = 26,19 USD, thực tế)
- Không có điểm bất thường cực đoan (max = 110,62 USD là lịch sử hợp lý cho WTI)
- Không có ngày trùng lặp

---

## Hàm Ý Kinh Doanh

### 1. Giá Dầu Như Động Lực Doanh Số

**Tương Quan Dự Kiến**:
- **Tương quan âm** (dầu thấp hơn → doanh số cao hơn): Chi phí vận chuyển giảm → nhà bán lẻ giảm giá → cầu tăng
- **Tương quan dương** (dầu cao hơn → doanh số cao hơn): Ở Ecuador xuất khẩu dầu, giá dầu cao → doanh thu chính phủ tăng → tiền lương khu vực công tăng → chi tiêu tiêu dùng tăng

**Hiệu ứng nào thống trị?** Đối với Ecuador, **tương quan dương** có thể mạnh hơn (doanh thu dầu > tiết kiệm chi phí). Tuy nhiên EDA cho thấy tương quan trực tiếp rất yếu — sử dụng `oil_lag_365` và `oil_regime` thay thế.

### 2. Tác Động Đặc Thù Danh Mục

**Độ Nhạy Cảm Dự Kiến Theo Nhóm Sản Phẩm**:
- **Độ nhạy cao**: AUTOMOTIVE (liên quan nhiên liệu), hàng tùy ý (ELECTRONICS, HOME APPLIANCES)
- **Độ nhạy thấp**: GROCERY I, BEVERAGES (nhu cầu thiết yếu hàng ngày, không co giãn)

### 3. ROI Khuyến Mãi Trong Cú Sốc Dầu

**Giả Thuyết**: Khuyến mãi có thể kém hiệu quả hơn trong vụ sụp đổ dầu (người tiêu dùng thắt chặt ngân sách bất kể giảm giá).

**Kiểm Tra**: So sánh mức tăng khuyến mãi (tăng doanh số mỗi mặt hàng khuyến mãi) trong giai đoạn dầu cao so với dầu thấp.

---

## Tích Hợp & Bước Tiếp Theo

### Feature Engineering Khuyến Nghị

**1. Feature Trễ** (nắm bắt hiệu ứng bị trì hoãn):
```python
df_oil['oil_lag_7'] = df_oil['dcoilwtico'].shift(7)    # trễ 1 tuần
df_oil['oil_lag_30'] = df_oil['dcoilwtico'].shift(30)  # trễ 1 tháng
df_oil['oil_lag_365'] = df_oil['dcoilwtico'].shift(365) # trễ 1 năm (mạnh nhất, r≈-0,30)
```

**2. Trung Bình Trượt** (làm mịn biến động):
```python
df_oil['oil_ma_7'] = df_oil['dcoilwtico'].rolling(7).mean()
df_oil['oil_ma_30'] = df_oil['dcoilwtico'].rolling(30).mean()
```

**3. Chỉ Số Thay Đổi Giá** (nắm bắt cú sốc):
```python
df_oil['oil_pct_change'] = df_oil['dcoilwtico'].pct_change()
df_oil['oil_volatility'] = df_oil['dcoilwtico'].rolling(30).std()
```

**4. Cờ Chế Độ** (chỉ số nhị phân):
```python
df_oil['is_oil_crash'] = (df_oil['dcoilwtico'] < 40).astype(int)  # 2015-2016 (96 ngày)
df_oil['is_oil_boom'] = (df_oil['dcoilwtico'] > 90).astype(int)   # 2013-2014
# oil_regime: phân loại 3 cấp (Cao/Sụp đổ/Phục hồi)
```

### Bước Tiếp Theo Để Xác Nhận

1. **Phân Tích Tương Quan**:
   - Tổng hợp doanh số theo ngày, nối với dầu, tính tương quan
   - Kỳ vọng: tương quan trực tiếp rất yếu; lag-365 mạnh nhất (~-0,30)

2. **Tối Ưu Hóa Độ Trễ**:
   - Kiểm tra tương quan ở độ trễ 0, 7, 14, 30, 60, 365 ngày
   - Tìm độ trễ tối ưu nơi tương quan mạnh nhất → lag-365

3. **Kiểm Tra Mô Hình**:
   - Huấn luyện mô hình đường cơ sở không có giá dầu → lấy RMSE
   - Huấn luyện mô hình với giá dầu (và độ trễ) → đo cải thiện RMSE
   - Mức tăng kỳ vọng: giảm 5-15% RMSE nếu dầu có liên quan

---

## Kết Luận

Dataset giá dầu là **biến ngoại sinh quan trọng kinh doanh, chất lượng cao** cho dự báo bán lẻ Ecuador. Với chỉ 3,5% dữ liệu thiếu (dễ điền) và bao phủ 4,6 năm, nó cung cấp:

1. **Bối cảnh kinh tế vĩ mô** thiếu trong dữ liệu cấp cửa hàng
2. **Phát hiện phá vỡ cấu trúc** (vụ sụp đổ 2015-2016)
3. **Tiềm năng chỉ số dẫn** qua feature trễ (lag-365 là mạnh nhất)

**Rủi Ro Chính**:
- Overfitting vào giá dầu nếu sự thay đổi chế độ hiếm (chỉ một vụ sụp đổ lớn trong dataset)
- Hiệu ứng trễ có thể thay đổi theo nhóm sản phẩm (cần mô hình riêng biệt)
- Giá dầu một mình không thể giải thích sự không đồng nhất cấp cửa hàng (kết hợp với metadata cửa hàng)

**Chỉ Số Thành Công**:
- Mục tiêu: Cải thiện RMSE đường cơ sở 10%+ khi bao gồm feature dầu
- Giải thích phương sai doanh số trong giai đoạn sụp đổ 2015-2016
- Xác định nhóm sản phẩm nào nhạy cảm nhất với dầu

Dataset này nên được **tích hợp ngay lập tức** vào tất cả mô hình chuỗi thời gian — sự liên quan kinh doanh và chất lượng dữ liệu biện minh cho việc coi nó là feature cốt lõi, không phải tùy chọn. Sử dụng `oil_lag_365` và `oil_regime` là các feature chính; tránh sử dụng giá dầu đồng thời do tương quan giả với xu hướng doanh số.
