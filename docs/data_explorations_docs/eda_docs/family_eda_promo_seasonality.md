## 1. MỤC ĐÍCH: TẠI SAO FILE NÀY TỒN TẠI?

Trong quy trình xây dựng mô hình AI dự báo doanh số, việc vội vàng đưa dữ liệu thô vào mô hình là nguyên nhân hàng đầu dẫn đến thất bại. File notebook `family_eda_promo_seasonality.ipynb` được sinh ra để đóng vai trò "Trinh sát", giải quyết 3 nhiệm vụ cốt lõi mà sếp và đội ngũ kỹ thuật cần biết:

1.  **Định vị trọng tâm:** Xác định xem "nồi cơm" của doanh nghiệp nằm ở nhóm hàng nào (để ưu tiên nguồn lực tối ưu hóa cho nhóm đó).
2.  **Giải mã hành vi:** Hiểu rõ thói quen mua sắm của khách hàng theo thời gian (Mùa vụ, cuối tuần, lễ tết).
3.  **Đánh giá đòn bẩy:** Trả lời câu hỏi "Chạy khuyến mãi (Promotion) có thực sự tăng doanh số không?" để quyết định chiến lược Marketing.

> **Tóm lại:** File này chuyển hóa dữ liệu thô thành **Chiến lược chọn Mô hình (Model Selection)** và **Chiến lược tạo đặc trưng (Feature Engineering)**.

---

## 2. QUY TRÌNH THỰC HIỆN (WORKFLOW)

Để đi đến kết luận, notebook này đã thực hiện quy trình 4 bước chặt chẽ:

* **Bước 1: Nạp & Làm sạch (Load & Clean):** Đọc dữ liệu bán hàng, chuẩn hóa định dạng thời gian.
* **Bước 2: Gom nhóm (Aggregation):** Thay vì nhìn vào từng cửa hàng nhỏ lẻ (nhiễu cao), ta gom doanh số lại theo **Nhóm hàng (Family)**. Việc này giúp nhìn thấy xu hướng chung của toàn thị trường rõ nét hơn.
* **Bước 3: Tính toán chỉ số KPI:** Tạo ra các thước đo quan trọng:
    * *Sales Share:* Tỷ trọng đóng góp doanh thu.
    * *Seasonality Index:* Chỉ số mùa vụ (bán chạy gấp mấy lần ngày thường).
    * *Promo Lift:* Sức bật doanh số khi có khuyến mãi.
* **Bước 4: Trực quan hóa (Visualization):** Vẽ 7 biểu đồ chi tiết để mổ xẻ dữ liệu (phân tích kỹ ở phần 3).

---

## 3. PHÂN TÍCH CHI TIẾT & INSIGHT TỪNG BIỂU ĐỒ (CHART-BY-CHART ANALYSIS)

Đây là phần quan trọng nhất. Chúng ta sẽ đi qua từng biểu đồ để hiểu dữ liệu đang "kể" câu chuyện gì.

###  3.1. Bar Chart: Top 15 Product Families (Top 15 Nhóm hàng)
*(Biểu đồ cột ngang xếp hạng tổng doanh thu)*

* **Mô tả:** Trục tung là tên nhóm hàng, trục hoành là tổng doanh số tích lũy.
* ** Insight (Điều nhìn thấy):**
    * Thị trường bị chi phối hoàn toàn bởi **GROCERY I** (Tạp hóa) và **BEVERAGES** (Đồ uống). Cột doanh số của chúng dài vượt trội so với phần còn lại.
    * Các nhóm hàng đuôi (như Books, Baby Care) có cột rất ngắn, đóng góp doanh thu không đáng kể.
* ** Hành động (Action Needs):**
    * Khi huấn luyện AI, cần đặt **Trọng số (Sample Weight)** cao nhất cho Grocery và Beverages. Nếu dự báo sai 1% ở đây, thiệt hại lớn hơn sai 50% ở nhóm Sách.

###  3.2. Pie Chart: Sales Composition (Cơ cấu doanh thu)
*(Biểu đồ tròn thể hiện thị phần Top 10 vs Others)*

* **Mô tả:** Miếng bánh thị phần của Top 10 nhóm hàng so với phần còn lại.
* ** Insight:**
    * Xác nhận quy luật **Pareto (80/20)**: Chỉ cần khoảng 6-7 nhóm hàng chủ lực đã chiếm tới ~80% tổng doanh thu của chuỗi siêu thị.
* ** Hành động:**
    * Chiến lược "Chia để trị": Có thể xây dựng một mô hình phức tạp, chính xác cao cho Top 10. Các nhóm hàng nhỏ còn lại ("Others") có thể dùng mô hình đơn giản hơn để tiết kiệm chi phí tính toán mà không ảnh hưởng nhiều đến tổng kết quả.

###  3.3. Stacked Area Chart: Sales Contribution Over Time
*(Biểu đồ miền xếp chồng theo thời gian)*

* **Mô tả:** Các dải màu chồng lên nhau thể hiện doanh số qua các năm (2013-2017).
* ** Insight:**
    * **Sự ổn định:** Các nhóm thiết yếu (Grocery) duy trì dải màu dày và đều đặn.
    * ** Cú sốc mùa vụ (Quan trọng):** Hãy nhìn nhóm **SCHOOL AND OFFICE SUPPLIES**. Bình thường dải màu của nó mỏng dính (bán ế), nhưng cứ đến **Tháng 8-9** hàng năm lại phình to đột ngột. Đây là mùa tựu trường tại khu vực Sierra (Ecuador).
* ** Hành động:**
    * **Bắt buộc:** Phải tạo biến `is_school_season` (tháng 8, 9 = 1, còn lại = 0).
    * **Lưu ý:** Không được dùng kỹ thuật trung bình trượt (Moving Average) cho nhóm này vì nó sẽ san bằng cái đỉnh nhọn kia, dẫn đến dự báo sai trầm trọng (Under-forecasting).

###  3.4. Seasonality Heatmap (Bản đồ nhiệt mùa vụ)
*(Biểu đồ nhiệt: Trục ngang là Thứ/Tháng, màu càng đậm là bán càng chạy)*

* **Mô tả:** Soi sức mua chi tiết theo lịch.
* ** Insight:**
    * **Hiệu ứng cuối tuần:** Ở hầu hết các nhóm (Thịt, Sữa, Bia), các ô tương ứng với **Thứ 7, Chủ Nhật** có màu đậm nhất.
    * **Hiệu ứng tháng:** Nhóm *Beverages/Liquor* đậm màu vào tháng 12 (Lễ hội). Nhóm *School* đậm màu tháng 8, 9.
* ** Hành động:**
    * Mô hình cần các đặc trưng (Features): `day_of_week` (0-6), `is_weekend` (0/1), `month_of_year` (1-12). Máy sẽ học quy luật: "Cứ thấy cuối tuần là tự động cộng thêm doanh số".

###  3.5. Box Plots: Daily Sales Distribution
*(Biểu đồ hộp đo lường độ biến động)*

* **Mô tả:** Hộp càng dài = Doanh số trồi sụt thất thường. Hộp càng ngắn = Doanh số ổn định.
* ** Insight:**
    * Nhóm **PRODUCE** (Rau củ) và **MEATS** (Thịt) có cái hộp rất dài và nhiều chấm đen (outliers) phía trên. Lý do: Đây là hàng tươi sống, phụ thuộc ngày nhập hàng và cuối tuần, rất khó đoán.
    * Nhóm **BREAD** (Bánh mì) có hộp ngắn, doanh số bán ra đều đặn mỗi ngày.
* ** Hành động:**
    * Với nhóm biến động cao (Produce), cần thêm các biến trễ (**Lag Features**): Doanh số của 1 ngày trước, 7 ngày trước để mô hình bám sát biến động.

###  3.6. Promo Comparison (Bar Chart - Hiệu quả Khuyến mãi)
*(So sánh doanh số: Cột Không KM vs Cột Có KM)*

* **Mô tả:** Hai cột cạnh nhau. Chênh lệch chiều cao cho thấy hiệu quả khuyến mãi.
* ** Insight:**
    * **Nhóm nhạy cảm:** Tạp hóa, Tẩy rửa (Cleaning), Chăm sóc cá nhân có cột "Promo" cao gấp 2-3 lần cột "No Promo". -> Khách chờ giảm giá mới mua.
    * **Nhóm thờ ơ:** Xăng dầu, Bánh mì, Rượu... chênh lệch rất ít.
* ** Hành động:**
    * Biến `on_promotion` là biến quan trọng nhất (Top Feature) cho nhóm Tạp hóa.
    * Với nhóm thờ ơ, khuyến mãi không phải là yếu tố dự báo chính, có thể giảm trọng số của biến này.

###  3.7. Trends (Line Chart - Xu hướng)
*(Biểu đồ đường trung bình trượt 7 ngày)*

* **Mô tả:** Đường đi của doanh số theo thời gian.
* ** Insight:**
    * Xu hướng chung là đi lên (Uptrend).
    * **Sự kiện Ngoại lai (Outlier):** Có một đoạn gãy khúc hoặc tăng vọt bất thường vào **Tháng 4/2016**. Đây là hệ quả của trận động đất lớn tại Ecuador năm 2016.
* ** Hành động:**
    * **Xử lý dữ liệu:** Cần đánh dấu đoạn này bằng biến `is_earthquake` hoặc thay thế dữ liệu đoạn này bằng giá trị trung bình để mô hình không học sai quy luật bình thường.

---

## 4. KẾT LUẬN & CHIẾN LƯỢC TIẾP THEO

Từ những phân tích trên, file này đã hoàn thành nhiệm vụ và đưa ra chiến lược cụ thể cho bước tiếp theo (Modeling):

1.  **Chiến lược Mô hình hóa:**
    * Không dùng "một size cho tất cả".
    * Tách riêng chiến thuật cho nhóm **High Volume** (Grocery, Beverage) và nhóm **Seasonal/Sparse** (School Supplies, Books).

2.  **Chiến lược Feature Engineering (Tạo đặc trưng):**
    * **Phải có:** `DayOfWeek`, `IsWeekend` (Bắt hiệu ứng cuối tuần).
    * **Phải có:** `IsSchoolSeason` (Bắt cú sốc tháng 8-9).
    * **Phải có:** `OnPromotion` (Bắt hiệu ứng giá).
    * **Phải có:** `IsEarthquake` (Xử lý nhiễu năm 2016).

3.  **Chiến lược Xử lý dữ liệu:**
    * Các nhóm hàng có nhiều số 0 (Books, Baby Care) nên được xử lý bằng các mô hình chuyên biệt cho dữ liệu thưa (như Tweedie Regression) thay vì RMSE thông thường.

> **Tổng kết:** Báo cáo này cung cấp bản đồ chỉ đường chi tiết, giúp đội ngũ kỹ thuật tránh đi đường vòng và tập trung vào những yếu tố thực sự tạo ra doanh số.