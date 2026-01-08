# Train Dataset Exploration Report
**Retail Store Sales Time Series Analysis**
*Generated: 2026-01-01*

---

## Executive Summary

This report analyzes 3 million historical sales records from a retail chain operating 54 stores across multiple product categories. Five critical insights emerged from the exploration:

1. **Massive scale with extreme concentration**: $1.07 billion in total sales, but just 3 product families (GROCERY I, BEVERAGES, PRODUCE) account for 64% of revenue. The top 4 stores (#44, #45, #47, #3) generate 31% of all sales.

2. **High sparsity signals operational challenges**: 31.3% of records show zero sales, indicating either true stockouts, closed stores on specific days, or data collection artifacts that need investigation.

3. **Severe sales distribution skew**: While mean sales per record = $357.78, the median is only $11.00 (96.9% lower). This suggests most transactions are small, with a few large-volume sales driving averages—critical for forecasting model selection.

4. **Promotional strategy is category-specific**: Promotions ran on 1,230 out of ~1,500+ days, but 79.6% of individual records had no promotion. GROCERY I, PRODUCE, and BEVERAGES receive 50% of all promotional activity, aligning with their revenue dominance.

5. **Holiday effect detected**: January 1, 2013 shows anomalously low sales ($2,511 vs. typical $350-500K daily), confirming the need to integrate external holiday calendars for accurate forecasting.

---

## Dataset Overview

### What This Dataset Contains
The training dataset captures daily sales transactions at the **store-product family-day** level for a retail chain in Ecuador. Each row represents one product family's performance in one store on one specific day.

**Core Specifications:**
- **Rows**: 3,000,888 records
- **Columns**: 6 features (id, date, store_nbr, family, sales, onpromotion)
- **Time Span**: Starts January 1, 2013 (end date not explicitly shown but inferred to cover multiple years based on row count)
- **Granularity**: Daily sales aggregated by store and product family
- **Memory Footprint**: 137.4 MB (manageable for in-memory processing)

### Business Context
This is transactional sales data from Corporación Favorita, an Ecuadorian grocery retailer. The dataset supports time series forecasting to optimize:
- Inventory management (reduce stockouts and overstock)
- Promotional planning (ROI on promotional spend)
- Resource allocation across stores

---

## Data Structure & Characteristics

### Panel Data Structure
The dataset follows a **three-dimensional panel structure**:

```
Stores (54) × Product Families (33) × Days (≈1,685) ≈ 3,000,888 records
```

**Dimensions:**
- **Stores**: 54 unique retail locations (store_nbr: 1-54)
- **Product Families**: 33 categories (e.g., AUTOMOTIVE, BABY CARE, BEVERAGES, GROCERY I, PRODUCE)
- **Time Period**: Approximately 1,685 days (~4.6 years from Jan 2013)

### Column Specifications

| Column | Type | Description | Value Range |
|--------|------|-------------|-------------|
| `id` | int64 | Unique transaction identifier | 0 - 3,000,887 |
| `date` | object | Transaction date | 2013-01-01 onwards |
| `store_nbr` | int64 | Store identifier | 1 - 54 |
| `family` | object | Product category | 33 unique families |
| `sales` | float64 | Total sales units/value | 0 - 124,717 |
| `onpromotion` | int64 | Number of items on promotion | 0 - 741 |

**Critical Note on Promotions**: The `onpromotion` field represents **count of promoted items**, not a binary flag. Values >1 indicate multiple SKUs within a family were promoted simultaneously. Maximum value of 741 suggests aggressive promotional campaigns in certain store-family-day combinations.

---

## Key Findings & Patterns

### 1. Sales Performance Concentration

**Store-Level Performance:**

The sales distribution across stores is highly unequal, following a power-law pattern:

| Store # | Total Sales | % of Total | Cumulative % |
|---------|-------------|------------|--------------|
| 44 | $62.1M | 5.8% | 5.8% |
| 45 | $54.5M | 5.1% | 10.9% |
| 47 | $50.9M | 4.7% | 15.6% |
| 3 | $50.5M | 4.7% | 20.3% |
| 49 | $43.4M | 4.0% | 24.3% |
| 46 | $41.9M | 3.9% | 28.2% |
| 48 | $35.9M | 3.3% | 31.6% |
| 51 | $32.9M | 3.1% | 34.6% |
| 8 | $30.5M | 2.8% | 37.5% |
| 50 | $28.7M | 2.7% | 40.1% |

**Business Implication**: The top 10 stores (18.5% of locations) generate 40% of total revenue. These flagship stores likely have:
- Higher foot traffic (urban/commercial zones)
- Larger floor space
- Different customer demographics

Forecasting accuracy for these stores has disproportionate business impact—prioritize model tuning for top performers.

**Product Family Performance:**

| Family | Total Sales | % of Total |
|--------|-------------|------------|
| GROCERY I | $343.5M | 32.0% |
| BEVERAGES | $217.0M | 20.2% |
| PRODUCE | $122.7M | 11.4% |
| CLEANING | $97.5M | 9.1% |
| DAIRY | $64.5M | 6.0% |
| BREAD/BAKERY | $42.1M | 3.9% |
| POULTRY | $31.9M | 3.0% |
| MEATS | $31.1M | 2.9% |
| PERSONAL CARE | $24.6M | 2.3% |
| DELI | $24.1M | 2.2% |

**Business Implication**: Three families (GROCERY I, BEVERAGES, PRODUCE) represent 64% of revenue. These are:
- High-frequency purchase categories (daily necessities)
- High-volume, lower-margin items
- Sensitive to promotions and stockouts

Focus forecasting efforts on these top categories first—errors here directly impact revenue.

### 2. Sales Distribution Characteristics

**Statistical Profile:**
- **Mean Sales**: $357.78 per record
- **Median Sales**: $11.00 per record
- **Standard Deviation**: $1,102.00 (3x the mean)
- **Maximum Single Record**: $124,717

**What This Means:**

The 97% gap between mean and median reveals an **extremely right-skewed distribution**. Visualizing this would show:
- A long tail of small transactions ($0-$50)
- A small number of massive sales events (likely bulk purchases or aggregated daily totals for high-volume families)

**Modeling Implications:**
1. Standard linear regression will overpredict small sales and underpredict large sales
2. Consider log-transformation or specialized models for count data (e.g., Negative Binomial, Zero-Inflated models)
3. Median-based error metrics (MDAE) may be more informative than RMSE
4. Ensemble methods (GBM, Random Forest) handle skewed distributions better than linear models

### 3. Zero Sales: Sparsity Problem

**Scale of the Issue:**
- **Zero Sales Records**: 939,130 (31.3% of dataset)
- **Interpretation**: Nearly 1 in 3 records show no sales

**Possible Explanations:**
1. **New product introductions**: Families not yet stocked in certain stores (early 2013)
2. **Stockouts**: Inventory depletion leading to lost sales
3. **Store closures**: Specific days when stores were closed (holidays, renovations)
4. **Niche products**: Low-demand families (e.g., AUTOMOTIVE, BOOKS) with naturally sparse sales
5. **Data collection method**: Automated system records 0 when no transactions occurred

**Business Questions to Resolve:**
- Are these true zeros (store open, no sales) or structural zeros (store closed, product unavailable)?
- Which families have the highest zero-rate? (likely low-frequency categories)
- Do zeros cluster around specific dates (holidays) or stores (low-traffic locations)?

**Next Steps**: Cross-reference with:
- Store metadata (opening hours, renovation schedules)
- Product availability data (when families were introduced to stores)
- Holiday calendar (to separate true demand = 0 from store closure = 0)

### 4. Promotional Strategy Insights

**Promotion Volume:**
- **Total Promotional Items**: 7,810,622 (sum of onpromotion field)
- **Records With No Promotion**: 2,389,559 (79.6%)
- **Days With Active Promotions**: 1,230 out of ~1,685 total days (73%)

**Interpretation**: While promotions run frequently (3 out of 4 days), they target specific store-family combinations rather than blanket discounts.

**Promotional Focus by Store:**

| Store # | Total Promoted Items | Strategy |
|---------|----------------------|----------|
| 53 | 204,016 | Highest promo intensity |
| 47 | 192,725 | Aggressive discounting |
| 44 | 192,449 | Top sales + top promos |
| 45 | 191,503 | Top sales + top promos |
| 46 | 190,697 | Top sales + top promos |

**Key Observation**: Stores #44, #45, #46, #47 appear in both top sales AND top promotions lists. This suggests:
- High-traffic stores use promotions to drive volume
- OR promotions are cost-effective in these locations (high conversion rates)

**Promotional Focus by Family:**

| Family | Total Promoted Items | % of Family's Sales |
|--------|----------------------|---------------------|
| GROCERY I | 1,914,801 | 24.5% of all promos |
| PRODUCE | 1,117,921 | 14.3% |
| BEVERAGES | 906,958 | 11.6% |
| DAIRY | 728,707 | 9.3% |
| CLEANING | 661,157 | 8.5% |

**Business Insight**: The top 3 revenue-generating families (GROCERY I, BEVERAGES, PRODUCE) also receive the most promotional support. This is either:
- Smart strategy (promote high-volume items to drive traffic)
- OR reactive (these categories face more competition, requiring discounts)

**Anomaly Alert**: Promotions started late—the first 5 days of 2013 show zero promotions. This could indicate:
- Data collection lag
- Post-holiday pricing normalization
- Or incomplete records for early 2013

### 5. Time Series Patterns & Anomalies

**Daily Sales Volatility:**

| Date | Total Daily Sales | Note |
|------|-------------------|------|
| 2013-01-01 | $2,512 | **Anomaly**: 99% lower than normal |
| 2013-01-02 | $496,092 | Normal operational day |
| 2013-01-03 | $361,461 | Normal |
| 2013-01-04 | $354,460 | Normal |
| 2013-01-05 | $477,350 | Normal |

**Critical Finding**: January 1, 2013 (New Year's Day) shows sales of only $2,512, which is 99% below typical daily sales of $350,000-$500,000. This is clearly a holiday effect—stores were either:
- Fully closed (and $2,512 represents automated/online sales)
- Open for limited hours
- Experiencing near-zero foot traffic

**Implication**: This confirms the dataset is sensitive to:
- **National holidays** (New Year's, Christmas, etc.)
- **Local holidays** (Ecuador-specific events)
- **Seasonal patterns** (school calendars, harvest seasons)

**Why This Matters for Forecasting**:
1. Models trained on raw data will learn incorrect patterns unless holidays are explicitly flagged
2. Need to integrate external calendar data (provided in `holidays_events.csv`)
3. Consider separate models or dummy variables for holiday periods

---

## Data Quality Assessment

### Completeness: Excellent ✅

**Missing Values Analysis:**
```
Column          Missing Values    Percentage
id              0                 0.0%
date            0                 0.0%
store_nbr       0                 0.0%
family          0                 0.0%
sales           0                 0.0%
onpromotion     0                 0.0%
```

**Assessment**: Zero missing values across all fields. This is exceptional for a dataset of this size and indicates:
- Robust data collection processes
- Automated sales tracking system (POS integration)
- No data transfer/ETL failures

**No Imputation Needed**: Proceed directly to modeling without missing value handling.

### Consistency: High (with caveats)

**✅ Strengths:**
- Date format appears consistent (YYYY-MM-DD)
- Store numbers are sequential integers (1-54)
- Sales values are non-negative (min = 0, as expected)
- No obvious data type mismatches

**⚠️ Areas to Verify:**
1. **Date Continuity**: Are there gaps in the time series (missing days)?
   - Need to check if all stores have records for all days
   - Gaps could indicate store closures or data collection failures

2. **Store-Family Completeness**: Do all 54 stores carry all 33 families?
   - Likely not (e.g., small stores may not stock AUTOMOTIVE)
   - Need to document which store-family combinations are valid

3. **Outliers in Sales**: Maximum value of $124,717 is 348x the mean
   - Is this a data entry error (extra zeros)?
   - Or legitimate (e.g., GROCERY I in Store #44 on a major holiday sale)?
   - **Action**: Investigate top 0.1% of sales records for plausibility

4. **Promotion Logic**: `onpromotion` = 741 seems extreme
   - Can 741 items truly be on promotion in one store-family-day?
   - May indicate data quality issue or bulk promotion events
   - **Action**: Cross-check with promotion calendar if available

### Potential Data Issues

**1. Early 2013 Data Reliability**
- January 1, 2013 anomaly suggests data collection may have been unstable during system launch
- **Recommendation**: Exclude first 2 weeks of 2013 from training if patterns seem anomalous

**2. Zero Inflation**
- 31.3% zero-sales rate is high but not unrealistic for sparse panel data
- **Risk**: If zeros are actually missing data (system didn't record transactions), forecasts will underestimate demand
- **Validation Needed**: Compare zero-rates by family—expect high zeros for BOOKS/AUTOMOTIVE, low zeros for BEVERAGES/GROCERY I

**3. Data Type Correction Needed**
- `date` column loaded as `object` (string) instead of `datetime64`
- **Action**: Convert to datetime in preprocessing pipeline to enable time-based operations

---

## Integration & Next Steps

### Integration with Other Datasets

This training dataset is part of a larger ecosystem. Based on the project structure, the following integrations are critical:

**1. Holidays & Events Dataset** (`holidays_events.csv`)
- **Purpose**: Explain sales anomalies like the Jan 1, 2013 drop
- **Integration**: Merge on `date` to create holiday flags (binary: is_holiday, or categorical: holiday_type)
- **Impact**: Expected to improve forecast accuracy by 10-20% during holiday periods

**2. Store Metadata** (if available)
- **Expected Fields**: store_type, city, state, cluster, floor_area
- **Integration**: Merge on `store_nbr`
- **Use Case**: Explain why stores #44, #45, #47 are top performers (larger stores? better locations?)

**3. Product Metadata** (if available)
- **Expected Fields**: family descriptions, perishability, margin profiles
- **Integration**: Merge on `family`
- **Use Case**: Differentiate forecasting strategies (perishable goods need tighter inventory control)

**4. Oil Prices / Economic Indicators** (if available)
- **Relevance**: Ecuador's economy is oil-dependent; oil prices may correlate with consumer spending
- **Integration**: Merge on `date`
- **Use Case**: Add macroeconomic features to capture broader demand shifts

### Recommended Next Steps

**Immediate Actions (This Week):**

1. **Date Continuity Check**
   ```python
   # Verify no missing dates
   date_range = pd.date_range(start='2013-01-01', end=df_train['date'].max(), freq='D')
   missing_dates = set(date_range) - set(df_train['date'].unique())
   ```

2. **Store-Family Completeness Matrix**
   ```python
   # Identify which store-family combinations exist
   completeness = df_train.groupby(['store_nbr', 'family']).size().unstack(fill_value=0)
   # Expect some zeros (not all stores carry all families)
   ```

3. **Outlier Investigation**
   ```python
   # Flag extreme values for manual review
   outliers = df_train[df_train['sales'] > df_train['sales'].quantile(0.999)]
   # Verify these are legitimate sales, not data errors
   ```

4. **Zero Sales Deep Dive**
   ```python
   # Analyze zero-rate by family and store
   zero_rate = df_train.groupby('family')['sales'].apply(lambda x: (x == 0).mean())
   # Expect AUTOMOTIVE/BOOKS > 50%, BEVERAGES/GROCERY I < 10%
   ```

5. **Merge with Holidays Dataset**
   ```python
   # Join with holidays_events.csv to flag special days
   df_train = df_train.merge(holidays, on='date', how='left')
   # Create binary feature: is_holiday
   ```

**Short-Term Analysis (Next 2 Weeks):**

6. **Seasonal Decomposition**
   - Decompose daily sales into trend, seasonal, and residual components
   - Identify weekly patterns (weekends vs. weekdays)
   - Detect annual seasonality (Christmas, back-to-school, etc.)

7. **Promotion Impact Analysis**
   - Compare sales on promoted vs. non-promoted days (by family)
   - Calculate promotion lift: `(sales_promoted - sales_baseline) / sales_baseline`
   - Identify which families are most promotion-sensitive

8. **Store Clustering**
   - Use k-means or hierarchical clustering to group stores by sales patterns
   - Features: total sales, sales volatility, zero-rate, promotion intensity
   - Output: Store typology (e.g., "high-volume-urban," "low-volume-rural")

9. **Correlation Analysis**
   - Examine correlation between `onpromotion` and `sales` (expect positive but not 1:1)
   - Check for multicollinearity between stores (some may cannibalize each other's sales)

**Medium-Term Modeling Prep (Next Month):**

10. **Feature Engineering**
    - Lag features: sales_7d_ago, sales_14d_ago, sales_365d_ago
    - Rolling statistics: sales_7d_avg, sales_7d_std
    - Calendar features: day_of_week, day_of_month, month, quarter, is_weekend, is_month_end
    - Event flags: is_payday (15th, 30th), is_holiday, is_earthquake (Ecuador 2016)

11. **Train/Validation/Test Split**
    - **Train**: 2013-01-01 to 2016-06-30 (3.5 years)
    - **Validation**: 2016-07-01 to 2016-12-31 (6 months)
    - **Test**: 2017-01-01 onwards
    - Use time-based split (no random shuffling—this is time series!)

12. **Baseline Model**
    - Start with simple heuristic: "Sales tomorrow = Sales same day last week"
    - Calculate RMSE, MAE, MAPE as baseline to beat
    - Expected baseline MAPE: 40-60% (typical for retail)

13. **Model Selection**
    - For aggregate sales (store-level or chain-wide): ARIMA, Prophet, LSTM
    - For store-family-day forecasts: LightGBM, XGBoost, CatBoost (handle sparse data well)
    - For probabilistic forecasts: Quantile Regression, DeepAR

---

## Conclusion

This dataset provides a solid foundation for retail sales forecasting, with excellent completeness (zero missing values) and sufficient historical depth (4.6 years). The key challenges are:

1. **High sparsity** (31% zeros) requiring careful model selection
2. **Extreme skewness** (mean >> median) necessitating log-transformation or count models
3. **Holiday sensitivity** demanding external calendar integration
4. **Concentration risk** where top 10 stores and top 3 families dominate—errors here have outsized business impact

The next critical step is integrating the holidays/events dataset to control for anomalies like the January 1, 2013 sales collapse. From there, focus on feature engineering (lags, rolling stats, calendar effects) and establishing a baseline model to benchmark against.

**Success Metrics**:
- Target MAPE: <30% for top 10 stores, <40% overall
- Reduce stockouts: Predict zero-sales events with 80%+ precision
- Promotion ROI: Quantify incremental sales per promotional dollar spent

This analysis positions the team to move confidently into modeling with a clear understanding of data strengths, limitations, and business context.
