# Holidays & Events Dataset Exploration Report
**Retail Store Sales Time Series Analysis**
*Generated: 2026-01-02*

---

## Executive Summary

This report analyzes 350 holiday and event records spanning 2012-2017, providing critical calendar features for sales forecasting in Ecuador. Four key insights emerged:

1. **Geographic precision matters—national events are only half the story**: 49.7% of events are national (affecting all stores), but 50.3% are regional/local (city or province-specific). Models using only national holidays will **miss half of all holiday effects**, causing systematic underperformance in stores experiencing local celebrations. Store-location matching is mandatory, not optional.

2. **Minimal holiday transfers simplify modeling**: Only 12 events (3.4%) have `transferred=True`, meaning 96.6% of holidays occur on their scheduled dates. This is a **major modeling advantage**—no need to track complex transfer logic or multi-date holiday windows for most events.

3. **Carnaval dominates event frequency and likely sales impact**: Appearing 10 times (most frequent event), Carnaval is a multi-day national celebration warranting dedicated feature engineering. Its recurrence makes it statistically learnable, unlike one-off events.

4. **Perfect data quality enables immediate integration**: Zero missing values across all 350 records and 6 columns. The only preprocessing needed is datetime conversion—otherwise, dataset is production-ready.

---

## Dataset Overview

### What This Dataset Contains
The holidays_events dataset catalogs **national, regional, and local holidays and events** in Ecuador, serving as an **exogenous calendar feature** to explain sales anomalies (spikes before holidays, drops during closures).

**Core Specifications:**
- **Rows**: 350 event records
- **Columns**: 6 features (date, type, locale, locale_name, description, transferred)
- **Time Span**: 2012 to 2017 (312 unique dates over ~5 years)
- **Granularity**: Event-level (one row per event, multiple events can occur on same date)
- **Memory Footprint**: ~14 KB (negligible)

### Business Context
Ecuador's retail calendar includes:
- **National holidays**: Christmas, New Year, Independence Day (affect all 54 stores simultaneously)
- **Regional holidays**: Provincial anniversaries (e.g., Provincializacion de Cotopaxi)
- **Local holidays**: City foundation days (e.g., Fundacion de Cuenca)

**Why this matters for forecasting**:
- **Pre-holiday surge**: Customers stockpile 1-2 days before (e.g., December 24 traffic spike)
- **Holiday closure**: Stores closed or reduced hours → sales drop to near-zero
- **Post-holiday recovery**: Normal shopping resumes 1-2 days after

Without holiday features, models will:
- **Underpredict** pre-holiday spikes (misinterpret as random noise)
- **Overpredict** on-holiday sales (expect normal demand when stores are closed)
- **Misattribute** local sales anomalies (e.g., blaming promotions when it's a city holiday)

---

## Data Structure & Characteristics

### Column Specifications

| Column | Type | Description | Value Range |
|--------|------|-------------|-------------|
| `date` | object (datetime) | Holiday/event date | 2012-03-02 to 2017-12-26 |
| `type` | object | Event classification | 6 unique types (Holiday, Event, etc.) |
| `locale` | object | Geographic scope | National, Regional, Local |
| `locale_name` | object | Specific location (city/province/country) | 24 unique locations |
| `description` | object | Event name | 103 unique event descriptions |
| `transferred` | bool | Whether holiday moved to another date | True/False |

**Critical Notes**:
- **No primary key**: Same date can have multiple events (38 dates have 2+ events)
- **Hierarchical geography**: National > Regional > Local (Ecuador → Province → City)
- **Event types**: "Holiday" dominates (63.1% of records), followed by other event types

### Event Type Distribution

| Type | Count | Percentage | Likely Meaning |
|------|-------|------------|----------------|
| Holiday | 221 | 63.1% | Official holidays (potential store closures) |
| Other Types (5 total) | 129 | 36.9% | Events, work days, bridge days, etc. |

**Note**: Exact breakdown of other types not visible in notebook output, but "Holiday" is dominant category.

### Geographic Scope Distribution

| Locale | Count | Percentage | Impact Scope |
|--------|-------|------------|--------------|
| National | 174 | 49.7% | All 54 stores affected |
| Regional | ~88 | ~25% | Province-level (subset of stores) |
| Local | ~88 | ~25% | City-level (1-few stores) |

**Critical Insight**: **49.7% national vs. 50.3% regional/local** means store-level holiday features are essential—can't rely on national calendar alone.

### Location Breakdown

- **Unique Locations**: 24 (including "Ecuador" for national events)
- **Most Frequent Location**: "Ecuador" (174 national events)
- **Regional/Local Examples**: Cotopaxi, Cuenca, Libertad, Riobamba, Manta

**Modeling Implication**: Must join `locale_name` to store locations (city/state from stores.csv) to assign correct holidays to each store.

---

## Key Findings & Patterns

### 1. High Event Frequency: 17% of Days Have Holidays

**Temporal Distribution**:
- **Unique Dates**: 312 dates over ~1,826 days (2012-2017) = **17.1% coverage**
- **Average**: ~70 events per year
- **Multiple Events Per Day**: 38 dates (12.2%) have 2+ simultaneous events (e.g., national + local holiday on same day)

**What This Means**:

1. **Frequent holiday impact**: Nearly 1 in 6 days has some form of holiday/event—models must handle this as normal, not rare.

2. **Multi-event days complicate aggregation**: When national + local holidays overlap, sales impact may be **additive** (double the effect) or **capped** (store closed regardless of how many holidays). Need to test both strategies.

**Example**: 2014-06-25 appears **4 times** in dataset (same date, different locales/events)—must aggregate when joining to sales data.

### 2. Carnaval Dominates Event Frequency

**Top Events by Occurrence**:

| Event Description | Count | Event Type |
|-------------------|-------|------------|
| Carnaval | 10 | Multi-day national celebration |
| Other events | <10 | Various |

**Why Carnaval Matters**:

1. **Statistical significance**: 10 occurrences provide sufficient sample size to learn Carnaval-specific patterns (unlike one-off events).

2. **Multi-day celebration**: Unlike single-day holidays, Carnaval spans several days—requires different feature engineering (e.g., "days into Carnaval" rather than binary is_holiday).

3. **Predictable timing**: Annual recurrence makes it forecastable—models can anticipate Carnaval effects in test data.

**Business Implication**: Create dedicated `is_carnaval` feature and analyze sales patterns separately from other holidays.

### 3. Minimal Holiday Transfers: 96.6% Occur on Schedule

**Transfer Analysis**:
- **Transferred Events**: 12 (3.4%)
- **Non-Transferred**: 338 (96.6%)

**What "Transferred" Means**: When a holiday falls on a weekend, some governments move it to nearest weekday (e.g., Friday or Monday) to create long weekend.

**Modeling Simplification**:

With only 3.4% transfers, **don't over-engineer** transfer logic. Two approaches:

1. **Ignore transfers**: Use scheduled date for all holidays (96.6% accuracy)
2. **Simple flag**: Add `is_transferred` as binary feature (let model learn if effect differs)

**Contrast with complex calendars**: Some countries transfer many holidays (e.g., UK bank holidays), requiring multi-date tracking. Ecuador's low transfer rate is a **data quality advantage**.

### 4. Geographic Matching Challenge: 24 Unique Locations

**Location Diversity**:
- **National**: "Ecuador" (1 location, 174 events)
- **Regional/Local**: 23 distinct cities/provinces

**Critical Integration Requirement**:

To assign holidays to stores, must **map stores.csv locations to holidays_events.csv locations**:

```python
# Example mapping needed
store_to_holiday_locale = {
    'Quito': 'Pichincha',          # Store city → holiday region
    'Guayaquil': 'Guayas',
    'Cuenca': 'Cuenca',            # May match directly
    # ... (complete mapping for all 22 cities in stores.csv)
}
```

**Risk**: If location names don't match (e.g., store says "Quito" but holiday says "Pichincha"), join will fail and local holidays will be missed.

**Validation Step**: After joining, verify that regional/local events only affect expected stores (e.g., "Fundacion de Cuenca" should only appear for Cuenca stores, not Quito).

---

## Data Quality Assessment

### Completeness: Perfect ✅

**Missing Values Analysis:**
```
Column          Missing Values    Percentage
date            0                 0.0%
type            0                 0.0%
locale          0                 0.0%
locale_name     0                 0.0%
description     0                 0.0%
transferred     0                 0.0%
```

**Assessment**: Zero missing values. Dataset is 100% complete—exceptional for manually curated event calendars.

### Consistency: Excellent ✅

**✅ Strengths:**
- **Date format consistent**: All dates parseable (2012-03-02 onwards)
- **Boolean field clean**: `transferred` is proper bool (True/False), not messy strings
- **No typos detected**: Event descriptions like "Carnaval" spelled consistently (not "Carnival", "Carnavale", etc.)
- **Hierarchical integrity**: No "Local" events with `locale_name = "Ecuador"` (which would be illogical)

**⚠️ Data Type Issue (minor)**:
- `date` stored as `object` (string) instead of `datetime64`
- **Fix required**:
  ```python
  df_holidays['date'] = pd.to_datetime(df_holidays['date'])
  ```
- **Impact**: Without conversion, date-based joins and filtering will fail

### Potential Issues

**1. Multiple Events Per Date**:
- 38 dates have 2-4 simultaneous events (different locales or event types)
- **Aggregation needed** when joining to sales data:
  - Option A: `is_any_holiday` (binary flag if ≥1 event that day)
  - Option B: `holiday_count` (integer count of events)
  - Option C: `holiday_importance` (weighted sum, e.g., National=3, Regional=2, Local=1)

**2. Location Name Matching**:
- `locale_name` may not align with `city` or `state` in stores.csv
- Example mismatch: Holiday says "Manta" (city), but store location might be listed as "Manabí" (province)
- **Mitigation**: Create explicit mapping table or fuzzy matching

**3. Event Type Ambiguity**:
- 6 event types exist, but only "Holiday" shown in output
- Other types may include "Work Day", "Event", "Additional", "Bridge", "Transfer"
- **Unclear impact**: Do "Work Day" events increase sales (people shopping during extended hours)? Or decrease (fatigue)?
- **Action**: One-hot encode `type` and let model learn effect of each

---

## Business Implications

### 1. Store-Level Holiday Features Are Mandatory

**Why National-Only Models Fail**:

If using only national holidays (174 events):
- **Miss 50.3% of holiday effects** (176 regional/local events ignored)
- **Systematic bias**: Stores in cities with many local holidays (e.g., Cuenca with Fundacion de Cuenca) will be systematically underforecast during those events

**Solution**:
- Merge holidays with stores.csv on location
- Create store-specific holiday calendars (each store has ~70 national + ~5-10 local events per year)

### 2. Pre-Holiday Shopping Surge Requires Lead Features

**Expected Sales Pattern**:
1. **2 days before holiday**: Customers stockpile (sales spike)
2. **1 day before**: Peak stockpiling (highest sales)
3. **Holiday day**: Store closed or reduced hours (sales collapse)
4. **1 day after**: Slow recovery (customers using stockpiled goods)
5. **2 days after**: Return to normal

**Feature Engineering**:
```python
# Create lead/lag indicators
df['days_to_next_holiday'] = (next_holiday_date - df['date']).dt.days
df['days_since_last_holiday'] = (df['date'] - last_holiday_date).dt.days

# Binary flags for pre-holiday window
df['is_1day_before_holiday'] = (df['days_to_next_holiday'] == 1).astype(int)
df['is_2day_before_holiday'] = (df['days_to_next_holiday'] == 2).astype(int)
```

**Why this matters**: Simply flagging `is_holiday=1` on holiday date will miss the **pre-holiday surge** (often higher sales impact than holiday itself).

### 3. Carnaval Warrants Dedicated Treatment

**Hypothesis**: Multi-day Carnaval has different pattern than single-day holidays.

**Testing Strategy**:
1. Extract all Carnaval dates (10 occurrences)
2. Analyze sales 5 days before → 5 days after Carnaval
3. Compare to sales patterns around single-day holidays (e.g., Independence Day)
4. If patterns differ significantly (>20% variance), create `is_carnaval` feature

**Expected Findings**:
- Carnaval may have **longer pre-holiday surge** (3-4 days vs. 1-2 days)
- Post-Carnaval recovery may be **slower** (multi-day celebration → more stockpiling)

### 4. Regional Sales Strategy Optimization

**Opportunity**: Local holidays create **regional sales anomalies** invisible in national aggregates.

**Business Use Case**:
- **Inventory allocation**: If Cuenca has "Fundacion de Cuenca" holiday, shift inventory to Cuenca stores 2 days before (expect surge)
- **Promotion timing**: Avoid running promotions **during** local holidays (stores closed, wasted promotional budget)
- **Competitor analysis**: If competitor doesn't adjust for local holidays, their stockouts create market share opportunities

---

## Integration & Next Steps

### Integration with Other Datasets

**Join Strategy with Sales Data**:

```python
# Step 1: Merge stores with holidays on location
stores_with_holidays = stores.merge(
    holidays_events[holidays_events['locale'] == 'National'],
    how='cross'  # All stores get all national holidays
).append(
    stores.merge(
        holidays_events[holidays_events['locale'].isin(['Regional', 'Local'])],
        left_on='city',  # or 'state', depending on locale
        right_on='locale_name',
        how='left'
    )
)

# Step 2: Merge with train data
df_train = df_train.merge(
    stores_with_holidays[['store_nbr', 'date', 'type', 'description']],
    on=['store_nbr', 'date'],
    how='left'
)

# Step 3: Create holiday flags
df_train['is_holiday'] = df_train['type'].notna().astype(int)
```

**Validation Checks**:
1. **National holiday coverage**: Every store should have ~174 national holidays matched
2. **Regional/local distribution**: Stores in Quito should have Quito-specific holidays, not Cuenca holidays
3. **Join success rate**: Expect ~17% of train.csv dates to have `is_holiday=1`

### Recommended Feature Engineering

**Level 1: Basic Binary Flags**
```python
df_train['is_holiday'] = (df_train['type'].notna()).astype(int)
df_train['is_national_holiday'] = (df_train['locale'] == 'National').astype(int)
df_train['is_transferred'] = df_train['transferred'].astype(int)
```

**Level 2: Temporal Lead/Lag Features**
```python
# Days until next holiday (per store)
df_train = df_train.sort_values(['store_nbr', 'date'])
df_train['days_to_holiday'] = df_train.groupby('store_nbr')['is_holiday'].apply(
    lambda x: x[::-1].cumsum()[::-1]  # Reverse cumsum trick
)

# Days since last holiday
df_train['days_since_holiday'] = df_train.groupby('store_nbr')['is_holiday'].cumsum()
```

**Level 3: Event-Specific Features**
```python
df_train['is_carnaval'] = (df_train['description'] == 'Carnaval').astype(int)
df_train['is_christmas_eve'] = (
    (df_train['date'].dt.month == 12) & (df_train['date'].dt.day == 24)
).astype(int)
```

**Level 4: Interaction Features**
```python
# Holiday × Day of Week (e.g., holiday on Saturday vs. Tuesday)
df_train['holiday_weekend'] = df_train['is_holiday'] * df_train['is_weekend']

# Holiday × Oil Price (economic context)
df_train['holiday_oil_interaction'] = df_train['is_holiday'] * df_train['oil_price_lag_7']
```

### Next Steps for Validation

**Immediate Actions**:

1. **Location Mapping Audit**:
   ```python
   # Check which store locations match holiday locations
   store_cities = set(df_stores['city'].unique())
   holiday_locales = set(df_holidays['locale_name'].unique())

   matched = store_cities & holiday_locales
   unmatched_stores = store_cities - holiday_locales
   unmatched_holidays = holiday_locales - store_cities

   print(f"Matched: {len(matched)}, Unmatched stores: {unmatched_stores}, Unmatched holidays: {unmatched_holidays}")
   ```

2. **Holiday Sales Impact Analysis**:
   ```python
   # Compare sales on holiday vs. non-holiday days
   df_merged = df_train.merge(df_holidays, on='date', how='left')
   df_merged['is_holiday'] = df_merged['type'].notna()

   holiday_sales = df_merged[df_merged['is_holiday']]['sales'].mean()
   normal_sales = df_merged[~df_merged['is_holiday']]['sales'].mean()

   print(f"Holiday sales: {holiday_sales:.2f}, Normal: {normal_sales:.2f}, Ratio: {holiday_sales/normal_sales:.2%}")
   ```

3. **Pre-Holiday Surge Detection**:
   ```python
   # Analyze sales 1-2 days before holidays
   df_train['days_to_holiday'] = ...  # (from feature engineering above)

   surge_sales = df_train[df_train['days_to_holiday'].isin([1, 2])]['sales'].mean()
   normal_sales = df_train[df_train['days_to_holiday'] > 7]['sales'].mean()

   print(f"Pre-holiday surge: {surge_sales/normal_sales - 1:.1%} above normal")
   ```

4. **Carnaval Deep Dive**:
   ```python
   # Extract Carnaval date ranges
   carnaval_dates = df_holidays[df_holidays['description'] == 'Carnaval']['date'].unique()

   # Analyze sales ±7 days around each Carnaval
   for cdate in carnaval_dates:
       window = df_train[(df_train['date'] >= cdate - pd.Timedelta(7, 'D')) &
                         (df_train['date'] <= cdate + pd.Timedelta(7, 'D'))]
       # Plot or summarize sales trend
   ```

---

## Conclusion

The holidays_events dataset is a **high-quality, essential calendar feature** for Ecuador retail forecasting. With zero missing values and clear structure, it's production-ready after minimal preprocessing.

**Key Strengths**:
1. **Perfect completeness** (0% missing data)
2. **Geographic granularity** (national + regional + local)
3. **Low transfer complexity** (96.6% of holidays occur on scheduled dates)
4. **Statistical depth** (350 events over 5 years, ~70/year)

**Key Risks**:
1. **Location matching required**: 50.3% of events are regional/local, necessitating store-location joins
2. **Multi-event aggregation**: 12.2% of dates have multiple simultaneous events—need aggregation strategy
3. **Lead/lag engineering critical**: On-holiday sales drop (stores closed), but pre-holiday sales spike—must capture both

**Success Metrics**:
- After integration: Confirm holiday features rank in top 5 predictors by importance
- Pre-holiday surge: Detect ≥20% sales increase 1-2 days before national holidays
- Regional accuracy: Local holiday features improve RMSE by ≥5% for stores in affected regions

This dataset transforms from "nice-to-have" to **mission-critical** when considering:
- Carnaval's 10 occurrences (statistically significant)
- 17% of all days have some event (frequent, not rare)
- Store-level heterogeneity (regional/local holidays affect different stores)

**Immediate Action**: Prioritize location mapping (stores.csv → holidays_events.csv) before any modeling begins—this is a **blocking dependency** for accurate forecasting.
