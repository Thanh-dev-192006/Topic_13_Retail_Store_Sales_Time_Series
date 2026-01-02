Exploratory Data Analysis (EDA) Report

Dataset: Stores
Objective: Understand the structure and quality of the store dataset and derive actionable insights for modeling and business decision-making.

1. Dataset Overview
1.1 Size and Coverage

Number of records: 54 stores

Number of features: 6

Unit of analysis: One row represents one physical store

Geographic coverage:

Cities: 22

States: 16

Time coverage:

No temporal dimension is present; the dataset represents a static snapshot of the store network.

Business implication:
This dataset is best used as a store dimension table in a data warehouse and as a lookup table when joining with time-dependent datasets (sales, transactions, promotions). It is not suitable for standalone time-series analysis.

2. Data Structure and Granularity
2.1 Variables
Column	Data Type	Description
store_nbr	Integer	Unique store identifier
city	Categorical	City where the store is located
state	Categorical	State/region
type	Categorical	Store type (A–E)
cluster	Integer	Store cluster/segment
type_encoded	Integer	Numeric encoding of type
2.2 Granularity

Grain: One row = one store

No duplicated store_nbr

No pre-aggregated metrics

Modeling relevance:

store_nbr functions as a primary key

Dataset can be directly joined into fact tables without additional normalization

3. Identified Patterns and Key Findings
3.1 Distribution of Store Types
Store Type	Count	Percentage
D	18	~33.3%
A	9	~16.7%
B	8	~14.8%
C	8	~14.8%
E	11	~20.4%

Finding:

Type D stores account for approximately one-third of all stores.

Store types are relatively balanced; no single type dominates the dataset.

Business implication:

Store type is a potentially strong predictor for sales or demand

No severe class imbalance risk when using type in predictive models

3.2 Cluster Distribution

Number of clusters: 17

Largest cluster: 5 stores

Smallest cluster: 1 store

Finding:

Cluster sizes are uneven, with several small clusters.

So what for modeling:

Clusters may introduce noise if used directly

Consider grouping clusters or applying regularization if included as categorical features

3.3 Geographic Concentration

Quito: 22 out of 54 stores (~40.7%)

All other cities have fewer than 5 stores each

Finding:

Strong geographic concentration in Quito

Business implication:

Models may overfit patterns specific to Quito

Predictions for less-represented cities may have higher uncertainty

4. Data Quality Issues and Handling Decisions
4.1 Missing Values

Missing rate: 0% across all columns

Decision:
No imputation required.

4.2 Redundant Feature: type_encoded

type_encoded is a direct one-to-one numeric mapping of type

Provides no additional information

Decision:

Drop type_encoded during modeling

Retain type for flexible encoding strategies

Modeling impact:
Reduces multicollinearity and unnecessary feature duplication.

4.3 Categorical Cardinality

type: 5 categories

state: 16 categories

city: 22 categories

Risk:
Some cities have very low representation.

Handling strategy:

Group rare cities into an “Other” category, or

Apply target encoding once sales data is joined

5. Integration Notes (Joins and Relationships)
5.1 Join Keys

Primary key: store_nbr

5.2 Relationships

Stores (1) → (N) Sales

Stores (1) → (N) Transactions

Integration implication:

Clean star-schema integration

Low join complexity and low risk of key mismatches

6. Recommended Next Steps
6.1 For Modeling

Remove type_encoded

Encode features:

type: one-hot encoding

city / state: grouping or target encoding

Test interaction effects:

Store type × promotions

Cluster × demand volatility

6.2 For Business Analysis

Compare performance between:

Quito vs. non-Quito stores

Large vs. small clusters

Identify store types with higher promotional ROI

6.3 For Data Engineering

Standardize city and state naming

Document cluster definitions (currently missing metadata)

7. Executive Summary

The dataset is small, clean, and structurally sound

Significant geographic bias toward Quito (~41%)

No missing or duplicate records

Minor feature redundancy, easily resolved

Conclusion

The Stores dataset is clean, well-structured, and suitable for use as a store dimension table in analytical and modeling workflows. It contains no missing values or duplicate identifiers, and all key fields are consistent and integration-ready.

However, the dataset shows a strong geographic concentration in Quito (~41%) and uneven cluster sizes, which may introduce bias in downstream models. Feature redundancy (type_encoded) should be removed, and categorical variables—especially city and cluster—require careful encoding or aggregation.

Overall, the data is production-ready, with the main risks stemming from representation and geographic bias rather than data quality.
