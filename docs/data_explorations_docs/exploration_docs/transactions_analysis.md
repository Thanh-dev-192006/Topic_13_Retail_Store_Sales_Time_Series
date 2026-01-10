# Transaction Count Dataset Exploration Report
**Retail Store Sales Time Series Analysis**
*Generated: 2026-01-02*

---

## Executive Summary

This report analyzes 83,488 daily transaction count records across 54 stores, serving as a **foot traffic indicator** for retail forecasting. Four critical insights emerged:

1. **Significant data sparsity reflects store operations**: 8.4% of expected store-day records are missing from raw data (7,664 out of 91,152 expected records). However, this is **not random**—missing data concentrates in newly opened stores (store 52 missing 93% of timeline) and national holidays (Christmas Day consistently absent). This is a **data quality strength**, not a flaw, as it accurately reflects business reality.

2. **Weekend traffic surge drives 26% uplift**: Saturdays average 1,953 transactions per store vs. Thursdays at 1,550 (+26%)—a strong weekly seasonality pattern. This foot traffic boost likely amplifies sales across all product families, making day-of-week a critical feature for forecasting.

3. **Extreme heterogeneity across stores**: Transaction volumes vary 6.8× between busiest (store 44: 4,337/day) and quietest (store 26: 635/day) locations. This suggests store-level fixed effects or embeddings are essential—one-size-fits-all models will underperform.

4. **Christmas Eve spike reveals promotional opportunity**: December 24, 2015 recorded 171,169 total transactions (2× daily average)—the highest single-day traffic in dataset. This pre-holiday surge indicates customers stockpiling, creating a critical window for promotional effectiveness testing.

---

## Dataset Overview

### What This Dataset Contains
The transactions dataset provides daily **transaction counts** at each store, serving as a **store activity proxy** to supplement sales forecasting. Unlike sales data (which varies by product family), transaction counts measure overall foot traffic—capturing how busy a store is regardless of what customers buy.

**Core Specifications:**
- **Rows**: 83,488 store-day records (raw data)
- **Columns**: 3 features (date, store_nbr, transactions)
- **Time Span**: January 1, 2013 to August 15, 2017 (1,688 days)
- **Granularity**: Store-day level (no product family breakdown)
- **Expected Full Panel**: 91,152 records (54 stores × 1,688 days)
- **Missing**: 7,664 records (8.4% sparsity)

### Business Context
Transaction counts differ from sales revenue in important ways:
- **Transaction count** = number of checkout events (baskets)
- **Sales revenue** = dollar value of those baskets

This distinction matters because:
- **High transactions, low sales** → Customers buying cheap/essential items (value shoppers)
- **Low transactions, high sales** → Customers buying expensive/bulk items (premium/wholesale shoppers)

For forecasting, transactions provide a **store-level traffic indicator** that broadcasts to all product families—useful for separating "store was busy" from "this specific product family had high demand."

---

## Data Structure & Characteristics

### Column Specifications

| Column | Type | Description | Value Range |
|--------|------|-------------|-------------|
| `date` | object (datetime) | Calendar date | 2013-01-01 to 2017-08-15 |
| `store_nbr` | int64 | Store identifier | 1 - 54 |
| `transactions` | int64 | Number of checkout transactions that day | 0 - 8,359 |

**Critical Notes**:
- **Primary key**: (date, store_nbr) composite—no duplicates found
- **Store-level aggregation**: No product family dimension (broadcasts when joined to train.csv)
- **Count data**: Transactions are discrete, non-negative integers

### Panel Data Structure

**Expected vs. Actual Coverage**:
```
Expected: 54 stores × 1,688 days = 91,152 store-days
Actual:   83,488 store-days
Missing:  7,664 store-days (8.4% sparsity)
```

**Why This Matters**:
- Time series models require complete panels to compute lags/rolling features
- **Solution applied**: Create full panel grid and impute missing records with `transactions = 0`, flagged via `is_imputed = 1`

---

## Key Findings & Patterns

### 1. Store Heterogeneity: 6.8× Volume Variance

**Transaction Volume by Store (Top 5 vs. Bottom 5)**:

| Rank | Store # | Avg Transactions/Day | Traffic Tier |
|------|---------|----------------------|--------------|
| 1 | 44 | 4,337 | Flagship (ultra-high traffic) |
| 2 | 45 | 3,891 | Flagship |
| 3 | 47 | 3,542 | High-traffic urban |
| 4 | 3 | 3,201 | High-traffic urban |
| 5 | 49 | 2,847 | Urban core |
| ... | ... | ... | ... |
| 50 | 33 | 721 | Low-traffic rural/suburban |
| 51 | 20 | 698 | Low-traffic |
| 52 | 52 | 683 | Newly opened (limited data) |
| 53 | 43 | 651 | Low-traffic |
| 54 | 26 | 635 | Minimal traffic |

**Critical Finding**: Store 44 averages **6.8× more transactions** than store 26—indicating massive heterogeneity in store size, location, or customer base.

**Business Implications**:

1. **Modeling Strategy**: One global model will struggle—consider:
   - Store-specific models or embeddings
   - Hierarchical models with store-level random effects
   - Stratified training (high-traffic vs. low-traffic stores)

2. **Operational Insights**:
   - High-traffic stores (44, 45, 47) likely need:
     - More checkout lanes (to handle 4,000+ daily transactions)
     - Deeper inventory (risk of stockouts higher)
     - More staff (customer service load)
   - Low-traffic stores (<700/day) may be:
     - Rural/convenience formats (different customer behavior)
     - Newly opened (still ramping up)
     - Underperforming (potential closure candidates)

3. **Promotion Effectiveness**: Testing promotions in store 44 vs. store 26 may yield vastly different ROI—stratify experiments by traffic tier.

### 2. Weekly Seasonality: Weekend Traffic Surge

**Average Transactions per Store-Day by Day of Week**:

| Day | Avg Transactions | % vs. Baseline (Thursday) |
|-----|------------------|---------------------------|
| Saturday | 1,953 | +26.0% |
| Sunday | 1,847 | +19.2% |
| Friday | 1,612 | +4.0% |
| Monday | 1,583 | +2.1% |
| Tuesday | 1,551 | +0.1% |
| Thursday | 1,550 | 0.0% (baseline) |
| Wednesday | 1,541 | -0.6% |

**Key Observation**: **Saturday is 26% busier than Thursday**—a strong, consistent weekly pattern.

**Why This Matters for Forecasting**:

1. **Feature Engineering**: Add day-of-week features (one-hot encoding or cyclic encoding with sine/cosine).

2. **Weekend Effect on Sales**: Weekend traffic surge likely boosts sales across **all product families** (not just specific categories), so:
   - Don't attribute weekend sales lift solely to product-specific demand
   - Separate "traffic-driven sales" from "product-driven sales" by including transaction counts as covariate

3. **Staffing & Inventory**: Retailers already know weekends are busy, but this quantifies it—Saturday needs **26% more capacity** than midweek.

### 3. Holiday Traffic Spikes: Christmas Eve Dominance

**Top 10 Highest Traffic Days (Total Transactions Across All Stores)**:

| Date | Total Transactions | Multiple of Avg Daily |
|------|-------------------|----------------------|
| 2015-12-24 | 171,169 | 2.03× |
| 2014-12-24 | 166,542 | 1.98× |
| 2013-12-23 | 162,891 | 1.94× |
| 2016-12-24 | 161,237 | 1.92× |
| 2014-12-23 | 158,492 | 1.88× |

**Average Daily Total**: ~84,114 transactions (across all 54 stores)

**Critical Finding**: **December 23-24 consistently dominates** traffic—reaching **2× normal levels**. This is pre-Christmas stockpiling behavior.

**Business Implications**:

1. **Promotional Strategy**: Christmas Eve traffic spike suggests:
   - High customer urgency (last-minute shopping)
   - Willingness to buy in bulk (stocking up for holiday)
   - **Opportunity**: Test premium pricing vs. deep discounts—customers may be less price-sensitive when urgency is high

2. **Inventory Risk**: If 2× normal traffic but inventory not doubled, risk of catastrophic stockouts (losing sales at peak demand).

3. **Forecasting**: Models without holiday features will **severely underpredict** December 23-24. Must integrate `holidays_events.csv` to flag pre-holiday days.

### 4. Missing Data as Business Signal: Store Openings & Closures

**Stores with Highest Missing Data Rates**:

| Store # | Missing Days | % of Timeline | Interpretation |
|---------|--------------|---------------|----------------|
| 52 | 1,570 | 93% | Opened April 20, 2017 (only 118 days active) |
| 22 | 1,017 | 60% | Opened late or frequent closures |
| 42 | 968 | 57% | Late opening or data collection gap |
| 21 | 940 | 56% | Late opening |
| 29 | 814 | 48% | Partial timeline coverage |

**Dates With Zero Records Across All Stores (Store Closures)**:
- **December 25** (2013, 2014, 2015, 2016) — Christmas Day
- **January 1, 2016** — New Year's Day
- **January 3, 2016** — Post-holiday closure

**What This Means**:

1. **Not random missingness**: Missing data is **structurally informative**:
   - New stores (like 52) physically didn't exist for 93% of timeline
   - National holidays → all stores closed → legitimately 0 transactions

2. **Imputation Strategy**: Fill missing with `transactions = 0` is **correct**, but add `is_imputed` flag:
   - `is_imputed = 1` → Store wasn't open or data not collected
   - `is_imputed = 0` → Store was open and recorded 0-N transactions

3. **Modeling Implication**: For stores like 52, early timeline has **no signal** (store didn't exist). Consider:
   - Masking pre-opening periods in training
   - Or using `is_imputed` as feature to let model learn "this store was closed"

---

## Data Quality Assessment

### Completeness: Good (after imputation) ✅

**Raw Data Missing Values**:
```
Column          Missing Values    Percentage
date            0                 0.0%
store_nbr       0                 0.0%
transactions    0                 0.0%
```

**Assessment**: Zero missing in raw records. However, **full panel has 8.4% sparsity** (expected 91,152 records, got 83,488).

**Solution Applied**:
1. Generate full panel grid: All 54 stores × All 1,688 days
2. Left join raw data
3. Impute missing `transactions = 0` with `is_imputed = 1` flag

**After Imputation**: 91,152 complete records (100% coverage).

### Consistency: Excellent ✅

**✅ Strengths:**
- **No duplicates**: (date, store_nbr) pairs are unique
- **No negative values**: `transactions` range is 0 - 8,359 (all valid)
- **No outliers**: Max of 8,359 is plausible for busy stores (matches store 44's high-traffic profile)
- **Date continuity**: After imputation, every date from 2013-01-01 to 2017-08-15 is covered

**⚠️ Areas to Verify:**
1. **Store 52 ramp-up**: Newly opened store may show unusual growth trajectory—verify sales patterns align with transaction growth
2. **Zero transactions on open days**: Some records show 0 transactions when store was supposedly open—could be:
   - Data collection failure
   - Actual closure (e.g., emergency, renovation)
   - Or genuinely no customers that day (unlikely but possible)

---

## Business Implications

### 1. Transaction Count as Traffic Proxy

**Key Use Case**: Decompose sales into components:
```
Sales = Traffic × Conversion Rate × Basket Size
```

Where:
- **Traffic** = transaction count (this dataset)
- **Conversion Rate** = % of store visitors who buy
- **Basket Size** = average sales per transaction

**Modeling Application**:
- Include `transactions` as covariate in sales forecasting models
- If sales spike but transactions don't → customers buying more per visit (basket size up)
- If transactions spike but sales don't → customers buying cheaper items (basket size down)

This decomposition helps diagnose **why** sales change (traffic vs. behavior shift).

### 2. Store Clustering by Traffic Patterns

**Hypothesis**: Stores with similar transaction patterns likely share:
- Customer demographics
- Geographic characteristics (urban vs. rural)
- Store format (supermarket vs. convenience)

**Clustering Strategy**:
1. Extract features per store:
   - Mean transactions/day
   - Weekend uplift %
   - Holiday spike intensity
   - Coefficient of variation (volatility)
2. Run k-means or hierarchical clustering
3. Result: Store typology (e.g., "high-traffic urban," "low-traffic rural," "seasonal tourist")

**Business Value**: Tailor strategies by cluster (e.g., urban stores need different promotions than rural).

### 3. Promotion Effectiveness Testing

**Experiment Design**:
- **Control group**: Stores with typical traffic (no promotion)
- **Treatment group**: Stores with promotion
- **Metric**: Compare **sales per transaction** (basket size) between groups

**Why this works**: If promotion increases sales but **not** transactions, it means:
- Same customers came (traffic unchanged)
- But they bought more (basket size up)
- → Promotion successfully upsold existing traffic

If promotion increases **both** sales and transactions, it means:
- More customers came (traffic up)
- → Promotion successfully attracted new visitors

### 4. Staffing & Capacity Planning

**Actionable Insight**:
- **Saturday needs 26% more cashiers** than Thursday (to handle 1,953 vs. 1,550 transactions)
- **Christmas Eve needs 100% more capacity** (2× normal traffic)
- Low-traffic stores (<700/day) may be over-staffed if using same ratios as high-traffic stores

**ROI**: Right-sizing staffing reduces labor costs while maintaining service quality.

---

## Integration & Next Steps

### Integration with Other Datasets

**Join Strategy**:
```python
# Merge transactions into sales data (many-to-one: many families per store-day)
df_train = df_train.merge(df_transactions[['date', 'store_nbr', 'transactions', 'is_imputed']],
                          on=['date', 'store_nbr'],
                          how='left')
```

**Expected Result**: Each store-family-day record in train.csv inherits same `transactions` count (broadcast).

**Validation Checks**:
1. **Date range alignment**: Verify transactions.csv covers full train.csv date range
2. **Store coverage**: All 54 stores in train.csv should have matching transaction data
3. **Imputation flag**: Check if high `is_imputed` rates correlate with low sales (confirming store closures)

### Recommended Feature Engineering

**1. Lag Features** (capture momentum):
```python
# Per-store lags
df_transactions['trans_lag_1'] = df_transactions.groupby('store_nbr')['transactions'].shift(1)
df_transactions['trans_lag_7'] = df_transactions.groupby('store_nbr')['transactions'].shift(7)
df_transactions['trans_lag_14'] = df_transactions.groupby('store_nbr')['transactions'].shift(14)
```

**2. Rolling Statistics** (smooth noise):
```python
# 7-day rolling mean per store
df_transactions['trans_roll_7'] = (
    df_transactions.groupby('store_nbr')['transactions']
    .rolling(7, min_periods=1).mean()
    .reset_index(level=0, drop=True)
)
```

**3. Weekend/Holiday Interactions**:
```python
# Flag weekend
df_transactions['is_weekend'] = df_transactions['date'].dt.dayofweek.isin([5, 6]).astype(int)

# Interaction: weekend × store type (after merging stores.csv)
df_merged['weekend_effect'] = df_merged['is_weekend'] * (df_merged['type'] == 'A').astype(int)
```

**4. Normalized Traffic** (account for store heterogeneity):
```python
# Z-score per store (standardize to mean=0, std=1)
store_stats = df_transactions.groupby('store_nbr')['transactions'].agg(['mean', 'std'])
df_transactions = df_transactions.merge(store_stats, on='store_nbr', suffixes=('', '_store'))
df_transactions['trans_zscore'] = (df_transactions['transactions'] - df_transactions['mean']) / df_transactions['std']
```

### Next Steps for Validation

**Immediate Actions**:

1. **Correlation Analysis**:
   ```python
   # Merge transactions with sales, calculate correlation
   df_merged = df_train.merge(df_transactions, on=['date', 'store_nbr'])
   correlation = df_merged[['sales', 'transactions']].corr()
   # Expected: positive correlation (more traffic → more sales)
   ```

2. **Sales per Transaction Analysis**:
   ```python
   # Calculate basket size
   df_merged['basket_size'] = df_merged['sales'] / df_merged['transactions'].replace(0, np.nan)
   # Analyze: Does basket size vary by store type? By day of week?
   ```

3. **Imputation Flag Validation**:
   ```python
   # Compare sales on imputed vs. non-imputed days
   df_merged.groupby('is_imputed')['sales'].agg(['mean', 'median', 'sum'])
   # Expect: imputed days (store closed) have ~0 sales
   ```

4. **Store Opening Timeline**:
   ```python
   # Identify first active date per store
   store_openings = df_transactions[df_transactions['is_imputed'] == 0].groupby('store_nbr')['date'].min()
   # Use to mask pre-opening periods in training data
   ```

---

## Conclusion

The transactions dataset is a **high-quality, business-critical traffic indicator** with excellent consistency and strategic value for retail forecasting. With only 8.4% sparsity (structurally explained by store openings/holidays), it provides:

1. **Store activity proxy** to separate foot traffic effects from product-specific demand
2. **Strong weekly seasonality** (26% weekend uplift) for time-series modeling
3. **Holiday surge detection** (2× normal traffic on Christmas Eve)
4. **Store heterogeneity insights** (6.8× variance between busiest/quietest stores)

**Key Strengths**:
- Zero missing in raw data (100% complete records)
- No duplicates (clean primary key)
- Structurally informative missingness (not data quality issue)
- Wide dynamic range (0-8,359) captures real variance

**Key Risks**:
- Imputation needed for 8.4% of full panel (mitigated by `is_imputed` flag)
- Newly opened stores (e.g., store 52) have sparse history—may need separate models
- Weekend/holiday effects require explicit features (models won't auto-detect without encoding)

**Success Metrics**:
- After joining with sales: Confirm positive correlation between transactions and sales
- Feature importance: Validate transaction-based features rank in top 10 predictors
- Basket size analysis: Identify stores/days with abnormal sales-per-transaction ratios

This dataset should be **immediately integrated** into forecasting pipelines—its store-level granularity and temporal patterns make it essential for capturing traffic-driven sales dynamics.
