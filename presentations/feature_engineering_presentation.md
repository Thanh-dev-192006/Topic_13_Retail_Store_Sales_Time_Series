# Layout Slide Thuyết Trình: Tiền xử lý & Kỹ nghệ Đặc trưng (Feature Engineering)

**Chủ đề:** Dự báo Doanh số Bán lẻ Chuỗi Cửa hàng Favorita (Ecuador)  
**Tổng số slide:** 12

---

## Slide 1: Tiêu đề
- **Tiêu đề lớn:** Dự báo Doanh số Bán lẻ - Giai đoạn Tiền xử lý & Feature Engineering.
- **Phụ đề:** Tối ưu hóa Dữ liệu Chuỗi Thời Gian cho Mô Hình Máy Học.
- **Nội dung:** Tên người trình bày / Tên Nhóm và Ngày tháng.

---

## Slide 2: Tổng quan Pipeline Dữ liệu
- **Tiêu đề:** Tổng quan Quá trình Chuẩn bị Dữ liệu.
- **Hình ảnh gợi ý:** Sơ đồ luồng (Flowchart) từ Dữ liệu thô $\rightarrow$ Làm sạch $\rightarrow$ Kiểm tra Tính Dừng $\rightarrow$ Kỹ nghệ Đặc trưng (Calendar, Oil, Holiday, Target, Lag) $\rightarrow$ Tập Dữ liệu Cuối cùng.
- **Bullet points:**
  - Tiền xử lý và Stationarity Checks (Kiểm định chuỗi dừng).
  - Tích hợp dữ liệu đa nguồn (Kinh tế vĩ mô, Lịch, Địa lý).
  - Tránh rò rỉ dữ liệu (Data Leakage) khi tạo đặc trưng.

---

## Slide 3: Tiền xử lý - Khám phá Tính Dừng (Stationarity Checks)
- **Tiêu đề:** Khám phá Tính Dừng (Stationarity) của Dữ liệu Doanh số
- **Mục đích:** Mô hình AR/MA/ARIMA truyền thống yêu cầu chuỗi thời gian phải dừng (Stationary) - tức là trung bình (mean) và phương sai (variance) không đổi theo thời gian.
- **Nội dung:** Giới thiệu phương pháp kiểm định kép để xác nhận tính dừng dựa trên file `01_stationarity_checks.ipynb`.
  - **ADF Test (Augmented Dickey-Fuller):** 
    - Giả thuyết H0: Chuỗi có nghiệm đơn vị (Unit root) $\rightarrow$ Không dừng.
  - **KPSS Test (Kwiatkowski-Phillips-Schmidt-Shin):** 
    - Giả thuyết H0: Chuỗi có tính dừng (Level/Trend stationary).
  - Phân tích biểu đồ **Chuỗi gốc (Raw Series)**, đường trung bình động (Rolling Mean) và độ lệch chuẩn. Nếu đường Rolling Mean trôi đi theo thời gian, đó là dấu hiệu của sự không dừng.

---

## Slide 4: Kết quả Stationarity - Phân rã & Sai phân
- **Tiêu đề:** Kết quả Kiểm định & Khử Tính Không dừng (Differencing)
- **Nội dung:**
  - **Seasonal Decomposition (Phân rã chu kỳ):** Sử dụng Additive model (period=7) phát hiện sức mạnh của Trend và Seasonality trong doanh số toàn quốc. ACF & PACF plots minh họa rõ chu kỳ tuần rải rác.
  - **Kết quả Kiểm định Gốc (Original Series):** Thường bị sai lệch ở ADF và KPSS $\rightarrow$ Cần thực hiện sai phân.
  - **Giải pháp - Tự động hóa Sai phân (Differencing):**
    - Sử dụng hàm `ndiffs` từ thư viện `pmdarima` để tự động dò tìm bậc vi phân tối ưu $d$.
    - Bậc `d` an toàn nhất (recommended_d) sẽ được tổng hợp từ kết quả của cả ADF và KPSS.
  - **Khuyến nghị tiếp theo:** Quá trình tự động đề xuất tham số $d$ sẽ tiết kiệm thời gian, dùng để định hình Order cho lưới Hyperparameter Tuning của các mô hình ARIMA/SARIMA sau này. Dữ liệu tĩnh (đã differenced) được lưu lại chờ cho vòng đời lập mô hình tại `06_modeling`.

---

## Slide 5: Feature Engineering - Đặc trưng Thời gian (Temporal)
- **Tiêu đề:** Khai phá Chu kỳ Thời gian Khách hàng.
- **Nội dung:** Các đặc trưng thời gian trích xuất từ cột Date:
  - **Đơn vị lịch:** `year`, `quarter`, `month`, `week_of_year`, `day_of_week`.
  - **Cờ nhị phân (Binary Flags):** Đầu tháng (`is_month_start`), Cuối tháng (`is_month_end`), Cuối tuần (`is_weekend`).
  - **Điểm nhấn:** Cờ `is_payday` (Ngày 15 và cuối tháng). Ở Ecuador, chu kỳ phát lương có tương quan cực mạnh với các đợt tăng cao điểm (spikes) trong doanh số.

---

## Slide 6: Feature Engineering - Yếu tố Vĩ mô (Giá Dầu)
- **Tiêu đề:** Dữ liệu Ngoại lai - Sự phụ thuộc vào Giá Dầu (Oil Price).
- **Nội dung:**
  - Kinh tế Ecuador phụ thuộc mạnh vào xuất khẩu dầu mỏ, tác động dòng tiền tiêu dùng trực tiếp.
  - **Xử lý:** Missing values vào cuối tuần được điền bằng lệnh Forward Fill (`ffill`).
  - **Đặc trưng phái sinh:**
    - Giá dầu của tuần trước, 2 tuần trước (`oil_price_lag_7`, `oil_price_lag_14`).
    - Đường trung bình động 28 ngày (`oil_price_rolling_mean_28`) làm mịn nhiễu ngắn hạn.
    - Tỷ lệ thay đổi (`oil_price_change_pct`) so với 7 ngày trước để đo lường "Cú sốc giá" (Price shock).

---

## Slide 7: Feature Engineering - Ngày lễ & Sự kiện (Holidays)
- **Tiêu đề:** Ngày Lễ và Hiệu ứng Địa lý.
- **Nội dung:**
  - Lịch Ecuador có hệ thống ngày lễ phức tạp với ngày dời lịch (Transferred holidays). Chỉ giữ lại ngày nghỉ thực tế.
  - Phân vùng địa lý thông minh: Khớp ngày lễ theo **National** (toàn quốc), **Regional** (Bang/Tỉnh), và **Local** (Thành phố).
  - Cờ nhận diện riêng lễ hội lớn Carnaval (`is_carnaval`) do sức ảnh hưởng mạnh đến nhu cầu sắm sửa.

---

## Slide 8: Feature Engineering - Giai đoạn Lan Toả (Halo Effect)
- **Tiêu đề:** Hiệu ứng Lan Toả của Ngày Lễ (Halo Effect).
- **Nội dung:** Hàng hóa có xu hướng bán chạy **trước** ngày lễ (tâm lý tích trữ) và sụt giảm **sau** đó.
  - Đo lường khoảng cách thời gian liền kề:
    - Số ngày đếm ngược cho đến ngày lễ tiếp theo (`days_to_next_holiday`).
    - Số ngày trôi qua kể từ ngày lễ gần nhất (`days_after_last_holiday`).
  - *Mở rộng:* Cờ ảnh hưởng từ sự kiện động đất thảm họa tháng 4/2016 kéo lượng mua hàng cứu trợ tăng vọt tại một số khu vực.

---

## Slide 9: Feature Engineering - Đặc trưng Cửa hàng
- **Tiêu đề:** Mã hóa Thuộc tính Cửa hàng (Store Encoding).
- **Nội dung:**
  - Tại sao không dùng One-Hot Encoding cho 54 cửa hàng? Tránh số chiều không gian biến (Curse of Dimensionality) quá lớn.
  - Phương pháp thay thế:
    - **Label Encoding** cho phân loại cửa hàng (`store_type`).
    - **Frequency Encoding** cho vùng miền (`city` và `state`), giúp thuật toán phân tách được quy mô và mật độ của các đô thị so với vùng ven.

---

## Slide 10: Feature Engineering - Trễ & Trung bình Động (Lag/Rolling)
- **Tiêu đề:** Đặc trưng Tự Hồi Quy (Lag & Rolling).
- **Nội dung:** Sử dụng diễn biến quá khứ để định hình quy luật tương lai.
  - **Lags:** $t-1, t-2, t-3$ (Động lượng mua sắm tức thời), $t-7, t-14, t-364$ (Biến động chu kỳ tuần/năm).
  - **Rolling Stats:** Đường trung bình $7, 14, 28$ ngày qua, kèm theo Độ lệch chuẩn $7$ ngày đo lường mức độ bất ổn (volatility).
  - **Bắt buộc:** Phải sắp xếp dữ liệu (Sort) theo Store - Family - Date.

---

## Slide 11: Ngăn chặn rò rỉ dữ liệu (Data Leakage)
- **Tiêu đề:** Chiến lược Chống Rò Rỉ Dữ Liệu Toàn diện.
- **Nội dung:**
  - Đối với chuỗi thời gian, nghiêm cấm sử dụng dữ liệu tương lai để tính feature hiện tại.
  - **Quy tắc `.shift(1)`:** Tất cả phép tính Rolling window (ví dụ: `rolling_mean_7` của doanh số hoặc Transaction) đều phải dịch lùi 1 thời điểm.
  - **Target Encoding cho Cặp Store-Family (`store_family_te`):** Thay vì dùng Mean toàn cục dễ gây Overfit.
    - Sử dụng **KFold Out-of-fold (OOF) Encoding** (với n_splits=5).
    - Phép tính phân bổ Mean chỉ dùng trên các K-1 folds còn lại, kết hợp hệ số `smoothing=10` để làm trơn các nhóm có ít dữ liệu, đảm bảo Test Set là unseen.

---

## Slide 12: Tổng kết & Bước tiếp theo
- **Tiêu đề:** Sẵn sàng cho Giai đoạn Mô hình Hóa.
- **Nội dung:**
  - Thành quả: Từ bộ dữ liệu rất mỏng (6 cột) ban đầu, chúng ta đã phát triển thành ma trận mở rộng với hàng tá đặc trưng (Temporal, Macros, Trend, Lag...) chứa tín hiệu mạnh mẽ.
  - Các đặc trưng đã sẵn sàng để truyền vào các thuật toán dự báo phi tuyến tính dựa trên cây quyết định định hướng.
  - **Bước tiếp theo:** Training các model như LightGBM, XGBoost, CatBoost, và các kỹ thuật Model Ensembling cho chuỗi thời gian.
