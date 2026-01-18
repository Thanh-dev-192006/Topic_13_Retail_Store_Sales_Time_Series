# Báo cáo Phân tích External Drivers: Oil, Holidays & Seasonality
**Dự án:** Store Sales - Time Series Forecasting (Kaggle Favorita)

## 1. Phân tích Giá Dầu (Oil Price Analysis)
*Mục tiêu: Kiểm chứng giả thuyết kinh tế vĩ mô về tác động của giá dầu lên doanh số bán lẻ.*

### A. Oil Price vs Sales Timeline (Biểu đồ đường)
* **Quan sát:** Biểu đồ thể hiện hai xu hướng dài hạn trái ngược. Giá dầu (đường đỏ) giảm sâu từ năm 2014-2015, trong khi Doanh số (đường xanh) có xu hướng tăng trưởng đều đặn theo thời gian.
* **Insight:** Không có sự đồng pha ngắn hạn. Giá dầu giảm không kéo theo doanh số giảm ngay lập tức. Sự tăng trưởng của Sales chủ yếu do quy mô doanh nghiệp mở rộng (Trend).

### B. Scatter Plot (Biểu đồ phân tán)
* **Quan sát:** Các điểm dữ liệu phân bố thành hình đám mây ngang hoặc khối tròn, không tạo thành đường chéo rõ rệt.
* **Insight:** Hệ số tương quan (Correlation) rất thấp hoặc âm nhẹ (-0.5). Đây là **Tương quan giả (Spurious Correlation)** do hai xu hướng dài hạn đi ngược chiều nhau, không phải quan hệ nhân quả.

### C. Lag Correlation (Biểu đồ nhiệt độ trễ)
* **Quan sát:** Các biến `oil_lag_1`, `oil_lag_7`, `oil_lag_30` đều có màu nhạt (tương quan thấp) so với `sales_lag_365`.
* **Kết luận:** Việc cố gắng tìm độ trễ của giá dầu (ví dụ: dầu giảm hôm nay thì 30 ngày sau sales tăng) không mang lại giá trị dự báo đáng kể.

---

## 2. Phân tích Ngày Lễ (Holiday Analysis)
*Mục tiêu: Xác định hành vi mua sắm trong các dịp đặc biệt.*

### A. Impact: Normal vs Holiday (Boxplot)
* **Quan sát:** Hộp dữ liệu của ngày lễ (`Holiday Event`) thường có biên độ rộng hơn và trung vị (median) cao hơn nhẹ so với ngày thường.
* **Insight:** Ngày lễ có tác động tích cực, nhưng không đồng đều (có lễ bán rất chạy, có lễ bình thường).

### B. Sales by Holiday Type (Biểu đồ cột)
* **Quan sát:**
    * **Bridge (Ngày cầu):** Doanh số thường cao nhất. Đây là các ngày nghỉ kẹp giữa lễ và cuối tuần, kích cầu mua sắm/du lịch mạnh.
    * **Transfer (Nghỉ bù):** Doanh số cao hơn ngày lễ gốc.
* **Hành động:** Feature `holiday_type` là bắt buộc phải có trong model.

### C. Sales Pattern: Before/During/After (Boxplot)
* **Quan sát:** Nhóm `Before Holiday` (Trước lễ 2 ngày) thường có doanh số cao hơn hoặc bằng `During Holiday`.
* **Insight:** Hiệu ứng **"Tích trữ" (Stockpiling)**. Người dân mua thực phẩm dự trữ trước khi siêu thị đóng cửa hoặc trước khi đi nghỉ dài ngày.
* **Hành động:** Cần tạo feature `days_to_next_holiday` (đếm ngược đến ngày lễ) để bắt được xu hướng này.

---

## 3. Phân tích Cấu trúc Chuỗi thời gian (Advanced Time Series)
*Mục tiêu: Hiểu rõ quy luật vận động nội tại của dữ liệu.*

### A. STL Decomposition (Phân rã chuỗi)
* **Trend:** Đường đi lên đều đặn. $\rightarrow$ Doanh nghiệp đang tăng trưởng tốt.
* **Seasonal:** Dao động hình sin đều đặn (như nhịp tim). $\rightarrow$ Xác nhận tính mùa vụ theo tuần (Weekly Seasonality) rất mạnh.
* **Resid (Nhiễu):** Các gai nhọn bất thường (đặc biệt là tháng 4/2016).

### B. ACF & PACF (Tự tương quan)
* **ACF (Autocorrelation):** Các đỉnh cao vút ở Lag 7, 14, 21.
    * *Ý nghĩa:* Doanh số có "trí nhớ" theo chu kỳ 7 ngày (Chủ Nhật tuần này giống Chủ Nhật tuần trước).
* **PACF (Partial Autocorrelation):** Cột cao nhất ở Lag 1 và Lag 7.
    * *Ý nghĩa:* Doanh số hôm nay phụ thuộc trực tiếp nhất vào **Hôm qua** và **Ngày này tuần trước**.

### C. Correlation Matrix with Lag 365 (Biểu đồ nhiệt tổng hợp)
* **Quan sát:** `sales_lag_365` có màu đỏ đậm nhất (Tương quan dương mạnh nhất).
* **Kết luận:** Dữ liệu lịch sử cùng kỳ năm ngoái là yếu tố dự báo mạnh mẽ nhất, vượt xa các yếu tố ngoại sinh như giá dầu.

---

## 4. Phân tích Sự kiện & Bất thường (Event Analysis)

### A. Weekly Heatmap
* **Quan sát:** Vùng màu đậm luôn xuất hiện ở Tuần 51-52 hàng năm.
* **Insight:** Giáng sinh và Năm mới là mùa cao điểm nhất trong năm.

### B. Earthquake Impact (Động đất 2016)
* **Quan sát:** Một cú nhảy vọt (Spike) dựng đứng vào ngày 16/04/2016, kéo dài khoảng 2 tuần.
* **Insight:** Panic Buying (Mua sắm hoảng loạn) sau thiên tai.
* **Hành động:** Đây là **Outlier (Nhiễu)**. Cần tạo biến `is_earthquake` hoặc xử lý (smooth) giai đoạn này để tránh model học sai quy luật cho các năm sau.

---

## 5. Tổng kết & Đề xuất Feature Engineering

Dựa trên các phân tích trên, chiến lược xây dựng model sẽ tập trung vào:

1.  **Lags Features:** Ưu tiên tạo `Lag_1`, `Lag_7`, `Lag_365`.
2.  **Calendar Features:** `day_of_week`, `day_of_month` (để bắt Payday), `month`.
3.  **Holiday Features:** `holiday_type` (đặc biệt chú ý Bridge/Transfer), `days_to_next_holiday`.
4.  **Oil Features:** Sử dụng như một biến phụ trợ (có thể dùng Rolling Mean 30 ngày thay vì giá hàng ngày), không đặt trọng số quá cao.
5.  **Event Handling:** Gắn cờ riêng cho sự kiện Động đất 2016.