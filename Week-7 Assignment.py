# Databricks notebook source


# CSV DATA LOADING

df = spark.read.format('csv').option('inferschema', True)\
    .option('header',True)\
        .load("/Volumes/workspace/default/csv_dataset")

df.display()

# COMMAND ----------

df.printSchema()

# DATA CLEANING
#HANDLE NULLS
# Check number of rows before removing null values

print("Rows before removing null values:", df.count())

# Remove rows containing null values
df = df.dropna()

# Check number of rows after removing null values
print("Rows after removing null values:", df.count())

# REMOVE DUPLICATES

print("Before:",df.count())

df = df.dropDuplicates()

print("After:",df.count())

# DELTA TABLE
# CONVERT INTO DELTA TABLE
# Rename columns to remove spaces for Delta compatibility

from pyspark.sql.functions import col
df_filter = df.select([col(c).alias(c.replace(" ", "_")) for c in df.columns])

df_filter.write.format("delta") \
.mode("overwrite") \
.saveAsTable("workspace.default.delta_data")

# LOAD DELTA TABLE

delta_df=spark.read.format("delta")\
.table("workspace.default.delta_data")

delta_df.display()

# INCREMNETAL/NEW DATASET
# CREATE INCREMNETAL DATASET

incremental_df=df.limit(10)
incremental_df.display()

# MODIFY INCREMNETAL RECORD

from pyspark.sql.functions import col
incremental_df=incremental_df.withColumn(
    "Profit",
    col("Profit").cast("double") * 2
)
incremental_df.display()

# ADD NEW RECORD

new_record = spark.createDataFrame([
(99999,"CA-99999","2024-01-01","2024-01-05","Second Class",
"CUST999","Shrishti","Consumer","India","Jaipur","Rajasthan",302001,"Central","OFF001",
"Office Supplies","Binders","Notebook","5000.0","2","0.1",1200.0)
],df.schema)
incremental_df=incremental_df.union(new_record)
display(incremental_df)


# SAVE INCREMNETAL DATASET

from pyspark.sql.functions import col
incremental_df_clean = incremental_df.select([col(c).alias(c.replace(" ", "_")) for c in incremental_df.columns])

incremental_df_clean.write.format("delta")\
.mode("overwrite")\
.saveAsTable("workspace.default.incremental_delta")

# LOAD INCREMNETAL DATASET

incremental_df=spark.read.format("delta")\
.table("workspace.default.incremental_delta")

incremental_df.display()

# MERGE OPEARTION


from delta.tables import DeltaTable

# Load Delta Table
delta_table = DeltaTable.forName(
    spark,
    "workspace.default.delta_data"
)


incremental_df_dedup = incremental_df.dropDuplicates(["Order_ID"])
delta_table.alias("target") \
.merge(incremental_df_dedup.alias("source"),"target.Order_ID = source.Order_ID") \
.whenMatchedUpdate(
    set={
        "Sales": "source.Sales",
        "Profit": "source.Profit"
    }) \
.whenNotMatchedInsert(
    values={
        "Order_ID": "source.Order_ID",
        "Sales": "source.Sales",
        "Profit": "source.Profit"
    }) \
.execute()

# MERGE RESULTS

final_df = spark.read.table("workspace.default.delta_data")

display(final_df)



print("before merge",incremental_df.count())

print("merged dataset",final_df.count())

# VALIDATION
# ROW COUNT

print("Original Dataset Rows :", df.count())
print("Incremental Dataset Rows :", incremental_df.count())
print("Final Dataset Rows :", final_df.count())
print("New Rows Inserted :", final_df.count() - df.count())

# CHECK DUPLICATES

from pyspark.sql.functions import col, count

final_df.groupBy("Order_ID").count().filter(col("count") > 1).display()

# FINAL OUTPUT

final_df.printSchema()