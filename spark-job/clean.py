from pyspark.sql import SparkSession
from pyspark.sql.functions import col, regexp_replace, trim, expr
from pyspark.sql.types import StructType, StructField, StringType, FloatType



spark = SparkSession.builder \
    .appName("Job Listings Data Cleaning") \
    .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.4.1") \
    .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:8020") \
    .config("spark.mongodb.write.connection.uri", "mongodb://admin:admin@mongodb:27017/bigdata?authSource=admin") \
    .config("spark.mongodb.write.database", "bigdata") \
    .config("spark.mongodb.write.collection", "job_listings") \
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
    .load("hdfs://namenode:8020/data/job_data.csv")

cleaned_df = df \
    .withColumn("Company", trim(col("Company"))) \
    .withColumn("Company", regexp_replace(col("Company"), "\"", "")) \
    .withColumn("Job_Title", trim(col("Job_Title"))) \
    .withColumn("Location", trim(col("Location"))) \
    .withColumn("Location", regexp_replace(col("Location"), "\"", "")) \
    .withColumn("Date_Posted", 
                expr("CASE " +
                     "WHEN Date LIKE '%d' THEN date_sub(current_date(), cast(regexp_replace(Date, 'd', '') as int)) " +
                     "WHEN Date LIKE '%30d+%' THEN date_sub(current_date(), 30) " +
                     "ELSE null END")) \
    .withColumn("Min_Salary", 
        expr("CAST(REGEXP_EXTRACT(Salary, r'\\$(\\d+)K', 1) AS INT) * 1000")) \
    .withColumn("Max_Salary", 
        expr("CAST(REGEXP_EXTRACT(Salary, r'- \\$(\\d+)K', 1) AS INT) * 1000")) \
    .withColumn("Salary_Source", 
            expr("CASE " +
                 "WHEN Salary LIKE '%Employer est.%' THEN 'Employer Estimate' " +
                 "WHEN Salary LIKE '%Glassdoor est.%' THEN 'Glassdoor Estimate' " +
                 "ELSE 'Other' END")) \
    .drop("Date", "Salary") \
    .withColumnRenamed("Company_Score", "Company_Rating")

cleaned_df.write \
    .format("mongodb") \
    .mode("append") \
    .save()

print("Data has been cleaned and saved to MongoDB")