# Store Metadata Dataset Exploration Report
**Retail Store Sales Time Series Analysis**
*Generated: 2026-01-02*

---

## Executive Summary

This report analyzes metadata for 54 retail stores across Ecuador, serving as the foundational dimension table for sales forecasting. Four critical insights emerged:

1. **Geographic concentration creates modeling risk**: Quito dominates with 22 stores (40.7% of network), while 16 other cities have only 1-2 stores each. This extreme concentration means models may overfit to Quito's patterns and underperform in underrepresented regions—critical for national expansion planning.

2. **Store type hierarchy suggests strategic segmentation**: Five store types (A-E) show balanced distribution, with Type D as the plurality (33.3%). The alphabetical ordering (A→E) likely represents a business-defined hierarchy (e.g., size, format, or market tier), making this a key predictive feature for sales stratification.

3. **Cluster system lacks documentation but shows granularity**: 17 clusters for 54 stores (3.2 stores/cluster average) indicates fine-grained segmentation—possibly based on demographics, sales performance, or competitive landscape. However, without metadata explaining cluster definitions, business interpretation is limited.

4. **Perfect data quality enables immediate use**: Zero missing values, no duplicates, and clean categorical fields mean this dataset is production-ready. The only redundancy is `type_encoded` (a duplicate of `type`), which should be dropped to avoid multicollinearity.

---

## Dataset Overview

### What This Dataset Contains
The stores dataset is a **static dimension table** cataloging each retail location's characteristics. It provides geographic and operational metadata to segment stores in sales forecasting models.

**Core Specifications:**
- **Rows**: 54 stores (one row per physical location)
- **Columns**: 6 features (store_nbr, city, state, type, cluster, type_encoded)
- **Time Span**: No temporal dimension (snapshot, not time-series)
- **Granularity**: Store-level (no sub-store breakdowns)
- **Memory Footprint**: ~3 KB (negligible)

### Business Context
Corporación Favorita operates a geographically dispersed retail network across Ecuador. This dataset enables:
- **Market segmentation**: Group stores by type, cluster, or region for targeted strategies
- **Expansion analysis**: Identify underserved regions (few stores) vs. saturated markets (Quito)
- **Performance benchmarking**: Compare sales across store types or clusters to find best practices
- **Resource allocation**: Prioritize inventory, staffing, and promotions based on store characteristics

As a **dimension table**, this data joins to transactional datasets (train.csv, transactions.csv) via `store_nbr` as the primary key.

---

## Data Structure & Characteristics

### Column Specifications

| Column | Type | Description | Value Range |
|--------|------|-------------|-------------|
| `store_nbr` | int64 | Unique store identifier (primary key) | 1 - 54 |
| `city` | object | City location of store | 22 unique cities |
| `state` | object | Ecuadorian province/state | 16 unique states |
| `type` | object | Store type/format classification | A, B, C, D, E |
| `cluster` | int64 | Store cluster/segment ID | 1 - 17 |
| `type_encoded` | int64 | Numeric encoding of `type` (0-4) | 0 - 4 |

**Critical Notes**:
- **Primary key**: `store_nbr` is unique (no duplicates)
- **Redundancy**: `type_encoded` is a simple label-encoding of `type` (A=0, B=1, C=2, D=3, E=4)—provides no new information
- **Geographic hierarchy**: `city` nests within `state` (many-to-one relationship)

### Store Type Distribution

| Type | Count | Percentage | Likely Meaning |
|------|-------|------------|----------------|
| D | 18 | 33.3% | Mid-tier standard stores (plurality format) |
| E | 11 | 20.4% | Specialty or convenience format |
| A | 9 | 16.7% | Flagship or superstore format |
| B | 8 | 14.8% | Regional format |
| C | 8 | 14.8% | Compact format |

**Interpretation**: The alphabetical ordering (A→E) suggests a business-defined hierarchy. Without metadata, we hypothesize:
- **Type A**: Large-format stores (superstores, hypermarkets)
- **Type B-D**: Mid-tier formats with decreasing size/assortment
- **Type E**: Small-format (convenience, urban, or specialty)

**Modeling Implication**: Relatively balanced distribution (no type <15%) means no severe class imbalance—safe to use as categorical feature with one-hot encoding.

### Cluster Distribution

**Cluster Characteristics**:
- **Number of Clusters**: 17
- **Stores per Cluster**: Range = 1-5 stores, Average = 3.2 stores/cluster
- **Distribution**: Uneven—some clusters have 5 stores, others just 1

**What This Suggests**:
- High granularity (17 segments for 54 stores) indicates **sophisticated business segmentation**
- Possible clustering criteria: customer demographics, sales volume tiers, competitive intensity, or geographic markets
- Single-store clusters may represent outliers (e.g., pilot formats, legacy acquisitions, or unique markets)

**Data Gap**: No metadata explaining cluster definitions—limits business interpretation.

**Modeling Implication**:
- Small clusters (n=1-2) may cause overfitting if used as categorical features
- Consider grouping into "macro-clusters" (e.g., collapse clusters 1-5, 6-10, etc.)
- Or use as numeric feature if clusters have ordinal meaning (e.g., cluster 1 = lowest sales tier)

---

## Key Findings & Patterns

### 1. Geographic Concentration: Quito Dominance

**Store Count by City (Top 5)**:

| City | Store Count | % of Total |
|------|-------------|------------|
| Quito | 22 | 40.7% |
| Guayaquil | 4 | 7.4% |
| Cuenca | 3 | 5.6% |
| Santo Domingo | 2 | 3.7% |
| Ambato | 2 | 3.7% |
| Other (17 cities) | 21 | 38.9% |

**Critical Finding**: Quito alone accounts for **41% of all stores**, while 17 other cities have only 1 store each.

**Why This Matters**:

1. **Model Overfitting Risk**: Machine learning models trained on this dataset will learn Quito-specific patterns (e.g., urban density, income levels, competition) and may fail to generalize to rural or smaller markets.

2. **Performance Variance**: Sales forecasts for Quito stores (n=22, high sample size) will have lower uncertainty than forecasts for single-store cities (n=1, no peer comparison).

3. **Business Strategy**: Either:
   - Quito is **oversaturated** (too many stores competing for same customers)
   - Or Quito is the **core market** (highest population, purchasing power)

**Actionable Insight**:
- Segment models by "Quito vs. non-Quito" to test if different forecasting strategies needed
- For expansion, analyze if underrepresented regions (e.g., coastal cities beyond Guayaquil) are underserved opportunities

### 2. State-Level Distribution: Regional Clustering

**Store Count by State (Top 5)**:

| State | Store Count | % of Total |
|-------|-------------|------------|
| Pichincha (Quito's state) | 23 | 42.6% |
| Guayas (Guayaquil's state) | 7 | 13.0% |
| Azuay (Cuenca's state) | 4 | 7.4% |
| Los Ríos | 3 | 5.6% |
| Tungurahua | 3 | 5.6% |
| Other (11 states) | 14 | 25.9% |

**Key Observation**: Geographic concentration mirrors city patterns—Pichincha (Quito's state) holds 43% of stores.

**Business Implication**:
- **Highland region (Pichincha, Azuay)** dominates over **coastal region (Guayas)**
- May reflect population distribution, but also suggests potential coastal market gap

### 3. Store Type vs. Cluster: No Strong Relationship

**Analysis from Notebook**: Heatmap of cluster × type shows sparse distribution—no clear pattern like "all Type A stores in Cluster 1."

**What This Means**:
- **Clusters are NOT defined solely by store type**—they likely incorporate geography, sales volume, or other factors
- **Independence of features**: `type` and `cluster` provide complementary information (low multicollinearity)

**Modeling Implication**: Safe to include both `type` and `cluster` in models without redundancy concerns.

---

## Data Quality Assessment

### Completeness: Perfect ✅

**Missing Values Analysis:**
```
Column          Missing Values    Percentage
store_nbr       0                 0.0%
city            0                 0.0%
state           0                 0.0%
type            0                 0.0%
cluster         0                 0.0%
type_encoded    0                 0.0%
```

**Assessment**: Zero missing values. Dataset is 100% complete—exceptional for real-world data.

### Consistency: Excellent ✅

**✅ Strengths:**
- **No duplicate store IDs**: All `store_nbr` values are unique (1-54)
- **Valid categorical values**: All `type` values are A-E (no typos, nulls, or unexpected codes)
- **Numeric ranges valid**: `cluster` (1-17) and `type_encoded` (0-4) have no outliers
- **Geographic nesting**: All cities correctly map to their corresponding states (no mismatches)

**⚠️ Minor Redundancy:**
- `type_encoded` is a deterministic transformation of `type` (A→0, B→1, etc.)
- **Action**: Drop `type_encoded` in modeling to avoid multicollinearity
- **Retain `type`** for flexible encoding strategies (one-hot, target encoding, etc.)

### Potential Issues

**1. Categorical Cardinality**:
- **High cardinality**: 22 cities, 16 states
- **Sparse representation**: 17 cities have ≤2 stores each

**Risk**:
- One-hot encoding `city` creates 22 binary features—may cause overfitting in small datasets
- Models may not learn reliable patterns for rare cities (insufficient data)

**Mitigation**:
- **Grouping**: Collapse rare cities into "Other" category
- **Target encoding**: Replace city with average sales per city (only after joining sales data)
- **Hierarchical modeling**: Use `state` instead of `city` for broader groupings

**2. Cluster Metadata Missing**:
- Dataset provides cluster IDs (1-17) but no explanation of how clusters were defined
- **Impact**: Cannot interpret cluster effects (e.g., "why does Cluster 5 outperform Cluster 10?")

**Recommendation**: Document cluster definitions (ask business stakeholders or reverse-engineer from sales data).

---

## Business Implications

### 1. Store Type as Sales Stratification

**Hypothesis**: Store types (A-E) likely correlate with sales volume, assortment breadth, and customer demographics.

**Testing Strategy**:
1. Join stores.csv with train.csv on `store_nbr`
2. Compare average daily sales by `type`
3. Expected pattern: Type A > Type B > ... > Type E (if A = largest format)

**Business Use Case**:
- **Inventory planning**: Large stores (Type A) need deeper stock, small stores (Type E) need curated assortment
- **Promotional strategy**: Promotions may be more effective in high-traffic Type A stores
- **New store planning**: If opening a Type C store, benchmark against existing Type C performance

### 2. Geographic Expansion Opportunities

**Current Footprint**:
- **Saturated**: Quito (22 stores in one city)
- **Underserved**: Coastal cities (only Guayaquil has 4 stores, rest have 1-2)

**Strategic Questions**:
1. Is Quito **oversaturated** (cannibalization risk) or just the **core market** (high demand)?
2. Are underrepresented regions **low-opportunity** (small population) or **untapped growth** (unmet demand)?

**Data-Driven Approach**:
- Calculate **sales per store** in Quito vs. other regions
- If Quito stores have **lower sales/store** → oversaturation (expand elsewhere)
- If Quito stores have **higher sales/store** → high-demand market (concentration justified)

### 3. Cluster-Based Resource Allocation

**If cluster definitions were known**, businesses could:
- Allocate promotional budgets proportional to cluster size or sales potential
- Customize product assortment by cluster (e.g., urban clusters stock premium brands, rural clusters stock value brands)
- Prioritize store renovations/upgrades for high-ROI clusters

**Current Limitation**: Without cluster metadata, these strategies remain speculative.

---

## Integration & Next Steps

### Integration with Other Datasets

**Join Strategy**:
```python
# Merge store metadata into sales data
df_train = df_train.merge(df_stores, on='store_nbr', how='left')
```

**Expected Result**: Each sales record inherits store characteristics (city, state, type, cluster).

**Validation Checks**:
1. **Join completeness**: All `store_nbr` values in train.csv should match stores.csv (expect 54 stores)
2. **Orphan records**: If train.csv contains `store_nbr` not in stores.csv, investigate data quality issue
3. **Date coverage**: Verify all 54 stores have sales records (or identify store opening/closing dates)

### Recommended Feature Engineering

**1. Geographic Grouping**:
```python
# Simplify city into Quito vs. non-Quito
df_stores['is_quito'] = (df_stores['city'] == 'Quito').astype(int)

# Group states into regions (Highland vs. Coastal vs. Amazon)
region_map = {
    'Pichincha': 'Highland', 'Azuay': 'Highland', 'Tungurahua': 'Highland',
    'Guayas': 'Coastal', 'Manabí': 'Coastal', 'El Oro': 'Coastal',
    # ... (complete mapping)
}
df_stores['region'] = df_stores['state'].map(region_map)
```

**2. Cluster Aggregation**:
```python
# Group small clusters into macro-clusters
cluster_map = {1: 'Low', 2: 'Low', ..., 10: 'Medium', ..., 17: 'High'}
df_stores['cluster_group'] = df_stores['cluster'].map(cluster_map)
```

**3. Store Type Encoding**:
```python
# One-hot encoding for tree-based models
df_stores_encoded = pd.get_dummies(df_stores, columns=['type'], drop_first=False)

# Or ordinal encoding if A→E represents size hierarchy
type_order = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'E': 1}
df_stores['type_ordinal'] = df_stores['type'].map(type_order)
```

### Next Steps for Validation

**Immediate Actions**:

1. **Join with Sales Data**:
   ```python
   # Merge and analyze sales by store type
   df_merged = df_train.merge(df_stores, on='store_nbr')
   sales_by_type = df_merged.groupby('type')['sales'].agg(['sum', 'mean', 'std'])
   ```

2. **Geographic Sales Heatmap**:
   - Aggregate sales by city/state
   - Visualize to confirm if Quito's store concentration aligns with sales concentration

3. **Cluster Reverse-Engineering**:
   - Calculate average sales, promotion intensity, and zero-rate by cluster
   - Use k-means on these metrics to see if clusters align with performance tiers

4. **Store Type Validation**:
   - If Type A stores have significantly higher sales, confirm hypothesis that A = largest format
   - If no clear pattern, investigate alternative definitions (e.g., franchise vs. owned, urban vs. rural)

---

## Conclusion

The stores dataset is a **high-quality, production-ready dimension table** with zero missing values and clean structure. Its compact size (54 stores, 6 features) makes it easy to integrate and maintain.

**Key Strengths**:
1. **Perfect completeness** (0% missing data)
2. **Clean primary key** (store_nbr) for reliable joins
3. **Balanced store types** (no severe class imbalance)
4. **Rich segmentation** (type, cluster, geography)

**Key Risks**:
1. **Geographic bias**: Quito's 41% concentration may cause model overfitting
2. **Sparse cities**: 17 cities with ≤2 stores lack sufficient data for city-level modeling
3. **Undocumented clusters**: Missing metadata limits business interpretation
4. **Redundant feature**: `type_encoded` should be dropped

**Success Metrics**:
- After joining with sales data: Confirm `type` and `cluster` are statistically significant predictors
- Geographic segmentation: Test if Quito-specific models outperform national models
- Expansion planning: Identify underserved regions with high sales potential

This dataset is **immediately ready for integration**—the main value unlocks when combined with sales and transaction data to reveal store performance patterns.
