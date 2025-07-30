# streamlit_app.py

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Load and preprocess data
df = pd.read_excel("ads_scraping (2).xlsx")

# Parse and normalize
df['startDateFormatted'] = pd.to_datetime(df['startDateFormatted'], errors='coerce')
df['endDateFormatted'] = pd.to_datetime(df['endDateFormatted'], errors='coerce')
df['duration_days'] = (df['endDateFormatted'] - df['startDateFormatted']).dt.days
df['reach'] = pd.to_numeric(df['ad_details/aaa_info/eu_total_reach'], errors='coerce')
df['platforms'] = df['publisherPlatform']
df['brand'] = df['pageName']
df['isActive'] = df['isActive'].astype(bool)

# Filter for last 6 months (Feb–Jul 2025)
end_date = pd.Timestamp("2025-07-31", tz="UTC")
start_date = end_date - relativedelta(months=6)
mid_date = start_date + relativedelta(months=3)
df_filtered = df[(df['startDateFormatted'] >= start_date) & (df['startDateFormatted'] <= end_date)]

# Summary calculation function
def summary(df, value_col):
    curr = df[(df['startDateFormatted'] >= mid_date) & (df['startDateFormatted'] <= end_date)]
    prev = df[(df['startDateFormatted'] >= start_date) & (df['startDateFormatted'] < mid_date)]

    curr_agg = curr.groupby('brand')[value_col].sum()
    prev_agg = prev.groupby('brand')[value_col].sum()

    rank_curr = curr_agg.sort_values(ascending=False).rank(ascending=False, method="min")
    rank_prev = prev_agg.sort_values(ascending=False).rank(ascending=False, method="min")

    result = pd.DataFrame({
        'current': curr_agg,
        'previous': prev_agg,
        'change_pct': ((curr_agg - prev_agg) / prev_agg.replace(0, 1)) * 100,
        'rank_now': rank_curr,
        'rank_prev': rank_prev,
        'rank_change': rank_curr - rank_prev
    }).fillna(0)

    return result

# Header
st.title("Ad Intelligence Dashboard")
st.caption("Monitoring ad activity and reach over the past 6 months (Feb–Jul 2025)")

# --- OVERVIEW SECTION ---
st.header("Overview")

# 1. Ad Volume Share by Month (with Reach and Count tabs)
st.subheader("Ad Volume Share by Month")
month_tabs = st.tabs(["Feb", "Mar", "Apr", "May", "Jun", "Jul"])
months = [2, 3, 4, 5, 6, 7]

for i, month in enumerate(months):
    with month_tabs[i]:
        sub_tabs = st.tabs(["Number of Ads", "Reach"])

        month_data = df_filtered[df_filtered['startDateFormatted'].dt.month == month]

        with sub_tabs[0]:  # Number of Ads
            ad_counts = month_data['brand'].value_counts().reset_index()
            ad_counts.columns = ['brand', 'count']
            fig = px.pie(ad_counts, values='count', names='brand', title=f'Ad Count Share – {month:02d}/2025')
            st.plotly_chart(fig, use_container_width=True, key=f"pie_ads_{month}")

        with sub_tabs[1]:  # Reach
            reach_totals = month_data.groupby('brand')['reach'].sum().reset_index()
            fig = px.pie(reach_totals, values='reach', names='brand', title=f'Reach Share – {month:02d}/2025')
            st.plotly_chart(fig, use_container_width=True, key=f"pie_reach_{month}")

# 2. Summary Cards
reach_stats = summary(df_filtered, 'reach')
df_filtered['ad_count'] = 1
ads_stats = summary(df_filtered, 'ad_count')
duration_stats = summary(df_filtered, 'duration_days')
from pandas.tseries.offsets import MonthEnd

# Define current and previous month ranges
curr_month_start = pd.Timestamp("2025-07-01", tz="UTC")
curr_month_end = curr_month_start + MonthEnd(1)

prev_month_start = curr_month_start - MonthEnd(1)
prev_month_end = curr_month_start - pd.Timedelta(days=1)

# Ads active during those months
active_curr = df_filtered[
    (df_filtered['startDateFormatted'] <= curr_month_end) &
    (df_filtered['endDateFormatted'] >= curr_month_start)
]
active_prev = df_filtered[
    (df_filtered['startDateFormatted'] <= prev_month_end) &
    (df_filtered['endDateFormatted'] >= prev_month_start)
]

active_stats = pd.DataFrame(index=df_filtered['brand'].unique())
active_stats['current'] = active_curr.groupby('brand').size()
active_stats['previous'] = active_prev.groupby('brand').size()
active_stats = active_stats.fillna(0)
active_stats['change_pct'] = ((active_stats['current'] - active_stats['previous']) / active_stats['previous'].replace(0, 1)) * 100

active_stats['rank_now'] = active_stats['current'].rank(ascending=False, method="min")
active_stats['rank_prev'] = active_stats['previous'].rank(ascending=False, method="min")
active_stats['rank_change'] = active_stats['rank_now'] - active_stats['rank_prev']


akropolis = "AKROPOLIS | Vilnius"

def format_metric_card(label, val, pct, rank_now, rank_change, debug=False):
    # Corrected arrow logic: improved rank (e.g. 2→1) = ↓ in number = ↑ performance
    if rank_change > 0:
        arrow = "↓"  # rank got worse
        rank_color = "red"
    elif rank_change < 0:
        arrow = "↑"  # rank improved
        rank_color = "green"
    else:
        arrow = "→"
        rank_color = "gray"

    pct_color = "green" if pct > 0 else "red" if pct < 0 else "gray"

    st.markdown(f"""
    <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px;">
        <h5 style="margin:0;">{label}</h5>
        <h3 style="margin:5px 0;">{val}</h3>
        <p style="margin:0; color:{pct_color};">Δ {pct:.1f}%</p>
        <p style="margin:0; color:{rank_color};">{arrow} Rank {int(rank_now)}</p>
    """, unsafe_allow_html=True)

    if debug:
        st.markdown(f"""
        <small style="color:#666;">
        Debug: pct={pct:.2f}, rank_now={rank_now}, rank_change={rank_change}
        </small>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("</div>", unsafe_allow_html=True)


# Display all 4 metrics
col1, col2 = st.columns(2)
with col1:
    if akropolis in reach_stats.index:
        r = reach_stats.loc[akropolis]
        format_metric_card("Reach", f"{int(r['current']):,}", r['change_pct'], r['rank_now'], r['rank_change'], debug=False)
with col2:
    if akropolis in ads_stats.index:
        a = ads_stats.loc[akropolis]
        format_metric_card("New Ads", int(a['current']), a['change_pct'], a['rank_now'], a['rank_change'], debug=False)

col3, col4 = st.columns(2)
with col3:
    if akropolis in duration_stats.index and akropolis in ads_stats.index:
        d = duration_stats.loc[akropolis]
        a = ads_stats.loc[akropolis]['current']
        avg_dur = d['current'] / a if a else 0
        format_metric_card("Avg Duration", f"{avg_dur:.1f} days", d['change_pct'], d['rank_now'], d['rank_change'], debug=False)
with col4:
    if akropolis in active_stats.index:
        act = active_stats.loc[akropolis]
        format_metric_card(
            "Active Ads",
            int(act['current']),
            act['change_pct'],
            act['rank_now'],
            act['rank_change'],
            debug=False
        )

# --- IN DEPTH SECTION ---
import ast

st.header("In-Depth View")

# Start Date Distribution
st.subheader("Ad Start Date Distribution")
st.markdown("This chart shows the number of ads launched each day per brand to help identify campaign patterns and bursts.")
hist = px.histogram(df_filtered, x='startDateFormatted', color='brand', nbins=60, barmode='overlay')
st.plotly_chart(hist, use_container_width=True)

# Volume Trends
st.subheader("Volume Trends")
tabs = st.tabs(["Total", "FACEBOOK", "INSTAGRAM", "MESSENGER", "THREADS", "AUDIENCE_NETWORK"])
platforms = ["FACEBOOK", "INSTAGRAM", "MESSENGER", "THREADS", "AUDIENCE_NETWORK"]

# Total tab (weekly)
with tabs[0]:
    st.markdown("#### Reach (Total)")
    reach_trend = df_filtered.groupby([pd.Grouper(key='startDateFormatted', freq='W'), 'brand'])['reach'].sum().reset_index()
    fig = px.line(reach_trend, x='startDateFormatted', y='reach', color='brand')
    st.plotly_chart(fig, use_container_width=True, key="total_reach")

    st.markdown("#### New Ads (Total)")
    ads_trend = df_filtered.groupby([pd.Grouper(key='startDateFormatted', freq='W'), 'brand']).size().reset_index(name='ads')
    fig = px.line(ads_trend, x='startDateFormatted', y='ads', color='brand')
    st.plotly_chart(fig, use_container_width=True, key="total_ads")

# Fix platform list parsing
def parse_platforms(val):
    try:
        if isinstance(val, str):
            return ast.literal_eval(val)
        elif isinstance(val, list):
            return val
    except Exception:
        return []
    return []

exploded = df_filtered.copy()
exploded['platforms'] = exploded['platforms'].apply(parse_platforms)
exploded = exploded.explode('platforms')

for i, platform in enumerate(platforms):
    with tabs[i + 1]:
        st.markdown(f"#### Reach – {platform}")
        pf = exploded[exploded['platforms'] == platform]

        st.markdown(f"*Debug: {len(pf)} ads found for platform `{platform}`*")

        if pf.empty:
            st.warning(f"No data available for {platform}.")
        else:
            pf_reach = pf.groupby([pd.Grouper(key='startDateFormatted', freq='W'), 'brand'])['reach'].sum().reset_index()
            fig = px.line(pf_reach, x='startDateFormatted', y='reach', color='brand')
            st.plotly_chart(fig, use_container_width=True, key=f"reach_{platform}")

            st.markdown(f"#### New Ads – {platform}")
            pf_ads = pf.groupby([pd.Grouper(key='startDateFormatted', freq='W'), 'brand']).size().reset_index(name='ads')
            fig = px.line(pf_ads, x='startDateFormatted', y='ads', color='brand')
            st.plotly_chart(fig, use_container_width=True, key=f"ads_{platform}")

# --- ADDITIONAL SECTION: TEXT ANALYSIS ---
st.header("Ad Hook Analysis")

text_data = {
    "AKROPOLIS | Vilnius": """Based on the provided meta ads, the most frequent advertising hooks used by the brand can be classified into the following categories:

1. **Seasonal Style Guides and Trends:**
   - “Need inspiration for summer style? Subscribe to the AKROPOLIS newsletter and get the 'Style Guide' – a journey into seasonal trends.”
   - “Do you want to know this spring's style trends? Subscribe to the AKROPOLIS newsletter and get this season's 'Style Guide'!”
   - “The brand new FREE spring 'Style Guide' has blossomed! It contains the most current trends of the season for everyone – for her, him, and children.”

2. **Sales and Discounts:**
   - “Along with summer, the hottest sale of the season DYLAS arrives at AKROPOLIS!”
   - “Offers so good, you'll want everything! DYLAS at AKROPOLIS – awaits you with 20, 30, 40, and even 50% and many more discounts.”
   - “That feeling when you've long dreamed of quality jeans or a dress and suddenly you can buy it with a big discount.”

3. **Events and Experiences:**
   - “The famous heroes LILO and STITCH invite you to an unforgettable adventure weekend!”
   - “Sunday is NYKŠTUKO ice cream day! 🍦 ... the sweetest summer celebration.”
   - “As many as 4000 portions of summer flavors – such goodies await you at the free SUN365 ice cream fiesta!”

4. **Charity and Social Responsibility:**
   - “Give someone life – become a blood donor. 🎁 ❤️”
   - “The National Blood Center invites you to become a blood donor.”
   - “Give the miracle of life – become a blood donor now!”
""",
    "OZAS": """Here are the most frequent advertising hooks used by the brand, classified into different categories:

1. **Discounts and Promotions:**
   - “OPTOMETRY CENTER PPC OZAS ... FREE eye check. ✅ Up to 50% discount on sunglasses!”
   - “🎉 SAMSONITE celebrates its 10th birthday and offers special prices! ... at festive prices!”
   - “Were you waiting for a chance to shop with special discounts? ... Maxima announces the Great Discount Days!”

2. **New Store Openings and Product Launches:**
   - “PPC OZAS has opened a new Formosa Bubble Tea ... 🧋”
   - “The new Pegasas bookstore chain – now at PPC OZAS! 🎉”
   - “PPC OZAS has opened a modern and stylish SAMSONITE space ...”

3. **Events and Experiences:**
   - “SPOT entertainment weekend with Comic Con Baltics ... All entertainment – FREE! 🚀”
   - “Birdhouse workshops with Adventica PPC Ozas! ✨🐦”
   - “Exclusive premiere of 'Paddington Bear: Adventures in Peru' ... at 'Multikino' cinema.”
""",
    "PANORAMA": """Based on the provided meta ads, the most frequent advertising hooks used by the brand "Panorama" can be classified into the following categories:

1. **Ambassadors and Personal Stories:**
   - “Daivaras – Panorama's #GOODTASTEBASSADOR ...”
   - “Meet Gintarė – Panorama's #GOODTASTEBASSADOR ... subtle life philosophy.”
   - “Kristina is Panorama's #GOODTASTEBASSADOR, living the rhythm of this space for many years.”

2. **Events and Experiences:**
   - “The history of speed legends will speak at Panorama. 🏍️”
   - “🐾 A celebration for four-legged friends and their owners!”
   - “🎙️ Aistė and Gelminė live at Panorama – a weekend of feminine humor and style!”

3. **Discounts and Promotions:**
   - “Special discounts, gifts, and other surprises – Douglas, Drogas, L'Occitane...”
   - “🌡 When the thermometer reaches negative temperatures ... discounts! 🤩”
   - “Now – even more special offers for cosmetics and beauty products at #Panorama!”
""",
    "Summary": """### Most Generic Hooks:
1. **Discounts and Promotions/Sales and Discounts:** Used by all brands.
2. **Events and Experiences:** Common across all.

### Most Differentiated Hooks:
- **AKROPOLIS:** Seasonal style guides + social responsibility.
- **PANORAMA:** Personal stories and ambassadors.
- **OZAS:** New store openings and product launches.

**Differentiation Ranking:**
1. AKROPOLIS
2. PANORAMA
3. OZAS"""
}

brand_selection = st.selectbox("Select a brand to view ad hook strategy:", list(text_data.keys()), index=0)

# --- Hook Summary Card (replaces raw Markdown 'pre' block) ---
if brand_selection == "Summary":
    st.markdown(f"""
    <div style="border:1px solid #ccc; border-radius:10px; padding:20px; background-color:#fafafa;">
        <h4>Most Generic Hooks</h4>
        <ul>
            <li><strong>Discounts and Promotions/Sales and Discounts:</strong> Used by all brands.</li>
            <li><strong>Events and Experiences:</strong> Common across all.</li>
        </ul>
        <h4>Most Differentiated Hooks</h4>
        <ul>
            <li><strong>AKROPOLIS:</strong> Seasonal style guides + social responsibility.</li>
            <li><strong>PANORAMA:</strong> Personal stories and ambassadors.</li>
            <li><strong>OZAS:</strong> New store openings and product launches.</li>
        </ul>
        <h4>Brand Differentiation Ranking</h4>
        <ol>
            <li>AKROPOLIS</li>
            <li>PANORAMA</li>
            <li>OZAS</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div style="border:1px solid #ccc; border-radius:10px; padding:20px; background-color:#fafafa;">
    <pre style="white-space: pre-wrap; font-size: 0.95em;">{text_data[brand_selection]}</pre>
    </div>
    """, unsafe_allow_html=True)

# --- NEW CAMPAIGNS SECTION ---
st.header("New Campaigns – July 2025")

st.markdown("""
You can either view the top-performing ads this month, or read a summary of campaigns that are considered new compared to previous months.
""")

option = st.radio("Choose campaign view:", ["Top 5 Ads by Reach", "LLM-Based Campaign Summary"])

# Simple top 5
if option == "Top 5 Ads by Reach":
    july_ads = df_filtered[df_filtered['startDateFormatted'].dt.month == 7].copy()
    top_5 = july_ads[['pageName', 'reach', 'snapshot/body/text']].dropna(subset=['snapshot/body/text'])
    top_5 = top_5.sort_values(by='reach', ascending=False).head(5)

    for idx, row in top_5.iterrows():
        st.markdown(f"""
        <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:15px;">
            <strong>{row['pageName']}</strong><br>
            <em>Reach:</em> {int(row['reach']):,}<br>
            <p style="margin-top:10px;">{row['snapshot/body/text']}</p>
        </div>
        """, unsafe_allow_html=True)

# LLM-based textual summary
# LLM-based textual summary
else:
    st.markdown("""
    <div style="border:1px solid #ccc; border-radius:10px; padding:20px; background-color:#f9f9f9;">
    <h4>July Campaign Highlights – LLM Summary</h4>

    <p><strong>AKROPOLIS | Vilnius:</strong> July saw a renewed push around the <em>DYLAS</em> sale campaign, highlighting aggressive discount tiers (20–50%) with fresh creative. Although DYLAS existed before, the language and positioning differ from June, signaling a new phase. No continuation of the spring-style guides was observed.</p>

    <p><strong>OZAS:</strong> Launched a new campaign titled <em>"TALUTTI UŽSPOTINAM"</em>, promoting their dining partner via SPOT discounts. This food-centric initiative is new and did not appear in prior months. It reflects an experiential shift aimed at driving food court traffic.</p>

    <p><strong>PANORAMA:</strong> Introduced a brand-new store campaign for <em>HUPPA</em>—its first presence in Lithuania. The store opening was given high visibility through dedicated creative. Additionally, beauty and cosmetics promotions featured more prominently, suggesting a coordinated seasonal retail push not present in June.</p>

    <p><strong>Conclusion:</strong> Each brand introduced distinctive new campaigns in July: AKROPOLIS built urgency around discounts, OZAS emphasized food and app-based offers, and PANORAMA spotlighted retail expansion and beauty-focused sales.</p>
    </div>
    """, unsafe_allow_html=True)


