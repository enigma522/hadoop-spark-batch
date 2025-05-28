from pyspark.sql import SparkSession
from pyspark.sql.functions import col, regexp_replace, trim, expr
from pyspark.sql.types import StructType, StructField, StringType, FloatType

spark = SparkSession.builder \
    .appName("Job Listings Data Cleaning") \
    .config("spark.jars", "/opt/spark-job/lib/postgresql-42.7.5.jar") \
    .getOrCreate()

schema = StructType([
    StructField("Company", StringType(), True),
    StructField("Company_Score", FloatType(), True),
    StructField("Job_Title", StringType(), True),
    StructField("Location", StringType(), True),
    StructField("Date", StringType(), True),
    StructField("Salary", StringType(), True)
])


df = spark.read.format("csv") \
    .option("header", "true") \
    .schema(schema) \
    .load("/opt/spark-job/data/job_data.csv")


# Step 1: Clean and prepare original columns
cleaned_df = df \
    .withColumn("Company", trim(regexp_replace(col("Company"), "\"", ""))) \
    .withColumn("Job_Title", trim(col("Job_Title"))) \
    .withColumn("Location", trim(regexp_replace(col("Location"), "\"", ""))) \
    .withColumn("Salary", regexp_replace(col("Salary"), "[\\xa0\\u00a0]", " "))  # remove non-breaking spaces

# Step 2: Extract and parse dates properly
cleaned_df = cleaned_df.withColumn(
    "Date_Posted",
    expr("""
        CASE
            WHEN Date RLIKE '^[0-9]+d$' THEN date_sub(current_date(), CAST(regexp_replace(Date, 'd', '') AS INT))
            WHEN Date RLIKE '30d\\+' THEN date_sub(current_date(), 30)
            ELSE NULL
        END
    """)
)



cleaned_df = cleaned_df \
    .withColumn(
        "Min_Salary",
        expr("REGEXP_EXTRACT(Salary, r'\\$(\\d+)K - \\$\\d+K.*', 1)")
    ) \
    .withColumn(
        "Max_Salary",
        expr("REGEXP_EXTRACT(Salary, r'\\$\\d+K - \\$(\\d+)K.*', 1)")
    )

# Step 4: Salary Source Extraction
cleaned_df = cleaned_df.withColumn(
    "Salary_Source",
    expr("""
        CASE
            WHEN Salary LIKE '%Employer est.%' THEN 'Employer Estimate'
            WHEN Salary LIKE '%Glassdoor est.%' THEN 'Glassdoor Estimate'
            ELSE 'Other'
        END
    """)
)

# Step 5: Rename and drop
cleaned_df = cleaned_df \
    .drop("Date", "Salary") \
    .withColumnRenamed("Company_Score", "Company_Rating")

# Step 6: Debug log: Show intermediate results
cleaned_df.select(
    "Company", "Job_Title", "Location", "Date_Posted", 
    "Min_Salary", "Max_Salary", "Salary_Source"
).show(truncate=False)

# Optional: Schema check
cleaned_df.printSchema()
