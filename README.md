
##ASSIGMENT 1 - Ecommerce Data Cleaning - Python & Pandas Assignment

## Objective
Learn Python basics and perform basic data exploration and cleaning using Pandas.

## Dataset
- Source: Kaggle - Shopping Dataset
- File used: Combined_dataset.csv (1000+ ecommerce products)

## Steps Performed
1. Loaded CSV dataset into a Pandas DataFrame
2. Explored data (head, tail, shape, columns, data types)
3. Handled missing values (dropped nulls in critical columns, filled text columns with 'Unknown')
4. Filtered rows (rating >= 4) and selected relevant columns
5. Removed duplicate rows
6. Created derived column: total_amount = final_price × ratings_count
7. Saved cleaned dataset as cleaned_ecommerce_dataset.csv

## Note on Derived Column
The dataset had no quantity column. ratings_count (number of customer ratings) 
was used as a proxy for quantity to calculate total_amount.

## Output
- ecommerce_data_cleaning.ipynb (Jupyter Notebook)
- cleaned_ecommerce_dataset.csv (Cleaned dataset)

## Summary
- Original dataset rows: 1000
- After cleaning and filtering: 615
- Missing values handled: Yes
- Duplicates removed: Yes
- Derived column created: total_amount = final_price × ratings_count

- 
## ASSIGNMENT 2 - SQL Sales Analysis

### Objective
Analyze sales data using SQL with filtering, aggregation, and business queries.

### Dataset
- Source: Kaggle - Superstore Dataset
- File used: Sample - Superstore.csv (9994 records)

### Steps Performed
1. Loaded dataset into SQLite database
2. Explored table schema and sample data
3. Applied WHERE filters (region, category, date, sales)
4. Used GROUP BY for aggregations (sales, quantity, averages)
5. Sorted and limited results (top products, top categories)
6. Solved business use cases (monthly trends, top customers, duplicates)
7. Validated results (row counts, NULL checks)

### Key Insights
- West region has highest total sales
- Technology category generates most revenue
- Peak sales observed in Q4 months
- Top customers contribute significantly to overall revenue
- Duplicate Order IDs exist because one order has multiple products
- No NULL values in Sales, Region, or Category columns

### Output
- sql_sales_analysis.ipynb (Jupyter Notebook)
