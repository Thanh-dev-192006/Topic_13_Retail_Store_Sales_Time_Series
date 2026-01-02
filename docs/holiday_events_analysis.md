# Holidays & Events Dataset Analysis

## 1. Dataset Overview

### Basic Information
- **Dataset Size**: 350 rows × 6 columns
- **Time Coverage**: 2012-2017 (312 unique dates)
- **Geographic Scope**: Ecuador - national, regional, and local levels
- **Memory Usage**: 14.1+ KB
- **Data Quality**: 100% complete - no missing values in any column

### Temporal Distribution
- **Unique Dates**: 312 dates over ~5 years
- **Most Frequent Date**: 2014-06-25 (appears 4 times)
- **Average**: ~70 holiday/event entries per year
- This indicates multiple simultaneous events at different geographic levels

## 2. Data Structure

### Dimensions & Granularity

**Columns Breakdown:**
1. `date` (object): Event occurrence date
2. `type` (object): Event classification - 6 unique types
3. `locale` (object): Geographic scope - 3 levels
4. `locale_name` (object): Specific location name - 24 unique locations
5. `description` (object): Event name/description - 103 unique events
6. `transferred` (bool): Whether holiday was transferred to another date

**Geographic Hierarchy:**
```
National (Ecuador) - 174 entries (49.7%)
  └─ Regional (provinces) - varies by region
      └─ Local (cities/cantons) - varies by locality
```

### Event Type Distribution

Based on the data:
- **Holiday**: 221 entries (63.1%) - dominant category
- **5 Other Types**: 129 entries (36.9%) combined
- **Transferred Events**: Only 12 entries (3.4%) have `transferred=True`

**Key Insight**: The overwhelming majority (96.6%) of holidays are celebrated on their original dates, suggesting minimal impact from holiday transfers on sales patterns.

## 3. Key Patterns & Findings

### 3.1 Geographic Coverage Pattern

**National Events**: 174 entries (49.7%)
- Affect entire Ecuador simultaneously
- Highest impact on nationwide sales
- Include major holidays like Carnaval (appears 10 times - most frequent event)

**Regional/Local Events**: 176 entries (50.3%)
- 24 different locations tracked
- Cotopaxi, Cuenca, Libertad, Riobamba, Manta among tracked regions
- Create localized sales spikes that won't appear in national aggregates

**Business Implication**: Store-level forecasting MUST incorporate local holidays. A model using only national holidays will miss 50% of holiday effects.

### 3.2 Event Repetition Pattern

**Most Frequent Events:**
- "Carnaval": 10 occurrences (annual multi-day celebration)
- Other events: variable repetition across years

**Date Frequency:**
- 312 unique dates for 350 entries
- 38 dates (12.2%) have multiple simultaneous events
- Example: 2014-06-25 appears 4 times (likely different locales)

**Modeling Consideration**: Need to aggregate holiday impact per date-store combination, as multiple events can affect same day.

### 3.3 Temporal Consistency

**Coverage Analysis:**
- ~70 events per year on average
- Consistent tracking across 5-year period
- No seasonal bias in recording (all months represented)

**Data Completeness**: Zero missing values indicates clean, reliable data collection process.

## 4. Data Quality Assessment

### 4.1 Completeness ✅

```
Missing Values: 0 across all 6 columns (0.0%)
```

**Assessment**: Exceptional quality - no imputation needed.

### 4.2 Data Type Issues ⚠️

**Current State:**
- `date` column: stored as `object` (string)
- Should be: `datetime64[ns]`

**Required Transformation:**
```python
df['date'] = pd.to_datetime(df['date'])
```

**Impact**: Without conversion, date-based filtering and merging with time-series data will fail or perform poorly.

### 4.3 Categorical Encoding

**Current String Categories:**
- `type`: 6 unique values
- `locale`: 3 unique values (hierarchical)
- `locale_name`: 24 unique values
- `description`: 103 unique values

**Recommendation**: Keep as strings for joins with stores dataset, but create binary flags for modeling:
- `is_national_holiday`
- `is_regional_holiday`
- `is_local_holiday`
- `is_transferred`

### 4.4 Potential Issues

**1. Multiple Events Per Date-Location**
- 38 dates have overlapping events
- Need aggregation strategy: cumulative effect or flag presence

**2. Local Event Matching**
- Stores dataset must have location identifiers matching `locale_name`
- Risk: mismatched location names will cause failed joins

**3. Holiday Lag Effects**
- Dataset only captures exact date
- Real sales impact may span multiple days (before/after)
- Should engineer features like `days_to_holiday`, `days_since_holiday`

## 5. Integration with Other Datasets

### 5.1 Join Keys

**Primary Join Strategy:**
```python
# Merge with train data
train_merged = train.merge(
    holidays,
    on='date',
    how='left'
)

# Then filter by store location
train_merged = train_merged.merge(
    stores[['store_nbr', 'city']],
    on='store_nbr'
).query('locale_name == city OR locale == "National"')
```

**Critical Requirement**: Stores dataset MUST contain location information (city/region) that matches `locale_name` values.

### 5.2 Relationship with Train Dataset

**Expected Match Rate:**
- National holidays: affect all 54 stores × relevant dates
- Regional/local: affect subset of stores
- Overall: ~312 dates out of ~1,826 dates in 5-year period = 17.1% of days have some holiday

**Sales Impact Hypothesis:**
- National holidays → spike in sales day before, drop on holiday
- Local holidays → localized effects requiring store-level modeling
- Transferred holidays → minimal pattern disruption (only 3.4% of events)

### 5.3 Relationship with Oil Dataset

**Indirect Relationship:**
- Holidays don't directly affect oil prices
- But holiday timing may correlate with economic cycles
- Consider interaction features: `holiday × oil_price_change`

### 5.4 Feature Engineering Opportunities

**From Holidays Dataset:**
1. **Binary Flags:**
   - `is_holiday` (any type)
   - `is_national_holiday`
   - `is_work_day` (if Event type includes "Work Day")

2. **Count Features:**
   - `holiday_count_week` (number of holidays in same week)
   - `holiday_count_month`

3. **Temporal Features:**
   - `days_since_last_holiday`
   - `days_to_next_holiday`
   - `holiday_weekend_interaction` (holiday near weekend)

4. **Event-Specific:**
   - `is_carnaval` (most frequent, likely highest impact)
   - `is_transferred` (different sales pattern?)

## 6. Business Implications

### 6.1 For Sales Forecasting

**Critical Insights:**

1. **Store-Level Modeling Required**: 50.3% of holidays are regional/local
   - National-only model will underperform
   - Store clustering by region may improve efficiency

2. **Holiday Lead/Lag Effects**: Need 3-5 day windows
   - Shoppers stock up 1-2 days before
   - Stores may be closed on holiday
   - Shopping resumes 1-2 days after

3. **Carnaval Priority**: 10 occurrences make it statistically significant
   - Warrants dedicated feature or coefficient
   - Multi-day event likely has different pattern than single-day holiday

### 6.2 For Inventory Management

**Actionable Recommendations:**

1. **Pre-Holiday Stocking**: Increase inventory 2-3 days before national holidays
2. **Regional Differentiation**: Local managers need visibility to local holiday calendar
3. **Transfer Impact**: Minimal (3.4% of events) - don't over-optimize for this

### 6.3 Data Limitations

**What's Missing:**
- Holiday "importance" scale (all holidays weighted equally)
- Store closure information (are stores open during holidays?)
- Customer traffic patterns (just sales, not foot traffic)
- Multi-day event boundaries (Carnaval duration unclear)

**Workaround**: Use sales data itself to learn holiday importance through model coefficients.

## 7. Next Steps & Recommendations

### 7.1 Immediate Data Preparation

**Priority Actions:**
1. ✅ Convert `date` column to datetime format
2. ✅ Verify location name matching with stores dataset
3. ✅ Create binary holiday flags for each store-date combination
4. ✅ Engineer lag/lead features (±3 days window)

### 7.2 Integration Validation

**Before Modeling:**
```python
# Check 1: Date range alignment
assert holidays['date'].min() <= train['date'].min()
assert holidays['date'].max() >= train['date'].max()

# Check 2: Location matching
stores_locations = set(stores['city'].unique())
holiday_locations = set(holidays['locale_name'].unique())
unmatched = holiday_locations - stores_locations
print(f"Unmatched locations: {unmatched}")

# Check 3: Coverage rate
holiday_dates = set(holidays['date'])
train_dates = set(train['date'])
coverage = len(holiday_dates & train_dates) / len(train_dates)
print(f"Holiday coverage: {coverage:.1%}")
```

### 7.3 Feature Engineering Pipeline

**Proposed Hierarchy:**
```
Level 1 (Basic): is_holiday, is_national
Level 2 (Temporal): days_to_holiday, days_since_holiday  
Level 3 (Advanced): holiday_type_onehot, is_carnaval, holiday_clusters
Level 4 (Interaction): holiday × day_of_week, holiday × oil_price
```

Start with Level 1-2, add 3-4 based on model performance gains.

### 7.4 Modeling Considerations

**Recommendations:**

1. **Separate Holiday Coefficients**: Don't treat all holidays equally
   - Group by `type` and estimate separate effects
   - Carnaval should have its own coefficient

2. **Regional Model Variants**: Consider 3 model types
   - National stores only
   - Regional hubs
   - Local/rural stores
   
3. **Holiday Importance Learning**: Use L1 regularization to auto-select important holidays

4. **Validation Strategy**: Ensure test set includes major holidays
   - Don't accidentally put all Carnavals in training set

### 7.5 Documentation Needs

**For Team Collaboration:**
- Create location mapping table (holiday locale → store city)
- Document holiday impact assumptions (e.g., "sales drop 50% on national holidays")
- Track model performance separately for holiday vs. non-holiday periods

---

## Summary Statistics

| Metric | Value | Implication |
|--------|-------|-------------|
| Total Events | 350 | Sufficient for statistical learning |
| National Holidays | 174 (49.7%) | Half of events affect all stores |
| Unique Dates | 312 | ~17% of days in 5-year period |
| Missing Values | 0 (0%) | Clean dataset, no preprocessing needed |
| Transferred Holidays | 12 (3.4%) | Negligible pattern disruption |
| Most Frequent Event | Carnaval (10×) | Warrants dedicated feature |
| Location Diversity | 24 unique | Requires store-level location matching |

**Overall Assessment**: High-quality dataset ready for integration. Primary challenge is geographic matching with stores dataset, not data cleaning. Holiday features will be crucial for model performance during peak shopping periods.