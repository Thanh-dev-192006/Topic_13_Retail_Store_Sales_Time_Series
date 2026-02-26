# Báo Cáo Tổng Hợp Phân Tích Hiệu Suất Cửa Hàng

## Tổng Quan

Phân tích hiệu suất của **54 cửa hàng** trong hệ thống bán lẻ tại Ecuador, sử dụng dữ liệu sales từ 2013-01-01 đến 2017-08-15 (~1.684 ngày). Dữ liệu gồm 3.000.888 bản ghi (54 cửa hàng × 33 nhóm sản phẩm × ~1.684 ngày).

**Datasets sử dụng:**
- `train.csv`: Dữ liệu sales (id, date, store_nbr, family, sales, onpromotion)
- `stores.csv`: Metadata cửa hàng (store_nbr, city, state, type, cluster)

---

## 1. Phân Khúc Cửa Hàng

### 1.1. Loại Cửa Hàng (A, B, C, D, E)

| Khía cạnh | Phát hiện |
|--------|----------|
| **Phân bố** | 5 loại với số lượng cửa hàng khác nhau |
| **Khác biệt doanh số** | Sự khác biệt có ý nghĩa giữa các loại (kiểm định Kruskal-Wallis, p=0,000256) |
| **Loại A** | Doanh số cao nhất — đây có thể là cửa hàng lớn, vị trí đắc địa (trung bình 39,2 triệu USD/cửa hàng) |
| **Loại C/E** | Doanh số thấp hơn — có thể là cửa hàng nhỏ hoặc ở khu vực ít dân cư |
| **Biến động** | Các loại có doanh số cao cũng có CV cao hơn — biến động lớn hơn |

**Phát Hiện Chính:** Loại cửa hàng là proxy tốt cho quy mô/công suất cửa hàng. Nên dùng loại làm feature trong mô hình.

### 1.2. Cluster (1-17)

| Khía cạnh | Phát hiện |
|--------|----------|
| **Ý nghĩa** | Cluster nhóm các cửa hàng có đặc tính kinh doanh tương tự |
| **Tính đồng nhất** | Các cửa hàng trong cùng cluster có mẫu doanh số tương tự hơn so với giữa các cluster (CV nội cluster = 0,385) |
| **Loại × Cluster** | Mỗi cluster thường chứa 1-2 loại cửa hàng → cluster là sự tinh chỉnh của loại |
| **Phạm vi doanh số** | Các cluster có sự khác biệt đáng kể về doanh số (kiểm định Kruskal-Wallis) |

**Phát Hiện Chính:** Cluster nắm bắt nhiều thông tin hơn loại đơn thuần. Nên dùng cả loại + cluster, hoặc dùng cluster thay loại.

### 1.3. Sự Tập Trung Hiệu Suất

- **Top 5 cửa hàng** chiếm ~24,4% tổng doanh số
- **Top 10 cửa hàng** chiếm ~40,2% tổng doanh số
- **Bottom 10 cửa hàng** chỉ chiếm ~6,8% tổng doanh số
- **Tỷ lệ Max/Min**: Cửa hàng lớn nhất có doanh số gấp ~23x cửa hàng nhỏ nhất (62,1 triệu USD vs 2,7 triệu USD)

---

## 2. Phân Tích Địa Lý

### 2.1. Phân Tích Theo Thành Phố

| Thành phố | Đặc điểm |
|------|-----------|
| **Quito** | Thủ đô, nhiều cửa hàng nhất (~18-22), thị trường chính, vùng Highland |
| **Guayaquil** | Thành phố lớn thứ 2, ven biển, doanh số bình quân mỗi cửa hàng cao |
| **Ambato, Cuenca** | Thành phố vừa, 2-4 cửa hàng mỗi thành phố |
| **Các thành phố nhỏ** | 1 cửa hàng mỗi thành phố, doanh số thấp hơn |

### 2.2. Phân Tích Theo Bang

- **Pichincha** (Quito): Đóng góp nhiều nhất về tổng doanh số (do nhiều cửa hàng và doanh số mỗi cửa hàng cao)
- **Guayas** (Guayaquil): Doanh số bình quân mỗi cửa hàng cao, ít cửa hàng hơn Quito

### 2.3. Ven Biển vs. Vùng Cao

| Vùng | Đặc điểm |
|--------|-----------|
| **Ven biển** (Guayas, Manabí, El Oro, ...) | Ít cửa hàng hơn; doanh số trung bình 15,0 triệu USD/cửa hàng |
| **Vùng cao** (Pichincha, Azuay, Tungurahua, ...) | Nhiều cửa hàng hơn; doanh số trung bình 30,8 triệu USD/cửa hàng (Mann-Whitney có ý nghĩa) |

**Phát Hiện Chính:** Vùng địa lý ảnh hưởng đến hành vi tiêu dùng. Ven biển và vùng cao có thể có mẫu mùa vụ khác nhau → nên dùng region/state làm feature.

---

## 3. Chất Lượng Dữ Liệu & Mẫu

### 3.1. Doanh Số Bằng Không

- **~31,3% bản ghi** có doanh số bằng không (cửa hàng × nhóm × ngày)
- Cửa hàng 52 có tỷ lệ doanh số bằng không **93,5%** → cửa hàng mới mở (tháng 4 năm 2017)
- Cửa hàng 44 có tỷ lệ thấp nhất ở **17,9%**
- Tỷ lệ doanh số bằng không **khác nhau** giữa các loại cửa hàng (các loại nhỏ có tỷ lệ không cao hơn)
- **Tác động**: Cần xử lý zero-inflation trong mô hình (mô hình Zero-Inflated hoặc phương pháp hai giai đoạn)

### 3.2. Cửa Hàng Bất Thường

- Sử dụng phát hiện Z-score trên 4 số liệu: total_sales, avg_daily_sales, CV, zero_sales_pct
- Các cửa hàng có |Z| > 2 trên bất kỳ số liệu nào được gắn cờ là bất thường
- Các cửa hàng bất thường thường là: cửa hàng cực lớn (top 2-3) hoặc cửa hàng cực nhỏ/mới

### 3.3. Tính Nhất Quán Theo Thời Gian

- **Cửa hàng ổn định nhất**: Xếp hạng hiệu suất ổn định qua các năm → dễ dự đoán
- **Cửa hàng kém ổn định nhất**: Xếp hạng thay đổi nhiều → có thể do mở rộng, cải tạo hoặc thay đổi thị trường
- **Mẫu mùa vụ**: Tất cả cửa hàng đều có đỉnh tháng 12 và đáy tháng 2

---

## 4. Khả Năng Dự Đoán Của Cửa Hàng

Điểm Khả Năng Dự Đoán (0-1) dựa trên:
- **Điểm CV (40%)**: Nghịch đảo của hệ số biến thiên
- **Điểm Doanh Số Bằng Không (30%)**: Nghịch đảo của tỷ lệ doanh số bằng không
- **Điểm Ổn Định (30%)**: Nghịch đảo của độ lệch chuẩn xếp hạng hàng năm

| Loại | Đặc điểm |
|----------|-----------|
| **Khả năng dự đoán cao** | Cửa hàng lớn, Loại A, ít doanh số bằng không, xếp hạng ổn định |
| **Khả năng dự đoán thấp** | Cửa hàng nhỏ, Loại C/E, nhiều doanh số bằng không, xếp hạng dao động |

---

## 5. Khuyến Nghị Cho Mô Hình Hóa

### 5.1. Kiến Trúc Mô Hình

| Phương pháp | Ưu điểm | Nhược điểm | Khuyến nghị |
|----------|------|------|----------------|
| **Mô hình toàn cục** (tất cả cửa hàng) | Đơn giản, ít tham số | Mất mẫu đặc thù cửa hàng | Chỉ làm đường cơ sở |
| **Mô hình theo loại cửa hàng** | Nắm bắt sự khác biệt loại | 5 mô hình, độ phức tạp vừa phải | Điểm khởi đầu tốt |
| **Mô hình theo cluster** | Nhóm tốt hơn loại | 17 mô hình, một số cluster nhỏ | Tốt hơn theo loại |
| **Mô hình theo cửa hàng** | Độ chính xác tốt nhất | 54 mô hình, tốn kém, rủi ro overfitting | Chỉ cho top 10 cửa hàng |
| **Mô hình phân cấp** | Cân bằng tốt nhất | Phức tạp để triển khai | **Phương pháp khuyến nghị** |

### 5.2. Feature Engineering

Từ phân tích này, các feature quan trọng cho mô hình:

1. **Feature cấp cửa hàng:**
   - `store_type` (A-E): Feature phân loại (p=0,000256)
   - `store_cluster` (1-17): Phân loại hoặc embedding (CV nội cluster=0,385)
   - `city`, `state`: Feature địa lý (không one-hot trực tiếp — dùng region)
   - `region` (Coastal/Highland): Feature nhị phân (30,8M vs 15,0M USD/cửa hàng)
   - `store_avg_daily_sales`: Số liệu, nắm bắt quy mô cửa hàng
   - `store_zero_rate`: Số liệu, nắm bắt độ thưa thớt (17,9% đến 93,5%)
   - `store_cv`: Số liệu, nắm bắt biến động
   - `store_predictability_score`: Điểm tổng hợp (0,4*cv + 0,3*zero + 0,3*stability)

2. **Feature tương tác:**
   - `type × family`: Mỗi loại có thể bán khác nhau cho từng nhóm hàng (xác nhận bởi heatmap Biểu đồ 36)
   - `cluster × season`: Mẫu mùa vụ có thể khác nhau giữa các cluster
   - `region × holiday`: Hiệu ứng ngày lễ khác nhau giữa Ven biển và Vùng cao

### 5.3. Chiến Lược Cụ Thể

1. **Top 10-15 cửa hàng** (chiếm ~40% doanh số, điểm khả năng dự đoán > 0,7): Nên có mô hình riêng lẻ hoặc mô hình được tinh chỉnh
2. **Cửa hàng có tỷ lệ doanh số bằng không cao** (>50%, bao gồm Cửa hàng 52): Dùng mô hình hai giai đoạn (dự đoán không vs. khác không, rồi dự đoán số lượng)
3. **Mô hình hóa dựa trên cluster**: Huấn luyện mô hình chung cho mỗi cluster, giúp các cửa hàng ít dữ liệu vẫn có mô hình tốt
4. **Feature thời gian**: Phân rã mùa vụ cấp cửa hàng nên được tính trước làm feature

---

## 6. Biểu Đồ Đã Tạo (Sau Kiểm Toán)

| # | Biểu đồ | File | Mô tả |
|---|---------------|------|--------|
| 1 | Top/Bottom 10 Cửa Hàng | `outputs/top_bottom_stores.png` | Biểu đồ cột so sánh cửa hàng tốt nhất và kém nhất |
| 2 | Biểu đồ Hộp Loại Cửa Hàng | `outputs/store_type_boxplots.png` | Phân phối doanh số theo loại A-E |
| 3 | Phân Tích Doanh Số Bằng Không | `outputs/zero_sales_analysis.png` | Mẫu doanh số bằng không theo cửa hàng và loại |
| 4 | Nhóm Hàng × Loại Cửa Hàng | `outputs/family_by_type.png` | Cơ cấu nhóm sản phẩm × loại cửa hàng |
| 5 | Điểm Khả Năng Dự Đoán | `outputs/predictability_score.png` | Xếp hạng khả năng dự đoán cửa hàng |

*(Biểu đồ 6-14 của phiên bản gốc đã bị xóa theo kế hoạch kiểm toán EDA phase2 — các phát hiện chính được giữ lại trong các số liệu tính toán bên dưới)*

---

## 7. Số Liệu Đã Xuất

File `outputs/store_metrics.csv` chứa số liệu cho 54 cửa hàng:

| Cột | Mô tả |
|--------|--------|
| `store_nbr` | ID Cửa hàng (1-54) |
| `city`, `state` | Vị trí |
| `type` | Loại cửa hàng (A-E) |
| `cluster` | Cluster cửa hàng (1-17) |
| `region` | Coastal / Highland |
| `total_sales` | Tổng doanh số 2013-2017 |
| `avg_daily_sales` | Doanh số trung bình mỗi ngày (mỗi bản ghi) |
| `median_daily_sales` | Doanh số trung vị hàng ngày |
| `std_daily_sales` | Độ lệch chuẩn |
| `cv` | Hệ số Biến Thiên |
| `zero_sales_pct` | % bản ghi có doanh số bằng không |
| `rank_total` | Xếp hạng theo tổng doanh số |
| `predictability` | Điểm khả năng dự đoán (0-1) |

---

*Notebook: `store_performance_analysis.ipynb`*
*Tạo ra như một phần của giai đoạn 03_eda_deep_dive*
