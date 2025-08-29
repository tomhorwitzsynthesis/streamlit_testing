import streamlit as st
import pandas as pd
import os
from utils.config import DATA_ROOT  # <-- import here

TOPIC_INSIGHTS_PATH = os.path.join(DATA_ROOT, "agility", "topic_insights.xlsx")

def load_topic_insights():
    if not os.path.exists(TOPIC_INSIGHTS_PATH):
        st.error("topic_insights.xlsx not found in agility folder.")
        return None
    try:
        df = pd.read_excel(TOPIC_INSIGHTS_PATH)
        return df
    except Exception as e:
        st.error(f"Error loading topic_insights.xlsx: {e}")
        return None

def render() -> None:
    st.subheader("🧠 Key Communication Topics with Examples")
    st.info("This section has been disabled per request.")
