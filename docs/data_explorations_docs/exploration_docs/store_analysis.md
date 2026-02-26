# Báo Cáo Khám Phá Dataset Metadata Cửa Hàng
**Phân Tích Chuỗi Thời Gian Doanh Số Bán Lẻ**
*Tạo ngày: 2026-01-02*

---

## Tóm Tắt Điều Hành

Báo cáo này phân tích metadata cho 54 cửa hàng bán lẻ trên khắp Ecuador, phục vụ như bảng chiều nền tảng cho dự báo doanh số. Bốn phát hiện quan trọng nổi bật:

1. **Sự tập trung địa lý tạo rủi ro mô hình hóa**: Quito thống trị với 22 cửa hàng (40,7% mạng lưới), trong khi 16 thành phố khác chỉ có 1-2 cửa hàng mỗi nơi. Sự tập trung cực đoan này có nghĩa là mô hình có thể overfitting vào các mẫu của Quito và hoạt động kém ở các khu vực ít được đại diện hơn.

2. **Thứ bậc loại cửa hàng gợi ý phân đoạn chiến lược**: Năm loại cửa hàng (A-E) cho thấy phân phối cân bằng, với Loại D là đa số (33,3%). Thứ tự chữ cái (A→E) có thể đại diện cho thứ bậc kinh doanh được xác định (ví dụ: kích thước, định dạng hoặc cấp thị trường).

3. **Hệ thống cluster thiếu tài liệu nhưng có độ chi tiết**: 17 cluster cho 54 cửa hàng (trung bình 3,2 cửa hàng/cluster) chỉ ra phân đoạn chi tiết — có thể dựa trên nhân khẩu học, hiệu suất doanh số hoặc bối cảnh cạnh tranh. Tuy nhiên, không có metadata giải thích định nghĩa cluster.

4. **Chất lượng dữ liệu hoàn hảo cho phép sử dụng ngay lập tức**: Không có giá trị thiếu, không có bản sao và các trường phân loại sạch — dataset sẵn sàng cho sản xuất. Sự dư thừa duy nhất là `type_encoded` (bản sao của `type`), nên bị xóa để tránh đa cộng tuyến.

---

## Tổng Quan Dataset

### Dataset Này Chứa Gì
Dataset cửa hàng là **bảng chiều tĩnh** liệt kê đặc điểm của từng địa điểm bán lẻ. Nó cung cấp metadata địa lý và vận hành để phân đoạn cửa hàng trong các mô hình dự báo doanh số.

**Thông Số Cốt Lõi:**
- **Hàng**: 54 cửa hàng (một hàng mỗi địa điểm thực tế)
- **Cột**: 6 feature (store_nbr, city, state, type, cluster, type_encoded)
- **Khoảng Thời Gian**: Không có chiều thời gian (ảnh chụp nhanh, không phải chuỗi thời gian)
- **Chi Tiết**: Cấp cửa hàng (không có phân tách dưới cửa hàng)
- **Dung Lượng Bộ Nhớ**: ~3 KB (không đáng kể)

### Bối Cảnh Kinh Doanh
Corporación Favorita vận hành mạng lưới bán lẻ phân tán địa lý trên khắp Ecuador. Dataset này cho phép:
- **Phân đoạn thị trường**: Nhóm cửa hàng theo loại, cluster hoặc khu vực cho chiến lược mục tiêu
- **Phân tích mở rộng**: Xác định khu vực thiếu phục vụ vs. thị trường bão hòa (Quito)
- **Benchmarking hiệu suất**: So sánh doanh số qua các loại hoặc cluster để tìm thực hành tốt nhất
- **Phân bổ nguồn lực**: Ưu tiên hàng tồn kho, nhân sự và khuyến mãi dựa trên đặc điểm cửa hàng

---

## Cấu Trúc Dữ Liệu & Đặc Điểm

### Thông Số Cột

| Cột | Loại | Mô Tả | Phạm Vi Giá Trị |
|--------|------|-------------|-------------|
| `store_nbr` | int64 | Định danh cửa hàng duy nhất (khóa chính) | 1 - 54 |
| `city` | object | Vị trí thành phố của cửa hàng | 22 thành phố duy nhất |
| `state` | object | Tỉnh/bang Ecuador | 16 bang duy nhất |
| `type` | object | Phân loại loại/định dạng cửa hàng | A, B, C, D, E |
| `cluster` | int64 | ID cluster/phân đoạn cửa hàng | 1 - 17 |
| `type_encoded` | int64 | Mã hóa số của `type` (0-4) | 0 - 4 |

**Ghi Chú Quan Trọng**:
- **Khóa chính**: `store_nbr` là duy nhất (không có bản sao)
- **Dư thừa**: `type_encoded` là biến đổi label-encoding đơn giản của `type` (A=0, B=1, v.v.) — không cung cấp thông tin mới
- **Thứ bậc địa lý**: `city` nằm trong `state` (quan hệ nhiều-một)

### Phân Phối Loại Cửa Hàng

| Loại | Số lượng | Phần trăm | Ý nghĩa có thể |
|------|-------|------------|----------------|
| D | 18 | 33,3% | Cửa hàng tiêu chuẩn cấp trung (định dạng đa số) |
| E | 11 | 20,4% | Định dạng đặc biệt hoặc tiện lợi |
| A | 9 | 16,7% | Định dạng flagship hoặc siêu cửa hàng |
| B | 8 | 14,8% | Định dạng khu vực |
| C | 8 | 14,8% | Định dạng nhỏ gọn |

**Diễn Giải**: Thứ tự chữ cái (A→E) gợi ý thứ bậc kinh doanh được xác định:
- **Loại A**: Cửa hàng định dạng lớn (siêu thị, siêu cửa hàng), doanh số trung bình 39,2 triệu USD
- **Loại B-D**: Định dạng cấp trung với kích thước/phân loại giảm dần
- **Loại E**: Định dạng nhỏ (tiện lợi, thành thị hoặc đặc biệt)

**Hàm Ý Mô Hình Hóa**: Phân phối tương đối cân bằng (không có loại nào <15%) có nghĩa là không có mất cân bằng lớp nghiêm trọng — an toàn khi sử dụng như feature phân loại với mã hóa one-hot.

### Phân Phối Cluster

**Đặc Điểm Cluster**:
- **Số Cluster**: 17
- **Cửa Hàng Mỗi Cluster**: Phạm vi = 1-5 cửa hàng, Trung bình = 3,2 cửa hàng/cluster
- **Phân Phối**: Không đều — một số cluster có 5 cửa hàng, các cluster khác chỉ 1

**Gợi Ý**:
- Chi tiết cao (17 phân đoạn cho 54 cửa hàng) chỉ ra **phân đoạn kinh doanh phức tạp**
- Tiêu chí phân cụm có thể: nhân khẩu học khách hàng, cấp khối lượng doanh số, cường độ cạnh tranh hoặc thị trường địa lý
- Cluster thành viên đơn có thể đại diện cho điểm ngoại lệ (ví dụ: định dạng thí điểm, mua lại di sản hoặc thị trường độc đáo)

**Khoảng Trống Dữ Liệu**: Không có metadata giải thích định nghĩa cluster — giới hạn diễn giải kinh doanh.

**Hàm Ý Mô Hình Hóa**:
- Các cluster nhỏ (n=1-2) có thể gây overfitting nếu sử dụng như feature phân loại
- Xem xét nhóm thành "macro-cluster" hoặc sử dụng như feature số nếu cluster có ý nghĩa thứ tự

---

## Phát Hiện & Mẫu Chính

### 1. Sự Tập Trung Địa Lý: Sự Thống Trị Của Quito

**Số Lượng Cửa Hàng Theo Thành Phố (Top 5)**:

| Thành phố | Số Cửa Hàng | % Tổng |
|------|-------------|------------|
| Quito | 22 | 40,7% |
| Guayaquil | 4 | 7,4% |
| Cuenca | 3 | 5,6% |
| Santo Domingo | 2 | 3,7% |
| Ambato | 2 | 3,7% |
| Khác (17 thành phố) | 21 | 38,9% |

**Phát Hiện Quan Trọng**: Chỉ Quito chiếm **41% tất cả cửa hàng**, trong khi 17 thành phố khác chỉ có 1 cửa hàng mỗi nơi.

**Tại Sao Điều Này Quan Trọng**:
1. **Rủi Ro Overfitting Mô Hình**: Mô hình machine learning được huấn luyện trên dataset này sẽ học các mẫu đặc thù Quito và có thể thất bại trong việc tổng quát hóa cho thị trường nông thôn hoặc nhỏ hơn.
2. **Phương Sai Hiệu Suất**: Dự báo doanh số cho cửa hàng Quito (n=22, kích thước mẫu cao) sẽ có độ không chắc chắn thấp hơn so với dự báo cho thành phố một cửa hàng.

**Hàm Ý Actionable**:
- Phân đoạn mô hình theo "Quito vs. không phải Quito" để kiểm tra xem các chiến lược dự báo khác nhau có cần thiết không
- Không mã hóa one-hot `city` trực tiếp — 17 thành phố có một cửa hàng sẽ dẫn đến overfitting
- Dùng `region` (Highland/Coastal) hoặc cờ nhị phân `is_quito` thay thế

### 2. Phân Phối Cấp Bang: Phân Cụm Khu Vực

**Số Lượng Cửa Hàng Theo Bang (Top 5)**:

| Bang | Số Cửa Hàng | % Tổng |
|-------|-------------|------------|
| Pichincha (bang của Quito) | 23 | 42,6% |
| Guayas (bang của Guayaquil) | 7 | 13,0% |
| Azuay (bang của Cuenca) | 4 | 7,4% |
| Los Ríos | 3 | 5,6% |
| Tungurahua | 3 | 5,6% |
| Khác (11 bang) | 14 | 25,9% |

**Hàm Ý Kinh Doanh**:
- **Vùng Highland (Pichincha, Azuay)** thống trị so với **vùng Coastal (Guayas)**
- Có thể phản ánh phân phối dân số, nhưng cũng gợi ý tiềm năng khoảng trống thị trường ven biển

### 3. Loại Cửa Hàng vs. Cluster: Không Có Quan Hệ Mạnh

**Từ Phân Tích Notebook**: Heatmap của cluster × loại cho thấy phân phối thưa thớt — không có mẫu rõ ràng như "tất cả cửa hàng Loại A ở Cluster 1."

**Ý Nghĩa**:
- **Cluster KHÔNG được xác định chỉ bởi loại cửa hàng** — chúng có thể kết hợp địa lý, khối lượng doanh số hoặc các yếu tố khác
- **Tính độc lập của feature**: `type` và `cluster` cung cấp thông tin bổ sung (đa cộng tuyến thấp)

**Hàm Ý Mô Hình Hóa**: An toàn khi bao gồm cả `type` và `cluster` trong mô hình mà không có lo ngại dư thừa. CV nội cluster = 0,385 xác nhận rằng cluster nắm bắt phương sai không được giải thích bởi loại đơn thuần.

---

## Đánh Giá Chất Lượng Dữ Liệu

### Tính Đầy Đủ: Hoàn Hảo ✅

```
Cột             Giá Trị Thiếu    Phần Trăm
store_nbr       0                0,0%
city            0                0,0%
state           0                0,0%
type            0                0,0%
cluster         0                0,0%
type_encoded    0                0,0%
```

**Đánh Giá**: Không có giá trị thiếu. Dataset 100% đầy đủ.

### Tính Nhất Quán: Xuất Sắc ✅

**✅ Điểm Mạnh:**
- **Không có ID cửa hàng trùng lặp**: Tất cả giá trị `store_nbr` là duy nhất (1-54)
- **Giá trị phân loại hợp lệ**: Tất cả giá trị `type` là A-E (không có lỗi chính tả, null hoặc mã bất ngờ)
- **Phạm vi số hợp lệ**: `cluster` (1-17) và `type_encoded` (0-4) không có điểm ngoại lệ
- **Lồng địa lý**: Tất cả thành phố ánh xạ chính xác đến bang tương ứng

**⚠️ Dư Thừa Nhỏ:**
- `type_encoded` là biến đổi xác định của `type` (A→0, B→1, v.v.)
- **Hành động**: Xóa `type_encoded` trong mô hình hóa để tránh đa cộng tuyến
- **Giữ lại `type`** để linh hoạt lựa chọn chiến lược mã hóa (one-hot, target encoding, v.v.)

### Vấn Đề Tiềm Ẩn

**1. Cardinality Phân Loại Cao**:
- **Cardinality cao**: 22 thành phố, 16 bang
- **Đại diện thưa thớt**: 17 thành phố có ≤2 cửa hàng mỗi nơi

**Rủi Ro**: Mã hóa one-hot `city` tạo 22 feature nhị phân — có thể gây overfitting
**Giảm Thiểu**: Nhóm các thành phố hiếm thành danh mục "Khác"; sử dụng `state` thay vì `city` cho các nhóm rộng hơn

**2. Thiếu Metadata Cluster**:
- Dataset cung cấp ID cluster (1-17) nhưng không có giải thích về cách cluster được xác định
- **Khuyến Nghị**: Tài liệu hóa định nghĩa cluster (hỏi các bên liên quan kinh doanh hoặc reverse-engineer từ dữ liệu doanh số)

---

## Hàm Ý Kinh Doanh

### 1. Loại Cửa Hàng Như Phân Tầng Doanh Số

**Chiến Lược Kiểm Tra**:
1. Nối stores.csv với train.csv theo `store_nbr`
2. So sánh doanh số trung bình hàng ngày theo `type`
3. Mẫu kỳ vọng: Loại A ($39,2M) > Loại B > ... > Loại E (nếu A = định dạng lớn nhất)
4. Xác nhận bởi kiểm định Kruskal-Wallis: H=21,46, p=0,000256 ✅

### 2. Cơ Hội Mở Rộng Địa Lý

**Dấu Chân Hiện Tại**:
- **Bão hòa**: Quito (22 cửa hàng trong một thành phố)
- **Thiếu phục vụ**: Các thành phố ven biển (chỉ Guayaquil có 4 cửa hàng, còn lại có 1-2)

**Câu Hỏi Chiến Lược**:
1. Quito có **bão hòa** (rủi ro ăn thịt lẫn nhau) hay chỉ là **thị trường cốt lõi** (cầu cao)?
2. Các khu vực ít được đại diện hơn là **cơ hội thấp** (dân số nhỏ) hay **tăng trưởng chưa khai thác** (cầu chưa được đáp ứng)?

---

## Tích Hợp & Bước Tiếp Theo

### Chiến Lược Join Với Dữ Liệu Khác

```python
# Nối metadata cửa hàng vào dữ liệu doanh số
df_train = df_train.merge(df_stores, on='store_nbr', how='left')
```

**Kết Quả Kỳ Vọng**: Mỗi bản ghi doanh số kế thừa đặc điểm cửa hàng (city, state, type, cluster).

### Feature Engineering Khuyến Nghị

**1. Nhóm Địa Lý**:
```python
# Đơn giản hóa thành phố thành Quito vs. không phải Quito
df_stores['is_quito'] = (df_stores['city'] == 'Quito').astype(int)

# Nhóm bang thành các vùng (Highland vs. Coastal vs. Amazon)
region_map = {
    'Pichincha': 'Highland', 'Azuay': 'Highland', 'Tungurahua': 'Highland',
    'Guayas': 'Coastal', 'Manabí': 'Coastal', 'El Oro': 'Coastal',
    # ... (ánh xạ đầy đủ)
}
df_stores['region'] = df_stores['state'].map(region_map)
```

**2. Mã Hóa Loại Cửa Hàng**:
```python
# Mã hóa one-hot cho mô hình dựa trên cây
df_stores_encoded = pd.get_dummies(df_stores, columns=['type'], drop_first=False)

# Hoặc mã hóa thứ tự nếu A→E đại diện thứ bậc kích thước
type_order = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'E': 1}
df_stores['type_ordinal'] = df_stores['type'].map(type_order)
```

**3. Feature Lookup Cấp Cửa Hàng** (từ EDA hiệu suất):
```python
# Thêm từ store_metrics.csv
store_features = pd.read_csv('outputs/store_metrics.csv')
df_stores = df_stores.merge(store_features[['store_nbr', 'total_sales',
    'avg_daily_sales', 'zero_sales_pct', 'cv', 'predictability']],
    on='store_nbr')
```

---

## Kết Luận

Dataset cửa hàng là **bảng chiều sẵn sàng cho sản xuất, chất lượng cao** với không có giá trị thiếu và cấu trúc sạch. Kích thước nhỏ gọn của nó (54 cửa hàng, 6 feature) làm cho nó dễ tích hợp và duy trì.

**Điểm Mạnh Chính**:
1. **Tính đầy đủ hoàn hảo** (0% dữ liệu thiếu)
2. **Khóa chính sạch** (store_nbr) cho join đáng tin cậy
3. **Loại cửa hàng cân bằng** (không có mất cân bằng lớp nghiêm trọng)
4. **Phân đoạn phong phú** (loại, cluster, địa lý)

**Rủi Ro Chính**:
1. **Thiên lệch địa lý**: Sự tập trung 41% của Quito có thể gây overfitting mô hình — dùng `is_quito` và `region` thay vì `city`
2. **Thành phố thưa thớt**: 17 thành phố có ≤2 cửa hàng thiếu dữ liệu đủ cho mô hình cấp thành phố
3. **Cluster chưa được tài liệu hóa**: Thiếu metadata giới hạn diễn giải kinh doanh
4. **Feature dư thừa**: `type_encoded` nên bị xóa

Dataset này **sẵn sàng tích hợp ngay lập tức** — giá trị chính mở ra khi kết hợp với dữ liệu doanh số và giao dịch để tiết lộ các mẫu hiệu suất cửa hàng.
