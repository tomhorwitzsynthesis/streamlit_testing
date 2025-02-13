import streamlit as st
import pandas as pd
import plotly.express as px
import hmac

st.set_page_config(layout="wide")

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False


if not check_password():
    st.stop()  # Do not continue if check_password is not True.

# Function to load data
@st.cache_data
def load_data():
    xls = pd.ExcelFile("Biovela/streamlit_data.xlsx")
    sheets = xls.sheet_names
    data = {sheet: pd.read_excel(xls, sheet_name=sheet) for sheet in sheets}
    return data

# Load data
data = load_data()

# Streamlit App Layout
st.title("Biovela Survey Results By Brand")

# Streamlit header
st.header("Data grouped by buying sliced meat from this brand most often (Question S20_1)")

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

    # Debugging: Show transformed data
    #st.subheader("Debugging: Transformed Data")
    #st.write(df_melted.head())  # Show first few rows of the transformed data
    
    # Ensure Percentage is numerical and remove NaN values
    df_melted.dropna(inplace=True)
    df_melted["Percentage"] = pd.to_numeric(df_melted["Percentage"], errors="coerce")
    df_melted["Percentage"] = df_melted["Percentage"] * 100

    # Debugging: Check if dataframe is empty
    if df_melted.empty:
        st.error("Error: No data available for visualization. Please check the dataset.")
    else:
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

        # Move legend to the top and remove the legend title
        fig.update_layout(
            legend=dict(
                orientation="h",  # Horizontal legend
                yanchor="bottom",  # Align to bottom
                y=1.02,  # Position slightly above the chart
                xanchor="center",  # Center align
                x=0.5  # Center horizontally
            ),
            legend_title_text=""  # Remove legend title
        )

        # Display chart
        st.plotly_chart(fig, use_container_width=True)

st.write("Source: streamlit_data.xlsx")
