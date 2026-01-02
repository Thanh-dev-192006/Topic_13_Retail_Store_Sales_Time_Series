# Oil Dataset Analysis (oil.csv)

## 1. Dataset Overview

**Dataset name:** `oil.csv`
**Source:** Kaggle – Retail Store Sales Time Series (Ecuador)
**Business meaning:** Daily crude oil price (WTI) used as an external economic indicator influencing retail sales costs, pricing, and demand.

### Size & Coverage

* **Number of rows:** 1,218 records
* **Number of columns:** 2
* **Time coverage:** From **2013-01-01** to **2017-08-31**
* **Frequency:** Daily (calendar days)

This dataset provides a continuous timeline of oil prices across more than **4.5 years**, which aligns well with the coverage of the main `train.csv` sales dataset.

---

## 2. Data Structure & Granularity

### Columns

| Column name  | Data type | Description                            |
| ------------ | --------- | -------------------------------------- |
| `date`       | datetime  | Calendar date (daily granularity)      |
| `dcoilwtico` | float     | Daily WTI crude oil price (USD/barrel) |

### Granularity

* **Temporal granularity:** 1 row = 1 day
* **Entity granularity:** Global oil price (no store or product-level breakdown)

This dataset is **exogenous** (external variable) and must be joined to sales data purely by **date**.

---

## 3. Data Quality Assessment

### Missing Values

Initial missing value analysis shows:

* **`date`:** 0 missing values (0%)
* **`dcoilwtico`:** 43 missing values (~3.5%)

#### Interpretation

* Missing oil prices occur mainly on **weekends and market holidays** when oil trading does not take place.
* These are **structural missing values**, not data errors.

### Decision & Handling

* **Action taken:** Forward fill (`ffill`) followed by backward fill (`bfill`).
* **Reasoning:**

  * Oil prices typically change gradually.
  * Forward fill preserves time-series continuity.
  * Dropping rows would break alignment with sales dates.

After handling:

* **Missing values remaining:** 0

This decision ensures the dataset remains suitable for time-series modeling and feature engineering.

---

## 4. Statistical Characteristics & Patterns

### Descriptive Statistics (after cleaning)

Key statistics for `dcoilwtico`:

* **Mean oil price:** ~52 USD/barrel
* **Minimum:** ~26 USD/barrel
* **Maximum:** ~106 USD/barrel
* **Standard deviation:** High volatility, reflecting real-world oil market fluctuations

### Temporal Patterns

#### Long-term Trend

* **2013–2014:** High oil prices (above 90 USD/barrel)
* **2015–2016:** Sharp decline, reaching lows around 26–30 USD/barrel
* **2017:** Partial recovery and stabilization around 45–55 USD/barrel

This large structural shift represents a **macro-economic shock** that likely affects:

* Transportation costs
* Product pricing strategies
* Consumer purchasing behavior

#### Volatility

* Significant price volatility is observed year-over-year.
* No clear weekly seasonality, but strong **regime changes** across years.

---

## 5. Business Implications

Oil price is a **leading economic indicator** in retail:

* Lower oil prices → lower transportation & logistics costs
* Potentially lower consumer prices
* Increased disposable income → higher demand

The dramatic oil price drop in 2015–2016 may explain:

* Changes in sales trends not attributable to promotions or holidays
* Structural breaks in time-series sales models

Therefore, oil price should be treated as:

* A **continuous numerical feature**
* Possibly with **lagged effects** (e.g., 7-day, 14-day lags)

---

## 6. Integration Notes

### Join Keys

* **Primary key:** `date`

### Relationship to Other Datasets

| Dataset               | Relationship                                    |
| --------------------- | ----------------------------------------------- |
| `train.csv`           | Many-to-one join on `date`                      |
| `holidays_events.csv` | Same date index, complementary exogenous signal |
| `stores.csv`          | No direct relationship                          |

### Integration Considerations

* Oil price applies globally → same value shared across all stores and products per day.
* After cleaning, no missing dates → safe for left join with `train.csv`.

---

## 7. Modeling Considerations ("So What?")

Why this dataset matters for modeling:

* Helps explain **macro-level trends** beyond store-level factors
* Can reduce unexplained variance in sales forecasting models
* Especially useful for:

  * ARIMAX / SARIMAX
  * Gradient Boosting (XGBoost, LightGBM)
  * LSTM with exogenous variables

Without oil price, models may incorrectly attribute economic effects to promotions or seasonality.

---

## 8. Recommended Next Steps

1. **Feature Engineering**

   * Create lag features: oil_price_lag_7, lag_14, lag_30
   * Rolling statistics: 7-day & 30-day moving averages

2. **Correlation Analysis**

   * Measure correlation between oil price and total sales
   * Segment by product family (e.g., perishable vs non-perishable)

3. **Model Testing**

   * Train baseline models with and without oil price
   * Quantify performance improvement (RMSE / MAE)

4. **Interaction Features**

   * Combine oil price with promotions or holidays

---

## 9. Summary

* The oil dataset is **clean, reliable, and business-relevant**.
* Missing values were minimal (~3.5%) and handled appropriately.
* Oil price shows strong long-term trends and regime shifts.
* Proper integration can significantly improve forecasting accuracy.

This dataset should be considered a **core exogenous input** for downstream sales modeling.
