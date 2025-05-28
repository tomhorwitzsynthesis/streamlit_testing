import streamlit as st
import pandas as pd
import plotly.express as px
from utils.file_io import load_agility_data
from utils.date_utils import get_selected_date_range
from utils.config import BRANDS
from pandas.tseries.offsets import MonthEnd

def render(mode: str = "by_company"):
    """
    Plot article volume trends by month.
    mode = "by_company" → lines per brand
    mode = "combined"   → one line summing all volumes
    """
    if mode not in {"by_company", "combined"}:
        st.error(f"Invalid mode '{mode}' in volume_trends.render(). Use 'by_company' or 'combined'.")
        return

    st.subheader("📈 Monthly Media Mention Trends")

    start_date, end_date = get_selected_date_range()

    # Normalize date range to full months
    start_month = pd.Timestamp(start_date).replace(day=1)
    end_month = (pd.Timestamp(end_date) - MonthEnd(1)).replace(day=1)
    months = pd.date_range(start=start_month, end=end_month, freq="MS")

    trend_data = []

    for brand in BRANDS:
        df = load_agility_data(brand)
        if df is None or "Published Date" not in df.columns:
            continue

        df["Published Date"] = pd.to_datetime(df["Published Date"], errors="coerce")
        df = df.dropna(subset=["Published Date"])
        df = df[(df["Published Date"] >= start_date) & (df["Published Date"] <= end_date)]

        if df.empty:
            continue

        df["Month"] = df["Published Date"].dt.to_period("M").dt.to_timestamp()
        monthly_counts = df.groupby("Month").size().reindex(months, fill_value=0)

        if mode == "by_company":
            for month, count in monthly_counts.items():
                trend_data.append({
                    "Month": month,
                    "Company": brand,
                    "Volume": count
                })
        else:  # combined
            for month, count in monthly_counts.items():
                trend_data.append({
                    "Month": month,
                    "Company": "All Brands",
                    "Volume": count if brand == BRANDS[0] else 0  # initialize only once
                })

    if not trend_data:
        st.warning("No volume data found.")
        return

    df_trend = pd.DataFrame(trend_data)

    if mode == "combined":
        df_trend = df_trend.groupby("Month", as_index=False).agg({"Volume": "sum"})
        df_trend["Company"] = "All Brands"

    fig = px.line(
        df_trend,
        x="Month",
        y="Volume",
        color="Company",
        markers=True,
        title="Monthly Trend of Media Mentions"
    )

    # Format x-axis as month labels
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Number of Articles",
        xaxis=dict(
            tickmode="array",
            tickvals=sorted(df_trend["Month"].unique()),
            ticktext=[pd.to_datetime(m).strftime('%b %Y') for m in sorted(df_trend["Month"].unique())]
        )
    )

    st.plotly_chart(fig, use_container_width=True)
