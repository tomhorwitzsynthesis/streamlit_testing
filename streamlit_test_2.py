import streamlit as st
import pandas as pd
import plotly.express as px

# Load data
@st.cache_data
def load_data():
    xls = pd.ExcelFile("test_data.xlsx")
    positivity_df = pd.read_excel(xls, sheet_name="Positivity")
    mentions_df = pd.read_excel(xls, sheet_name="Mentions")
    
    # Rename duplicate 'Positive' column to 'Negative'
    positivity_df.columns = ["Company", "Positive", "Neutral", "Negative"]
    
    return positivity_df, mentions_df

# Load the data
positivity_df, mentions_df = load_data()

# Streamlit layout
st.title("Company Sentiment & Mentions Dashboard")

# Bar Chart for Positivity
st.subheader("Sentiment Distribution per Company")
fig_bar = px.bar(
    positivity_df,
    x="Company",
    y=["Positive", "Neutral", "Negative"],
    title="Company Sentiment Analysis",
    barmode="group",
    labels={"value": "Count", "variable": "Sentiment"},
)
st.plotly_chart(fig_bar)

# Pie Chart for Mentions
st.subheader("Mentions Distribution")
fig_pie = px.pie(
    mentions_df,
    names="Company",
    values="Mentions",
    title="Mentions per Company",
)
st.plotly_chart(fig_pie)

st.write("Data source: text_data.xlsx")
