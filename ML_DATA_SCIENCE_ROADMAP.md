# XchangeFinder Data & Programming Upgrade

## Tracks included
- Data Analyst: CSV export, summary statistics, data quality, comparison tables; Python/R starters.
- Data Science: exploratory analysis, grouped currency-pair features, notebook workflow.
- Machine Learning: experimental linear trend estimate endpoint `/analytics/ml/forecast`; uses historical submission order, minimum three observations, bounded forecast horizon.
- Deep Learning: documented optional extension track (sequence modelling such as LSTM/GRU with chronological validation); not bundled or trained in this release because data volume and timestamp quality must first be verified.
- Programming language learning/integration: C, C++, Go, R, Rust, F# examples/notes; Python starter. These are integration examples and learning scaffolds, not full production SDKs.

## API examples
- `/analytics/data-quality`
- `/analytics/ml/forecast?from_currency=USD&to_currency=EUR&steps=3`
- `/analytics/pairs.csv`
- `/analytics/export.csv`

## Important limitation
The current schema does not necessarily contain timestamp columns; trend model treats row order as a sequence, not calendar time. Results are experimental, not live rate predictions or financial advice. Deep-learning model training requires richer validated data and a separately reviewed evaluation pipeline.
