# Báo Cáo Khám Phá Tập Dữ Liệu Giao Dịch
**Phân Tích Chuỗi Thời Gian Doanh Số Bán Lẻ**
*Tạo ngày: 2026-01-02*

---

## Tóm Tắt Điều Hành

Báo cáo này phân tích 83.488 bản ghi số lượng giao dịch hàng ngày trên 54 cửa hàng, đóng vai trò là **chỉ số lưu lượng khách** cho dự báo bán lẻ. Bốn phát hiện quan trọng nổi lên:

1. **Dữ liệu thưa thớt đáng kể phản ánh hoạt động cửa hàng**: 8,4% bản ghi ngày–cửa hàng dự kiến bị thiếu trong dữ liệu thô (7.664 trong số 91.152 bản ghi dự kiến). Tuy nhiên, điều này **không ngẫu nhiên** — dữ liệu thiếu tập trung ở các cửa hàng mới mở (cửa hàng 52 thiếu 93% lịch sử) và ngày lễ quốc gia (Ngày Giáng Sinh liên tục vắng mặt). Đây là **điểm mạnh chất lượng dữ liệu**, không phải lỗi, vì nó phản ánh chính xác thực tế kinh doanh.

2. **Lưu lượng cuối tuần tăng vọt 26%**: Thứ Bảy trung bình 1.953 giao dịch mỗi cửa hàng so với Thứ Năm ở mức 1.550 (+26%) — mẫu tính mùa vụ hàng tuần mạnh mẽ. Sự tăng lưu lượng khách này có thể khuếch đại doanh số trên tất cả nhóm sản phẩm, khiến ngày trong tuần là đặc trưng quan trọng cho dự báo.

3. **Tính không đồng nhất cực đoan giữa các cửa hàng**: Khối lượng giao dịch biến thiên 6,8 lần giữa cửa hàng bận nhất (cửa hàng 44: 4.337/ngày) và yên tĩnh nhất (cửa hàng 26: 635/ngày). Điều này cho thấy hiệu ứng cố định cấp cửa hàng hoặc embedding là cần thiết — mô hình một kích thước cho tất cả sẽ kém hiệu quả.

4. **Đỉnh Đêm Giáng Sinh tiết lộ cơ hội khuyến mãi**: Ngày 24 tháng 12 năm 2015 ghi nhận 171.169 tổng giao dịch (gấp 2 lần trung bình hàng ngày) — lưu lượng cao nhất trong một ngày trong tập dữ liệu. Đợt tăng đột biến trước ngày lễ này cho thấy khách hàng tích trữ hàng, tạo ra cửa sổ quan trọng để kiểm tra hiệu quả khuyến mãi.

---

## Tổng Quan Tập Dữ Liệu

### Nội Dung Tập Dữ Liệu
Tập dữ liệu giao dịch cung cấp **số lượng giao dịch** hàng ngày tại mỗi cửa hàng, đóng vai trò là **proxy hoạt động cửa hàng** để bổ sung dự báo doanh số. Không giống dữ liệu doanh số (biến theo nhóm sản phẩm), số lượng giao dịch đo lường lưu lượng khách tổng thể — nắm bắt mức độ bận rộn của cửa hàng bất kể khách hàng mua gì.

**Thông Số Cốt Lõi:**
- **Hàng**: 83.488 bản ghi ngày–cửa hàng (dữ liệu thô)
- **Cột**: 3 đặc trưng (date, store_nbr, transactions)
- **Khoảng Thời Gian**: 1 tháng 1 năm 2013 đến 15 tháng 8 năm 2017 (1.688 ngày)
- **Độ Chi Tiết**: Cấp ngày–cửa hàng (không có phân tích theo nhóm sản phẩm)
- **Bảng Đầy Đủ Dự Kiến**: 91.152 bản ghi (54 cửa hàng × 1.688 ngày)
- **Thiếu**: 7.664 bản ghi (8,4% thưa thớt)

### Bối Cảnh Kinh Doanh
Số lượng giao dịch khác với doanh thu doanh số theo những cách quan trọng:
- **Số lượng giao dịch** = số sự kiện thanh toán (giỏ hàng)
- **Doanh thu doanh số** = giá trị đô la của những giỏ hàng đó

Sự phân biệt này quan trọng vì:
- **Giao dịch cao, doanh số thấp** → Khách hàng mua mặt hàng rẻ/thiết yếu (người mua hàng theo giá trị)
- **Giao dịch thấp, doanh số cao** → Khách hàng mua mặt hàng đắt/số lượng lớn (người mua cao cấp/bán buôn)

Cho dự báo, giao dịch cung cấp **chỉ số lưu lượng cấp cửa hàng** phát sóng đến tất cả nhóm sản phẩm — hữu ích để tách "cửa hàng bận rộn" khỏi "nhóm sản phẩm cụ thể có nhu cầu cao".

---

## Cấu Trúc & Đặc Điểm Dữ Liệu

### Thông Số Cột

| Cột | Kiểu | Mô Tả | Phạm Vi Giá Trị |
|-----|------|--------|-----------------|
| `date` | object (datetime) | Ngày lịch | 2013-01-01 đến 2017-08-15 |
| `store_nbr` | int64 | Định danh cửa hàng | 1 - 54 |
| `transactions` | int64 | Số lượng giao dịch thanh toán trong ngày | 0 - 8.359 |

**Lưu Ý Quan Trọng:**
- **Khóa chính**: Tổ hợp (date, store_nbr) — không tìm thấy trùng lặp
- **Tổng hợp cấp cửa hàng**: Không có chiều nhóm sản phẩm (phát sóng khi kết hợp với train.csv)
- **Dữ liệu đếm**: Giao dịch là số nguyên rời rạc, không âm

### Cấu Trúc Dữ Liệu Bảng

**Phạm Vi Thực Tế vs. Dự Kiến:**
```
Dự Kiến:   54 cửa hàng × 1.688 ngày = 91.152 ngày-cửa hàng
Thực Tế:   83.488 ngày-cửa hàng
Thiếu:     7.664 ngày-cửa hàng (8,4% thưa thớt)
```

**Tại Sao Điều Này Quan Trọng:**
- Mô hình chuỗi thời gian yêu cầu bảng đầy đủ để tính lag/đặc trưng cuộn
- **Giải pháp áp dụng**: Tạo lưới bảng đầy đủ và điền giá trị thiếu với `transactions = 0`, đánh dấu qua `is_imputed = 1`

---

## Phát Hiện Chính & Mẫu

### 1. Tính Không Đồng Nhất Cửa Hàng: Phương Sai Khối Lượng 6,8 Lần

**Khối Lượng Giao Dịch Theo Cửa Hàng (Top 5 vs. Bottom 5):**

| Xếp Hạng | Cửa Hàng # | TB Giao Dịch/Ngày | Hạng Lưu Lượng |
|----------|------------|-------------------|----------------|
| 1 | 44 | 4.337 | Hàng đầu (lưu lượng cực cao) |
| 2 | 45 | 3.891 | Hàng đầu |
| 3 | 47 | 3.542 | Đô thị lưu lượng cao |
| 4 | 3 | 3.201 | Đô thị lưu lượng cao |
| 5 | 49 | 2.847 | Trung tâm đô thị |
| ... | ... | ... | ... |
| 50 | 33 | 721 | Nông thôn/ngoại ô lưu lượng thấp |
| 51 | 20 | 698 | Lưu lượng thấp |
| 52 | 52 | 683 | Mới mở (dữ liệu hạn chế) |
| 53 | 43 | 651 | Lưu lượng thấp |
| 54 | 26 | 635 | Lưu lượng tối thiểu |

**Phát Hiện Quan Trọng**: Cửa hàng 44 trung bình **gấp 6,8 lần giao dịch** so với cửa hàng 26 — cho thấy tính không đồng nhất lớn về quy mô cửa hàng, vị trí, hoặc cơ sở khách hàng.

**Hàm Ý Kinh Doanh:**

1. **Chiến Lược Mô Hình Hóa**: Một mô hình toàn cục sẽ gặp khó khăn — xem xét:
   - Mô hình riêng theo cửa hàng hoặc embedding
   - Mô hình phân cấp với hiệu ứng ngẫu nhiên cấp cửa hàng
   - Huấn luyện phân tầng (cửa hàng lưu lượng cao vs. thấp)

2. **Thông Tin Vận Hành:**
   - Cửa hàng lưu lượng cao (44, 45, 47) có thể cần:
     - Nhiều làn thanh toán hơn (để xử lý 4.000+ giao dịch hàng ngày)
     - Tồn kho sâu hơn (rủi ro hết hàng cao hơn)
     - Nhiều nhân viên hơn (tải dịch vụ khách hàng)
   - Cửa hàng lưu lượng thấp (<700/ngày) có thể là:
     - Định dạng nông thôn/tiện lợi (hành vi khách hàng khác nhau)
     - Mới mở (vẫn đang tăng dần)
     - Kém hiệu quả (ứng viên đóng cửa tiềm năng)

3. **Hiệu Quả Khuyến Mãi**: Kiểm tra khuyến mãi ở cửa hàng 44 vs. cửa hàng 26 có thể cho ROI rất khác nhau — phân tầng thử nghiệm theo hạng lưu lượng.

### 2. Tính Mùa Vụ Hàng Tuần: Đợt Tăng Lưu Lượng Cuối Tuần

**Trung Bình Giao Dịch Mỗi Ngày–Cửa Hàng Theo Ngày Trong Tuần:**

| Ngày | TB Giao Dịch | % So Với Cơ Sở (Thứ Năm) |
|------|--------------|--------------------------|
| Thứ Bảy | 1.953 | +26,0% |
| Chủ Nhật | 1.847 | +19,2% |
| Thứ Sáu | 1.612 | +4,0% |
| Thứ Hai | 1.583 | +2,1% |
| Thứ Ba | 1.551 | +0,1% |
| Thứ Năm | 1.550 | 0,0% (cơ sở) |
| Thứ Tư | 1.541 | -0,6% |

**Quan Sát Chính**: **Thứ Bảy bận hơn Thứ Năm 26%** — mẫu hàng tuần mạnh mẽ và nhất quán.

**Tại Sao Điều Này Quan Trọng Cho Dự Báo:**

1. **Feature Engineering**: Thêm đặc trưng ngày trong tuần (mã hóa one-hot hoặc mã hóa chu kỳ với sine/cosine).

2. **Hiệu Ứng Cuối Tuần Lên Doanh Số**: Đợt tăng lưu lượng cuối tuần có thể thúc đẩy doanh số trên **tất cả nhóm sản phẩm** (không chỉ danh mục cụ thể), vì vậy:
   - Đừng quy doanh số tăng cuối tuần chỉ cho nhu cầu sản phẩm cụ thể
   - Tách "doanh số do lưu lượng" khỏi "doanh số do sản phẩm" bằng cách đưa số lượng giao dịch làm biến đồng biến

3. **Nhân Sự & Tồn Kho**: Nhà bán lẻ đã biết cuối tuần bận rộn, nhưng điều này định lượng nó — Thứ Bảy cần **nhiều hơn 26% công suất** so với giữa tuần.

### 3. Đợt Tăng Lưu Lượng Ngày Lễ: Sự Thống Trị Đêm Giáng Sinh

**Top 10 Ngày Lưu Lượng Cao Nhất (Tổng Giao Dịch Trên Tất Cả Cửa Hàng):**

| Ngày | Tổng Giao Dịch | Bội Số Trung Bình Hàng Ngày |
|------|----------------|------------------------------|
| 2015-12-24 | 171.169 | 2,03 lần |
| 2014-12-24 | 166.542 | 1,98 lần |
| 2013-12-23 | 162.891 | 1,94 lần |
| 2016-12-24 | 161.237 | 1,92 lần |
| 2014-12-23 | 158.492 | 1,88 lần |

**Tổng Hàng Ngày Trung Bình**: ~84.114 giao dịch (trên tất cả 54 cửa hàng)

**Phát Hiện Quan Trọng**: **Ngày 23-24 tháng 12 liên tục thống trị** lưu lượng — đạt **gấp 2 lần mức bình thường**. Đây là hành vi tích trữ trước Giáng Sinh.

**Hàm Ý Kinh Doanh:**

1. **Chiến Lược Khuyến Mãi**: Đợt tăng lưu lượng Đêm Giáng Sinh gợi ý:
   - Tính cấp bách cao của khách hàng (mua sắm vào phút cuối)
   - Sẵn lòng mua số lượng lớn (tích trữ cho ngày lễ)
   - **Cơ hội**: Kiểm tra giá cao cấp vs. giảm giá sâu — khách hàng có thể ít nhạy cảm về giá khi tính cấp bách cao

2. **Rủi Ro Tồn Kho**: Nếu lưu lượng gấp 2 lần nhưng tồn kho không được tăng gấp đôi, có nguy cơ hết hàng thảm khốc (mất doanh số vào đỉnh nhu cầu).

3. **Dự Báo**: Mô hình không có đặc trưng ngày lễ sẽ **dự báo thấp nghiêm trọng** ngày 23-24 tháng 12. Phải tích hợp `holidays_events.csv` để đánh dấu ngày trước ngày lễ.

### 4. Dữ Liệu Thiếu Như Tín Hiệu Kinh Doanh: Mở Cửa & Đóng Cửa Hàng

**Cửa Hàng Có Tỷ Lệ Dữ Liệu Thiếu Cao Nhất:**

| Cửa Hàng # | Ngày Thiếu | % Lịch Sử | Diễn Giải |
|------------|------------|-----------|-----------|
| 52 | 1.570 | 93% | Mở 20/4/2017 (chỉ 118 ngày hoạt động) |
| 22 | 1.017 | 60% | Mở muộn hoặc đóng cửa thường xuyên |
| 42 | 968 | 57% | Mở muộn hoặc khoảng trống thu thập dữ liệu |
| 21 | 940 | 56% | Mở muộn |
| 29 | 814 | 48% | Phạm vi lịch sử một phần |

**Ngày Không Có Bản Ghi Nào Từ Tất Cả Cửa Hàng (Đóng Cửa Toàn Bộ):**
- **25 tháng 12** (2013, 2014, 2015, 2016) — Ngày Giáng Sinh
- **1 tháng 1 năm 2016** — Ngày Năm Mới
- **3 tháng 1 năm 2016** — Đóng cửa sau ngày lễ

**Ý Nghĩa:**

1. **Không phải thiếu ngẫu nhiên**: Dữ liệu thiếu có **thông tin cấu trúc**:
   - Cửa hàng mới (như 52) vật lý không tồn tại trong 93% lịch sử
   - Ngày lễ quốc gia → tất cả cửa hàng đóng cửa → hợp lệ 0 giao dịch

2. **Chiến Lược Điền Thiếu**: Điền thiếu với `transactions = 0` là **đúng**, nhưng thêm cờ `is_imputed`:
   - `is_imputed = 1` → Cửa hàng không mở hoặc không thu thập được dữ liệu
   - `is_imputed = 0` → Cửa hàng mở và ghi nhận 0-N giao dịch

3. **Hàm Ý Mô Hình Hóa**: Với các cửa hàng như 52, lịch sử sớm **không có tín hiệu** (cửa hàng chưa tồn tại). Xem xét:
   - Che giấu kỳ trước khi mở trong dữ liệu huấn luyện
   - Hoặc dùng `is_imputed` làm đặc trưng để mô hình học "cửa hàng này đã đóng cửa"

---

## Đánh Giá Chất Lượng Dữ Liệu

### Tính Đầy Đủ: Tốt (sau khi điền thiếu) ✅

**Giá Trị Thiếu Trong Dữ Liệu Thô:**
```
Cột             Giá Trị Thiếu    Phần Trăm
date            0                 0,0%
store_nbr       0                 0,0%
transactions    0                 0,0%
```

**Đánh Giá**: Không có giá trị thiếu trong bản ghi thô. Tuy nhiên, **bảng đầy đủ có 8,4% thưa thớt** (91.152 bản ghi dự kiến, nhận được 83.488).

**Giải Pháp Áp Dụng:**
1. Tạo lưới bảng đầy đủ: Tất cả 54 cửa hàng × Tất cả 1.688 ngày
2. Kết hợp trái dữ liệu thô
3. Điền `transactions = 0` bị thiếu với cờ `is_imputed = 1`

**Sau Khi Điền Thiếu**: 91.152 bản ghi đầy đủ (100% phủ sóng).

### Tính Nhất Quán: Xuất Sắc ✅

**✅ Điểm Mạnh:**
- **Không có trùng lặp**: Các cặp (date, store_nbr) là duy nhất
- **Không có giá trị âm**: Phạm vi `transactions` là 0 - 8.359 (tất cả hợp lệ)
- **Không có ngoại lệ**: Max 8.359 là hợp lý cho cửa hàng bận rộn (phù hợp hồ sơ lưu lượng cao của cửa hàng 44)
- **Tính liên tục ngày**: Sau khi điền thiếu, mỗi ngày từ 2013-01-01 đến 2017-08-15 được phủ sóng

**⚠️ Khu Vực Cần Xác Minh:**
1. **Tăng tốc cửa hàng 52**: Cửa hàng mới mở có thể cho thấy quỹ đạo tăng trưởng bất thường — xác minh mẫu doanh số phù hợp với tăng trưởng giao dịch
2. **Giao dịch bằng không trong ngày mở cửa**: Một số bản ghi có 0 giao dịch khi cửa hàng được cho là mở — có thể là:
   - Lỗi thu thập dữ liệu
   - Đóng cửa thực tế (ví dụ: khẩn cấp, sửa chữa)
   - Hoặc thực sự không có khách hàng hôm đó (không chắc nhưng có thể)

---

## Hàm Ý Kinh Doanh

### 1. Số Lượng Giao Dịch Như Proxy Lưu Lượng

**Trường Hợp Sử Dụng Chính**: Phân rã doanh số thành các thành phần:
```
Doanh Số = Lưu Lượng × Tỷ Lệ Chuyển Đổi × Giá Trị Giỏ Hàng
```

Trong đó:
- **Lưu Lượng** = số lượng giao dịch (tập dữ liệu này)
- **Tỷ Lệ Chuyển Đổi** = % khách thăm cửa hàng mua hàng
- **Giá Trị Giỏ Hàng** = doanh số trung bình mỗi giao dịch

**Ứng Dụng Mô Hình Hóa:**
- Đưa `transactions` làm biến đồng biến trong mô hình dự báo doanh số
- Nếu doanh số tăng vọt nhưng giao dịch không tăng → khách hàng mua nhiều hơn mỗi lần ghé thăm (giá trị giỏ hàng tăng)
- Nếu giao dịch tăng vọt nhưng doanh số không tăng → khách hàng mua mặt hàng rẻ hơn (giá trị giỏ hàng giảm)

Phân rã này giúp chẩn đoán **tại sao** doanh số thay đổi (lưu lượng vs. thay đổi hành vi).

### 2. Phân Cụm Cửa Hàng Theo Mẫu Lưu Lượng

**Giả Thuyết**: Các cửa hàng có mẫu giao dịch tương tự có thể chia sẻ:
- Nhân khẩu học khách hàng
- Đặc điểm địa lý (đô thị vs. nông thôn)
- Định dạng cửa hàng (siêu thị vs. tiện lợi)

**Chiến Lược Phân Cụm:**
1. Trích xuất đặc trưng mỗi cửa hàng:
   - Trung bình giao dịch/ngày
   - % uplift cuối tuần
   - Cường độ đỉnh ngày lễ
   - Hệ số biến thiên (biến động)
2. Chạy k-means hoặc phân cụm phân cấp
3. Kết quả: Phân loại cửa hàng (ví dụ: "đô thị lưu lượng cao", "nông thôn lưu lượng thấp", "khách du lịch theo mùa")

**Giá Trị Kinh Doanh**: Điều chỉnh chiến lược theo cụm (ví dụ: cửa hàng đô thị cần khuyến mãi khác cửa hàng nông thôn).

### 3. Kiểm Tra Hiệu Quả Khuyến Mãi

**Thiết Kế Thử Nghiệm:**
- **Nhóm kiểm soát**: Cửa hàng có lưu lượng điển hình (không có khuyến mãi)
- **Nhóm điều trị**: Cửa hàng có khuyến mãi
- **Số liệu**: So sánh **doanh số mỗi giao dịch** (giá trị giỏ hàng) giữa các nhóm

**Tại Sao Điều Này Hiệu Quả**: Nếu khuyến mãi tăng doanh số nhưng **không** tăng giao dịch, nghĩa là:
- Cùng lượng khách đến (lưu lượng không đổi)
- Nhưng họ mua nhiều hơn (giá trị giỏ hàng tăng)
- → Khuyến mãi bán thêm thành công cho lưu lượng hiện có

Nếu khuyến mãi tăng **cả** doanh số lẫn giao dịch, nghĩa là:
- Nhiều khách hàng hơn đến (lưu lượng tăng)
- → Khuyến mãi thu hút thành công khách mới

### 4. Lập Kế Hoạch Nhân Sự & Công Suất

**Thông Tin Có Thể Hành Động:**
- **Thứ Bảy cần thêm 26% thu ngân** so với Thứ Năm (để xử lý 1.953 vs. 1.550 giao dịch)
- **Đêm Giáng Sinh cần gấp đôi công suất** (lưu lượng gấp 2 lần bình thường)
- Cửa hàng lưu lượng thấp (<700/ngày) có thể dư thừa nhân sự nếu dùng cùng tỷ lệ như cửa hàng lưu lượng cao

**ROI**: Phân bổ nhân sự đúng mức giảm chi phí lao động trong khi duy trì chất lượng dịch vụ.

---

## Tích Hợp & Bước Tiếp Theo

### Tích Hợp Với Các Tập Dữ Liệu Khác

**Chiến Lược Kết Hợp:**
```python
# Kết hợp giao dịch vào dữ liệu doanh số (nhiều-một: nhiều nhóm mỗi ngày-cửa hàng)
df_train = df_train.merge(df_transactions[['date', 'store_nbr', 'transactions', 'is_imputed']],
                          on=['date', 'store_nbr'],
                          how='left')
```

**Kết Quả Dự Kiến**: Mỗi bản ghi ngày–cửa hàng–nhóm trong train.csv kế thừa cùng số lượng `transactions` (phát sóng).

**Kiểm Tra Xác Thực:**
1. **Căn chỉnh phạm vi ngày**: Xác minh transactions.csv bao phủ toàn bộ phạm vi ngày của train.csv
2. **Phủ sóng cửa hàng**: Tất cả 54 cửa hàng trong train.csv phải có dữ liệu giao dịch khớp
3. **Cờ điền thiếu**: Kiểm tra xem tỷ lệ `is_imputed` cao có tương quan với doanh số thấp không (xác nhận đóng cửa hàng)

### Feature Engineering Được Khuyến Nghị

**1. Đặc Trưng Lag** (nắm bắt động lực):
```python
# Lag mỗi cửa hàng
df_transactions['trans_lag_1'] = df_transactions.groupby('store_nbr')['transactions'].shift(1)
df_transactions['trans_lag_7'] = df_transactions.groupby('store_nbr')['transactions'].shift(7)
df_transactions['trans_lag_14'] = df_transactions.groupby('store_nbr')['transactions'].shift(14)
```

**2. Thống Kê Cuộn** (làm mịn nhiễu):
```python
# Trung bình cuộn 7 ngày mỗi cửa hàng
df_transactions['trans_roll_7'] = (
    df_transactions.groupby('store_nbr')['transactions']
    .rolling(7, min_periods=1).mean()
    .reset_index(level=0, drop=True)
)
```

**3. Tương Tác Cuối Tuần/Ngày Lễ:**
```python
# Đánh dấu cuối tuần
df_transactions['is_weekend'] = df_transactions['date'].dt.dayofweek.isin([5, 6]).astype(int)

# Tương tác: cuối tuần × loại cửa hàng (sau khi kết hợp stores.csv)
df_merged['weekend_effect'] = df_merged['is_weekend'] * (df_merged['type'] == 'A').astype(int)
```

**4. Lưu Lượng Chuẩn Hóa** (tính đến tính không đồng nhất cửa hàng):
```python
# Z-score mỗi cửa hàng (chuẩn hóa về mean=0, std=1)
store_stats = df_transactions.groupby('store_nbr')['transactions'].agg(['mean', 'std'])
df_transactions = df_transactions.merge(store_stats, on='store_nbr', suffixes=('', '_store'))
df_transactions['trans_zscore'] = (df_transactions['transactions'] - df_transactions['mean']) / df_transactions['std']
```

### Bước Tiếp Theo Để Xác Thực

**Hành Động Ngay:**

1. **Phân Tích Tương Quan:**
   ```python
   # Kết hợp giao dịch với doanh số, tính tương quan
   df_merged = df_train.merge(df_transactions, on=['date', 'store_nbr'])
   correlation = df_merged[['sales', 'transactions']].corr()
   # Kỳ vọng: tương quan dương (nhiều lưu lượng → nhiều doanh số hơn)
   ```

2. **Phân Tích Doanh Số Mỗi Giao Dịch:**
   ```python
   # Tính giá trị giỏ hàng
   df_merged['basket_size'] = df_merged['sales'] / df_merged['transactions'].replace(0, np.nan)
   # Phân tích: Giá trị giỏ hàng có thay đổi theo loại cửa hàng? Theo ngày trong tuần?
   ```

3. **Xác Thực Cờ Điền Thiếu:**
   ```python
   # So sánh doanh số trong ngày điền thiếu vs. không điền thiếu
   df_merged.groupby('is_imputed')['sales'].agg(['mean', 'median', 'sum'])
   # Kỳ vọng: ngày điền thiếu (cửa hàng đóng) có doanh số ~0
   ```

4. **Dòng Thời Gian Mở Cửa Hàng:**
   ```python
   # Xác định ngày hoạt động đầu tiên mỗi cửa hàng
   store_openings = df_transactions[df_transactions['is_imputed'] == 0].groupby('store_nbr')['date'].min()
   # Dùng để che giấu kỳ trước khi mở trong dữ liệu huấn luyện
   ```

---

## Kết Luận

Tập dữ liệu giao dịch là **chỉ số lưu lượng chất lượng cao, quan trọng cho kinh doanh** với tính nhất quán xuất sắc và giá trị chiến lược cho dự báo bán lẻ. Với chỉ 8,4% thưa thớt (được giải thích về mặt cấu trúc bởi mở cửa hàng/ngày lễ), nó cung cấp:

1. **Proxy hoạt động cửa hàng** để tách hiệu ứng lưu lượng khỏi nhu cầu sản phẩm cụ thể
2. **Tính mùa vụ hàng tuần mạnh mẽ** (26% uplift cuối tuần) cho mô hình hóa chuỗi thời gian
3. **Phát hiện đỉnh ngày lễ** (lưu lượng gấp 2 lần vào Đêm Giáng Sinh)
4. **Thông tin tính không đồng nhất cửa hàng** (phương sai 6,8 lần giữa cửa hàng bận nhất/yên tĩnh nhất)

**Điểm Mạnh Chính:**
- Không có giá trị thiếu trong dữ liệu thô (100% bản ghi đầy đủ)
- Không có trùng lặp (khóa chính sạch)
- Dữ liệu thiếu có thông tin cấu trúc (không phải vấn đề chất lượng dữ liệu)
- Phạm vi động rộng (0-8.359) nắm bắt phương sai thực tế

**Rủi Ro Chính:**
- Cần điền thiếu cho 8,4% bảng đầy đủ (giảm thiểu bởi cờ `is_imputed`)
- Cửa hàng mới mở (ví dụ: cửa hàng 52) có lịch sử thưa thớt — có thể cần mô hình riêng
- Hiệu ứng cuối tuần/ngày lễ đòi hỏi đặc trưng rõ ràng (mô hình sẽ không tự phát hiện nếu không mã hóa)

**Chỉ Số Thành Công:**
- Sau khi kết hợp với doanh số: Xác nhận tương quan dương giữa giao dịch và doanh số
- Tầm quan trọng đặc trưng: Xác thực đặc trưng dựa trên giao dịch nằm trong top 10 dự đoán
- Phân tích giá trị giỏ hàng: Xác định cửa hàng/ngày có tỷ lệ doanh số-mỗi-giao dịch bất thường

Tập dữ liệu này nên được **tích hợp ngay** vào quy trình dự báo — độ chi tiết cấp cửa hàng và mẫu thời gian của nó là thiết yếu để nắm bắt động lực bán hàng do lưu lượng thúc đẩy.
