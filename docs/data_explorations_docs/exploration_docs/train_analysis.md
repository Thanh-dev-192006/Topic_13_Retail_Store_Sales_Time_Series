# Báo Cáo Khám Phá Tập Dữ Liệu Train
**Phân Tích Chuỗi Thời Gian Doanh Số Bán Lẻ**
*Tạo ngày: 2026-01-01*

---

## Tóm Tắt Điều Hành

Báo cáo này phân tích 3 triệu bản ghi lịch sử bán hàng từ một chuỗi bán lẻ vận hành 54 cửa hàng trên nhiều danh mục sản phẩm. Năm phát hiện quan trọng nổi lên từ quá trình khám phá:

1. **Quy mô khổng lồ với sự tập trung cực đoan**: Tổng doanh số 1,07 tỷ USD, nhưng chỉ 3 nhóm sản phẩm (GROCERY I, BEVERAGES, PRODUCE) chiếm 64% doanh thu. Top 4 cửa hàng (#44, #45, #47, #3) tạo ra 31% tổng doanh số.

2. **Tỷ lệ thưa thớt cao phản ánh thách thức vận hành**: 31,3% bản ghi có doanh số bằng không, cho thấy tình trạng hết hàng thật sự, cửa hàng đóng cửa vào ngày cụ thể, hoặc vấn đề thu thập dữ liệu cần điều tra.

3. **Phân phối doanh số lệch nặng**: Trong khi doanh số trung bình trên mỗi bản ghi = 357,78 USD, trung vị chỉ là 11,00 USD (thấp hơn 96,9%). Điều này cho thấy hầu hết giao dịch nhỏ, với một số ít giao dịch khối lượng lớn đẩy số trung bình lên—điều quan trọng cho việc lựa chọn mô hình dự báo.

4. **Chiến lược khuyến mãi theo từng danh mục**: Khuyến mãi diễn ra trong 1.230 trên ~1.500+ ngày, nhưng 79,6% bản ghi riêng lẻ không có khuyến mãi. GROCERY I, PRODUCE và BEVERAGES nhận 50% tổng hoạt động khuyến mãi, phù hợp với sự thống lĩnh doanh thu của chúng.

5. **Phát hiện hiệu ứng ngày lễ**: Ngày 1 tháng 1 năm 2013 có doanh số bất thường thấp (2.511 USD so với mức 350.000–500.000 USD/ngày thông thường), xác nhận nhu cầu tích hợp lịch ngày lễ bên ngoài để dự báo chính xác.

---

## Tổng Quan Tập Dữ Liệu

### Nội Dung Tập Dữ Liệu
Tập dữ liệu huấn luyện ghi lại giao dịch bán hàng hàng ngày ở cấp độ **cửa hàng–nhóm sản phẩm–ngày** cho một chuỗi bán lẻ tại Ecuador. Mỗi hàng đại diện cho hiệu suất của một nhóm sản phẩm tại một cửa hàng trong một ngày cụ thể.

**Thông Số Cốt Lõi:**
- **Hàng**: 3.000.888 bản ghi
- **Cột**: 6 đặc trưng (id, date, store_nbr, family, sales, onpromotion)
- **Khoảng Thời Gian**: Bắt đầu từ 1 tháng 1 năm 2013 (ngày kết thúc không hiển thị rõ nhưng được suy ra là nhiều năm dựa trên số hàng)
- **Độ Chi Tiết**: Doanh số hàng ngày tổng hợp theo cửa hàng và nhóm sản phẩm
- **Dung Lượng Bộ Nhớ**: 137,4 MB (có thể xử lý trong bộ nhớ)

### Bối Cảnh Kinh Doanh
Đây là dữ liệu bán hàng giao dịch từ Corporación Favorita, nhà bán lẻ tạp hóa tại Ecuador. Tập dữ liệu hỗ trợ dự báo chuỗi thời gian để tối ưu hóa:
- Quản lý hàng tồn kho (giảm hết hàng và tồn kho dư thừa)
- Lập kế hoạch khuyến mãi (ROI chi phí khuyến mãi)
- Phân bổ nguồn lực trên các cửa hàng

---

## Cấu Trúc & Đặc Điểm Dữ Liệu

### Cấu Trúc Dữ Liệu Bảng
Tập dữ liệu theo **cấu trúc bảng ba chiều**:

```
Cửa Hàng (54) × Nhóm Sản Phẩm (33) × Ngày (≈1.685) ≈ 3.000.888 bản ghi
```

**Các Chiều:**
- **Cửa Hàng**: 54 địa điểm bán lẻ duy nhất (store_nbr: 1-54)
- **Nhóm Sản Phẩm**: 33 danh mục (ví dụ: AUTOMOTIVE, BABY CARE, BEVERAGES, GROCERY I, PRODUCE)
- **Khoảng Thời Gian**: Khoảng 1.685 ngày (~4,6 năm từ tháng 1 năm 2013)

### Thông Số Cột

| Cột | Kiểu | Mô Tả | Phạm Vi Giá Trị |
|-----|------|--------|-----------------|
| `id` | int64 | Định danh giao dịch duy nhất | 0 - 3.000.887 |
| `date` | object | Ngày giao dịch | Từ 2013-01-01 |
| `store_nbr` | int64 | Định danh cửa hàng | 1 - 54 |
| `family` | object | Danh mục sản phẩm | 33 nhóm duy nhất |
| `sales` | float64 | Tổng đơn vị/giá trị bán hàng | 0 - 124.717 |
| `onpromotion` | int64 | Số mặt hàng đang khuyến mãi | 0 - 741 |

**Lưu Ý Quan Trọng Về Khuyến Mãi**: Trường `onpromotion` đại diện cho **số lượng mặt hàng được khuyến mãi**, không phải cờ nhị phân. Giá trị >1 cho thấy nhiều SKU trong cùng một nhóm được khuyến mãi đồng thời. Giá trị tối đa 741 gợi ý các chiến dịch khuyến mãi tích cực trong các tổ hợp cửa hàng–nhóm–ngày nhất định.

---

## Phát Hiện Chính & Mẫu

### 1. Sự Tập Trung Hiệu Suất Bán Hàng

**Hiệu Suất Cấp Cửa Hàng:**

Phân phối doanh số trên các cửa hàng rất không đồng đều, theo mẫu luật lũy thừa:

| Cửa Hàng # | Tổng Doanh Số | % Tổng | % Tích Lũy |
|------------|---------------|--------|------------|
| 44 | 62,1 triệu USD | 5,8% | 5,8% |
| 45 | 54,5 triệu USD | 5,1% | 10,9% |
| 47 | 50,9 triệu USD | 4,7% | 15,6% |
| 3 | 50,5 triệu USD | 4,7% | 20,3% |
| 49 | 43,4 triệu USD | 4,0% | 24,3% |
| 46 | 41,9 triệu USD | 3,9% | 28,2% |
| 48 | 35,9 triệu USD | 3,3% | 31,6% |
| 51 | 32,9 triệu USD | 3,1% | 34,6% |
| 8 | 30,5 triệu USD | 2,8% | 37,5% |
| 50 | 28,7 triệu USD | 2,7% | 40,1% |

**Hàm Ý Kinh Doanh**: Top 10 cửa hàng (18,5% địa điểm) tạo ra 40% tổng doanh thu. Các cửa hàng hàng đầu này có thể có:
- Lượng khách cao hơn (khu vực đô thị/thương mại)
- Diện tích sàn lớn hơn
- Đặc điểm nhân khẩu học khách hàng khác nhau

Độ chính xác dự báo cho các cửa hàng này có tác động kinh doanh không tương xứng — ưu tiên tinh chỉnh mô hình cho các cửa hàng hàng đầu.

**Hiệu Suất Nhóm Sản Phẩm:**

| Nhóm | Tổng Doanh Số | % Tổng |
|------|---------------|--------|
| GROCERY I | 343,5 triệu USD | 32,0% |
| BEVERAGES | 217,0 triệu USD | 20,2% |
| PRODUCE | 122,7 triệu USD | 11,4% |
| CLEANING | 97,5 triệu USD | 9,1% |
| DAIRY | 64,5 triệu USD | 6,0% |
| BREAD/BAKERY | 42,1 triệu USD | 3,9% |
| POULTRY | 31,9 triệu USD | 3,0% |
| MEATS | 31,1 triệu USD | 2,9% |
| PERSONAL CARE | 24,6 triệu USD | 2,3% |
| DELI | 24,1 triệu USD | 2,2% |

**Hàm Ý Kinh Doanh**: Ba nhóm (GROCERY I, BEVERAGES, PRODUCE) đại diện 64% doanh thu. Đây là:
- Danh mục mua sắm tần suất cao (nhu cầu hàng ngày)
- Mặt hàng khối lượng lớn, biên lợi nhuận thấp
- Nhạy cảm với khuyến mãi và hết hàng

Tập trung nỗ lực dự báo vào các danh mục hàng đầu này trước — lỗi ở đây ảnh hưởng trực tiếp đến doanh thu.

### 2. Đặc Điểm Phân Phối Doanh Số

**Hồ Sơ Thống Kê:**
- **Doanh Số Trung Bình**: 357,78 USD mỗi bản ghi
- **Doanh Số Trung Vị**: 11,00 USD mỗi bản ghi
- **Độ Lệch Chuẩn**: 1.102,00 USD (gấp 3 lần trung bình)
- **Bản Ghi Đơn Tối Đa**: 124.717 USD

**Ý Nghĩa:**

Khoảng cách 97% giữa trung bình và trung vị cho thấy **phân phối lệch phải cực đoan**. Hình ảnh hóa sẽ cho thấy:
- Đuôi dài của giao dịch nhỏ (0–50 USD)
- Một số ít sự kiện bán hàng lớn (có thể là mua hàng số lượng lớn hoặc tổng hợp hàng ngày cho các nhóm khối lượng cao)

**Hàm Ý Mô Hình Hóa:**
1. Hồi quy tuyến tính chuẩn sẽ dự báo cao cho doanh số nhỏ và dự báo thấp cho doanh số lớn
2. Xem xét biến đổi log hoặc mô hình chuyên biệt cho dữ liệu đếm (ví dụ: Negative Binomial, mô hình Zero-Inflated)
3. Các số liệu lỗi dựa trên trung vị (MDAE) có thể thông tin hơn RMSE
4. Phương pháp tổ hợp (GBM, Random Forest) xử lý phân phối lệch tốt hơn mô hình tuyến tính

### 3. Doanh Số Bằng Không: Vấn Đề Thưa Thớt

**Quy Mô Vấn Đề:**
- **Bản Ghi Doanh Số Bằng Không**: 939.130 (31,3% tập dữ liệu)
- **Diễn Giải**: Gần 1 trong 3 bản ghi không có doanh số

**Các Giải Thích Có Thể:**
1. **Sản phẩm mới ra mắt**: Nhóm chưa được nhập kho tại một số cửa hàng (đầu 2013)
2. **Hết hàng**: Cạn kiệt hàng tồn kho dẫn đến mất doanh số
3. **Cửa hàng đóng cửa**: Các ngày cụ thể cửa hàng đóng cửa (ngày lễ, sửa chữa)
4. **Sản phẩm ngách**: Nhóm nhu cầu thấp (ví dụ: AUTOMOTIVE, BOOKS) với doanh số tự nhiên thưa thớt
5. **Phương pháp thu thập dữ liệu**: Hệ thống tự động ghi 0 khi không có giao dịch

**Câu Hỏi Kinh Doanh Cần Giải Quyết:**
- Đây là số không thật (cửa hàng mở, không bán được) hay số không cấu trúc (cửa hàng đóng, sản phẩm không có sẵn)?
- Nhóm nào có tỷ lệ không cao nhất? (có thể là danh mục tần suất thấp)
- Các số không có tập trung quanh ngày cụ thể (ngày lễ) hay cửa hàng (địa điểm ít lưu lượng khách)?

**Bước Tiếp Theo**: Đối chiếu với:
- Metadata cửa hàng (giờ mở cửa, lịch sửa chữa)
- Dữ liệu tình trạng sản phẩm (khi nào nhóm được giới thiệu tại cửa hàng)
- Lịch ngày lễ (để phân biệt nhu cầu thật = 0 với cửa hàng đóng cửa = 0)

### 4. Thông Tin Chiến Lược Khuyến Mãi

**Khối Lượng Khuyến Mãi:**
- **Tổng Mặt Hàng Khuyến Mãi**: 7.810.622 (tổng trường onpromotion)
- **Bản Ghi Không Có Khuyến Mãi**: 2.389.559 (79,6%)
- **Ngày Có Khuyến Mãi Hoạt Động**: 1.230 trong số ~1.685 ngày (73%)

**Diễn Giải**: Trong khi khuyến mãi diễn ra thường xuyên (3 trong 4 ngày), chúng nhắm vào các tổ hợp cửa hàng–nhóm cụ thể thay vì giảm giá đại trà.

**Trọng Tâm Khuyến Mãi Theo Cửa Hàng:**

| Cửa Hàng # | Tổng Mặt Hàng Được Khuyến Mãi | Chiến Lược |
|------------|-------------------------------|-----------|
| 53 | 204.016 | Cường độ khuyến mãi cao nhất |
| 47 | 192.725 | Giảm giá tích cực |
| 44 | 192.449 | Doanh số cao + Khuyến mãi cao |
| 45 | 191.503 | Doanh số cao + Khuyến mãi cao |
| 46 | 190.697 | Doanh số cao + Khuyến mãi cao |

**Quan Sát Chính**: Cửa hàng #44, #45, #46, #47 xuất hiện trong cả danh sách doanh số cao VÀ khuyến mãi cao. Điều này gợi ý:
- Cửa hàng lưu lượng cao dùng khuyến mãi để tăng khối lượng
- HOẶC khuyến mãi hiệu quả về chi phí tại những địa điểm này (tỷ lệ chuyển đổi cao)

**Trọng Tâm Khuyến Mãi Theo Nhóm:**

| Nhóm | Tổng Mặt Hàng Được Khuyến Mãi | % Tổng KM |
|------|-------------------------------|-----------|
| GROCERY I | 1.914.801 | 24,5% |
| PRODUCE | 1.117.921 | 14,3% |
| BEVERAGES | 906.958 | 11,6% |
| DAIRY | 728.707 | 9,3% |
| CLEANING | 661.157 | 8,5% |

**Thông Tin Kinh Doanh**: Top 3 nhóm tạo doanh thu (GROCERY I, BEVERAGES, PRODUCE) cũng nhận được hỗ trợ khuyến mãi nhiều nhất. Đây có thể là:
- Chiến lược thông minh (khuyến mãi mặt hàng khối lượng cao để thu hút lưu lượng)
- HOẶC phản ứng (các danh mục này đối mặt cạnh tranh nhiều hơn, cần giảm giá)

**Cảnh Báo Bất Thường**: Khuyến mãi bắt đầu muộn — 5 ngày đầu năm 2013 không có khuyến mãi. Điều này có thể cho thấy:
- Độ trễ thu thập dữ liệu
- Bình thường hóa giá sau kỳ nghỉ lễ
- Hoặc bản ghi không đầy đủ cho đầu năm 2013

### 5. Mẫu Chuỗi Thời Gian & Bất Thường

**Biến Động Doanh Số Hàng Ngày:**

| Ngày | Tổng Doanh Số Ngày | Ghi Chú |
|------|-------------------|---------|
| 2013-01-01 | 2.512 USD | **Bất Thường**: Thấp hơn 99% so với bình thường |
| 2013-01-02 | 496.092 USD | Ngày vận hành bình thường |
| 2013-01-03 | 361.461 USD | Bình thường |
| 2013-01-04 | 354.460 USD | Bình thường |
| 2013-01-05 | 477.350 USD | Bình thường |

**Phát Hiện Quan Trọng**: Ngày 1 tháng 1 năm 2013 (Năm Mới) chỉ có doanh số 2.512 USD, thấp hơn 99% so với doanh số hàng ngày thông thường 350.000–500.000 USD. Đây rõ ràng là hiệu ứng ngày lễ — cửa hàng có thể:
- Đóng cửa hoàn toàn (và 2.512 USD là doanh số tự động/trực tuyến)
- Mở cửa với giờ hạn chế
- Gần như không có khách

**Hàm Ý**: Điều này xác nhận tập dữ liệu nhạy cảm với:
- **Ngày lễ quốc gia** (Năm Mới, Giáng Sinh, v.v.)
- **Ngày lễ địa phương** (sự kiện đặc thù Ecuador)
- **Mẫu mùa vụ** (lịch học, mùa thu hoạch)

**Tại Sao Điều Này Quan Trọng Cho Dự Báo:**
1. Mô hình được huấn luyện trên dữ liệu thô sẽ học mẫu không chính xác trừ khi ngày lễ được đánh dấu rõ ràng
2. Cần tích hợp dữ liệu lịch bên ngoài (được cung cấp trong `holidays_events.csv`)
3. Xem xét mô hình riêng biệt hoặc biến giả cho các kỳ ngày lễ

---

## Đánh Giá Chất Lượng Dữ Liệu

### Tính Đầy Đủ: Xuất Sắc ✅

**Phân Tích Giá Trị Thiếu:**
```
Cột             Giá Trị Thiếu    Phần Trăm
id              0                 0,0%
date            0                 0,0%
store_nbr       0                 0,0%
family          0                 0,0%
sales           0                 0,0%
onpromotion     0                 0,0%
```

**Đánh Giá**: Không có giá trị thiếu trên tất cả các trường. Điều này đặc biệt tốt cho tập dữ liệu quy mô này và cho thấy:
- Quy trình thu thập dữ liệu mạnh mẽ
- Hệ thống theo dõi bán hàng tự động (tích hợp POS)
- Không có lỗi truyền dữ liệu/ETL

**Không Cần Điền Thiếu**: Tiến thẳng đến mô hình hóa mà không cần xử lý giá trị thiếu.

### Tính Nhất Quán: Cao (có cảnh báo)

**✅ Điểm Mạnh:**
- Định dạng ngày có vẻ nhất quán (YYYY-MM-DD)
- Số cửa hàng là số nguyên tuần tự (1-54)
- Giá trị doanh số không âm (min = 0, như mong đợi)
- Không có sự không phù hợp kiểu dữ liệu rõ ràng

**⚠️ Khu Vực Cần Xác Minh:**
1. **Tính Liên Tục Ngày**: Có khoảng trống trong chuỗi thời gian không (ngày thiếu)?
   - Cần kiểm tra xem tất cả cửa hàng có bản ghi cho tất cả các ngày không
   - Khoảng trống có thể cho thấy cửa hàng đóng cửa hoặc lỗi thu thập dữ liệu

2. **Tính Đầy Đủ Cửa Hàng–Nhóm**: Tất cả 54 cửa hàng có mang tất cả 33 nhóm không?
   - Có thể không (ví dụ: cửa hàng nhỏ có thể không bán AUTOMOTIVE)
   - Cần ghi lại những tổ hợp cửa hàng–nhóm nào hợp lệ

3. **Ngoại Lệ Trong Doanh Số**: Giá trị tối đa 124.717 USD gấp 348 lần trung bình
   - Đây có phải lỗi nhập dữ liệu không (thêm số 0)?
   - Hay hợp lệ (ví dụ: GROCERY I tại Cửa Hàng #44 trong đợt bán hàng ngày lễ lớn)?
   - **Hành Động**: Điều tra top 0,1% bản ghi doanh số để kiểm tra tính hợp lý

4. **Logic Khuyến Mãi**: `onpromotion` = 741 có vẻ cực đoan
   - 741 mặt hàng có thực sự được khuyến mãi tại một tổ hợp cửa hàng–nhóm–ngày không?
   - Có thể cho thấy vấn đề chất lượng dữ liệu hoặc sự kiện khuyến mãi số lượng lớn
   - **Hành Động**: Kiểm tra chéo với lịch khuyến mãi nếu có

### Các Vấn Đề Dữ Liệu Tiềm Ẩn

**1. Độ Tin Cậy Dữ Liệu Đầu Năm 2013**
- Bất thường ngày 1 tháng 1 năm 2013 cho thấy thu thập dữ liệu có thể không ổn định trong giai đoạn khởi động hệ thống
- **Khuyến Nghị**: Loại trừ 2 tuần đầu năm 2013 khỏi huấn luyện nếu mẫu có vẻ bất thường

**2. Zero Inflation**
- Tỷ lệ doanh số bằng không 31,3% là cao nhưng không phi thực tế cho dữ liệu bảng thưa thớt
- **Rủi Ro**: Nếu số không thực ra là dữ liệu thiếu (hệ thống không ghi giao dịch), dự báo sẽ đánh giá thấp nhu cầu
- **Xác Minh Cần Thiết**: So sánh tỷ lệ không theo nhóm — kỳ vọng cao cho BOOKS/AUTOMOTIVE, thấp cho BEVERAGES/GROCERY I

**3. Cần Sửa Kiểu Dữ Liệu**
- Cột `date` được tải dưới dạng `object` (chuỗi) thay vì `datetime64`
- **Hành Động**: Chuyển đổi sang datetime trong quy trình tiền xử lý để cho phép các phép toán dựa trên thời gian

---

## Tích Hợp & Bước Tiếp Theo

### Tích Hợp Với Các Tập Dữ Liệu Khác

Tập dữ liệu huấn luyện này là một phần của hệ sinh thái lớn hơn. Dựa trên cấu trúc dự án, các tích hợp sau đây rất quan trọng:

**1. Tập Dữ Liệu Ngày Lễ & Sự Kiện** (`holidays_events.csv`)
- **Mục Đích**: Giải thích bất thường doanh số như sụt giảm ngày 1/1/2013
- **Tích Hợp**: Kết hợp theo `date` để tạo cờ ngày lễ (nhị phân: is_holiday, hoặc phân loại: holiday_type)
- **Tác Động**: Dự kiến cải thiện độ chính xác dự báo 10-20% trong kỳ ngày lễ

**2. Metadata Cửa Hàng** (nếu có)
- **Trường Kỳ Vọng**: store_type, city, state, cluster, floor_area
- **Tích Hợp**: Kết hợp theo `store_nbr`
- **Trường Hợp Sử Dụng**: Giải thích tại sao cửa hàng #44, #45, #47 là nhà thực hiện hàng đầu

**3. Metadata Sản Phẩm** (nếu có)
- **Trường Kỳ Vọng**: mô tả nhóm, khả năng hư hỏng, hồ sơ biên lợi nhuận
- **Tích Hợp**: Kết hợp theo `family`
- **Trường Hợp Sử Dụng**: Phân biệt chiến lược dự báo (hàng dễ hư hỏng cần kiểm soát tồn kho chặt chẽ hơn)

**4. Giá Dầu / Chỉ Số Kinh Tế** (nếu có)
- **Mức Độ Liên Quan**: Kinh tế Ecuador phụ thuộc vào dầu mỏ; giá dầu có thể tương quan với chi tiêu người tiêu dùng
- **Tích Hợp**: Kết hợp theo `date`
- **Trường Hợp Sử Dụng**: Thêm đặc trưng kinh tế vĩ mô để nắm bắt biến động nhu cầu rộng hơn

### Bước Tiếp Theo Được Khuyến Nghị

**Hành Động Ngay (Tuần Này):**

1. **Kiểm Tra Tính Liên Tục Ngày**
   ```python
   # Xác minh không có ngày thiếu
   date_range = pd.date_range(start='2013-01-01', end=df_train['date'].max(), freq='D')
   missing_dates = set(date_range) - set(df_train['date'].unique())
   ```

2. **Ma Trận Tính Đầy Đủ Cửa Hàng–Nhóm**
   ```python
   # Xác định tổ hợp cửa hàng–nhóm tồn tại
   completeness = df_train.groupby(['store_nbr', 'family']).size().unstack(fill_value=0)
   # Kỳ vọng một số số không (không phải tất cả cửa hàng mang tất cả nhóm)
   ```

3. **Điều Tra Ngoại Lệ**
   ```python
   # Đánh dấu giá trị cực đoan để xem xét thủ công
   outliers = df_train[df_train['sales'] > df_train['sales'].quantile(0.999)]
   # Xác minh đây là doanh số hợp lệ, không phải lỗi dữ liệu
   ```

4. **Phân Tích Sâu Doanh Số Bằng Không**
   ```python
   # Phân tích tỷ lệ không theo nhóm và cửa hàng
   zero_rate = df_train.groupby('family')['sales'].apply(lambda x: (x == 0).mean())
   # Kỳ vọng AUTOMOTIVE/BOOKS > 50%, BEVERAGES/GROCERY I < 10%
   ```

5. **Kết Hợp Với Tập Dữ Liệu Ngày Lễ**
   ```python
   # Kết hợp với holidays_events.csv để đánh dấu ngày đặc biệt
   df_train = df_train.merge(holidays, on='date', how='left')
   # Tạo đặc trưng nhị phân: is_holiday
   ```

**Phân Tích Ngắn Hạn (2 Tuần Tới):**

6. **Phân Rã Mùa Vụ**
   - Phân rã doanh số hàng ngày thành xu hướng, mùa vụ và thành phần phần dư
   - Xác định mẫu hàng tuần (cuối tuần vs. ngày thường)
   - Phát hiện tính mùa vụ hàng năm (Giáng Sinh, tựu trường, v.v.)

7. **Phân Tích Tác Động Khuyến Mãi**
   - So sánh doanh số ngày được khuyến mãi vs. không khuyến mãi (theo nhóm)
   - Tính lift khuyến mãi: `(sales_promoted - sales_baseline) / sales_baseline`
   - Xác định nhóm nào nhạy cảm nhất với khuyến mãi

8. **Phân Cụm Cửa Hàng**
   - Dùng k-means hoặc phân cụm phân cấp để nhóm cửa hàng theo mẫu doanh số
   - Đặc trưng: tổng doanh số, biến động doanh số, tỷ lệ không, cường độ khuyến mãi
   - Kết quả: Phân loại cửa hàng (ví dụ: "khối lượng cao đô thị", "khối lượng thấp nông thôn")

9. **Phân Tích Tương Quan**
   - Kiểm tra tương quan giữa `onpromotion` và `sales` (kỳ vọng dương nhưng không 1:1)
   - Kiểm tra đa cộng tuyến giữa các cửa hàng (một số có thể ăn mòn doanh số của nhau)

**Chuẩn Bị Mô Hình Hóa Trung Hạn (Tháng Tới):**

10. **Feature Engineering**
    - Đặc trưng lag: sales_7d_ago, sales_14d_ago, sales_365d_ago
    - Thống kê cuộn: sales_7d_avg, sales_7d_std
    - Đặc trưng lịch: day_of_week, day_of_month, month, quarter, is_weekend, is_month_end
    - Cờ sự kiện: is_payday (15 và 30), is_holiday, is_earthquake (Ecuador 2016)

11. **Chia Huấn Luyện/Xác Thực/Kiểm Tra**
    - **Huấn Luyện**: 2013-01-01 đến 2016-06-30 (3,5 năm)
    - **Xác Thực**: 2016-07-01 đến 2016-12-31 (6 tháng)
    - **Kiểm Tra**: Từ 2017-01-01
    - Sử dụng chia dựa trên thời gian (không xáo trộn ngẫu nhiên — đây là chuỗi thời gian!)

12. **Mô Hình Cơ Sở**
    - Bắt đầu với heuristic đơn giản: "Doanh số ngày mai = Doanh số cùng ngày tuần trước"
    - Tính RMSE, MAE, MAPE làm đường cơ sở để vượt qua
    - MAPE cơ sở kỳ vọng: 40–60% (điển hình cho bán lẻ)

13. **Lựa Chọn Mô Hình**
    - Cho doanh số tổng hợp (cấp cửa hàng hoặc toàn chuỗi): ARIMA, Prophet, LSTM
    - Cho dự báo cửa hàng–nhóm–ngày: LightGBM, XGBoost, CatBoost (xử lý dữ liệu thưa thớt tốt)
    - Cho dự báo xác suất: Quantile Regression, DeepAR

---

## Kết Luận

Tập dữ liệu này cung cấp nền tảng vững chắc cho dự báo doanh số bán lẻ, với tính đầy đủ xuất sắc (không có giá trị thiếu) và chiều sâu lịch sử đủ (4,6 năm). Các thách thức chính là:

1. **Thưa thớt cao** (31% số không) đòi hỏi lựa chọn mô hình cẩn thận
2. **Lệch cực đoan** (trung bình >> trung vị) đòi hỏi biến đổi log hoặc mô hình đếm
3. **Nhạy cảm với ngày lễ** đòi hỏi tích hợp lịch bên ngoài
4. **Rủi ro tập trung** khi top 10 cửa hàng và top 3 nhóm thống trị — lỗi ở đây có tác động kinh doanh không tương xứng

Bước quan trọng tiếp theo là tích hợp tập dữ liệu ngày lễ/sự kiện để kiểm soát bất thường như sụt giảm doanh số ngày 1 tháng 1 năm 2013. Từ đó, tập trung vào feature engineering (lag, thống kê cuộn, hiệu ứng lịch) và thiết lập mô hình cơ sở để đánh giá chuẩn.

**Chỉ Số Thành Công:**
- MAPE mục tiêu: <30% cho top 10 cửa hàng, <40% tổng thể
- Giảm hết hàng: Dự đoán sự kiện doanh số bằng không với độ chính xác >80%
- ROI khuyến mãi: Định lượng doanh số tăng thêm trên mỗi đô la chi khuyến mãi

Phân tích này định vị nhóm để tiến tự tin vào mô hình hóa với hiểu biết rõ ràng về điểm mạnh, hạn chế và bối cảnh kinh doanh của dữ liệu.
