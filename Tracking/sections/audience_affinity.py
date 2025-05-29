# sections/audience_affinity.py

import streamlit as st
import pickle
import pandas as pd
from utils.config import BRAND_NAME_MAPPING

def render():

    try:
        with open('Tracking/data/audience_affinity/audience_affinity_outputs.pkl', 'rb') as f:
            affinity_data = pickle.load(f)

        summary_df = affinity_data.get("summary_df")
        gpt_summary = affinity_data.get("gpt_summary")

        if summary_df is None or summary_df.empty:
            st.error("❌ No summary data available.")
            return

        # Apply brand name mapping
        summary_df["Brand"] = summary_df["Brand"].map(
            lambda x: BRAND_NAME_MAPPING.get(x, x)
        )

        # --- Dropdown Selection ---
        view_option = st.selectbox(
            "Select View",
            ["Audience Averages", "Customers & End Users", "Job Seekers & Talent", "Professionals", "Decision Makers & Investors"]
        )

        st.subheader(f"🔍 {view_option} View")

        audience_map = {
            "Customers & End Users": {
                "pct_col": "Customers & End Users_%High",
                "detail_cols": ["Customer_Problem_Solving", "Customer_Clarity_Offerings", "Customer_Innovation"]
            },
            "Job Seekers & Talent": {
                "pct_col": "Job Seekers & Talent_%High",
                "detail_cols": ["Talent_Employer_Branding", "Talent_Career_Growth", "Talent_Market_Impact"]
            },
            "Professionals": {
                "pct_col": "Professionals_%High",
                "detail_cols": ["Pro_Expertise", "Pro_Industry_Relevance", "Pro_Innovation"]
            },
            "Decision Makers & Investors": {
                "pct_col": "Decision Makers & Investors_%High",
                "detail_cols": ["Investor_Long_Term", "Investor_Positioning", "Investor_Market_Influence"]
            }
        }

        if view_option == "Audience Averages":
            cols_to_show = [col for col in summary_df.columns if col.endswith("_%High")]
            display_df = summary_df[["Brand"] + cols_to_show].copy()
        else:
            mapping = audience_map.get(view_option, {})
            pct_col = mapping.get("pct_col")
            detail_cols = mapping.get("detail_cols", [])
            cols_to_show = [pct_col] + detail_cols
            display_df = summary_df[["Brand"] + cols_to_show].copy()
            display_df = display_df.rename(columns={pct_col: "Audience %High"})

        st.dataframe(display_df.set_index("Brand"), use_container_width=True)

        # GPT Summary
        if gpt_summary:
            st.markdown("---")
            st.subheader("🧠 Summary")
            st.markdown(gpt_summary)

    except Exception as e:
        st.error("🚨 Failed to load audience affinity data.")
        st.exception(e)
