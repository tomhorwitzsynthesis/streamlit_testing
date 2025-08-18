# streamlit_app.py

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta
from utils.date_utils import get_selected_date_range
from utils.file_io import load_ads_data
import ast


def _parse_platforms(val):
    try:
        if isinstance(val, str):
            return ast.literal_eval(val)
        elif isinstance(val, list):
            return val
    except Exception:
        return []
    return []


def _summary(df: pd.DataFrame, value_col: str, split_mid: datetime):
    curr = df[df['startDateFormatted'] >= split_mid]
    prev = df[df['startDateFormatted'] < split_mid]

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


def _format_metric_card(label, val, pct, rank_now, rank_change, debug=False):
    if rank_change > 0:
        arrow = "↓"
        rank_color = "red"
    elif rank_change < 0:
        arrow = "↑"
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


def render():

    df = load_ads_data()
    if df is None or df.empty:
        st.info("No ads data available.")
        return

    # Use global selected date range for pie chart and cards
    start_date, end_date = get_selected_date_range()

    # Clip to selected range for pie chart and cards
    if "startDateFormatted" in df.columns:
        df_filtered = df[(df['startDateFormatted'] >= pd.to_datetime(start_date)) & (df['startDateFormatted'] < pd.to_datetime(end_date))].copy()
    else:
        df_filtered = df.copy()

    # Always use Feb 2025 - July 2025 for all other graphs
    fixed_start = pd.Timestamp(2025, 2, 1)
    fixed_end = pd.Timestamp(2025, 7, 31)
    df_fixed = df[(df['startDateFormatted'] >= fixed_start) & (df['startDateFormatted'] <= fixed_end)].copy()

    # Pie charts and cards for selected months only
    st.markdown("### Ad Volume Share (Selected Months)")
    sub_tabs = st.tabs(["Number of Ads", "Reach"])
    with sub_tabs[0]:
        ad_counts = df_filtered['brand'].value_counts().reset_index()
        if not ad_counts.empty:
            ad_counts.columns = ['brand', 'count']
            fig = px.pie(ad_counts, values='count', names='brand', title=f'Ad Count Share – {start_date.strftime("%b %Y")} to {end_date.strftime("%b %Y")}')
            st.plotly_chart(fig, use_container_width=True, key="pie_ads_selected")
        else:
            st.info("No ads in selected months.")

    with sub_tabs[1]:
        reach_totals = df_filtered.groupby('brand')['reach'].sum().reset_index()
        if not reach_totals.empty:
            fig = px.pie(reach_totals, values='reach', names='brand', title=f'Reach Share – {start_date.strftime("%b %Y")} to {end_date.strftime("%b %Y")}')
            st.plotly_chart(fig, use_container_width=True, key="pie_reach_selected")
        else:
            st.info("No reach data in selected months.")

    # Summary cards using mid-point of selected range
    mid_date = start_date + (end_date - start_date) / 2

    reach_stats = _summary(df_filtered, 'reach', mid_date)
    df_filtered['ad_count'] = 1
    ads_stats = _summary(df_filtered, 'ad_count', mid_date)
    duration_stats = _summary(df_filtered, 'duration_days', mid_date) if 'duration_days' in df_filtered.columns else None

    # Active ads stats for current vs previous month relative to end_date
    from pandas.tseries.offsets import MonthEnd
    curr_month_start = pd.Timestamp(end_date).to_period('M').to_timestamp()
    curr_month_end = curr_month_start + MonthEnd(1)
    prev_month_start = curr_month_start - MonthEnd(1)
    prev_month_end = curr_month_start - pd.Timedelta(days=1)

    active_curr = df_filtered[(df_filtered['startDateFormatted'] <= curr_month_end) & (df_filtered['endDateFormatted'] >= curr_month_start)]
    active_prev = df_filtered[(df_filtered['startDateFormatted'] <= prev_month_end) & (df_filtered['endDateFormatted'] >= prev_month_start)]

    active_stats = pd.DataFrame(index=df_filtered['brand'].unique())
    active_stats['current'] = active_curr.groupby('brand').size()
    active_stats['previous'] = active_prev.groupby('brand').size()
    active_stats = active_stats.fillna(0)
    active_stats['change_pct'] = ((active_stats['current'] - active_stats['previous']) / active_stats['previous'].replace(0, 1)) * 100
    active_stats['rank_now'] = active_stats['current'].rank(ascending=False, method="min")
    active_stats['rank_prev'] = active_stats['previous'].rank(ascending=False, method="min")
    active_stats['rank_change'] = active_stats['rank_now'] - active_stats['rank_prev']

    target_brand = next(iter(df_filtered['brand'].dropna().unique()), None)

    if target_brand:
        col1, col2 = st.columns(2)
        with col1:
            if target_brand in reach_stats.index:
                r = reach_stats.loc[target_brand]
                _format_metric_card("Reach", f"{int(r['current']):,}", r['change_pct'], r['rank_now'], r['rank_change'], debug=False)
        with col2:
            if target_brand in ads_stats.index:
                a = ads_stats.loc[target_brand]
                _format_metric_card("New Ads", int(a['current']), a['change_pct'], a['rank_now'], a['rank_change'], debug=False)

        col3, col4 = st.columns(2)
        with col3:
            if duration_stats is not None and target_brand in duration_stats.index and target_brand in ads_stats.index:
                d = duration_stats.loc[target_brand]
                a = ads_stats.loc[target_brand]['current']
                avg_dur = d['current'] / a if a else 0
                _format_metric_card("Avg Duration", f"{avg_dur:.1f} days", d['change_pct'], d['rank_now'], d['rank_change'], debug=False)
        with col4:
            if target_brand in active_stats.index:
                act = active_stats.loc[target_brand]
                _format_metric_card("Active Ads", int(act['current']), act['change_pct'], act['rank_now'], act['rank_change'], debug=False)

    # In-Depth View (use only Feb-Jul 2025)
    st.markdown("### In-Depth View")

    st.markdown("Ad Start Date Distribution")
    hist = px.histogram(df_fixed, x='startDateFormatted', color='brand', nbins=60, barmode='overlay')
    st.plotly_chart(hist, use_container_width=True)

    st.markdown("### Volume Trends")
    tabs = st.tabs(["Total", "FACEBOOK", "INSTAGRAM", "MESSENGER", "THREADS", "AUDIENCE_NETWORK"])
    platforms = ["FACEBOOK", "INSTAGRAM", "MESSENGER", "THREADS", "AUDIENCE_NETWORK"]

    with tabs[0]:
        st.markdown("#### Reach (Total)")
        reach_trend = df_fixed.groupby([pd.Grouper(key='startDateFormatted', freq='W'), 'brand'])['reach'].sum().reset_index()
        fig = px.line(reach_trend, x='startDateFormatted', y='reach', color='brand')
        st.plotly_chart(fig, use_container_width=True, key="total_reach")

        st.markdown("#### New Ads (Total)")
        ads_trend = df_fixed.groupby([pd.Grouper(key='startDateFormatted', freq='W'), 'brand']).size().reset_index(name='ads')
        fig = px.line(ads_trend, x='startDateFormatted', y='ads', color='brand')
        st.plotly_chart(fig, use_container_width=True, key="total_ads")

    exploded = df_fixed.copy()
    exploded['platforms'] = exploded.get('publisherPlatform', exploded.get('platforms', None))
    exploded['platforms'] = exploded['platforms'].apply(_parse_platforms)
    exploded = exploded.explode('platforms')

    for i, platform in enumerate(platforms):
        with tabs[i + 1]:
            st.markdown(f"#### Reach – {platform}")
            pf = exploded[exploded['platforms'] == platform]
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

    # Text analysis and new campaigns sections can be added later as optional blocks


