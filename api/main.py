import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://admin:admin@localhost:27017/")
db = client["bigdata"]
collection = db["job_listings"]

# Fetch data from MongoDB and convert to DataFrame
def get_data():
    cursor = collection.find({}, {"_id": 0})
    df = pd.DataFrame(list(cursor))
    return df

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Job Listings Dashboard"

# Charts
def company_chart(df):
    company_counts = df["company"].value_counts().reset_index()
    company_counts.columns = ['company', 'count']
    fig = px.bar(company_counts, x='company', y='count', title="Jobs by Company")
    return dcc.Graph(figure=fig)

def location_chart(df):
    location_counts = df["location"].value_counts().reset_index()
    location_counts.columns = ['location', 'count']
    fig = px.bar(location_counts,
                 x="location", y="count",
                 labels={"location": "Location", "count": "Number of Jobs"},
                 title="Number of Job Listings by Location")
    return dcc.Graph(figure=fig)

def time_chart(df):
    if "posted_at" in df.columns:
        df["posted_at"] = pd.to_datetime(df["posted_at"])
        df["date"] = df["posted_at"].dt.date
        counts = df["date"].value_counts().sort_index().reset_index()
        counts.columns = ["Date", "Job Postings"]
        fig = px.line(counts, x="Date", y="Job Postings", title="Job Postings Over Time")
        return dcc.Graph(figure=fig)
    return html.Div("No posted_at data available")

# Layout
app.layout = dbc.Container([
    html.H1("Job Listings Dashboard", className="text-center mt-4 mb-4"),
    dbc.Tabs([
        dbc.Tab(label="By Company", children=[company_chart(get_data())]),
        dbc.Tab(label="By Location", children=[location_chart(get_data())]),
        dbc.Tab(label="Postings Over Time", children=[time_chart(get_data())]),
    ])
], fluid=True)

if __name__ == "__main__":
    app.run(debug=True)
