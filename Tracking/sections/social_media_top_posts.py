import streamlit as st
import pandas as pd
from utils.config import BRANDS
from utils.date_utils import get_selected_date_range
from utils.file_io import load_social_data

POST_TEXT_COLUMNS = ["Post", "post_text"]

def render(selected_platforms=None):
    if selected_platforms is None:
        selected_platforms = ["facebook", "linkedin"]

    st.subheader("🏆 Top Social Media Posts")

    start_date, end_date = get_selected_date_range()

    for platform in selected_platforms:
        st.markdown(f"### {platform.capitalize()}")
        all_posts = []

        for brand in BRANDS:
            df = load_social_data(brand, platform)
            if df is None or df.empty or "Published Date" not in df.columns:
                continue

            df = df.dropna(subset=["Published Date"])
            df = df[(df["Published Date"] >= start_date) & (df["Published Date"] <= end_date)]
            if df.empty:
                continue

            post_col = next((col for col in POST_TEXT_COLUMNS if col in df.columns), None)
            if not post_col or "input.url" not in df.columns:
                continue

            # Compute engagement
            if platform == "facebook":
                df["Engagement"] = (
                    df.get("likes", 0).fillna(0) +
                    df.get("num_comments", 0).fillna(0) * 3 +
                    df.get("num_shares", 0).fillna(0) * 5
                )
            elif platform == "linkedin":
                df["Engagement"] = (
                    df.get("num_likes", 0).fillna(0) +
                    df.get("num_comments", 0).fillna(0) * 3
                )
            else:
                continue

            df = df[df["Engagement"] > 0]
            if df.empty:
                continue

            for _, row in df.iterrows():
                preview = str(row[post_col])[:30].replace("\n", " ").strip()
                url = row["input.url"]
                link = f"[{preview}...]({url})"
                all_posts.append({
                    "Company": brand,
                    "Date": row["Published Date"].strftime('%Y-%m-%d'),
                    "Post": link,
                    "Engagement": int(row["Engagement"])
                })

        if not all_posts:
            st.info(f"No {platform.capitalize()} posts found in the selected date range.")
            continue

        df_all = pd.DataFrame(all_posts).sort_values(by="Engagement", ascending=False)

        # Tabs: Overall + each brand
        tab_labels = ["🌍 Overall"] + [f"🏢 {brand}" for brand in BRANDS]
        tabs = st.tabs(tab_labels)

        with tabs[0]:
            st.markdown("**Top 5 posts overall**")
            st.markdown(df_all.head(5).to_markdown(index=False), unsafe_allow_html=True)

        for i, brand in enumerate(BRANDS, start=1):
            with tabs[i]:
                brand_df = df_all[df_all["Company"] == brand]
                if brand_df.empty:
                    st.info(f"No posts for {brand}.")
                else:
                    st.markdown(f"**Top posts for {brand}**")
                    st.markdown(brand_df.head(5).to_markdown(index=False), unsafe_allow_html=True)
