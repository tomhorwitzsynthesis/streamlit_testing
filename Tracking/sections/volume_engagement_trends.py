import streamlit as st
import pandas as pd
import plotly.express as px
from utils.config import BRANDS
from utils.date_utils import get_selected_date_range
from utils.file_io import load_social_data

PLATFORMS = ["facebook", "linkedin"]

def render(selected_platforms=None):
    st.subheader("📈 Social Media Volume & Engagement Trends")

    start_date, end_date = get_selected_date_range()
    months = pd.date_range(start=start_date, end=end_date, freq="MS")
    month_labels = [m.strftime('%b %Y') for m in months]

    for platform in selected_platforms:
        st.markdown(f"### {platform.capitalize()}")

        combined_data = {
            "Month": [],
            "Company": [],
            "Volume": [],
            "Engagement": [],
            "Engagement_Per_Follower": []
        }

        for brand in BRANDS:
            df = load_social_data(brand, platform)
            if df is None or df.empty or "Published Date" not in df.columns:
                continue

            df = df.dropna(subset=["Published Date"])
            df = df[(df["Published Date"] >= start_date) & (df["Published Date"] <= end_date)]
            if df.empty:
                continue

            df["Month"] = df["Published Date"].dt.to_period("M")

            for month in months:
                period = month.to_period("M")
                month_df = df[df["Month"] == period]
                if month_df.empty:
                    continue

                volume = len(month_df)

                if platform == "facebook":
                    engagement = (
                        month_df.get("likes", pd.Series(0)).sum() +
                        month_df.get("num_comments", pd.Series(0)).sum() * 3 +
                        month_df.get("num_shares", pd.Series(0)).sum() * 5
                    )
                    followers = month_df.get("page_followers", pd.Series()).dropna()
                else:  # LinkedIn
                    engagement = (
                        month_df.get("num_likes", pd.Series(0)).sum() +
                        month_df.get("num_comments", pd.Series(0)).sum() * 3
                    )
                    followers = month_df.get("user_followers", pd.Series()).dropna()

                follower_count = followers.iloc[-1] if not followers.empty else 0
                engagement_per_follower = engagement / follower_count if follower_count > 0 else 0

                combined_data["Month"].append(month.strftime('%b %Y'))
                combined_data["Company"].append(brand)
                combined_data["Volume"].append(volume)
                combined_data["Engagement"].append(engagement)
                combined_data["Engagement_Per_Follower"].append(engagement_per_follower)

        if not combined_data["Month"]:
            st.info(f"No {platform.capitalize()} data found.")
            continue

        df_combined = pd.DataFrame(combined_data)

        tab1, tab2, tab3 = st.tabs(["📊 Volume", "🔥 Engagement", "📈 Engagement Per Follower"])

        with tab1:
            fig_volume = px.line(
                df_combined,
                x="Month",
                y="Volume",
                color="Company",
                markers=True,
                title=f"{platform.capitalize()} - Monthly Post Volume"
            )
            fig_volume.update_layout(xaxis=dict(categoryorder="array", categoryarray=month_labels))
            st.plotly_chart(fig_volume, use_container_width=True)

        with tab2:
            fig_engagement = px.line(
                df_combined,
                x="Month",
                y="Engagement",
                color="Company",
                markers=True,
                title=f"{platform.capitalize()} - Monthly Engagement Trend"
            )
            fig_engagement.update_layout(xaxis=dict(categoryorder="array", categoryarray=month_labels))
            st.plotly_chart(fig_engagement, use_container_width=True)

        with tab3:
            fig_epf = px.line(
                df_combined,
                x="Month",
                y="Engagement_Per_Follower",
                color="Company",
                markers=True,
                title=f"{platform.capitalize()} - Engagement per Follower"
            )
            fig_epf.update_layout(xaxis=dict(categoryorder="array", categoryarray=month_labels))
            st.plotly_chart(fig_epf, use_container_width=True)
