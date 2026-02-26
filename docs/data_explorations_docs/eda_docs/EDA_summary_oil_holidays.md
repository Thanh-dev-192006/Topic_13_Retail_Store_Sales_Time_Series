# Tóm Tắt EDA: Giá Dầu và Sự Kiện Ngày Lễ

**Notebook nguồn:** `notebooks/03_eda_deep_dive/Hai_eda/oil_holidays_event.ipynb`
**Câu hỏi kinh doanh được giải đáp:** Q1, Q2, Q3
**Cập nhật lần cuối:** 2026-02-21

---

## Phát Hiện Chính

### Phát Hiện 1: Giá Dầu và Doanh Số Di Chuyển Ngược Chiều Trong Dài Hạn
**Biểu đồ:** Biểu đồ đường trục kép — tổng doanh số hàng ngày (trục y trái, màu xanh) so với giá dầu dcoilwtico (trục y phải, màu đỏ), toàn bộ giai đoạn 2013-2017 (Biểu đồ 1)
**Quan sát:** Giá dầu giảm mạnh từ 2014 đến 2016 (từ ~110 USD/thùng xuống mức thấp nhất 26,19 USD) trong khi tổng doanh số tăng đơn điệu trong cùng giai đoạn (từ ~140 triệu USD năm 2013 lên ~288 triệu USD năm 2016). Hai chuỗi di chuyển ngược chiều về dài hạn. Không có sự đồng biến ngắn hạn rõ ràng: sự tăng vọt dầu không tạo ra phản ứng doanh số tức thì. Ba chế độ dầu khác biệt có thể nhìn thấy trong biểu đồ: Cao (2013-2014, giá ổn định trên 70 USD), Sụp đổ (2015-2016, 96 ngày sụp đổ với giá dưới 40 USD, chiếm 7,9% dataset), và Phục hồi (2017, giá trong khoảng 45-55 USD).
**Hàm Ý Feature Engineering:** Không đưa giá dầu đồng thời như dự đoán trực tiếp — xu hướng dài hạn ngược chiều sẽ tạo ra hệ số âm giả mà làm lệch mô hình. Dầu chỉ nên được đưa vào như feature phụ trợ có trễ hoặc mã hóa chế độ. Tạo `oil_regime` (phân loại: Cao/Sụp đổ/Phục hồi) để nắm bắt sự khác biệt hành vi cấu trúc qua các giai đoạn kinh tế vĩ mô.

### Phát Hiện 2: Độ Trễ Dầu-365 Chiếm Ưu Thế So Với Tất Cả Độ Trễ Ngắn Hạn
**Biểu đồ:** Biểu đồ cột — nhãn độ trễ (Độ trễ 1, 7, 14, 30, 365) trên trục x so với tương quan Pearson với doanh số hàng ngày trên trục y (Biểu đồ 3)
**Quan sát:** Tương quan độ trễ-1 với doanh số xấp xỉ -0,02 (gần bằng không). Độ trễ-7, Độ trễ-14 và Độ trễ-30 cũng yếu (tất cả dưới |0,10|). Độ trễ-365 cho thấy độ lớn tương quan cao nhất ở khoảng -0,30, vượt đáng kể tất cả các độ trễ ngắn hạn. Mẫu này chỉ ra rằng sự liên quan của giá dầu đến doanh số là có cấu trúc và cấp độ chế độ, không phải vận hành. Dấu của tương quan độ trễ-365 là âm, nhất quán với xu hướng dài hạn ngược chiều có thể thấy trong Biểu đồ 1.
**Hàm Ý Feature Engineering:** Đưa `oil_lag_365` là feature dầu chính. Các độ trễ ngắn hạn (độ trễ-1 đến độ trễ-30) có sức mạnh dự đoán gần bằng không và nên được loại trừ để giảm nhiễu. Để hiệu quả tính toán, trung bình trượt 30 ngày của giá dầu có thể thay thế cho giá trị hàng ngày thô, làm mịn sự biến động mà không mất tín hiệu chế độ.

### Phát Hiện 3: Hiệu Ứng Tích Trữ — Doanh Số Cao Hơn Trước Ngày Lễ So Với Trong Ngày Lễ
**Biểu đồ:** Biểu đồ con 2×2 — (A) is_holiday_event so với doanh số (hộp), (B) holiday_category so với doanh số trung bình (cột), (C) locale_category so với doanh số trung bình (cột), (D) period_type Trước/Trong/Sau/Bình thường so với doanh số (hộp) (Biểu đồ 4)
**Quan sát:** Biểu đồ D cho thấy cửa sổ "Trước Ngày Lễ" (2 ngày trước ngày lễ) có doanh số trung vị cao hơn cửa sổ "Trong Ngày Lễ". Hiệu ứng tích trữ này phản ánh khách hàng mua thực phẩm và hàng gia dụng trước khi cửa hàng giảm giờ hoặc đóng cửa. Biểu đồ B cho thấy ngày Bridge và ngày Transfer có doanh số trung bình cao nhất trong tất cả các loại kỳ nghỉ — cao hơn cả ngày "Nghỉ lễ" thông thường. Biểu đồ C cho thấy ngày lễ phạm vi Quốc gia có tác động mạnh hơn và đồng đều hơn so với ngày lễ Địa phương hoặc Khu vực. Biểu đồ A xác nhận ngày lễ làm tăng doanh số một cách khiêm tốn nhìn chung, nhưng phương sai rộng, phản ánh sự không đồng nhất về loại được thể hiện trong Biểu đồ B.
**Hàm Ý Feature Engineering:** Feature ngày lễ chính không phải là `is_holiday` (nhị phân vào ngày lễ) mà là `days_to_next_holiday` (biến đếm ngược nắm bắt mức tăng cầu trước kỳ nghỉ). Tạo `holiday_type` (phân loại: Nghỉ lễ, Bridge, Transfer, Bổ sung, Sự kiện, Ngày làm việc) để cho phép mô hình học riêng biệt phần thưởng Bridge/Transfer. Tạo `is_transfer_day` và `is_bridge_day` như các cờ nhị phân cho các loại phụ ngày lễ có tác động cao nhất.

### Phát Hiện 4: Tính Mùa Vụ Hàng Năm Ổn Định và Các Tuần 51-52 Luôn Là Đỉnh
**Biểu đồ:** Heatmap lịch — năm (hàng 2013-2017) so với số tuần 1-52 (cột), ô = doanh số hàng ngày trung bình (Biểu đồ 5)
**Quan sát:** Các ô tối nhất (doanh số cao nhất) xuất hiện nhất quán trong các tuần 51-52 (giai đoạn Giáng sinh và Năm mới) trong mỗi năm từ 2013 đến 2017. Các ô sáng nhất (doanh số thấp nhất) xuất hiện nhất quán trong các tuần 6-9 (tháng 2). Mẫu mùa vụ ổn định qua các năm — các tuần đỉnh và đáy giống nhau trong mọi năm. Một điểm bất thường sáng rõ xuất hiện ở tuần 16 năm 2016 (trận động đất tháng 4 năm 2016). Sự ổn định của tính mùa vụ trong 5 năm xác nhận việc sử dụng feature `lag_365` và feature lịch năm-theo-năm.
**Hàm Ý Feature Engineering:** Tính mùa vụ hàng năm là xác định và có thể học được. Tạo `week_of_year`, `month` và `is_december` (cho hiệu ứng các tuần đỉnh 51-52). Heatmap lịch xác nhận `lag_365` có giá trị cấu trúc: cùng tuần năm ngoái là ủy quyền đáng tin cậy cho mức kỳ vọng năm nay. Điểm bất thường tháng 4 năm 2016 trong heatmap xác nhận nhu cầu về cờ nhị phân `is_earthquake` (ngày 16 tháng 4 năm 2016 và khoảng 15 ngày tiếp theo) để ngăn mô hình học mua sắm hoảng loạn như mẫu mùa vụ lặp lại.

---

## Khuyến Nghị Feature Engineering

| Tên Feature | Kiểu | Mô Tả | Độ Ưu Tiên |
|---|---|---|---|
| `oil_lag_365` | số | Giá dầu đúng 365 ngày trước; tương quan dầu-doanh số mạnh nhất (~-0,30) | CAO |
| `oil_regime` | phân loại (3 cấp độ) | Cao (>70 USD, 2013-2014), Sụp đổ (<40 USD, 2015-2016, 96 ngày), Phục hồi (2017) | CAO |
| `days_to_next_holiday` | số | Đếm ngược bằng ngày đến ngày lễ áp dụng tiếp theo (quốc gia cho tất cả cửa hàng, địa phương cho cửa hàng phù hợp); nắm bắt hiệu ứng tích trữ | CAO |
| `holiday_type` | phân loại (6 cấp độ) | Loại kỳ nghỉ: Nghỉ lễ, Bridge, Transfer, Bổ sung, Sự kiện, Ngày làm việc; Bridge/Transfer có doanh số trung bình cao nhất | CAO |
| `is_transfer_day` | nhị phân | 1 nếu loại kỳ nghỉ là Transfer; ngày Transfer cho thấy doanh số cao hơn ngày lễ thông thường | CAO |
| `is_bridge_day` | nhị phân | 1 nếu loại kỳ nghỉ là Bridge; ngày Bridge có doanh số trung bình cao nhất trong tất cả các loại kỳ nghỉ | CAO |
| `is_earthquake` | nhị phân | 1 cho ngày 16 tháng 4 năm 2016 và ~15 ngày tiếp theo; đỉnh mua sắm hoảng loạn có thể thấy trong phần dư heatmap lịch | CAO |
| `week_of_year` | số (1-52) | Nắm bắt tính mùa vụ hàng năm ổn định; các tuần 51-52 nhất quán tối nhất trong heatmap | CAO |
| `oil_ma_30` | số | Trung bình trượt 30 ngày của giá dầu; tín hiệu chế độ được làm mịn để sử dụng cùng hoặc thay thế lag_365 | TRUNG BÌNH |
| `is_national_holiday` | nhị phân | 1 cho các sự kiện phạm vi quốc gia (49,7% tổng số hồ sơ kỳ nghỉ); tác động đồng đều mạnh hơn địa phương | TRUNG BÌNH |
| `locale_type` | phân loại | Phạm vi Quốc gia / Khu vực / Địa phương; Quốc gia có tác động doanh số trung bình cao hơn Địa phương theo Biểu đồ 4C | TRUNG BÌNH |

---

## Hàm Ý Mô Hình Hóa

- Giá dầu không được sử dụng như feature đồng thời: tương quan âm dài hạn giả (do xu hướng ngược chiều) sẽ làm giảm chất lượng mô hình. Sử dụng `oil_lag_365` và `oil_regime` thay thế.
- Hiệu ứng tích trữ có nghĩa là lịch ngày lễ phải được mã hóa như biến dẫn (`days_to_next_holiday`) thay vì cờ nhị phân đồng thời. Mô hình chỉ sử dụng `is_holiday` vào ngày lễ sẽ có hệ thống dự đoán thấp cửa sổ 2 ngày trước kỳ nghỉ và dự đoán cao vào chính ngày lễ.
- Các loại phụ kỳ nghỉ Bridge và Transfer cần mã hóa riêng biệt: chúng có doanh số cao hơn đáng kể so với ngày lễ chuẩn và sẽ bị dự báo thấp nếu gộp vào một cờ `is_holiday` duy nhất.
- Heatmap lịch xác nhận tính mùa vụ hàng năm ổn định và nhất quán từ 2013 đến 2017. Điều này biện minh cho việc sử dụng `lag_365` như feature mà không lo ngại rằng tính mùa vụ đã thay đổi qua các năm.
- Trận động đất tháng 4 năm 2016 phải được đánh dấu rõ ràng. Nếu không đánh dấu, mô hình sẽ học đỉnh mua sắm hoảng loạn như một phần của tính mùa vụ tháng 4 và dự báo quá cao doanh số tháng 4 các năm tiếp theo (tập kiểm tra 2017).
- Phạm vi ngày lễ địa phương so với quốc gia cần khớp ở cấp cửa hàng: các sự kiện quốc gia ảnh hưởng đến tất cả 54 cửa hàng đồng thời, trong khi các sự kiện khu vực và địa phương phải được nối với stores.csv qua thành phố/bang. Bỏ qua việc nối này có nghĩa là 50,3% hiệu ứng ngày lễ bị bỏ sót cho các cửa hàng bị ảnh hưởng.

---

## Ghi Chú Chất Lượng Dữ Liệu

- Dataset dầu: 43 giá trị thiếu (3,5%) vào cuối tuần và ngày nghỉ thị trường khi giao dịch dầu dừng lại. Điền tiếp (forward-fill) là phù hợp và đã được áp dụng. Sau khi điền, không còn giá trị thiếu.
- Dataset ngày lễ: 350 bản ghi, không có giá trị thiếu — sẵn sàng cho sản xuất. 9,9% ngày có nhiều sự kiện đồng thời (quốc gia + địa phương trùng lặp); chiến lược tổng hợp cần thiết khi nối với train.csv (khuyến nghị: lấy loại sự kiện ưu tiên cao nhất mỗi ngày mỗi cửa hàng).
- Trận động đất ngày 16 tháng 4 năm 2016 có thể thấy như điểm bất thường sáng trong heatmap lịch (Biểu đồ 5). Biểu đồ động đất độc lập đã bị xóa (Biểu đồ 6 đã xóa theo kế hoạch phase2) vì điểm bất thường đã được nắm bắt trong Biểu đồ 5 và trong phần dư STL. Hành động feature engineering (`is_earthquake` flag) vẫn là bắt buộc bất kể việc xóa biểu đồ.
- Ngày sụp đổ dầu (giá < 40 USD): tổng cộng 96 ngày (7,9% dataset), tập trung trong 2015-2016. Chế độ này thống kê hiếm nhưng quan trọng về kinh tế — nó trùng với giai đoạn thắt lưng buộc bụng tài khóa của Ecuador và có thể đã thay đổi hành vi tiêu dùng theo cách cần mô hình hóa riêng biệt.
