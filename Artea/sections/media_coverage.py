import streamlit as st
import pandas as pd
import plotly.express as px
from utils.file_io import load_agility_data
from utils.date_utils import get_selected_date_range
from utils.config import BRANDS

REGIONS = {
    "Total": None,
    "Lithuania": "Lithuania",
    "Latvia": "Latvia",
    "Estonia": "Estonia"
}

def render(mode: str = "by_brand"):
    """
    Display brand media coverage using pie charts.
    mode: 
      - "by_brand" → total brand share (one chart)
      - "by_brand_and_country" → one pie chart per country
    """
    if mode not in {"by_brand", "by_brand_and_country"}:
        st.error(f"Invalid mode '{mode}' in media_coverage.render(). Use 'by_brand' or 'by_brand_and_country'.")
        return

    st.subheader("📰 Media Mentions Coverage Share")

    st.markdown("""
    This section visualizes the share of media mentions across brands. 
    Use this to evaluate visibility or dominance in earned media.
    """)

    start_date, end_date = get_selected_date_range()

    all_data = []

    for brand in BRANDS:
        df = load_agility_data(brand)
        if df is None or "Published Date" not in df.columns:
            continue

        df["Published Date"] = pd.to_datetime(df["Published Date"], errors="coerce")
        df = df.dropna(subset=["Published Date"])
        df = df[(df["Published Date"] >= start_date) & (df["Published Date"] <= end_date)]

        if df.empty:
            continue

        df["Company"] = brand
        all_data.append(df)

    if not all_data:
        st.warning("No data available for the selected period.")
        return

    df_all = pd.concat(all_data, ignore_index=True)

    if mode == "by_brand":
        _plot_share_pie(df_all, title="Total Media Coverage Share")
    else:  # by_brand_and_country
        tabs = st.tabs([f"🌍 {region}" for region in REGIONS.keys()])
        for (region_name, country_filter), tab in zip(REGIONS.items(), tabs):
            with tab:
                region_df = df_all if country_filter is None else df_all[df_all["Country"] == country_filter]
                if region_df.empty:
                    st.info("No data for this region.")
                    continue
                _plot_share_pie(region_df, title=f"{region_name} Media Coverage Share")

def _plot_share_pie(df: pd.DataFrame, title: str):
    counts = df.groupby("Company").size().reset_index(name="Articles")
    total = counts["Articles"].sum()
    counts["Percentage"] = (counts["Articles"] / total) * 100

    fig = px.pie(
        counts,
        names="Company",
        values="Articles",
        hover_data=["Percentage"],
        labels={"Percentage": "% of Total"},
        title=title
    )

    fig.update_traces(
        textinfo="label+percent",
        hovertemplate="%{label}: %{value} articles (%{customdata[0]:.1f}%)"
    )

    st.plotly_chart(fig, use_container_width=True)
