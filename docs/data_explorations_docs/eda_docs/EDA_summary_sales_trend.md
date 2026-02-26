# Tóm Tắt EDA: Xu Hướng và Phân Phối Doanh Số Tổng Thể

**Notebook nguồn:** `notebooks/03_eda_deep_dive/Thanh_eda/Overall_sales_growth.ipynb`
**Câu hỏi kinh doanh được giải đáp:** Q1, Q7
**Cập nhật lần cuối:** 2026-02-21

---

## Phát Hiện Chính

### Phát Hiện 1: Doanh Số Tăng Từ 140 Triệu USD Lên 288 Triệu USD (2013-2016) Với Xu Hướng Tăng Mạnh
**Biểu đồ:** Biểu đồ đường kép — bảng trên: doanh số hàng ngày đã được giới hạn 2013-2017; bảng dưới: tổng doanh số hàng tháng với trung bình trượt 3 tháng (Biểu đồ 17)
**Quan sát:** Tổng doanh số hàng năm: 2013=140,4 triệu USD, 2014=209,5 triệu USD, 2015=240,9 triệu USD, 2016=288,7 triệu USD, 2017=194,2 triệu USD (một phần năm, chỉ tháng 1-8). Tăng trưởng theo năm: 2014=+49,2%, 2015=+15,0%, 2016=+19,8%. CAGR từ 2013 đến 2016 là 8,45%. Bảng hàng ngày (trên) cho thấy nhiễu hàng tuần tần số cao trên xu hướng tăng trưởng cơ bản. Bảng hàng tháng với trung bình trượt 3 tháng (dưới) tách rõ ràng quỹ đạo tăng trưởng và tiết lộ đỉnh tháng 12 và đáy tháng 2 mỗi năm. Đỉnh tháng 4 năm 2016 có thể thấy trong cả hai bảng, do trận động đất Ecuador (mua sắm hoảng loạn). Năm 2017 không đầy đủ (-32,7% so với 2016) phản ánh dữ liệu không đầy đủ (chỉ 8 tháng), không phải sự sụt giảm thực sự.
**Hàm Ý Feature Engineering:** Xu hướng tăng đơn điệu từ 2013-2016 phải được nắm bắt. Đưa vào `year` như feature số hoặc `days_since_epoch` (ngày kể từ 2013-01-01) để cho phép mô hình học độ dốc xu hướng. Bước khử xu hướng (trừ thành phần xu hướng) trước khi mô hình hóa tính mùa vụ là phương án thay thế. Không mô hình hóa dữ liệu 2017 một phần như đường cơ sở toàn năm — che đi hoặc giảm trọng số dữ liệu 2017 khi tính thống kê hàng năm.

### Phát Hiện 2: Phân Rã STL Xác Nhận Xu Hướng, Tính Mùa Vụ Hàng Năm Ổn Định và Phần Dư Động Đất
**Biểu đồ:** Phân rã STL 4 bảng — Quan sát / Xu hướng / Tính mùa vụ / Phần dư, mô hình nhân tính, khoảng=365 (Biểu đồ 18)
**Quan sát:** Thành phần Xu hướng cho thấy tăng trưởng lên đơn điệu đến 2016, sau đó 2017 một phần. Thành phần Mùa vụ cho thấy sóng hàng năm ổn định, lặp lại với tháng 12 là đỉnh nhất quán và tháng 2 là đáy nhất quán — mẫu này giống hệt nhau qua tất cả 5 năm, xác nhận rằng tính mùa vụ hàng năm không thay đổi về mặt cấu trúc. Thành phần Phần dư chủ yếu phẳng (gần 1,0 trong mô hình nhân tính) suốt chuỗi, với một đỉnh rõ ràng vào tháng 4 năm 2016. Đỉnh này trong phần dư — không phải trong thành phần mùa vụ — xác nhận hiệu ứng động đất là điểm bất thường, không phải mẫu mùa vụ học được.
**Hàm Ý Feature Engineering:** Kết quả STL xác nhận bộ feature sau là đủ để nắm bắt cấu trúc phân rã: (1) `days_since_epoch` hoặc `year` cho thành phần Xu hướng, (2) `week_of_year`, `month`, `day_of_week` cho thành phần Mùa vụ, (3) cờ nhị phân `is_earthquake` cho đỉnh phần dư tháng 4 năm 2016. Cấu trúc nhân tính của STL ngụ ý rằng biến đổi mục tiêu `log1p(sales)` là phù hợp — nó chuyển đổi tính mùa vụ nhân tính thành cộng tính, điều mà hầu hết các mô hình hồi quy giả định.

### Phát Hiện 3: Tháng 12 Là Đỉnh Nhất Quán; Tháng 2 Là Đáy Nhất Quán Qua Tất Cả Các Năm
**Biểu đồ:** Biểu đồ đa đường — tháng (trục x, 1-12) so với tổng doanh số hàng tháng (trục y), một đường mỗi năm 2013-2017 (Biểu đồ 21)
**Quan sát:** Trong mỗi năm từ 2013 đến 2017, tháng 12 là tháng có doanh số cao nhất: đỉnh trung bình 808.565 USD mỗi ngày. Trong mỗi năm, tháng 2 là tháng có doanh số thấp nhất: đáy trung bình 571.895 USD mỗi ngày. Tỷ lệ tháng 12/tháng 2 là khoảng 1,41 lần (doanh số cao hơn 41% vào tháng 12 so với tháng 2). 5 đường theo gần như cùng hình mùa vụ — xác nhận tính mùa vụ ổn định và bất biến theo năm. Đường 2016 lệch nhẹ lên tháng 4 (hiệu ứng động đất), và đường 2017 kết thúc vào tháng 8. Thứ tự tháng-trong-năm nhất quán: Q4 (tháng 10-12) rõ ràng là quý cao nhất, Q1 (tháng 2-3) là thấp nhất.
**Hàm Ý Feature Engineering:** `month` (1-12) là feature mạnh và đáng tin cậy. `is_december` (nhị phân) có thể thêm vào để nắm bắt đỉnh tháng 12 cực đoan. `is_q4` (tháng 10-12 = 1) nắm bắt mùa cao điểm rộng hơn. Sự ổn định mùa vụ năm-theo-năm có nghĩa là `lag_365` (cùng ngày năm ngoái) là feature hợp lệ và mạnh mẽ — nếu mẫu mùa vụ đang thay đổi, lag_365 sẽ mang thông tin lỗi thời, nhưng sự ổn định được thể hiện ở đây xác nhận độ tin cậy của nó.

### Phát Hiện 4: Phân Phối Doanh Số Lệch Phải Nặng; 31,3% Bản Ghi Bằng Không
**Biểu đồ:** Biểu đồ con 2×2 — trên trái: histogram doanh số hàng ngày đã giới hạn; trên phải: biểu đồ hộp theo năm; dưới trái: biểu đồ hộp theo day_of_week; dưới phải: biểu đồ cột ngày không-bán so với bán (Biểu đồ 22)
**Quan sát:** Histogram (trên trái) cho thấy độ lệch phải cực đoan: mean = 357,78 USD, median = 11,00 USD, khoảng cách 3.152% giữa mean và median. Độ lệch = 7,36, kurtosis = 154,56. Phân phối có đuôi phải nặng; giá trị lớn nhất trong một bản ghi = 124.717 USD (349 lần mean). Biểu đồ cột không-bán so với bán (dưới phải) cho thấy 939.130 bản ghi doanh số bằng không trong tổng số 3.000.888 = tỷ lệ không 31,3%. Biểu đồ hộp theo năm (trên phải) cho thấy phương sai (độ rộng IQR) tăng theo năm khi doanh nghiệp mở rộng. Biểu đồ hộp theo ngày trong tuần (dưới trái) cho thấy thứ 7 và chủ nhật có doanh số trung vị cao hơn rõ ràng so với ngày trong tuần: trung bình thứ 7 825.218 USD/ngày (cấp cửa hàng) so với thứ 5 505.269 USD/ngày — phần thưởng cuối tuần +63% ở cấp tổng hợp. Ở cấp giao dịch, thứ 7 cho thấy +26% giao dịch hơn so với thứ 5.
**Hàm Ý Feature Engineering:** Áp dụng biến đổi `log1p(sales)` vào biến mục tiêu trước khi huấn luyện. Độ lệch thô 7,36 của doanh số thô có nghĩa là mất mát RMSE trên doanh số chưa biến đổi sẽ bị thống trị bởi các bản ghi giá trị lớn hiếm gặp. Sau biến đổi log1p, phần dư gần hơn nhiều với phân phối chuẩn và RMSE trở thành mục tiêu tối ưu hóa có ý nghĩa. Đối với các bản ghi doanh số bằng không (31,3%), đánh giá hai phương pháp: (1) bao gồm bằng không với biến đổi log1p (log1p(0) = 0, hợp lệ); hoặc (2) sử dụng mô hình hai giai đoạn (Giai đoạn 1: bộ phân loại không/khác không; Giai đoạn 2: hồi quy chỉ trên bản ghi khác không). Phương án sau được khuyến nghị cho các tổ hợp cửa hàng-nhóm có tỷ lệ không cao.

---

## Khuyến Nghị Feature Engineering

| Tên Feature | Kiểu | Mô Tả | Độ Ưu Tiên |
|---|---|---|---|
| `log1p_sales` | số | Biến đổi log1p của doanh số mục tiêu; chuẩn hóa phân phối độ lệch=7,36 cho hàm mất mát hồi quy | CAO |
| `day_of_week` | phân loại / tuần hoàn (0-6) | Ngày trong tuần; Thứ 7=cao nhất (+26% giao dịch), Thứ 5=thấp nhất; dùng one-hot hoặc mã hóa sin/cos | CAO |
| `month` | phân loại / tuần hoàn (1-12) | Tháng trong năm; Tháng 12=đỉnh (808k USD/ngày), Tháng 2=đáy (572k USD/ngày); mẫu ổn định qua tất cả 5 năm | CAO |
| `year` | số | Năm lịch 2013-2017; nắm bắt thành phần xu hướng CAGR 8,45% từ phân rã STL | CAO |
| `days_since_epoch` | số | Ngày kể từ 2013-01-01; feature xu hướng liên tục, thay thế hoặc bổ sung cho `year` | CAO |
| `is_earthquake` | nhị phân | 1 cho ngày 16 tháng 4 năm 2016 và ~15 ngày tiếp theo; đỉnh bất thường được tách trong bảng Phần dư STL | CAO |
| `is_weekend` | nhị phân | 1 cho Thứ 7 hoặc Chủ Nhật; mức tăng giao dịch +17-26% xác nhận trong EDA giao dịch | CAO |
| `is_december` | nhị phân | 1 cho Tháng 12; nắm bắt đỉnh Giáng sinh/Năm mới, tháng cao nhất nhất quán qua tất cả các năm | TRUNG BÌNH |
| `week_of_year` | số (1-52) | Tính mùa vụ hàng năm chi tiết; các tuần 51-52 tối nhất trong heatmap lịch mỗi năm | TRUNG BÌNH |
| `lag_365` | số | Doanh số cùng ngày năm trước (mỗi cửa hàng-nhóm); hợp lệ vì mẫu mùa vụ bất biến theo năm | TRUNG BÌNH |
| `is_q4` | nhị phân | 1 cho Tháng 10-12; cờ mùa cao điểm rộng nắm bắt Q4 là quý cao nhất | THẤP |

---

## Hàm Ý Mô Hình Hóa

- Áp dụng biến đổi mục tiêu `log1p(sales)` trước khi huấn luyện bất kỳ mô hình hồi quy nào. Độ lệch 7,36 của doanh số thô làm cho mất mát RMSE không ổn định và bị thống trị bởi các sự kiện giá trị đuôi. Sau biến đổi log1p, phân phối gần hơn nhiều với phân phối chuẩn, làm cho gradient boosting chuẩn hoặc các mô hình tuyến tính trở nên phù hợp.
- Cấu trúc zero-inflation (31,3% số không) cần xử lý rõ ràng. Phương pháp khuyến nghị: huấn luyện mô hình LightGBM hoặc XGBoost trên doanh số đã biến đổi log1p bao gồm số không — nhiều mô hình dựa trên cây xử lý zero-inflation khá tốt mà không cần bộ phân loại không riêng biệt. Đối với các cửa hàng có tỷ lệ không cao nhất (Cửa hàng 52 ở 93,5%), phương pháp hai giai đoạn (bộ phân loại + hồi quy) phù hợp hơn.
- Xu hướng tăng đơn điệu (CAGR 8,45%) phải được mã hóa như feature, không được giả định đi. Một mô hình không có feature xu hướng sẽ có thiên lệch hệ thống: dự báo thấp trong các năm sau của giai đoạn huấn luyện và dự báo cao nếu tính mùa vụ được học trên đường cơ sở năm đầu.
- Trận động đất tháng 4 năm 2016 phải được đánh dấu là `is_earthquake = 1`. Bảng phần dư STL cho thấy nó là đỉnh bất thường rõ ràng. Không có cờ này, mô hình sẽ học mua sắm hoảng loạn như một phần của tính mùa vụ tháng 4 và dự báo cao doanh số tháng 4 năm 2017.
- Hiệu ứng cuối tuần (+17-26% giao dịch vào thứ 7) được xác nhận độc lập cả trong dataset giao dịch (6,8 lần sự không đồng nhất cửa hàng và thứ 7 +26% so với thứ 5) và trong biểu đồ hộp phân phối doanh số (bảng ngày trong tuần). Tính nhất quán này qua hai nguồn dữ liệu làm cho `day_of_week` trở thành feature có độ tin cậy cao.
- Năm 2017 một phần (chỉ tháng 1-8) nên được xử lý cẩn thận trong các phân chia train/validation. Nếu dữ liệu 2017 được sử dụng cho huấn luyện, sự vắng mặt của tháng 9-12 năm 2017 có nghĩa là mô hình không thể học từ mùa cao điểm 2017 — xác nhận trên dữ liệu 2017 sẽ ước tính thấp đỉnh tháng 12. Phân chia khuyến nghị: huấn luyện trên 2013-2016, xác nhận trên 2017.
- Giới hạn IQR được áp dụng cho tổng hàng ngày (0 điểm bất thường tìm thấy sau khi giới hạn với tiêu chí 3*IQR). Điều này xác nhận không có tổng hàng ngày cực đoan nào bị xóa — đuôi nặng trong histogram là thực, không phải tạo tác lỗi dữ liệu.

---

## Ghi Chú Chất Lượng Dữ Liệu

- train.csv: 3.000.888 hàng, 6 cột, không có giá trị thiếu. Độ lệch=7,36, kurtosis=154,56 xác nhận từ thống kê `describe()` trong notebook.
- Số bản ghi doanh số bằng không: 939.130 (31,3%) — xác nhận từ `(df['sales'] == 0).sum()` số liệu tính toán.
- Doanh số hàng năm: 2013=140,4 triệu USD, 2014=209,5 triệu USD, 2015=240,9 triệu USD, 2016=288,7 triệu USD, 2017=194,2 triệu USD (một phần tháng 1-8) — xác nhận từ tổng hợp hàng năm trong notebook.
- Giới hạn IQR: lower_bound và upper_bound được tính; 0 bản ghi bị xóa sau khi áp dụng tiêu chí 3*IQR. Biểu đồ chuỗi thời gian với các điểm bất thường được đánh dấu màu đỏ (Biểu đồ 16, đã xóa) cho thấy không có điểm đỏ, xác nhận không có điểm bất thường nào được gắn cờ.
- Cột `date` được tải như kiểu `object` trong dữ liệu thô; phải chuyển đổi sang `datetime64` trong pipeline tiền xử lý trước khi lập chỉ số theo thời gian và tính toán lag.
- Dữ liệu 2017 bao gồm ngày 1 tháng 1 đến ngày 15 tháng 8 năm 2017 (227 ngày trong 365, hoặc 62% năm). Con số -32,7% YoY cho 2017 hoàn toàn là tạo tác một phần năm và không chỉ ra sự sụt giảm kinh doanh thực sự.
