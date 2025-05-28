-- ./postgres/init.sql
CREATE TABLE IF NOT EXISTS job_listings (
    id SERIAL PRIMARY KEY,
    company VARCHAR(255),
    score FLOAT,
    title VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(10),
    days_ago INT,
    salary_min INT,
    salary_max INT,
    source VARCHAR(50)
);
