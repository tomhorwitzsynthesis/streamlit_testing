import streamlit as st
import pandas as pd
from utils.config import BRAND_NAME_MAPPING
from utils.date_utils import get_selected_date_range
from utils.file_io import load_social_data

POST_TEXT_COLUMNS = ["Post", "post_text", "content"]

def render(selected_platforms=None):
    if selected_platforms is None:
        selected_platforms = ["facebook", "linkedin"]

    st.subheader("🏆 Top Social Media Posts")

    start_date, end_date = get_selected_date_range()

    for platform in selected_platforms:
        st.markdown(f"### {platform.capitalize()}")
        all_posts = []

        for brand_key, brand_display in BRAND_NAME_MAPPING.items():
            df = load_social_data(brand_key, platform)
            if df is None or df.empty or "Published Date" not in df.columns:
                continue

            df = df.dropna(subset=["Published Date"])
            df = df[(df["Published Date"] >= start_date) & (df["Published Date"] <= end_date)]
            if df.empty:
                continue

            post_col = next((col for col in POST_TEXT_COLUMNS if col in df.columns), None)
            if not post_col:
                continue
            
            # Check for URL column - Facebook has both "url" and "input.url"
            url_col =  "url" if "url" in df.columns else None
            if not url_col:
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
                url = row[url_col]
                link = f"[{preview}...]({url})"
                all_posts.append({
                    "Company": brand_display,
                    "Date": row["Published Date"].strftime('%Y-%m-%d'),
                    "Post": link,
                    "Engagement": int(row["Engagement"])
                })

        if not all_posts:
            st.info(f"No {platform.capitalize()} posts found in the selected date range.")
            continue

        df_all = pd.DataFrame(all_posts).sort_values(by="Engagement", ascending=False)

        # Tabs: Overall + each brand
        brand_display_names = list(BRAND_NAME_MAPPING.values())
        tab_labels = ["🌍 Overall"] + [f"🏢 {brand}" for brand in brand_display_names]
        tabs = st.tabs(tab_labels)

        with tabs[0]:
            st.markdown("**Top 5 posts overall**")
            st.markdown(df_all.head(5).to_markdown(index=False), unsafe_allow_html=True)

        for i, brand_display in enumerate(brand_display_names, start=1):
            with tabs[i]:
                brand_df = df_all[df_all["Company"] == brand_display]
                if brand_df.empty:
                    st.info(f"No posts for {brand_display}.")
                else:
                    st.markdown(f"**Top posts for {brand_display}**")
                    st.markdown(brand_df.head(5).to_markdown(index=False), unsafe_allow_html=True)
