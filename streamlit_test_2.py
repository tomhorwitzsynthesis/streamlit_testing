import streamlit as st
import pandas as pd
import plotly.express as px

import hmac


def check_password():
    """Returns `True` if the user had a correct password."""

    def login_form():
        """Form with widgets to collect user information"""
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username"] in st.secrets[
            "passwords"
        ] and hmac.compare_digest(
            st.session_state["password"],
            st.secrets.passwords[st.session_state["username"]],
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the username or password.
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    # Return True if the username + password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show inputs for username + password.
    login_form()
    if "password_correct" in st.session_state:
        st.error("😕 User not known or password incorrect")
    return False


if not check_password():
    st.stop()


if not check_password():
    st.stop()  # Do not continue if check_password is not True.

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
