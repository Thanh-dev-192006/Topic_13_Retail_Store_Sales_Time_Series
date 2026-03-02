# Tổng quan Feature Engineering (Ecuador Retail Sales)

Các notebook trong thư mục `04_feature_engineering/features` tập trung vào việc tạo ra các đặc trưng (features) mới từ dữ liệu thô để nâng cao sức mạnh dự báo của mô hình Machine Learning. Quá trình này không chỉ làm giàu thông tin cho mô hình mà còn xử lý triệt để các rủi ro về rò rỉ dữ liệu (Data Leakage). 

---

## MỤC TIÊU VÀ VAI TRÒ CỦA THƯ MỤC NÀY
Trong bất kỳ bài toán Machine Learning (đặc biệt là dữ liệu chuỗi thời gian - Time Series), thuật toán không thể tự "hiểu" được ngày "2016-01-01" là ngày gì, hay tại sao doanh số hôm nay lại cao đột biến. **Dữ liệu thô (Raw Data) thường rất nghèo nàn tín hiệu.**

**Vai trò cốt lõi của folder `features`:**
1. **Dịch ngôn ngữ con người sang ngôn ngữ máy học**: Bẻ gãy cấu trúc thời gian, mã hóa đặc tính cửa hàng thành các con số mà thuật toán (như LightGBM, XGBoost) có thể tính toán được.
2. **Cung cấp "trí nhớ" cho mô hình (Lags & Rolling)**: Tạo ra các biến mô tả quá khứ (hôm qua bán được bao nhiêu, trung bình tuần trước thế nào) để mô hình có cơ sở nội suy dự đoán ngày mai.
3. **Bơm thêm kiến thức ngoại lai (External Knowledge)**: Mang các yếu tố vĩ mô như giá dầu, lịch nghỉ lễ quốc gia vào tập dữ liệu để giải thích các cú sốc (Spikes/Dips) bất thường mà dữ liệu nội bộ không thể giải thích.

---

## BỨC TRANH TOÀN CẢNH: PIPELINE FEATURE ENGINEERING
Toàn bộ quá trình Feature Engineering được chia thành các luồng xử lý độc lập (Modular) trước khi được ghép lại thành một bức tranh hoàn chỉnh (Final Dataset). Quy trình luân chuyển như sau:

**1. Khởi nguồn (Raw Input):**
Bắt đầu với dữ liệu đã được làm sạch cơ bản (`train_cleaned.csv`), gồm các cột cốt lõi: `date`, `store_nbr` (cửa hàng), `family` (nhóm hàng), và `sales` (doanh số mục tiêu).

**2. Phân nhánh xử lý đặc trưng (Luồng song song):**
- **Luồng 1 (Temporal - Thời gian):** Phân tách `date` thành ngày, tháng, năm, quý, thứ trong tuần. Đánh dấu cờ (flag) các ngày quan trọng như cuối tuần, ngày 15 (Payday), cuối tháng.
- **Luồng 2 (Holidays - Ngày lễ):** Đối chiếu lịch nghỉ lễ với vị trí địa lý của từng cửa hàng. Đánh dấu xem hôm nay có phải là ngày lễ Quốc gia/Địa phương không, hay là cận kề ngày lễ (Halo effect).
- **Luồng 3 (External/Macro - Kinh tế vĩ mô):** Dóng hàng giá dầu (Oil Price) theo trục thời gian, điền khuyết các ngày cuối tuần và tính toán sự biến động giá so với tuần trước.
- **Luồng 4 (Store Encoding - Thuộc tính cửa hàng):** Chuyển đổi loại cửa hàng (Type A, B, C...) và phân bổ địa lý (City, State) thành các trọng số số học (Frequency Encoding) để mô hình hiểu được quy mô thị trường.
- **Luồng 5 (Target Encoding - Hành vi cơ sở):** Tính toán doanh số trung bình lịch sử của từng bộ đôi [Cửa hàng - Nhóm hàng] một cách bảo mật (chống Data Leakage qua KFold OOF) để mô hình có điểm neo (baseline) ban đầu.

**3. Tái tổ hợp & Tự hồi quy (Merge & Lags):**
Gộp tất cả các luồng trên lại với nhau bằng khóa là `date` và `store_nbr`. Sau đó, tiến hành **sắp xếp cực kỳ nghiêm ngặt** theo thời gian để tạo ra các biến độ trễ (Lags: doanh số $t-1, t-7...$) và trung bình trượt (Rolling Stats).

**4. Điểm kết thúc (Output):**
Sản sinh ra một ma trận dữ liệu (Dataset) khổng lồ, giàu tín hiệu, sẵn sàng để đưa vào huấn luyện các mô hình dự báo phức tạp ở thư mục `06_modeling`.

---

Dưới đây là nội dung chi tiết về mục đích, lý do triển khai và ý nghĩa của từng biến được tạo ra trong các notebook tương ứng.

---

## 1. feature_external.ipynb (Đặc trưng Ngoại lai)
**Mục tiêu**: Bổ sung các yếu tố kinh tế vĩ mô và phân bố địa lý ảnh hưởng đến sức mua của người dân. Cụ thể là giá dầu (vì Ecuador là nước xuất khẩu dầu mỏ) và thông tin về cụm cửa hàng.

**Giải thích chi tiết các biến và lý do triển khai:**
- **Oil Price (Đặc trưng Giá dầu)**: Sự biến động của giá dầu ảnh hưởng trực tiếp đến thu nhập quốc gia và tâm lý tiêu dùng.
  - `oil_price`: Giá dầu được điền khuyết bằng phương pháp Forward Fill (`ffill`). Mặc dù thị trường dầu không giao dịch vào cuối tuần/lễ (tạo ra Missing Values), nhưng giá của ngày hôm trước vẫn là thước đo kỳ vọng kinh tế tốt nhất hiện có để áp dụng cho những ngày nghỉ này.
  - `oil_price_lag_7` và `oil_price_lag_14`: Biến trễ 7 ngày và 14 ngày. **Lý do**: Tác động kinh tế không diễn ra ngay lập tức. Cần một khoảng thời gian (lag) để sự thay đổi của giá dầu ngấm vào túi tiền và hành vi chi tiêu của người dân. Thực nghiệm EDA cho thấy độ trễ 14 ngày có tương quan tốt nhất với doanh số.
  - `oil_price_rolling_mean_28`: Đường trung bình động 28 ngày. Giúp "làm mượt" các nhiễu động giá hàng ngày, giúp mô hình nắm bắt được chu kỳ xu hướng dài hạn (thị trường đang bò hay gấu).
  - `oil_price_change_pct`: % thay đổi giá dầu so với tuần trước. Biến này dùng để phát hiện các "cú sốc giá" (price shocks). Việc giá tăng/giảm đột ngột 10% trong 1 tuần sẽ có tác động tâm lý mạnh hơn nhiều so với việc giá nhích lên từ từ.

- **Store Data (Mã hóa Cửa hàng)**: Các mô hình dạng cây (Tree-based) cần số liệu dạng số thay vì chuỗi văn bản.
  - `store_type_encoded`: Label Encoding chuyển loại cửa hàng (A-E) thành số (0-4).
  - `city_freq` và `state_freq`: Tần suất xuất hiện (Frequency Encoding) của thành phố và tỉnh/bang. **Lý do**: Nếu dùng One-Hot Encoding cho hàng chục thành phố, số lượng cột sẽ bùng nổ (Curse of Dimensionality). Frequency encoding thay tên thành phố bằng tỷ lệ % số cửa hàng ở thành phố đó $\rightarrow$ Giúp mô hình ngầm hiểu được quy mô và mật độ thị trường (thành phố lớn có tỷ lệ lớn hơn). Dữ liệu này được fit trên tập train và map sang tập test.

---

## 2. feature_holiday.ipynb (Đặc trưng Ngày lễ)
**Mục tiêu**: Các ngày lễ và sự kiện đặc biệt thay đổi hoàn toàn lưu lượng khách hàng. Quá trình này giúp mô hình nhận diện chính xác ngày nào, ở đâu sẽ có đột biến doanh số.

**Giải thích chi tiết các biến và lý do triển khai:**
- **Xử lý Transferred Holidays**: Tại Ecuador, một số ngày lễ bị chính phủ dời lịch rớt vào ngày khác. Các dòng có `transferred = True` (ngày lễ gốc bị dời đi) sẽ diễn ra như một ngày làm việc bình thường. **Lý do**: Cần loại bỏ những dòng này và tạo biến `is_transferred_holiday` cho những ngày lễ được bù để mô hình không đánh giá sai sức mua của ngày bị dời lịch.
- **Phạm vi Địa lý (Geographic Scope)**: 
  - `is_national_holiday`, `is_regional_holiday`, `is_local_holiday`. **Lý do**: Một ngày kỷ niệm thành lập của thành phố A (Local) sẽ không làm tăng doanh số ở thành phố B. Việc map chính xác `city` và `state` của cửa hàng với phạm vi của ngày lễ giúp đánh cờ (flag) chính xác.
- `is_carnaval`: Cờ nhị phân (1/0) dành riêng cho Lễ hội Carnaval. Đây là mùa mua sắm và du lịch cực lớn tại Nam Mỹ, tạo ra hành vi mua sắm khác biệt hoàn toàn (đặc biệt các mặt hàng đồ uống, tiệc tùng).
- **Halo Effect (Hiệu ứng Lan tỏa)**: 
  - `days_to_next_holiday`: Càng gần đến ngày lễ, người dân càng tăng cường mua sắm tích trữ (Pre-holiday surge).
  - `days_after_last_holiday`: Ngay sau ngày lễ, nhu cầu thường sụt giảm mạnh (Post-holiday dip) vì mọi người đã mua đủ đồ. Biến này cung cấp "khoảng cách thời gian" để mô hình đo lường hiệu ứng này.

---

## 3. feature_target_encoding.ipynb (Mã hóa Biến mục tiêu)
**Mục tiêu**: Cung cấp cho mô hình một con số cơ sở (baseline) ước lượng: Cửa hàng X bán nhóm hàng Y bình thường được bao nhiêu doanh số tiềm năng?

**Giải thích chi tiết các biến và lý do triển khai:**
- `store_family_te`: Là doanh số trung bình trong lịch sử của cặp `store_nbr` - `family`. Thay vì để thuật toán tự lần mò qua các Node của cây quyết định, biến này trực tiếp nói cho mô hình biết baseline tiêu chuẩn.
- **Lý do triển khai bằng KFold Out-of-Fold (OOF)**: Đây là biện pháp phòng vệ Data Leakage cực kỳ quan trọng. 
  - Nếu chỉ tính trung bình toán học thông thường trên toàn tập Train, một quan sát của ngày hôm nay sẽ vô tình "vay mượn" chính con số doanh số của hôm nay để tính ra trung bình. Mô hình sẽ học vẹt và Overfitting cực nặng.
  - Quá trình chia 5 Folds (Splits) đảm bảo: Doanh số dự kiến của Nhóm A ở cụm 1, chỉ được cấu thành từ 4 cụm dữ liệu chứa Nhóm A khác, hoàn toàn không bị trộn lẫn thông tin của bản thân nó.
  - Có áp dụng `smoothing` để các sản phẩm quá hiếm (ít dữ liệu) sẽ dần tiến về trung bình toàn cục, không bị nhiễu.

---

## 4. feature_temporal.ipynb (Tiền xử lý Thời gian & Tạo Lag tự hồi quy)
**Mục tiêu**: Cắt xẻ dữ liệu thời gian thành các chu kỳ (mùa vụ) và tận dụng dòng chảy độ trễ của lịch sử (Lags) để dự đoán tương lai. Đây là cốt lõi của bài toán Time-Series.

**Giải thích chi tiết các biến và lý do triển khai:**
- **Đặc trưng Lịch (Calendar Features)**: 
  - `year`, `month`, `day`, `day_of_week`, `week_of_year`, `quarter`: Mô hình cây quyết định không hiểu định dạng Date ("2016-01-01"). Chúng ta cần bẻ gãy thời gian ra để mô hình dễ dàng phát hiện quy luật (Ví dụ: Tháng 12 đồ uống bán chạy, Cuối tuần siêu thị đông khách).
  - Cờ nhị phân `is_weekend`, `is_month_start`, `is_month_end`: Nhận diện các điểm chốt thường có xung lượng giao dịch cao.
  - `is_payday` (Cờ Ngày phát lương): Ở Ecuador, người dân lĩnh lương vào ngày 15 và ngày cuối cùng của tháng. Doanh số thường đạt đỉnh (Spike) ngay trong những ngày này. Đây là **Golden Feature** định hướng sức mua.

- **Đặc trưng Lùi Thời Gian (Lag Features)**:
  - **Lý do thiết yếu**: Doanh số ngày hôm nay được dự báo tốt nhất bằng cách xem doanh số của các ngày trước đó ra sao.
  - Chú ý quan trọng: Phải sort dữ liệu theo cụm (`store`, `family`) và theo `date` trước khi tính Lag để thời gian của từng mã hàng không bị lỗi chéo nhau.
  - `lag_1`, `lag_2`, `lag_3`: Doanh số 1-3 ngày trước (Bắt nhịp động lượng tăng/giảm ngắn hạn).
  - `lag_7` (Tuần trước): Vì hành vi mua sắm lặp lại theo tuần (Thứ Tư tuần này giống Thứ Tư tuần trước).
  - `lag_14`, `lag_28`, `lag_364`: Các mốc thời gian trung và dài hạn (1 năm trước) để làm mốc so sánh mùa vụ.

- **Đặc trưng Cửa hàng trôi (Rolling Statistics)**:
  - `rolling_mean_7`, `rolling_mean_14`, `rolling_mean_28`: Giá trị trung bình của doanh số tuần qua, 2 tuần qua...
  - `rolling_std_7`: Độ lệch chuẩn 7 ngày (biểu thị độ nhiễu loạn/bất ổn của sức mua).
  - **Bảo mật Rò rỉ (Shift Rule)**: Trước khi tính Rolling, toàn bộ dữ liệu phải được gọi lệnh `.shift(1)`. Việc này đảm bảo điểm tính toán khung trượt luôn lấp sau thực tại 1 ngày, mô hình tuyệt đối không ăn gian nhìn thấy số liệu của tương lai hay ngay thời điểm đang dự báo $(t)$.
