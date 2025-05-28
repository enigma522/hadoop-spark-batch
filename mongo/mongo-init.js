db = db.getSiblingDB('bigdata'); // switch to your DB

db.createCollection('job_listings');

// Optional: insert a dummy record to test
db.job_listings.insertOne({
  title: "Software Engineer",
  company: "Example Corp",
  location: "Remote",
  posted_at: new Date()
});
