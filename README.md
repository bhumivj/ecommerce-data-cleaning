
## ASSIGNMENT 1 - Ecommerce Data Cleaning - Python & Pandas Assignment

### Objective
Learn Python basics and perform basic data exploration and cleaning using Pandas.

### Dataset
- Source: Kaggle - Shopping Dataset
- File used: Combined_dataset.csv (1000+ ecommerce products)

### Steps Performed
1. Loaded CSV dataset into a Pandas DataFrame
2. Explored data (head, tail, shape, columns, data types)
3. Handled missing values (dropped nulls in critical columns, filled text columns with 'Unknown')
4. Filtered rows (rating >= 4) and selected relevant columns
5. Removed duplicate rows
6. Created derived column: total_amount = final_price × ratings_count
7. Saved cleaned dataset as cleaned_ecommerce_dataset.csv

### Note on Derived Column
The dataset had no quantity column. ratings_count (number of customer ratings) 
was used as a proxy for quantity to calculate total_amount.

### Output
- ecommerce_data_cleaning.ipynb (Jupyter Notebook)
- cleaned_ecommerce_dataset.csv (Cleaned dataset)

### Summary
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

## Assignment 3: SQL Analysis - Subqueries, CTEs, and Window Functions

- Dataset: Superstore Sales Data
- Tools: Python, SQLite, Pandas (Google Colab)
- Notebook: [superstore_sql_analysis.ipynb](./superstore_sql_analysis.ipynb)

### Topics Covered
- Subqueries (above average sales, highest order per customer)
- CTEs (total sales per customer, above average customers)
- Window Functions (RANK, ROW_NUMBER, PARTITION BY)
- Final Combined Query (JOIN + CTE + Window Function)
- Mini Project: Customer Sales Insights (Top 5, Bottom 5, Single order customers)

---

# Assignment 4 — Azure Data Factory Pipeline (Superstore Dataset)

## Objective
Build an end-to-end data pipeline using Azure Data Factory (ADF) to copy 
data from a source location to a destination in Azure Blob Storage, using 
IAM/RBAC for access control — built from zero prior cloud knowledge.

## Tools Used
- Azure Data Factory (ADF)
- Azure Blob Storage
- Azure IAM (Role-Based Access Control)

## Steps Performed

1. **Resource Group** — Created a resource group to organise all Azure 
   resources for this project.
   ![Resource Group](Azure%20screenshots/01-resource-group.png)

2. **Storage Container & Data Upload** — Created a Blob storage container 
   and uploaded the Superstore dataset.
   ![Storage Container Upload](Azure%20screenshots/02-storage-container-upload.png)

3. **ADF Studio Overview** — Opened Azure Data Factory Studio to begin 
   building the pipeline.
   ![ADF Studio Overview](Azure%20screenshots/03-adf-studio-overview.png)

4. **Linked Service** — Configured a linked service connecting ADF to the 
   Blob Storage account.
   ![Linked Service](Azure%20screenshots/04-linked-service.png)

5. **Source Dataset** — Created a dataset pointing to the source file in 
   Blob Storage.
   ![Source Dataset](Azure%20screenshots/05-dataset-source.png)

6. **Destination Dataset** — Created a dataset pointing to the destination 
   location in Blob Storage.
   ![Destination Dataset](Azure%20screenshots/06-dataset-destination.png)

7. **Get Metadata Activity** — Added a Get Metadata activity to read source 
   file properties before copying.
   ![Get Metadata Activity](Azure%20screenshots/07-getmetadata-activity.png)

8. **Pipeline Design** — Combined Get Metadata and Copy activities into a 
   single pipeline.
   ![Pipeline Design](Azure%20screenshots/08-pipeline-design.png)

9. **Pipeline Run — Success** — Triggered the pipeline and confirmed 
   successful execution.
   ![Pipeline Success](Azure%20screenshots/09-pipeline-success.png)

10. **Destination File Copied** — Verified the file was copied to the 
    destination container.
    ![Destination File Copied](Azure%20screenshots/10-destination-file-copied.png)

11. **IAM Roles (RBAC)** — Configured IAM roles to manage access permissions 
    for the storage account.
    ![IAM Roles](Azure%20screenshots/11-iam-roles.png)

## Summary
- Resource group, storage account, and container set up successfully
- ADF pipeline built with linked services, source/destination datasets, 
  Get Metadata and Copy activities
- Pipeline executed successfully; file copied to destination container
- IAM/RBAC roles configured for secure access management

---

## Assignment 5: Apache Spark - Data Cleaning & Aggregation (PySpark)

### Objective
Learn Apache Spark fundamentals and perform data cleaning, transformation, and aggregation using PySpark DataFrames.

### Dataset
Custom-generated dataset (12 rows, 17 columns) covering customer, transaction, and store information. Includes intentional duplicates and null values to demonstrate cleaning operations.

### Steps Performed
1. Created SparkSession and loaded dataset into DataFrame
2. Removed duplicate rows
3. Handled null values (fill/drop strategies)
4. Applied filters (age range, category, region, subscription)
5. Renamed and cast columns (schema transformation)
6. Performed aggregations (count, sum, avg, min, max)
7. Grouped data by category, region, city, store_id
8. Built a final end-to-end pipeline (dedupe → fill nulls → group → aggregate)

### Key Observations
- groupBy operations trigger Shuffle — most expensive part of any Spark pipeline
- Filtering before aggregation improves efficiency
- Null handling before aggregation prevents skewed results

### Tools Used
- Google Colab, PySpark 3.x

### Files
- `spark-assignment/Data/dataset.csv`
- `spark-assignment/Notebook/spark_basics.ipynb`
- `spark-assignment/Output/results.csv`
