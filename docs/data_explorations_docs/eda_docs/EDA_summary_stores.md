# Tóm Tắt EDA: Cấu Trúc và Phân Khúc Cửa Hàng

**Notebook nguồn:** `notebooks/01_data_exploration/Han_store.csv/Store_analyze.ipynb`
**Câu hỏi kinh doanh được giải đáp:** Q5
**Cập nhật lần cuối:** 2026-02-21

---

## Phát Hiện Chính

### Phát Hiện 1: Cluster là Phân Khúc Chi Tiết Hơn Loại Cửa Hàng Đơn Thuần
**Biểu đồ:** Heatmap Cluster (hàng 1-17) × Loại Cửa Hàng (cột A-E) — giá trị ô = số lượng cửa hàng (Biểu đồ 2)
**Quan sát:** Heatmap cho thấy hầu hết các cluster chỉ chứa cửa hàng cùng một loại, không có sự pha trộn. Sự đồng xuất hiện của cluster-loại là thưa thớt — phần lớn các ô khác không rơi vào mẫu giống đường chéo, xác nhận rằng tư cách thành viên cluster là sự tinh chỉnh nghiêm ngặt của tư cách thành viên loại. 17 cluster phân chia 54 cửa hàng với trung bình 3,2 cửa hàng/cluster (dao động 1-5). CV nội cluster = 0,385, thấp hơn đáng kể so với CV liên loại, xác nhận rằng cluster nắm bắt được sự biến động không được giải thích bởi loại đơn thuần.
**Hàm Ý Feature Engineering:** Sử dụng `store_cluster` (1-17) làm biến nhóm chính. Sử dụng `store_type` (A-E) như một biến hiệp biến bổ sung, không phải thay thế cho cluster. Heatmap cluster-loại biện minh cho việc đưa cả hai vào mô hình mà không có sự dư thừa — chúng bổ sung cho nhau, không cộng tuyến.

### Phát Hiện 2: Năm Loại Cửa Hàng Cho Thấy Hồ Sơ Doanh Số Khác Biệt
**Biểu đồ:** Heatmap Cluster × Loại (Biểu đồ 2) — phân phối loại có thể đọc từ marginals cột
**Quan sát:** 54 cửa hàng được phân phối theo 5 loại: D=18 (33,3%), E=11 (20,4%), A=9 (16,7%), B=8 (14,8%), C=8 (14,8%). Không có loại nào vượt quá 35%, phân phối tương đối cân bằng. Cửa hàng loại A tương ứng với các phân công cluster doanh số cao nhất; Cửa hàng loại C/E tập trung trong các nhóm doanh số thấp hơn. Kiểm định Kruskal-Wallis theo loại: H=21,46, p=0,000256 — sự khác biệt có ý nghĩa thống kê trong phân phối doanh số theo loại.
**Hàm Ý Feature Engineering:** Mã hóa `store_type` như một feature phân loại. Đối với mô hình dựa trên cây, mã hóa one-hot (5 cấp độ, không có rủi ro mất cân bằng lớp) là phù hợp. Nếu mối quan hệ thứ tự được giả định (Loại A = định dạng lớn nhất), mã hóa thứ tự A=5, B=4, C=3, D=2, E=1 là phương án thay thế hợp lệ và nên được kiểm tra so với one-hot.

### Phát Hiện 3: Mạng Lưới Có 54 Cửa Hàng Trải Rộng 22 Thành Phố và 16 Bang
**Biểu đồ:** Heatmap Cluster × Loại theo ngữ cảnh — phân phối địa lý từ các số liệu tính toán
**Quan sát:** Quito thống trị với 18 cửa hàng (33,3% mạng lưới). 5 thành phố hàng đầu có 34 cửa hàng (63,0% mạng lưới). 14 thành phố (63,6% tổng số thành phố) chỉ có 1 cửa hàng, khiến việc mô hình hóa ở cấp thành phố không đáng tin cậy cho những địa điểm đó.
**Hàm Ý Feature Engineering:** Không mã hóa one-hot `city` trực tiếp — 17 thành phố có một cửa hàng sẽ dẫn đến overfitting. Thay vào đó mã hóa ở cấp `state`, hoặc tạo cờ nhị phân `is_quito` và sử dụng `region` (Highland vs. Coastal) như một feature địa lý rộng hơn. Các feature địa lý nên được dẫn xuất từ `store_cluster` và `store_type` thay vì thành phố thô.

### Phát Hiện 4: Tính Hợp Lệ của Cluster Được Xác Nhận Bởi Tính Đồng Nhất Nội Cluster
**Biểu đồ:** Heatmap Cluster × Loại (Biểu đồ 2) — thành phần cluster có thể nhìn thấy từ cấu trúc hàng
**Quan sát:** CV nội cluster trung bình = 0,385. Điều này có nghĩa là các cửa hàng trong cùng cluster có ít biến động doanh số hơn so với các cửa hàng giữa các cluster, xác nhận rằng các phân công cluster theo định nghĩa kinh doanh có ý nghĩa cho phân khúc dự báo. Cluster 5 (1 cửa hàng: Cửa hàng #44) có doanh số cao nhất (62,1 triệu USD); Cluster 7 (2 cửa hàng) có mức thấp nhất ở mức trung bình 7,7 triệu USD.
**Hàm Ý Feature Engineering:** `store_cluster` nên được sử dụng như một khóa nhóm cho mô hình phân cấp (chia sẻ tham số trong cluster theo thời gian). Các cluster với n=1 (cửa hàng ngoại lệ như Cửa hàng #44) đảm bảo xử lý cá nhân. Đối với các cluster với n=2-3, chia sẻ tham số nhưng cho phép hiệu ứng ngẫu nhiên ở cấp cửa hàng.

---

## Khuyến Nghị Feature Engineering

| Tên Feature | Kiểu | Mô Tả | Độ Ưu Tiên |
|---|---|---|---|
| `store_type` | phân loại (5 cấp độ, one-hot) | Phân loại định dạng cửa hàng A-E; dự đoán có ý nghĩa thống kê (KW p=0,000256) | CAO |
| `store_cluster` | phân loại (17 cấp độ, embedding hoặc one-hot) | Nhóm cửa hàng chi tiết; biến phân đoạn chính với CV nội cluster=0,385 | CAO |
| `is_quito` | nhị phân | 1 nếu cửa hàng ở Quito (18/54 cửa hàng); nắm bắt phần thưởng thủ đô | TRUNG BÌNH |
| `region` | phân loại (Highland/Coastal) | Vùng địa lý vĩ mô; cửa hàng Highland (Quito) trung bình 30,8 triệu USD/cửa hàng so với Coastal 15,0 triệu USD/cửa hàng | TRUNG BÌNH |
| `store_type_ordinal` | số | Mã hóa thứ tự nếu A→E ngụ ý thứ bậc kích thước; cần xác nhận so với one-hot trong ablation | THẤP |

---

## Hàm Ý Mô Hình Hóa

- Cluster vượt trội hơn loại như biến nhóm chính: khi xây dựng mô hình phân cấp, tư cách thành viên cluster nên xác định cấp độ trung gian của phân cấp (toàn cục → cluster → cửa hàng).
- Phân phối loại tương đối cân bằng (không có loại nào dưới 15%) có nghĩa là mã hóa one-hot của `store_type` không mang rủi ro mất cân bằng lớp.
- Các cluster một cửa hàng (bao gồm Cửa hàng #44 tại Cluster 5) nên được mô hình hóa riêng lẻ — chia sẻ tham số cấp cluster với một thành viên duy nhất không cung cấp lợi ích chính quy hóa.
- Các feature địa lý ở cấp thành phố không đáng tin cậy: 63,6% thành phố chỉ có 1 cửa hàng, khiến hệ số cấp thành phố không thể nhận dạng được. Sử dụng `region` (Highland/Coastal) hoặc `state` thay thế.
- Thứ bậc 5 loại (A đến E) có thứ tự doanh số được xác nhận thống kê (p=0,000256). Thứ tự này nên được nắm bắt, không bị loại bỏ, trong biểu diễn feature.

---

## Ghi Chú Chất Lượng Dữ Liệu

- stores.csv có 54 hàng, 6 cột, không có giá trị thiếu — sẵn sàng cho sản xuất.
- `type_encoded` là phép biến đổi LabelEncoder xác định của `type` (A=0, B=1, C=2, D=3, E=4). Loại bỏ `type_encoded` khỏi các feature mô hình hóa để tránh đa cộng tuyến với `store_type`; giữ lại `type` để lựa chọn chiến lược mã hóa linh hoạt.
- Định nghĩa cluster không được ghi lại trong dataset. Ý nghĩa cluster phải được suy ngược từ các mẫu doanh số. Heatmap cho thấy cluster không hoàn toàn là hàm của loại — các yếu tố khác (có thể là địa lý hoặc dựa trên khối lượng doanh số) giải thích phân công cluster.
- `Store_analyze.ipynb` ở cấp gốc là bản sao chính xác của notebook này và đã được đánh dấu là không dùng nữa. Phiên bản chính tắc là `notebooks/01_data_exploration/Han_store.csv/Store_analyze.ipynb`.
