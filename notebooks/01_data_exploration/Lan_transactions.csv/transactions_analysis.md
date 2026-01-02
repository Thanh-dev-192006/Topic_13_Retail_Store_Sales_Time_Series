# transactions_analysis.md

> Dataset: `transactions.csv` (Favorita Grocery Sales Forecasting)  
> Granularity: **store-day** (1 dòng = 1 cửa hàng trong 1 ngày)  
> Target use-case: proxy cho **foot traffic / store activity** để join vào `train.csv` (store_nbr + date)

## 1. Dataset overview

**Kích thước & coverage**
- Số dòng (raw): **83,488**
- Số cột: **3** (`date`, `store_nbr`, `transactions`)
- Số cửa hàng: **54** (`store_nbr` 1–54)
- Khoảng thời gian: **2013-01-01 → 2017-08-15** (**1,688 ngày**)

**Full panel expectation**
- Nếu đủ dữ liệu theo dạng panel: 1,688 ngày × 54 stores = **91,152 store-days**
- Thực tế raw có 83,488 store-days ⇒ thiếu **7,664 store-days** (**8.41%**) so với full panel

**Ý nghĩa business**
- `transactions` là số giao dịch tại cửa hàng trong ngày ⇒ phản ánh **mức độ đông khách / hoạt động**.  
- Khi join vào `train.csv`, biến này có thể giúp model tách bạch: “do store traffic” vs “do demand theo product family”.

---

## 2. Cấu trúc dữ liệu (dimensions, granularity)

**Dimensions / keys**
- Primary key kỳ vọng: (`date`, `store_nbr`)  
  - Kiểm tra raw: **0 duplicates** theo (`date`, `store_nbr`) ⇒ khoá hợp lệ.
- `transactions` là integer dương (min **5**, max **8,359**).

**Granularity**
- Store-level, không có `family`/`item`.  
- Khi join với `train.csv` (granularity là store-family-day), `transactions` sẽ được **broadcast** cho tất cả families trong cùng (store, date).

**So what (modeling)**
- Có thể dùng `transactions` như **exogenous regressor** ở cấp store-day: lag(1,7,14), rolling mean, holiday/weekend effects, v.v.
- Vì `transactions` không theo từng family ⇒ tránh overfit vào product-level noise; hữu ích cho baseline signals.

---

## 3. Patterns phát hiện được (có số liệu + business implications)

### 3.1 Weekly seasonality (ngày trong tuần)
Trung bình `transactions` theo **mỗi store-day**:
- **Saturday**: ~**1,953**
- **Sunday**: ~**1,847**
- Thấp nhất là **Thursday**: ~**1,550**

Chênh lệch Saturday vs Thursday: **+26%**.

**So what**
- Nên thêm feature **day-of-week** (one-hot hoặc cyclic) vì có seasonality rõ.
- Khi forecast sales, weekend uplift có thể xuất hiện đồng loạt across families, do traffic tăng.

### 3.2 Holiday / peak days (đặc biệt cuối năm)
Tổng transactions (cộng tất cả stores) ngày cao nhất:
- **2015-12-24**: **171,169** transactions
- Mức này ~**2.03×** trung bình daily total (~**84,114**)

Top days cao nhất đều rơi vào **23–24/12** các năm.

**So what**
- Cần feature **holiday / pre-holiday** (đặc biệt Christmas eve) vì spike rất mạnh.
- Nếu model không có holiday features, khả năng bị underpredict peak.

### 3.3 “Missing” mang tính vận hành (closures / store opening)
Thiếu store-days không phân bố ngẫu nhiên:

**A. Ngày đóng cửa toàn hệ thống (0 record)**
Có **6 ngày** hoàn toàn không có record trong raw:
- **25/12** các năm **2013–2015** và **2016-12-25**
- **2016-01-01** và **2016-01-03**

**B. Store mở muộn / hoạt động ngắn**
Ví dụ store **52** bắt đầu xuất hiện từ **2017-04-20** (chỉ **118 ngày** data) ⇒ thiếu **1,570/1,688 ngày** (**93%**).
Các store thiếu nhiều ngày tiếp theo:  
- store 22 thiếu **1,017 ngày** (**60%**)  
- store 42 thiếu **968 ngày** (**57%**)  
- store 21 thiếu **940 ngày** (**56%**)  
- store 29 thiếu **814 ngày** (**48%**)

**So what**
- “Missing” ở đây phần lớn phản ánh **store chưa mở / store đóng cửa ngày lễ**, chứ không phải lỗi thu thập ngẫu nhiên.
- Khi làm feature engineering, nên có cờ `is_imputed` hoặc `is_open` để model phân biệt “0 vì đóng cửa” vs “0 vì thật sự không có giao dịch”.
- Nếu đánh đồng mọi missing = 0 mà không có cờ, model có thể học sai cho các store mở muộn.

### 3.4 Heterogeneity giữa stores (mức độ bận rộn khác nhau)
Mean transactions theo store có độ chênh lớn:
- Store cao nhất (store 44): ~**4,337** / store-day
- Store thấp nhất (store 26): ~**635** / store-day  
⇒ Tỷ lệ khoảng **6.8×**.

**So what**
- Nên scale/normalize theo store (store embeddings, store fixed effects) hoặc tạo features theo store (rolling mean per store).
- Không nên dùng 1 ngưỡng outlier chung cho mọi store vì base level khác nhau.

---

## 4. Vấn đề chất lượng dữ liệu & cách xử lý

### 4.1 Missing store-days (8.41% so với full panel)
**Issue:** thiếu record cho một số (store, date).  
**Decision:** tạo full grid (mọi ngày × mọi store) và **impute `transactions = 0`** cho các (store, date) thiếu, đồng thời thêm cột:
- `is_imputed` = 1 nếu dòng được bổ sung
- `is_imputed` = 0 nếu có trong raw

**Rationale**
- Với bài toán time series panel, full grid giúp tạo lag/rolling features nhất quán.
- Trong bối cảnh retail, thiếu record thường tương ứng **đóng cửa / store chưa hoạt động** ⇒ 0 là hợp lý, nhưng cần cờ để model biết đây là imputed.

### 4.2 Datatype & validation
- `date`: convert sang datetime, đảm bảo sort theo thời gian
- `store_nbr`: int
- `transactions`: int, kiểm tra min/max (không có giá trị âm, không có missing)

### 4.3 Duplicates
- Kiểm tra duplicates theo (`date`, `store_nbr`): **0** ⇒ không cần xử lý.

---

## 5. Ghi chú integration (join keys, quan hệ với datasets khác)

**Join keys**
- Với `train.csv`: join on (`date`, `store_nbr`)  
  - `train` có thêm `family` ⇒ quan hệ là **many-to-one** (nhiều family cùng 1 store-day share cùng transactions).
- Với `stores.csv`: join on (`store_nbr`)  
  - thêm metadata (city, state, cluster, type) ⇒ useful để explain heterogeneity.
- Với `oil.csv`: join on (`date`)  
  - oil là global-level ⇒ join many-to-one (mọi store-day trong cùng ngày share cùng giá dầu).
- Với `holidays_events.csv`: join chủ yếu theo `date` (và có thể theo `locale/locale_name` nếu map được store → city/state)  
  - nên chú ý holiday theo **locale** để tạo feature đúng cấp.

**Gợi ý join order**
1. Start từ `train` (store-family-day)  
2. Left join `transactions` theo (store, date)  
3. Join `stores` theo store_nbr  
4. Join `oil` theo date  
5. Join `holidays` theo date + locale mapping

---

## 6. Đề xuất next steps

1. **Feature engineering** từ transactions:
   - Lag features: t-1, t-7, t-14, t-28
   - Rolling mean/sum theo store: 7D, 28D
   - Weekend/holiday interaction: `is_weekend × rolling_mean`
2. **Store activity flags**
   - Tạo `is_open` (1 nếu raw có record, 0 nếu imputed) hoặc dùng `is_imputed` ngược lại.
   - Xem xét **mask**/exclude giai đoạn trước khi store mở (store 52, 22, 42, …) nếu model nhạy cảm với chuỗi dài toàn 0.
3. **Consistency check với train**
   - Kiểm tra overlap date range với `train.csv` và đảm bảo join không tạo missing bất ngờ.
4. **Business sanity checks**
   - Verify spike quanh Christmas eve bằng `holidays_events.csv` (pre-holiday effect) và xem có patterns tương tự quanh các dịp khác.

---

## Appendix: Key metrics (quick reference)

| Metric | Value |
|---|---:|
| Raw rows | 83,488 |
| Columns | 3 |
| Stores | 54 |
| Date range | 2013-01-01 → 2017-08-15 |
| Days (inclusive) | 1,688 |
| Expected full panel | 91,152 |
| Missing store-days | 7,664 (8.41%) |
| Max daily total transactions | 171,169 (2015-12-24) |
| Weekend uplift (Sat vs Thu mean) | +26% |
