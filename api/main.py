import dash
from dash import dcc, html, Output, Input
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
import requests
import json

# MongoDB connection
client = MongoClient("mongodb://admin:admin@localhost:27017/")
db = client["bigdata"]
collection = db["job_listings"]

# Druid SQL endpoint
DRUID_SQL_URL = "http://localhost:9999/druid/v2/sql/"

def get_data():
    # Only fetch documents with full structured fields
    query = {
        "Company": {"$exists": True},
        "Company_Rating": {"$exists": True},
        "Job_Title": {"$exists": True},
        "Location": {"$exists": True},
        "Date_Posted": {"$exists": True},
        "Min_Salary": {"$exists": True},
        "Max_Salary": {"$exists": True},
        "Salary_Source": {"$exists": True}
    }
    cursor = collection.find(query, {"_id": 0})
    df = pd.DataFrame(list(cursor))
    return df

def get_trending_jobs():
    sql_query = """
        SELECT "position_title", COUNT(*) AS cnt
        FROM "input-topic"
        WHERE "__time" >= CURRENT_TIMESTAMP - INTERVAL '1' HOUR
          AND "position_title" IS NOT NULL
        GROUP BY "position_title"
        ORDER BY cnt DESC
        LIMIT 10
    """
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(DRUID_SQL_URL, headers=headers, data=json.dumps({"query": sql_query}))
        response.raise_for_status()
        result = response.json()
        if result:
            df = pd.DataFrame(result)
            return df
    except Exception as e:
        print(f"Error fetching trending jobs from Druid: {e}")
    return pd.DataFrame()  # empty on error or no data

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Job Listings Dashboard"

# Batch Charts
def company_chart(df):
    company_counts = df["Company"].value_counts().reset_index()
    company_counts.columns = ['Company', 'Count']
    fig = px.bar(company_counts, x='Company', y='Count', title="Jobs by Company")
    return dcc.Graph(figure=fig)

def location_chart(df):
    location_counts = df["Location"].value_counts().reset_index()
    location_counts.columns = ['Location', 'Count']
    fig = px.bar(location_counts, x="Location", y="Count",
                 labels={"Location": "Location", "Count": "Number of Jobs"},
                 title="Number of Job Listings by Location")
    return dcc.Graph(figure=fig)

def time_chart(df):
    if "Date_Posted" in df.columns:
        df["Date_Posted"] = pd.to_datetime(df["Date_Posted"])
        df["Date"] = df["Date_Posted"].dt.date
        counts = df["Date"].value_counts().sort_index().reset_index()
        counts.columns = ["Date", "Job Postings"]
        fig = px.line(counts, x="Date", y="Job Postings", title="Job Postings Over Time")
        return dcc.Graph(figure=fig)
    return html.Div("No Date_Posted data available")

# Stream Chart (Trending Jobs Pie)
def trending_jobs_chart():
    df = get_trending_jobs()
    if not df.empty:
        fig = px.pie(df, names="position_title", values="cnt", title="Top 10 Trending Jobs (Last Hour)")
        return dcc.Graph(figure=fig)
    else:
        return html.Div("No trending jobs data available.")

# Layout
app.layout = dbc.Container([
    html.H1("Job Listings Dashboard", className="text-center mt-4 mb-4"),

    dbc.Row(
        dbc.Col([
            dbc.Label("Select View:", className="fw-bold"),
            dbc.Checklist(
                options=[
                    {"label": "Hot Jobs NOW 🔥", "value": "stream"},
                ],
                value=[],  # default Batch mode (unchecked)
                id="view-toggle-switch",
                switch=True,
                inline=True,
                inputStyle={"cursor": "pointer"},
                labelStyle={"cursor": "pointer", "fontWeight": "bold", "fontSize": "1.1rem"},
            )
        ], width="auto"), justify="center", className="mb-4"
    ),

    html.Div(id="content-area"),

    dcc.Interval(id='interval-component', interval=60*1000, n_intervals=0, disabled=True)
], fluid=True)

@app.callback(
    Output("content-area", "children"),
    Output("interval-component", "disabled"),
    Input("view-toggle-switch", "value"),
    Input('interval-component', 'n_intervals')
)
def render_content(toggle_value, n_intervals):
    if "stream" in toggle_value:
        return trending_jobs_chart(), False
    else:
        df = get_data()
        tabs = dbc.Tabs([
            dbc.Tab(label="By Company", children=[company_chart(df)]),
            dbc.Tab(label="By Location", children=[location_chart(df)]),
            dbc.Tab(label="Postings Over Time", children=[time_chart(df)]),
        ])
        return tabs, True

if __name__ == "__main__":
    app.run(debug=True)
