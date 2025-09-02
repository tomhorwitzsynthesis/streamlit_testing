import streamlit as st
from utils.date_utils import init_month_selector

# --- Section Imports ---
from sections.compos_matrix import render as render_matrix
from sections.sentiment_analysis import render as render_sentiment
from sections.topical_analysis import render as render_topics
from sections.volume_trends import render as render_volume
from sections.media_coverage import render as render_media_shares
from sections.top_3_archetypes import render_top_3_archetypes

from sections.volume_engagement_trends import render as render_social_trends
from sections.social_media_top_posts import render as render_top_posts

from sections.content_pillars import render as render_content_pillars

from sections.audience_affinity import render as render_audience_affinity
from sections.ads_dashboard import render as render_ads_dashboard
from sections.pr_ranking import render as render_pr_ranking
from sections.social_media_ranking import render as render_social_media_ranking

#from sections.content_pillar_analysis import render as render_pillars  # If implemented
# from sections.audience_affinity import render as render_affinity     # Optional

# --- Sidebar ---
st.sidebar.title("📁 Navigation")
section = st.sidebar.radio("Go to", [
    "Press Releases",
    "Social Media",
    "Audience Affinity",
    "Content Pillars"
])

# --- Month Filter ---
init_month_selector()  # Sets start_date / end_date globally

# --- Section Routing ---
if section == "Press Releases":
    st.title("📰 Press Release Dashboard")
    render_matrix()
    render_pr_ranking()
    # Top 3 Archetypes for PR (tabs per brand)
    st.markdown("### Top 3 Archetypes (PR)")
    pr_brands = ["Kauno grudai", "Acme grupe", "Ignitis Group", "SBA", "Thermo Fisher"]
    pr_tabs = st.tabs(pr_brands)
    for i, brand in enumerate(pr_brands):
        with pr_tabs[i]:
            render_top_3_archetypes("pr", brand)
    render_sentiment(mode="by_company")
    render_topics()
    render_volume(mode="by_company")
    render_media_shares(mode="by_brand")

elif section == "Social Media":
    st.title("📱 Social Media Dashboard")
    render_social_media_ranking()
    # Top 3 Archetypes for Social Media (tabs per brand)
    st.markdown("### Top 3 Archetypes (Social Media)")
    sm_brands = ["Kauno grudai", "Acme grupe", "Ignitis", "SBA", "Thermo Fisher"]
    sm_tabs = st.tabs(sm_brands)
    for i, brand in enumerate(sm_brands):
        with sm_tabs[i]:
            render_top_3_archetypes("linkedin", brand)
    render_social_trends(selected_platforms=["linkedin", "facebook"])
    render_top_posts(selected_platforms=["linkedin", "facebook"])

elif section == "Audience Affinity":
    st.title("🎯 Audience Affinity Dashboard")
    tab_pr, tab_li = st.tabs(["Press Releases", "LinkedIn"])
    with tab_pr:
        render_audience_affinity(source="pr")
    with tab_li:
        render_audience_affinity(source="linkedin")

elif section == "Content Pillars":
    st.title("🧱 Content Pillar Dashboard")
    render_content_pillars()
    #st.info("This section is under construction")
