# Oil Price Dataset Exploration Report
**Retail Store Sales Time Series Analysis**
*Generated: 2026-01-02*

---

## Executive Summary

This report analyzes 1,218 daily crude oil price records (WTI) spanning 4.6 years, serving as a critical macroeconomic indicator for retail forecasting. Three key insights emerged:

1. **High volatility with regime shifts**: Oil prices ranged from $26.19 to $110.62 per barrel (323% swing), with mean at $67.71 but median at $53.19—indicating a right-skewed distribution driven by 2013-2014 high-price periods before the 2015-2016 oil crash.

2. **Minimal missing data, structural gaps**: Only 43 missing values (3.5%), occurring on weekends and market holidays when oil trading ceases. Forward-fill imputation maintains time-series continuity without introducing bias.

3. **Ecuador-specific relevance amplified**: As an oil-exporting economy, Ecuador's retail sector is hypersensitive to oil price fluctuations—impacting transportation costs, consumer purchasing power, and government spending on subsidies. The 2015-2016 crash (prices dropping 76% from peak) likely triggered structural changes in consumer behavior.

---

## Dataset Overview

### What This Dataset Contains
The oil dataset provides daily West Texas Intermediate (WTI) crude oil prices, serving as an **exogenous macroeconomic feature** to explain retail sales trends beyond store-level factors.

**Core Specifications:**
- **Rows**: 1,218 daily records
- **Columns**: 2 features (date, dcoilwtico)
- **Time Span**: January 1, 2013 to August 31, 2017 (4.6 years)
- **Granularity**: Daily prices (calendar days, not just trading days)
- **Memory Footprint**: ~19 KB (negligible)

### Business Context
Ecuador's economy is heavily oil-dependent (petroleum exports represent ~40% of export earnings). Oil price fluctuations directly impact:
- **Government revenue** → affects public sector wages and subsidies
- **Inflation rates** → influences consumer purchasing power
- **Transportation costs** → impacts retail logistics and product pricing
- **Currency stability** → Ecuador uses USD but economic confidence correlates with oil

For retail forecasting, oil prices act as a **leading indicator** that captures macroeconomic shocks not visible in store-level data.

---

## Data Structure & Characteristics

### Column Specifications

| Column | Type | Description | Value Range |
|--------|------|-------------|-------------|
| `date` | object (datetime) | Calendar date | 2013-01-01 to 2017-08-31 |
| `dcoilwtico` | float64 | Daily crude oil price (USD/barrel) | $26.19 - $110.62 |

**Critical Notes**:
- **Global indicator**: Single price applies to all stores/products on a given day
- **Daily frequency**: Includes weekends/holidays (when markets are closed, prices are missing)
- **WTI benchmark**: West Texas Intermediate, the US crude oil pricing standard

---

## Key Findings & Patterns

### 1. Oil Price Distribution & Volatility

**Statistical Profile:**
- **Mean Price**: $67.71 per barrel
- **Median Price**: $53.19 per barrel
- **Standard Deviation**: $25.63 (38% of mean—extremely high volatility)
- **Range**: $26.19 to $110.62 (323% difference between min and max)

**What This Means:**

The 21% gap between mean and median reveals **right skew**—a few high-price periods (2013-2014) inflate the average. The distribution shows:
- Long tail of low prices during 2015-2016 oil crash
- Concentration around $45-$55 range in recovery period (2016-2017)
- No prices follow normal distribution—expect structural breaks in time series

**Modeling Implications:**
1. Do not assume oil prices are stationary—use differencing or log-transformation
2. Consider regime-switching models to capture distinct high/low price eras
3. Lagged effects likely (e.g., oil price shock today impacts sales 7-30 days later)

### 2. Missing Value Pattern: Weekends & Holidays

**Scale of the Issue:**
- **Missing Values**: 43 records (3.5% of dataset)
- **Cause**: Oil futures markets close on weekends and US federal holidays

**Handling Strategy:**
- **Forward fill (ffill)**: Carry last known price forward (assumes prices persist until market reopens)
- **Backward fill (bfill)**: For any leading NaNs (e.g., if dataset starts on weekend)

**Why This Works:**
- Oil prices exhibit **momentum**—Monday's opening price typically close to Friday's close
- Alternative (interpolation) would artificially smooth volatility
- Dropping rows would misalign dates with sales data

**After Imputation**: Zero missing values remain.

### 3. Long-Term Trend: The 2015-2016 Oil Crash

**Observed Regime Shifts:**

| Period | Price Range | Economic Context |
|--------|-------------|------------------|
| 2013-2014 | $90-$110/barrel | Pre-crash boom (OPEC production high, demand strong) |
| 2015-2016 | $26-$50/barrel | **Crash period** (oversupply, weak global demand) |
| 2017 | $45-$55/barrel | Partial recovery (OPEC production cuts) |

**Business Implications for Ecuador**:

During the **2015-2016 crash** (prices dropped 76% from $110 to $26):
- **Government budget crisis**: Ecuador lost billions in oil export revenue
- **Austerity measures**: Public spending cuts reduced disposable income
- **Currency pressure**: Despite using USD, economic confidence plummeted
- **Retail impact**: Consumers delayed big-ticket purchases, shifted to value brands

**Why This Matters for Forecasting**:
- Sales models trained on 2013-2014 data will fail in 2015-2016 without oil price feature
- Promotions may have been less effective during crash (consumers prioritized essentials)
- Store-level differences may widen (urban vs. rural, luxury vs. discount)

---

## Data Quality Assessment

### Completeness: Excellent ✅

**Missing Values Analysis:**
```
Column          Missing Values    Percentage
date            0                 0.0%
dcoilwtico      43                3.5%
```

**Assessment**: Only 43 missing values, all structurally explained (non-trading days). After imputation, dataset is 100% complete.

### Consistency: High ✅

**✅ Strengths:**
- Date format consistent (YYYY-MM-DD)
- No negative prices (min = $26.19, realistic)
- No extreme outliers (max = $110.62 is historically plausible for WTI)
- No duplicate dates

**⚠️ Areas to Verify:**
1. **Date alignment with train.csv**: Verify oil dataset covers all sales dates
2. **Currency**: Assume USD (WTI standard), but confirm if local currency conversions exist
3. **Lag effects**: Test 1-day, 7-day, 30-day lags to find optimal correlation with sales

---

## Business Implications

### 1. Oil Price as Sales Driver

**Expected Correlations**:
- **Negative correlation** (lower oil → higher sales): Transportation costs decrease → retailers lower prices → demand increases
- **Positive correlation** (higher oil → higher sales): In oil-exporting Ecuador, high oil prices → government revenue up → public sector wages rise → consumer spending increases

**Which effect dominates?** Needs empirical testing, but for Ecuador, the **positive correlation** likely stronger (oil revenue > cost savings).

### 2. Category-Specific Impacts

**Expected Sensitivity by Product Family**:
- **High sensitivity**: AUTOMOTIVE (fuel-related), discretionary goods (ELECTRONICS, HOME APPLIANCES)
- **Low sensitivity**: GROCERY I, BEVERAGES (daily necessities, inelastic demand)

**Testing Strategy**: Segment sales by family and measure correlation with oil prices.

### 3. Promotional ROI During Oil Shocks

**Hypothesis**: Promotions may be less effective during oil crashes (consumers tighten budgets regardless of discounts).

**Test**: Compare promotion lift (sales increase per promotional item) in high-oil vs. low-oil periods.

---

## Integration & Next Steps

### Integration with Other Datasets

**Join Strategy**:
```python
# Merge oil price into train data
df_train = df_train.merge(df_oil, on='date', how='left')
```

**Expected Result**: Every sales record gets same oil price for that date (broadcast join).

### Recommended Feature Engineering

**1. Lag Features** (capture delayed effects):
```python
df_oil['oil_lag_7'] = df_oil['dcoilwtico'].shift(7)    # 1-week lag
df_oil['oil_lag_30'] = df_oil['dcoilwtico'].shift(30)  # 1-month lag
```

**2. Rolling Averages** (smooth volatility):
```python
df_oil['oil_ma_7'] = df_oil['dcoilwtico'].rolling(7).mean()
df_oil['oil_ma_30'] = df_oil['dcoilwtico'].rolling(30).mean()
```

**3. Price Change Indicators** (capture shocks):
```python
df_oil['oil_pct_change'] = df_oil['dcoilwtico'].pct_change()
df_oil['oil_volatility'] = df_oil['dcoilwtico'].rolling(30).std()
```

**4. Regime Flags** (binary indicators):
```python
df_oil['is_oil_crash'] = (df_oil['dcoilwtico'] < 40).astype(int)  # 2015-2016
df_oil['is_oil_boom'] = (df_oil['dcoilwtico'] > 90).astype(int)   # 2013-2014
```

### Next Steps for Validation

**Immediate Actions**:

1. **Correlation Analysis**:
   ```python
   # Aggregate sales by date, merge with oil, calculate correlation
   daily_sales = df_train.groupby('date')['sales'].sum()
   corr_df = daily_sales.to_frame().merge(df_oil, on='date')
   correlation = corr_df[['sales', 'dcoilwtico']].corr()
   ```

2. **Visual Inspection**:
   - Plot oil prices over time (identify regime shifts)
   - Overlay total daily sales on same chart (check for visual correlation)

3. **Lag Optimization**:
   - Test correlations at lags of 0, 7, 14, 30, 60 days
   - Find optimal lag where correlation is strongest

4. **Model Testing**:
   - Train baseline model without oil price → get RMSE
   - Train model with oil price (and lags) → measure RMSE improvement
   - Expected lift: 5-15% reduction in RMSE if oil is relevant

---

## Conclusion

The oil price dataset is a **high-quality, business-critical exogenous variable** for Ecuador retail forecasting. With only 3.5% missing data (easily imputed) and 4.6 years of coverage, it provides:

1. **Macroeconomic context** missing from store-level data
2. **Structural break detection** (2015-2016 crash)
3. **Leading indicator potential** via lag features

**Key Risks**:
- Overfitting to oil price if regime shifts are rare (only one major crash in dataset)
- Lag effects may vary by product family (need separate models)
- Oil price alone cannot explain store-level heterogeneity (combine with store metadata)

**Success Metrics**:
- Target: Improve baseline RMSE by 10%+ when oil features included
- Explain sales variance during 2015-2016 crash period
- Identify which product families are most oil-sensitive

This dataset should be **immediately integrated** into all time-series models—its business relevance and data quality justify treating it as a core feature, not optional.
