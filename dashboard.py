import pandas as pd
import dash
from dash import dcc, html
import dash_table
import plotly.express as px

# === Load and preprocess giving data ===
giving_df = pd.read_csv("laf_email data 4.19.2025-5.2.2025.CSV")
giving_df['Lifetime Giving'] = giving_df['Lifetime Giving'].replace('[\$,]', '', regex=True).astype(float)
giving_df['Assigned Appeal ID'] = giving_df['Assigned Appeal ID'].astype(str).str.strip()
giving_df['Appeal Date'] = giving_df['Assigned Appeal Description'].str.extract(r'(\d{8})$')
giving_df['Appeal Date'] = pd.to_datetime(giving_df['Appeal Date'], format='%Y%m%d', errors='coerce')
giving_df = giving_df.dropna(subset=['Age', 'Lifetime Giving', 'Appeal Date'])
giving_df = giving_df[(giving_df['Appeal Date'] >= "2025-04-19") & (giving_df['Appeal Date'] <= "2025-05-02")]

# Apply age groups based on click data bins
age_bins = [0, 19, 31, 41, 51, 61, 71, 150]
age_labels = ['0-18', '19-30', '31-40', '41-50', '51-60', '61-70', '70+']
giving_df['Age Group'] = pd.cut(giving_df['Age'], bins=age_bins, labels=age_labels, right=False)

# === Load and preprocess click data ===
click_df = pd.read_csv("data/athletic giving week report.csv")
click_df.columns = click_df.columns.str.strip()
click_df['Assigned Appeal ID'] = click_df['Assigned Appeal ID'].astype(str).str.strip()

# === Merge datasets on Assigned Appeal ID ===
combined_df = pd.merge(giving_df, click_df, on='Assigned Appeal ID', how='inner')
combined_df = combined_df.dropna(subset=['Sport', 'Age Group', 'Subject Line'])

# === Group by Sport, Age Group, and Subject Line ===
grouped_df = (
    combined_df.groupby(['Sport', 'Age Group', 'Subject Line'], observed=True)['Lifetime Giving']
    .sum()
    .reset_index()
)

# === Dash App ===
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("Giving by Sport, Age Group, and Subject Line", style={'textAlign': 'center'}),
    html.Br(),

    dash_table.DataTable(
        id='sport-age-subject-table',
        columns=[
            {"name": "Sport", "id": "Sport"},
            {"name": "Age Group", "id": "Age Group"},
            {"name": "Subject Line", "id": "Subject Line"},
            {"name": "Total Giving", "id": "Lifetime Giving"}
        ],
        data=grouped_df.to_dict('records'),
        style_table={'overflowX': 'auto'},
        style_cell={'padding': '10px', 'textAlign': 'center'},
        style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'}
    ),

    html.Br(),

    dcc.Graph(
        id='sport-age-subject-bar',
        figure=px.bar(
            grouped_df,
            x='Age Group',
            y='Lifetime Giving',
            color='Subject Line',
            facet_col='Sport',
            barmode='group',
            title='Total Giving by Sport, Age Group, and Subject Line',
            labels={"Lifetime Giving": "Total Giving ($)"}
        )
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
