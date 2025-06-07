from fastapi import FastAPI, Query
from pymongo import MongoClient
from typing import List

app = FastAPI()

client = MongoClient("mongodb://admin:admin@localhost:27017/")
db = client["bigdata"]
collection = db["job_listings"]

@app.get("/jobs")
def get_jobs(
    company: str = Query(None),
    location: str = Query(None),
    min_salary: int = Query(None)
):
    query = {}
    if company:
        query["Company"] = company
    if location:
        query["Location"] = location
    if min_salary:
        query["Min_Salary"] = {"$gte": min_salary}
    
    jobs = list(collection.find(query, {"_id": 0}))  # Exclude _id
    return jobs
