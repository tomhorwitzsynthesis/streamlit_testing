import streamlit as st
import pandas as pd
import plotly.express as px

# Function to load data
@st.cache_data
def load_data():
    xls = pd.ExcelFile("streamlit_data.xlsx")
    sheets = xls.sheet_names
    data = {sheet: pd.read_excel(xls, sheet_name=sheet) for sheet in sheets}
    return data

# Load data
data = load_data()

# Streamlit App Layout
st.title("Biovela Survey Results")

# Dropdown to select sheet
selected_sheet = st.selectbox("Select a sheet to view:", list(data.keys()))

# Dropdown to select visualization type
visualization = st.radio("Select visualization type:", ["Bar Chart", "Table"])

# Load selected sheet
df = data[selected_sheet].copy()

# Rename first column to 'Category' (for better readability)
df.rename(columns={df.columns[0]: "Category"}, inplace=True)

# Identify brand columns (excluding the first column, which contains categories)
brand_cols = df.columns[1:]

# Display as Table
if visualization == "Table":
    df[brand_cols] = df[brand_cols].applymap(lambda x: f"{x:.2%}" if isinstance(x, (int, float)) else x)
    st.dataframe(df, use_container_width=True)

# Display as Bar Chart
elif visualization == "Bar Chart":
    # Melt dataframe to long format (for visualization)
    df_melted = df.melt(id_vars=["Category"], var_name="Brand", value_name="Percentage")

    # Create grouped bar chart
    fig = px.bar(
        df_melted, 
        x="Brand", 
        y="Percentage", 
        color="Category",  # Each category gets a different color
        barmode="group",
        title=f"Brand Preference by Category ({selected_sheet})",
        labels={"Percentage": "Percentage (%)"},
    )
    st.plotly_chart(fig, use_container_width=True)

st.write("Source: streamlit_data.xlsx")
