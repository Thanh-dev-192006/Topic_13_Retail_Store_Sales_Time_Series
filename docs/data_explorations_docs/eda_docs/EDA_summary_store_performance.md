# Tóm Tắt EDA: Phân Tích Hiệu Suất Cửa Hàng

**Notebook nguồn:** `notebooks/03_eda_deep_dive/Thanh_eda/store_performance_analysis.ipynb`
**Câu hỏi kinh doanh được giải đáp:** Q4, Q5, Q7
**Cập nhật lần cuối:** 2026-02-21

---

## Phát Hiện Chính

### Phát Hiện 1: Top 10 Cửa Hàng Tạo Ra 40,2% Doanh Thu; Bottom 10 Chỉ Tạo Ra 6,8%
**Biểu đồ:** Biểu đồ cột ngang (2 bảng) — trái: top 10 cửa hàng theo tổng doanh số (triệu USD); phải: bottom 10 cửa hàng theo tổng doanh số (triệu USD) (Biểu đồ 23)
**Quan sát:** Cửa hàng 44 dẫn đầu với tổng doanh số 62,1 triệu USD (5,8% tổng). Top 5 cửa hàng là: #44=62,1 triệu USD, #45=54,5 triệu USD, #47=50,9 triệu USD, #3=50,5 triệu USD, #49=43,4 triệu USD. Cùng nhau top 5 chiếm 24,4% tổng doanh thu. Top 10 cửa hàng chiếm 40,2% tổng doanh thu. Bottom 10 cửa hàng (bao gồm Cửa hàng 52 gần bằng không) chỉ chiếm 6,8%. Tỷ lệ Max/Min qua tất cả cửa hàng là 23,0 lần (Cửa hàng 44 so với Cửa hàng 52). Khoảng cách giữa hai bảng cực kỳ rõ ràng về mặt thị giác — bảng trái cho thấy các cột trong khoảng 28-62 triệu USD trong khi bảng phải cho thấy các cột trong khoảng 2-15 triệu USD.
**Hàm Ý Feature Engineering:** Một mô hình toàn cục duy nhất sẽ có hệ thống hoạt động kém cho cả cửa hàng đuôi và đầu. Khoảng cách doanh thu 23 lần đòi hỏi các feature cấp cửa hàng nắm bắt quy mô. Tạo `store_avg_daily_sales` (liên tục, nắm bắt quy mô cửa hàng) và `store_sales_tier` (phân loại: TOP10 = các cửa hàng tạo ra top 40,2% doanh thu; MID = 34 cửa hàng tiếp theo; TAIL = bottom 10 cửa hàng) để xử lý mô hình khác biệt.

### Phát Hiện 2: Các Loại Cửa Hàng Có Sự Khác Biệt Doanh Số Có Ý Nghĩa Thống Kê (KW p=0,000256)
**Biểu đồ:** Biểu đồ hộp (3 bảng) — loại cửa hàng A-E (trục x) so với tổng doanh số / doanh số trung bình hàng ngày / CV (trục y, 3 bảng riêng biệt) (Biểu đồ 24)
**Quan sát:** Cửa hàng loại A có tổng doanh số trung vị cao nhất và doanh số trung bình hàng ngày trung vị cao nhất. Tổng doanh số trung bình loại A mỗi cửa hàng = 39,2 triệu USD. Loại C có mức trung bình thấp nhất ở 11,0 triệu USD mỗi cửa hàng. Cửa hàng loại C và E cũng cho thấy CV tương đối cao hơn (hệ số biến thiên) so với Loại A, có nghĩa là các loại cửa hàng nhỏ hơn không chỉ có khối lượng thấp hơn mà còn biến động hơn. Kiểm định Kruskal-Wallis theo loại cho H=21,46, p=0,000256, xác nhận sự khác biệt có ý nghĩa thống kê trong phân phối doanh số giữa các loại. Cấu trúc 3 bảng cho thấy Loại A vượt trội không chỉ về mức (tổng doanh số) mà còn về tính nhất quán (CV thấp hơn).
**Hàm Ý Feature Engineering:** `store_type` (A-E) là feature được xác nhận thống kê (p=0,000256). Nó nắm bắt cả sự khác biệt mức (doanh số trung bình) và sự khác biệt biến động (CV). Đưa vào như feature phân loại trong tất cả mô hình cấp cửa hàng. Khi xây dựng mô hình đặc thù loại cửa hàng, kỳ vọng Loại A cần phương pháp dự báo khác với Loại C/E do sự khác biệt CV — mô hình Loại A có thể sử dụng khoảng dự báo chặt hơn, trong khi mô hình Loại C/E cần khoảng rộng hơn.

### Phát Hiện 3: Tỷ Lệ Doanh Số Bằng Không Dao Động Từ 17,9% (Cửa Hàng 44) Đến 93,5% (Cửa Hàng 52)
**Biểu đồ:** Biểu đồ cột ngang + biểu đồ hộp (2 bảng) — trái: zero_sales_pct của từng cửa hàng tô màu đỏ/cam/xanh; phải: loại cửa hàng so với phân phối zero_sales_pct (hộp) (Biểu đồ 35)
**Quan sát:** Cửa hàng 52 có zero_sales_pct là 93,5% — đây là cửa hàng gần mới mở tháng 4 năm 2017 (xác nhận bởi dataset giao dịch: 93% dòng thời gian có giao dịch được điền/không). Cửa hàng 44 có tỷ lệ không thấp nhất ở 17,9%. Biểu đồ hộp bảng phải theo loại cửa hàng cho thấy Loại E có zero_sales_pct trung vị cao nhất; Loại A có thấp nhất. Tỷ lệ không 31,3% tổng thể qua tất cả bản ghi cửa hàng-nhóm-ngày là trung bình có trọng số của phân phối rộng (17,9% đến 93,5%). Các cửa hàng màu đỏ trong bảng trái (tỷ lệ không cao) tập trung trong các loại cửa hàng doanh thu thấp hơn, định dạng nhỏ hơn.
**Hàm Ý Feature Engineering:** Tạo `store_zero_rate` như feature liên tục (mỗi cửa hàng, tính từ dữ liệu huấn luyện) để cho phép mô hình học mức độ nghiêm trọng zero-inflation ở cấp cửa hàng. Các cửa hàng có zero_rate > 50% nên được gắn cờ để xử lý mô hình hai giai đoạn (bộ phân loại không + hồi quy doanh số). Cửa hàng 52 nên được che đi hoặc loại trừ khỏi huấn luyện trong giai đoạn trước khi mở — tỷ lệ không 93,5% của nó là tạo tác cấu trúc của cửa hàng đóng cửa, không phải tín hiệu cầu.

### Phát Hiện 4: Cơ Cấu Nhóm Sản Phẩm Khác Nhau Theo Loại Cửa Hàng — Cần Feature Tương Tác
**Biểu đồ:** Heatmap (2 bảng) — top 10 nhóm hàng (hàng) so với loại cửa hàng A-E (cột), ô = doanh số tuyệt đối triệu USD (bảng trái) và % của tổng loại (bảng phải) (Biểu đồ 36)
**Quan sát:** GROCERY I và BEVERAGES thống trị về tuyệt đối qua tất cả loại cửa hàng, nhưng tỷ lệ phần trăm của họ khác nhau theo loại. Bảng phải (% của tổng loại) tiết lộ rằng một số loại cửa hàng nhỏ hơn có tỷ lệ tương đối cao hơn của PRODUCE hoặc BREAD/BAKERY so với cửa hàng Loại A. Cửa hàng Loại A có cơ cấu sản phẩm cân bằng hơn qua các nhóm, trong khi cửa hàng Loại E và C tập trung hơn vào ít nhóm hàng hơn. Heatmap xác nhận trực quan rằng hiệu ứng tương tác nhóm × loại cửa hàng tồn tại — một feature nhóm toàn cục không có tương tác loại sẽ bỏ qua sự khác biệt cấu thành này.
**Hàm Ý Feature Engineering:** Tạo feature tương tác `family_x_type` cho top 6 nhóm hàng (chiếm 83% doanh thu). Các tương tác này được biện minh bởi heatmap cho thấy các tỷ lệ phần trăm nhóm khác nhau qua các loại. Đối với mô hình dựa trên cây, tương tác được học ngầm định nếu cả `store_type` và `family_id` đều được bao gồm là feature (GBDT tự nhiên học các tương tác); đối với mô hình tuyến tính hoặc mạng thần kinh, các biến giả `family_x_type` rõ ràng hoặc embedding là cần thiết.

### Phát Hiện 5: Điểm Dự Đoán Được Phân Đoạn Cửa Hàng Thành Dễ Dự Báo và Khó Dự Báo
**Biểu đồ:** Biểu đồ cột ngang + biểu đồ hộp (2 bảng) — trái: điểm khả năng dự đoán của từng cửa hàng (0-1) tô màu theo RdYlGn; phải: loại cửa hàng so với điểm khả năng dự đoán (hộp) (Biểu đồ 37)
**Quan sát:** Điểm khả năng dự đoán = 0,4 × cv_score + 0,3 × zero_score + 0,3 × stability_score (trong đó mỗi thành phần là nghịch đảo của CV, tỷ lệ không, và độ lệch chuẩn xếp hạng hàng năm tương ứng — điểm cao hơn = dự đoán được hơn). Top 10 cửa hàng cụm ở khả năng dự đoán cao (vùng xanh, điểm > 0,7). Cửa hàng 52 có điểm thấp nhất (gần 0) do tỷ lệ không 93,5% và lịch sử tối thiểu. Cửa hàng Loại A cho thấy điểm khả năng dự đoán trung vị cao nhất trong biểu đồ hộp bảng phải; cửa hàng Loại E cho thấy thấp nhất. Phân phối điểm khả năng dự đoán tiết lộ hình dạng hai đỉnh — một cụm cửa hàng lớn có khả năng dự đoán cao và một cụm cửa hàng nhỏ/mới có khả năng dự đoán thấp.
**Hàm Ý Feature Engineering:** Tạo `store_predictability_score` như feature liên tục. Sử dụng nó để thúc đẩy các quyết định kiến trúc mô hình hóa: các cửa hàng có điểm > 0,7 là ứng viên cho mô hình cửa hàng riêng lẻ hoặc tinh chỉnh đặc thù cửa hàng; các cửa hàng có điểm < 0,3 nên được xử lý bởi mô hình chia sẻ cấp cluster hoặc loại (tín hiệu không đủ cho mô hình riêng lẻ). Điểm này cũng thông báo hậu xử lý: áp dụng khoảng dự báo rộng hơn cho các cửa hàng có khả năng dự đoán thấp để tránh độ chính xác giả.

---

## Khuyến Nghị Feature Engineering

| Tên Feature | Kiểu | Mô Tả | Độ Ưu Tiên |
|---|---|---|---|
| `store_sales_tier` | phân loại (TOP10/MID/TAIL) | Cấp doanh thu: top 10 cửa hàng (40,2% doanh thu), 34 tiếp theo, bottom 10 (6,8%); khóa phân đoạn mô hình chính | CAO |
| `store_avg_daily_sales` | số | Doanh số hàng ngày trung bình lịch sử mỗi cửa hàng; nắm bắt quy mô cửa hàng; cửa hàng hàng đầu (44) gấp 23 lần cửa hàng thấp nhất | CAO |
| `store_zero_rate` | số (0-1) | Tỷ lệ bản ghi doanh số bằng không mỗi cửa hàng; dao động từ 17,9% (Cửa hàng 44) đến 93,5% (Cửa hàng 52) | CAO |
| `store_type` | phân loại (A-E, one-hot) | Phân loại loại cửa hàng; dự đoán có ý nghĩa thống kê (KW p=0,000256); Loại A = trung bình 39,2 triệu USD | CAO |
| `store_cluster` | phân loại (1-17) | Nhóm cluster chi tiết; CV nội cluster=0,385, xác nhận tính hợp lệ cluster | CAO |
| `store_predictability_score` | số (0-1) | Điểm tổng hợp: 0,4*cv_inverse + 0,3*zero_rate_inverse + 0,3*rank_stability; thúc đẩy các quyết định kiến trúc mô hình | CAO |
| `store_cv` | số | Hệ số biến thiên mỗi cửa hàng; nắm bắt mức biến động độc lập với quy mô | TRUNG BÌNH |
| `region` | phân loại (Highland/Coastal) | Cửa hàng Highland (Quito) trung bình 30,8 triệu USD/cửa hàng so với Coastal 15,0 triệu USD/cửa hàng; Mann-Whitney có ý nghĩa | TRUNG BÌNH |
| `family_x_type` | số/nhị phân (tương tác) | Tương tác giữa chỉ số top 6 nhóm và loại cửa hàng; nắm bắt cơ cấu nhóm khác nhau theo loại có thể thấy trong heatmap | TRUNG BÌNH |

---

## Hàm Ý Mô Hình Hóa

- Mô hình riêng lẻ cho cửa hàng hàng đầu, mô hình chia sẻ cho cửa hàng đuôi: top 10 cửa hàng (40,2% doanh thu) có đủ dữ liệu và điểm khả năng dự đoán cao để hỗ trợ mô hình cửa hàng riêng lẻ hoặc tinh chỉnh đặc thù cửa hàng. Bottom 10 cửa hàng (6,8% doanh thu, khả năng dự đoán thấp) nên chia sẻ tham số qua mô hình cấp cluster hoặc loại.
- Phân cấp khuyến nghị: đường cơ sở toàn cục → tham số chia sẻ loại/cluster → hiệu ứng ngẫu nhiên cấp cửa hàng (cho mid/tail) → mô hình riêng lẻ (cho top 10). Cấu trúc phân cấp này cân bằng hiệu quả dữ liệu với độ chính xác đặc thù cửa hàng.
- Cửa hàng 52 cần xử lý đặc biệt: tỷ lệ không 93,5% là tạo tác cấu trúc của cửa hàng gần mới mở. Giai đoạn trước khi mở của nó nên được loại trừ khỏi huấn luyện (các bản ghi không được điền không mang tín hiệu cầu). Sau khi mở (từ tháng 4 năm 2017 trở đi), xử lý Cửa hàng 52 như vấn đề khởi động lạnh — sử dụng priors cluster hoặc loại cho đến khi tích lũy đủ lịch sử.
- Zero-inflation tập trung ở các cửa hàng cụ thể: tỷ lệ không 31,3% tổng thể che giấu sự không đồng nhất cực đoan. Mô hình hai giai đoạn (bộ phân loại không + hồi quy) nên được áp dụng có chọn lọc — bắt buộc cho các cửa hàng có zero_rate > 50%, tùy chọn cho các cửa hàng có zero_rate < 25%.
- Kruskal-Wallis p=0,000256 đối với sự khác biệt loại cửa hàng làm cho `store_type` trở thành feature bắt buộc thống kê. Đưa vào cả `store_type` và `store_cluster` là biện minh: heatmap cluster-loại (Biểu đồ 2) cho thấy chúng bổ sung cho nhau (cluster là tinh chỉnh của loại, không phải bản sao).
- Tương tác nhóm × loại là thực (heatmap Biểu đồ 36): cấu thành cơ cấu sản phẩm khác nhau theo loại cửa hàng. Mô hình dựa trên cây (LightGBM, XGBoost) sẽ học các tương tác này tự động nếu cả hai feature đều được đưa vào. Đối với mô hình tuyến tính hoặc mạng thần kinh, các thuật ngữ tương tác rõ ràng hoặc embedding là cần thiết.
- Tỷ lệ doanh thu max/min 23 lần (Cửa hàng 44 so với Cửa hàng 52) có nghĩa là trọng số mẫu quan trọng trong quá trình huấn luyện: nếu không có trọng số, mô hình sẽ tối ưu hóa cho nhiều tổ hợp cửa hàng-nhóm doanh thu thấp bằng chi phí của ít tổ hợp doanh thu cao. Áp dụng trọng số mẫu tỷ lệ với cấp doanh thu cửa hàng.

---

## Ghi Chú Chất Lượng Dữ Liệu

- Các số liệu tính toán từ notebook (giá trị có thẩm quyền để sử dụng trong xây dựng feature):
  - Cửa hàng 44: total_sales=62,1 triệu USD, zero_sales_pct=17,9% (tỷ lệ không thấp nhất)
  - Cửa hàng 52: total_sales=2,7 triệu USD, zero_sales_pct=93,5% (tỷ lệ không cao nhất)
  - Cửa hàng 45: total_sales=54,5 triệu USD; Cửa hàng 47: 50,9 triệu USD; Cửa hàng 3: 50,5 triệu USD; Cửa hàng 49: 43,4 triệu USD
  - Top 5 cửa hàng: 24,4% tổng; top 10: 40,2%; bottom 10: 6,8%
  - Loại A trung bình mỗi cửa hàng: 39,2 triệu USD; Loại C trung bình mỗi cửa hàng: 11,0 triệu USD (thấp nhất)
  - CV nội cluster trung bình: 0,385 (tính hợp lệ cluster xác nhận)
  - Kruskal-Wallis theo loại: H=21,46, p=0,000256
- Các số liệu cửa hàng được xuất sang `outputs/store_metrics.csv` với các cột: store_nbr, city, state, type, cluster, region, total_sales, avg_daily_sales, median_daily_sales, std_daily_sales, cv, zero_sales_pct, rank_total, predictability. Sử dụng file này như nguồn cho tất cả tra cứu feature cấp cửa hàng.
- Cửa hàng vùng Highland (thống trị bởi Quito/Pichincha): trung bình 30,8 triệu USD mỗi cửa hàng. Cửa hàng vùng Coastal: trung bình 15,0 triệu USD mỗi cửa hàng. Kiểm định Mann-Whitney U có ý nghĩa thống kê. Feature `region` (Highland/Coastal nhị phân) được xác nhận là dự đoán có ý nghĩa.
- Cluster 5 (1 cửa hàng: Cửa hàng #44, 62,1 triệu USD) và Cluster 7 (2 cửa hàng, trung bình 7,7 triệu USD) đại diện cho các cực của hiệu suất cấp cluster. Các cluster thành viên đơn nên được xử lý như cửa hàng riêng lẻ trong mô hình hóa, không phải như đại diện cluster.
- 10 biểu đồ đã bị xóa khỏi notebook này theo kế hoạch phase2 (Biểu đồ 25-34 đã xóa). Chúng bao gồm biểu đồ địa lý (biểu đồ cột thành phố/bang), heatmap nhất quán cửa hàng-theo-tháng, thanh ổn định xếp hạng và biểu đồ phân tán. Các phát hiện chính từ các biểu đồ đã xóa đó được nắm bắt đầy đủ trong các số liệu tính toán được liệt kê ở trên và trong 5 biểu đồ còn lại (23, 24, 35, 36, 37).
