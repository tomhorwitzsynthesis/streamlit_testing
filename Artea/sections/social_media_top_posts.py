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

    # Key takeaways for both platforms
    st.markdown("""
### 📌 Key Takeaways

**Facebook = spectacle + urgency**  
Contests, sports, and fraud alerts drive the highest engagement. Banks that tailor their content to excitement, national pride, and urgent warnings outperform those using purely educational or product-driven posts.

**LinkedIn = identity + credibility**  
Culture, rebrands, leadership, and values-focused posts resonate most. Banks succeed by humanizing themselves and sharing internal recognition, while hard business insights attract a narrower audience.
""")

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
            
            url_col =  "url" if "url" in df.columns else None
            if not url_col:
                continue

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

        st.markdown("---")
        if platform == "facebook":
            st.markdown("""
### 📊 Facebook Content Summary
                
#### Content of the top 5 posts for each bank

**Citadele & Swedbank**
- Contests and giveaways dominate (ticket draws, prizes, sports tie-ins).
- Sports sponsorships (basketball in particular) provide a strong emotional hook.
- Posts lean into excitement, emojis, and a celebratory tone.

**SEB & Artea**
- Fraud/security alerts attract high interaction — practical, widely relevant, and shareable.
- Surveys or data points on consumer behavior also spark interest when made relatable.

**Luminor**
- Attempts at engagement through webinars, financial education, or lifestyle tie-ins perform more modestly.
- The themes are useful but lack the immediate emotional payoff of contests or security alerts.

**Overall:**
- High-arousal content works best: competitions, national pride, and urgent warnings.
- Purely educational or product-driven posts struggle unless wrapped in lifestyle relevance.

**Cross-Bank Themes**
- Entertainment, urgency, and fun win.
- Contests and sports are the universal currency.
- Fraud/security alerts are the only serious theme that reliably breaks through.
""")
        elif platform == "linkedin":
            st.markdown("""
### 📊 LinkedIn Content Summary
                        
#### Content of the top 5 posts for each bank

**SEB & Swedbank**
- Employee culture and recognition posts (team events, awards, new hires) resonate strongly.
- Leadership and organizational changes (e.g., CEO announcements) also generate traction.
- These banks lean on LinkedIn as a brand/culture stage.

**Artea**
- Rebranding and identity-building is a winning theme — novelty and narrative matter.
- Values-based posts (e.g., solidarity with Ukraine) also gain visibility.

**Citadele**
- Focuses on thought-leadership (economic outlook, AI, leadership trends).
- While more niche in reach, it positions the brand as serious and analytical.

**Luminor**
- Engagement comes from light office culture and CSR/entrepreneurship programs.
- More human, but less differentiated compared to SEB/Swedbank.

**Overall:**
- Culture and identity posts dominate (internal recognition, rebrands, value-driven messages).
- Thought-leadership works, but it attracts a narrower, more specialized audience.

**Cross-Bank Themes**
- Banks succeed by humanizing themselves — employees, culture, values, brand identity.
- Hard business insights (Citadele’s angle) stand out as distinctive, but they do not maximize broad engagement.

**Key Takeaway**
- **LinkedIn = identity + credibility** (culture, rebrands, leadership, values).
- Banks that tailor their content to the emotional logic of LinkedIn outperform those trying to force one style across both.
""")
