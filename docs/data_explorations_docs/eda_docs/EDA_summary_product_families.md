# Tóm Tắt EDA: Nhóm Sản Phẩm, Khuyến Mãi và Tính Mùa Vụ

**Notebook nguồn:** `notebooks/03_eda_deep_dive/Lan_eda/family_eda_promo_seasonality.ipynb`
**Câu hỏi kinh doanh được giải đáp:** Q1, Q4, Q6
**Cập nhật lần cuối:** 2026-02-21

---

## Phát Hiện Chính

### Phát Hiện 1: Sáu Nhóm Hàng Chiếm 83% Tổng Doanh Thu
**Biểu đồ:** Biểu đồ cột ngang — top 15 nhóm sản phẩm xếp hạng theo tổng doanh số (tăng dần), trục x = tổng doanh số (Biểu đồ 7)
**Quan sát:** Một mình GROCERY I đóng góp 343,5 triệu USD (32,0% tổng doanh thu). Top 6 nhóm hàng — GROCERY I, BEVERAGES, PRODUCE, CLEANING, DAIRY, BREAD/BAKERY — tập thể chiếm khoảng 83% tổng 1,073 tỷ USD. Biểu đồ cột cho thấy sự sụt giảm dốc sau top 6: POULTRY (31,9 triệu USD), MEATS (31,1 triệu USD) và các nhóm hàng thấp hơn đều đóng góp dưới 3%. Phần đuôi dài của các nhóm hàng (BOOKS, BABY CARE, AUTOMOTIVE, v.v.) mỗi nhóm chỉ đạt doanh số hàng triệu USD đơn lẻ. Điều này xác nhận quy luật Pareto (80/20) tập trung ở cấp nhóm sản phẩm.
**Hàm Ý Feature Engineering:** Phân bổ nỗ lực mô hình hóa khác biệt theo cấp doanh thu. Top 6 nhóm hàng nên nhận các feature lag và chỉ số mùa vụ đặc thù nhóm. Các nhóm hàng đuôi (dưới MEATS) có thể chia sẻ bộ feature chung để giảm độ phức tạp mô hình. Tạo tra cứu `family_revenue_tier` (TOP6 / MID / TAIL) cho trọng số mẫu. GROCERY I xứng đáng được trọng số mẫu cao nhất: lỗi dự báo 1% ở đây tương đương ~3,4 triệu USD phân bổ sai.

### Phát Hiện 2: Cơ Cấu Doanh Thu Ổn Định Theo Thời Gian Nhưng Đồ Dùng Học Đường Có Đỉnh Hàng Năm
**Biểu đồ:** Biểu đồ diện tích xếp chồng — ngày (trục x) so với doanh số hàng ngày xếp chồng theo top 8 nhóm hàng + Khác (trục y), 2013-2017 (Biểu đồ 9)
**Quan sát:** GROCERY I duy trì dải màu cơ bản dày và ổn định trong suốt 5 năm, xác nhận thị phần thống trị và ổn định của nó. SCHOOL AND OFFICE SUPPLIES, gần như vô hình trong hầu hết năm, cho thấy đỉnh xung nhọn hàng năm rõ ràng vào tháng 8-9 — mùa tựu trường ở vùng Sierra (vùng cao) của Ecuador. Các đỉnh này sắc nét và hẹp (2-3 tháng), không dần dần. Tổng thể cột tăng lên theo thời gian, xác nhận tăng trưởng doanh số toàn hệ thống. Trận động đất tháng 4 năm 2016 có thể thấy như sự tăng chiều cao tổng cột ngắn ngủi.
**Hàm Ý Feature Engineering:** Tạo feature nhị phân `is_school_season` (tháng 8=1, tháng 9=1, tất cả tháng khác=0). Không áp dụng làm mịn trung bình trượt cho SCHOOL AND OFFICE SUPPLIES — đỉnh sẽ bị xóa, gây ra dự báo thấp nghiêm trọng trong tháng 8-9. Đối với nhóm hàng này cụ thể, giá trị thô hoặc cửa sổ lag ngắn (lag-7, lag-14) phù hợp hơn lag-365 vì độ lớn đỉnh có thể thay đổi theo năm.

### Phát Hiện 3: Chỉ Số Mùa Vụ Theo Nhóm Hàng Dao Động Từ Phẳng Đến 3,56 Lần
**Biểu đồ:** Heatmap mùa vụ — top 20 nhóm hàng (hàng) so với tháng 1-12 (cột), ô = chỉ số mùa vụ (month_mean / overall_mean) (Biểu đồ 10)
**Quan sát:** SCHOOL AND OFFICE SUPPLIES có chỉ số mùa vụ 3,56 vào tháng 8-9 (bán gấp 3,56 lần mức trung bình năm trong những tháng đó). BOOKS đạt 3,77 trong cùng cửa sổ (chỉ số mùa vụ cao nhất trong dataset). FROZEN FOODS đạt đỉnh 3,24 vào tháng 12. BEVERAGES và LIQUOR/BEER cho thấy chỉ số tăng cao vào tháng 12 (~1,5-2,0 lần). Các nhóm hàng tạp hóa cốt lõi (GROCERY I, DAIRY, CLEANING) cho thấy tính mùa vụ tương đối phẳng qua tất cả các tháng (chỉ số gần 1,0), chỉ ra rằng các nhóm hàng này không cần feature mùa vụ đặc thù nhóm — các feature lịch toàn cục là đủ.
**Hàm Ý Feature Engineering:** Tạo bảng tra cứu `family_seasonal_index` đặc thù nhóm (nhóm hàng x tháng = giá trị chỉ số). Đối với BOOKS và SCHOOL SUPPLIES, đưa vào tương tác `is_school_season` chuyên dụng. Đối với FROZEN FOODS và BEVERAGES, đưa vào tương tác `is_december` hoặc `month == 12`. Các nhóm hàng mùa vụ phẳng (GROCERY I, DAIRY) không cần feature mùa vụ đặc thù nhóm — chúng có thể chia sẻ feature `month` và `week_of_year` toàn cục, giảm độ phức tạp mô hình.

### Phát Hiện 4: Mức Tăng Khuyến Mãi PRODUCE Vượt 2 Lần; BREAD/BAKERY Gần Bằng Không
**Biểu đồ:** Biểu đồ cột nhóm — top 10 nhóm hàng (trục x) so với doanh số trung bình mỗi bản ghi (trục y), nhóm theo promo_flag (0=Không Khuyến Mãi màu xanh, 1=Khuyến Mãi màu cam) (Biểu đồ 12)
**Quan sát:** PRODUCE cho thấy mức tăng khuyến mãi cao nhất ở 2,08 lần (doanh số trung bình khi có khuyến mãi gấp hơn đôi so với không có). HOME CARE cho thấy mức tăng 2,04 lần. BEVERAGES cho thấy mức tăng 1,49 lần. BREAD/BAKERY cho thấy mức tăng gần bằng không — các cột cam và xanh gần bằng chiều cao nhau, nghĩa là khuyến mãi không tăng doanh số BREAD/BAKERY một cách có ý nghĩa. DAIRY và GROCERY I cho thấy mức tăng vừa phải (khoảng 1,3-1,5 lần). Sự biến động trong mức tăng khuyến mãi theo nhóm hàng là lý do chính để sử dụng feature tương tác khuyến mãi ở cấp nhóm hàng thay vì một cờ `on_promotion` toàn cục duy nhất.
**Hàm Ý Feature Engineering:** Tạo bảng tra cứu `family_promo_sensitivity` (nhóm hàng → tỷ lệ tăng tính từ biểu đồ này). Sử dụng nó để xây dựng feature tương tác `promo_x_family` cho các nhóm hàng có mức tăng cao (PRODUCE, HOME CARE). Đối với BREAD/BAKERY và các nhóm hàng không co giãn tương tự, cờ `on_promotion` có thể có hệ số bị ràng buộc hoặc gần bằng không. Không bỏ hoàn toàn `on_promotion` — ngay cả các nhóm hàng tăng thấp cũng hưởng lợi từ feature trong quá trình huấn luyện vì khuyến mãi ảnh hưởng đến sự phân chia quan sát-dự kiến của mô hình.

### Phát Hiện 5: BEVERAGES và GROCERY I Tương Quan Cao; BOOKS/SCHOOL SUPPLIES Tạo Thành Cụm Riêng
**Biểu đồ:** Heatmap tương quan — top 12 nhóm hàng (hàng và cột), ô = tương quan Pearson của doanh số hàng ngày (Biểu đồ 14)
**Quan sát:** BEVERAGES và GROCERY I cho thấy tương quan dương cao giữa các nhóm, chỉ ra chúng di chuyển cùng nhau về khối lượng doanh số hàng ngày. Cả hai đều là mua sắm thiết yếu hàng ngày bổ sung cho nhau theo cùng mẫu lưu lượng và khuyến mãi. BOOKS và SCHOOL AND OFFICE SUPPLIES tương quan với nhau nhưng cho thấy tương quan thấp hoặc âm với các nhóm hàng tạp hóa cốt lõi — cầu của chúng được thúc đẩy bởi lịch học, không phải lưu lượng cửa hàng chung. PRODUCE và MEATS cho thấy tương quan vừa phải (cả hai là hàng dễ hư hỏng bị ảnh hưởng bởi ngày trong tuần và mẫu khuyến mãi).
**Hàm Ý Feature Engineering:** Tương quan cao BEVERAGES-GROCERY I biện minh cho xử lý chung: các feature lag chia sẻ và feature khuyến mãi chia sẻ giữa hai nhóm hàng này sẽ không tạo ra sự dư thừa có hại. Ngược lại, BOOKS và SCHOOL SUPPLIES cần xử lý mùa vụ hoàn toàn riêng biệt — chỉ số mùa vụ của chúng tăng đột biến lên 3,56-3,77 vào tháng 8-9 trong khi các nhóm hàng tạp hóa cốt lõi vẫn phẳng. Một mô hình gộp tất cả nhóm hàng với một feature `month` duy nhất sẽ dự báo nghiêm trọng thấp BOOKS và SCHOOL SUPPLIES vào tháng 8-9.

---

## Khuyến Nghị Feature Engineering

| Tên Feature | Kiểu | Mô Tả | Độ Ưu Tiên |
|---|---|---|---|
| `family_id` | phân loại (33 cấp độ) | Định danh nhóm sản phẩm; dùng embedding cho mô hình thần kinh, one-hot cho mô hình dựa trên cây | CAO |
| `family_revenue_tier` | phân loại (TOP6/MID/TAIL) | Cấp tập trung doanh thu dựa trên ngưỡng 83% tại 6 nhóm hàng; thúc đẩy trọng số mẫu | CAO |
| `family_promo_sensitivity` | số (tra cứu) | Tỷ lệ tăng khuyến mãi ở cấp nhóm từ EDA (PRODUCE=2,08x, HOME CARE=2,04x, BREAD~1,0x); dùng như trọng số tương tác | CAO |
| `is_school_season` | nhị phân | 1 cho tháng 8 và tháng 9; nắm bắt đỉnh 3,56 lần SCHOOL SUPPLIES và đỉnh 3,77 lần BOOKS | CAO |
| `family_seasonal_index` | số (tra cứu: nhóm hàng x tháng) | Hệ số nhân đặc thù tháng cho mỗi nhóm hàng dẫn xuất từ heatmap mùa vụ; cho phép hiệu chỉnh mùa vụ đặc thù nhóm | CAO |
| `on_promotion` | nhị phân | 1 nếu bất kỳ mặt hàng nào trong nhóm đang được khuyến mãi ở cửa hàng-ngày đó; tín hiệu khuyến mãi chính, phải có trong tất cả mô hình nhóm | CAO |
| `promo_x_family_sensitivity` | số | Tương tác: on_promotion * family_promo_sensitivity; cá nhân hóa hiệu ứng khuyến mãi theo nhóm | TRUNG BÌNH |
| `is_december` | nhị phân | 1 cho tháng 12; BEVERAGES và FROZEN FOODS cho thấy chỉ số 1,5-3,24 lần vào tháng 12 | TRUNG BÌNH |

---

## Hàm Ý Mô Hình Hóa

- Một mô hình toàn cục với một feature phân loại `family` duy nhất sẽ không nắm bắt được sự khác biệt mùa vụ cực đoan giữa SCHOOL SUPPLIES (đỉnh 3,56 lần tháng 8) và GROCERY I (mùa vụ phẳng). Các chỉ số mùa vụ đặc thù nhóm hoặc tương tác là cần thiết.
- Sự tập trung 83% doanh thu vào 6 nhóm biện minh cho xử lý khác biệt: xây dựng các mô hình phức tạp, được điều chỉnh hơn cho top 6 (có thể mô hình nhóm riêng lẻ) và mô hình đơn giản hơn được gộp cho 27 nhóm còn lại.
- Độ nhạy khuyến mãi PRODUCE và HOME CARE (mức tăng >2 lần) có nghĩa là feature `on_promotion` là dự đoán quan trọng nhất cho các nhóm hàng này. Đối với BREAD/BAKERY, gần bằng không và có thể được giảm trọng số.
- Không áp dụng làm mịn trung bình trượt cho SCHOOL AND OFFICE SUPPLIES hoặc BOOKS trước khi huấn luyện — cả hai đều có đỉnh hẹp tháng 8-9 sẽ bị xóa bởi bất kỳ cửa sổ nào dài hơn 7 ngày, gây ra dự báo thấp hệ thống trong mùa tựu trường.
- Tương quan BEVERAGES-GROCERY I hỗ trợ các thành phần mô hình chung (cấu trúc lag chia sẻ, feature mùa vụ chia sẻ) nhưng không loại bỏ nhu cầu về chỉ số `family` để nắm bắt sự khác biệt mức trung bình giữa hai nhóm.
- BOOKS (zero_day_rate = 82,9%) và BABY CARE (zero_day_rate = 47,2%) là các nhóm hàng cực kỳ thưa thớt — mô hình hai giai đoạn (bộ phân loại zero + hồi quy) hoặc mô hình Tweedie phù hợp hơn hồi quy RMSE chuẩn cho các nhóm hàng này.

---

## Ghi Chú Chất Lượng Dữ Liệu

- train.csv: 3.000.888 hàng, không có giá trị thiếu. Cấu trúc bảng là 54 cửa hàng x 33 nhóm hàng x ~1.685 ngày.
- Các số liệu cấp nhóm được tính trong notebook: total_sales, avg_daily_sales, median_daily_sales, std_daily_sales, zero_day_rate, promo_day_rate, promo_sales_share, cv_daily — chúng có sẵn trong đầu ra notebook và nên được vật chất hóa như bảng tra cứu cho feature engineering.
- Giá trị tăng khuyến mãi theo nhóm: PRODUCE 2,08x, HOME CARE 2,04x, BEVERAGES 1,49x (số liệu tính toán xác nhận từ phase1). Các giá trị này là đầu ra trực tiếp của biểu đồ cột nhóm (Biểu đồ 12) và nên được coi là đầu vào có thẩm quyền cho tra cứu `family_promo_sensitivity`.
- 33 nhóm hàng tổng cộng; các nhóm hàng cấp thấp nhất (BOOKS zero_day_rate=82,9%, BABY CARE 47,2%) sẽ thống trị vấn đề zero-inflation và cần mô hình thưa thớt chuyên biệt. Hồi quy bình phương nhỏ nhất chuẩn trên các nhóm hàng này sẽ tạo ra giá trị dự đoán âm và tỷ lệ lỗi cao.
- Tăng trưởng hàng năm 2014-2016 biến đổi đáng kể theo nhóm hàng: BABY CARE +734%, MAGAZINES +730% ở trên; LINGERIE -27,9%, HOME APPLIANCES -28,5% ở dưới. Các mô hình giả định thị phần nhóm ổn định theo thời gian sẽ ước tính thấp các nhóm đang phát triển và ước tính cao các nhóm đang suy giảm — đưa vào `year` hoặc feature xu hướng trong các mô hình cấp nhóm.
