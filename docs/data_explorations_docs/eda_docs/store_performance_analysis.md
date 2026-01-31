# Store Performance Analysis - Summary Report

## Tổng Quan

Phân tích performance của **54 cửa hàng** trong hệ thống bán lẻ tại Ecuador, sử dụng dữ liệu sales từ 2013-01-01 đến 2017-08-15 (~1,684 ngày). Dữ liệu gồm 3,000,888 records (54 stores × 33 product families × ~1,684 days).

**Datasets sử dụng:**
- `train.csv`: Dữ liệu sales (id, date, store_nbr, family, sales, onpromotion)
- `stores.csv`: Metadata stores (store_nbr, city, state, type, cluster)

---

## 1. Store Segmentation Insights

### 1.1. Store Types (A, B, C, D, E)

| Aspect | Findings |
|--------|----------|
| **Phân bố** | 5 types với số lượng stores khác nhau |
| **Sales difference** | Significant difference giữa các types (Kruskal-Wallis test) |
| **Type A/D** | Thường có sales cao nhất - đây có thể là stores lớn, vị trí đắc địa |
| **Type C/E** | Sales thấp hơn - có thể là stores nhỏ hoặc ở khu vực ít dân cư |
| **Volatility** | Types có sales cao cũng có variance cao hơn (CV) |

**Key Insight:** Store type là proxy tốt cho store size/capacity. Nên dùng type làm feature trong model.

### 1.2. Clusters (1-17)

| Aspect | Findings |
|--------|----------|
| **Ý nghĩa** | Clusters nhóm stores theo đặc tính kinh doanh tương tự |
| **Homogeneity** | Stores trong cùng cluster có sales pattern tương tự hơn so với cross-cluster |
| **Type × Cluster** | Mỗi cluster thường chứa 1-2 store types → cluster = refinement của type |
| **Sales range** | Clusters có significant difference về sales (Kruskal-Wallis test) |

**Key Insight:** Cluster captures nhiều information hơn type alone. Nên dùng cả type + cluster, hoặc dùng cluster thay type.

### 1.3. Performance Concentration

- **Top 5 stores** chiếm ~20% tổng sales
- **Top 10 stores** chiếm ~40% tổng sales
- **Bottom 10 stores** chỉ chiếm ~5% tổng sales
- **Max/Min ratio**: Store lớn nhất có sales gấp ~20-25x store nhỏ nhất

---

## 2. Geographic Insights

### 2.1. City Analysis

| City | Đặc điểm |
|------|-----------|
| **Quito** | Capital, nhiều stores nhất (~18), market chính, Highland region |
| **Guayaquil** | Thành phố lớn thứ 2, coastal, sales per store cao |
| **Ambato, Cuenca** | Thành phố vừa, 2-4 stores mỗi city |
| **Các city nhỏ** | 1 store mỗi city, sales thấp hơn |

### 2.2. State Analysis

- **Pichincha** (Quito): Đóng góp nhiều nhất về total sales (do nhiều stores)
- **Guayas** (Guayaquil): Sales per store cao, ít stores hơn Quito

### 2.3. Coastal vs Highland

| Region | Đặc điểm |
|--------|-----------|
| **Coastal** (Guayas, Manabi, El Oro, etc.) | Sales per store có thể cao hơn, ít stores hơn |
| **Highland** (Pichincha, Azuay, Tungurahua, etc.) | Nhiều stores hơn, sales phân tán hơn |

**Key Insight:** Geographic region ảnh hưởng đến consumer behavior. Coastal và Highland có seasonal patterns khác nhau → nên dùng region/state làm feature.

---

## 3. Data Quality & Patterns

### 3.1. Zero Sales

- **~31% records** có zero sales (store × family × day)
- Một số stores có zero-sales rate **>40%** → stores nhỏ hoặc mới mở
- Zero-sales rate **khác nhau** giữa store types (types nhỏ có zero rate cao hơn)
- **Impact**: Cần xử lý zero-inflation trong model (Zero-Inflated models hoặc two-stage approach)

### 3.2. Outlier Stores

- Sử dụng Z-score detection trên 4 metrics: total_sales, avg_daily_sales, CV, zero_sales_pct
- Stores có |Z| > 2 trên bất kỳ metric nào được flag là outlier
- Outlier stores thường là: stores cực lớn (top 2-3) hoặc stores cực nhỏ/mới

### 3.3. Temporal Consistency

- **Most stable stores**: Performance rank ổn định qua các năm → predictable
- **Least stable stores**: Rank thay đổi nhiều → có thể do expansion, renovation, hoặc market changes
- **Seasonal patterns**: Tất cả stores đều có December peak và February dip

---

## 4. Store Predictability

Predictability Score (0-1) dựa trên:
- **CV Score (40%)**: Inverse of coefficient of variation
- **Zero Sales Score (30%)**: Inverse of zero-sales rate
- **Stability Score (30%)**: Inverse of yearly rank standard deviation

| Category | Đặc điểm |
|----------|-----------|
| **High predictability** | Stores lớn, Type A/D, ít zero sales, rank ổn định |
| **Low predictability** | Stores nhỏ, Type C/E, nhiều zero sales, rank dao động |

---

## 5. Recommendations cho Modeling

### 5.1. Model Architecture

| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| **Global model** (all stores) | Simple, ít parameters | Loses store-specific patterns | Baseline only |
| **Model per store type** | Captures type differences | 5 models, moderate complexity | Good starting point |
| **Model per cluster** | Better grouping than type | 17 models, some clusters small | Better than type |
| **Model per store** | Best accuracy | 54 models, expensive, overfit risk | Only for top stores |
| **Hierarchical model** | Best balance | Complex to implement | Recommended approach |

### 5.2. Feature Engineering

Từ phân tích này, các features quan trọng cho model:

1. **Store-level features:**
   - `store_type` (A-E): Categorical feature
   - `cluster` (1-17): Categorical hoặc embedding
   - `city`, `state`: Geographic features
   - `region` (Coastal/Highland): Binary feature
   - `store_avg_daily_sales`: Numeric, captures store size
   - `store_zero_pct`: Numeric, captures sparsity
   - `store_cv`: Numeric, captures volatility

2. **Interaction features:**
   - `type × family`: Mỗi type có thể bán khác nhau cho từng family
   - `cluster × season`: Seasonal patterns có thể khác nhau giữa clusters
   - `region × holiday`: Holiday effects khác nhau giữa Coastal và Highland

### 5.3. Chiến Lược Cụ Thể

1. **Top 10-15 stores** (chiếm ~40% sales): Nên có individual models hoặc fine-tuned models
2. **Stores có high zero-sales rate**: Dùng two-stage model (predict zero vs non-zero, rồi predict amount)
3. **Cluster-based modeling**: Train model chung cho mỗi cluster, giúp stores ít data vẫn có model tốt
4. **Temporal features**: Store-level seasonal decomposition nên được tính trước làm features

---

## 6. Visualizations Đã Tạo

| # | Visualization | File | Mô tả |
|---|---------------|------|--------|
| 1 | Top/Bottom 10 Stores | `outputs/top_bottom_stores.png` | Bar chart so sánh stores tốt nhất và kém nhất |
| 2 | Store Type Box Plots | `outputs/store_type_boxplots.png` | Distribution sales theo type A-E |
| 3 | Cluster Analysis | `outputs/cluster_analysis.png` | Sales distribution + type composition theo cluster |
| 4 | Cluster × Type Heatmap | `outputs/cluster_type_heatmap.png` | Cross-tabulation stores |
| 5 | City Analysis | `outputs/city_analysis.png` | Average và total sales theo city |
| 6 | State Analysis | `outputs/state_analysis.png` | Sales theo state |
| 7 | Coastal vs Highland | `outputs/coastal_vs_highland.png` | So sánh 2 vùng địa lý |
| 8 | Store × Time Heatmap | `outputs/store_time_heatmap.png` | Temporal consistency |
| 9 | Store Consistency | `outputs/store_consistency.png` | Yearly trajectory + rank stability |
| 10 | Scatter Analysis | `outputs/scatter_analysis.png` | Store characteristics vs sales |
| 11 | Outlier Z-Scores | `outputs/outlier_zscore.png` | Z-score heatmap cho 54 stores |
| 12 | Zero Sales Analysis | `outputs/zero_sales_analysis.png` | Zero-sales patterns |
| 13 | Family by Type | `outputs/family_by_type.png` | Product family × store type |
| 14 | Predictability Score | `outputs/predictability_score.png` | Store predictability ranking |

---

## 7. Metrics Đã Export

File `outputs/store_metrics.csv` chứa metrics cho 54 stores:

| Column | Mô tả |
|--------|--------|
| `store_nbr` | Store ID (1-54) |
| `city`, `state` | Location |
| `type` | Store type (A-E) |
| `cluster` | Store cluster (1-17) |
| `region` | Coastal / Highland |
| `total_sales` | Tổng sales 2013-2017 |
| `avg_daily_sales` | Sales trung bình mỗi ngày (per record) |
| `median_daily_sales` | Median daily sales |
| `std_daily_sales` | Standard deviation |
| `cv` | Coefficient of Variation |
| `zero_sales_pct` | % records có zero sales |
| `rank_total` | Rank theo total sales |
| `predictability` | Predictability score (0-1) |

---

*Notebook: `store_performance_analysis.ipynb`*
*Generated as part of 03_eda_deep_dive phase*
