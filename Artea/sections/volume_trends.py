import streamlit as st
import pandas as pd
import plotly.express as px
from utils.file_io import load_agility_data
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

    # Remove date selection
    # Instead, determine min/max dates from all brands' data
    all_dates = []
    for brand in BRANDS:
        df = load_agility_data(brand)
        if df is not None and "Published Date" in df.columns:
            df["Published Date"] = pd.to_datetime(df["Published Date"], errors="coerce")
            all_dates.extend(df["Published Date"].dropna().tolist())

    if not all_dates:
        st.warning("No data available for volume trends.")
        return

    start_month = pd.Timestamp(min(all_dates)).replace(day=1)
    end_month = pd.Timestamp(max(all_dates)).replace(day=1)
    months = pd.date_range(start=start_month, end=end_month, freq="MS")

    # Initialize data structures for all metrics
    volume_data = []
    impressions_data = []
    bmq_data = []

    for brand in BRANDS:
        df = load_agility_data(brand)
        if df is None or "Published Date" not in df.columns:
            continue

        df["Published Date"] = pd.to_datetime(df["Published Date"], errors="coerce")
        df = df.dropna(subset=["Published Date"])
        # Remove date filtering here

        if df.empty:
            continue

        df["Month"] = df["Published Date"].dt.to_period("M").dt.to_timestamp()
        
        # Volume data (count of articles)
        monthly_counts = df.groupby("Month").size().reindex(months, fill_value=0)
        
        # Impressions data (sum of impressions)
        if "Impressions" in df.columns:
            df["Impressions"] = pd.to_numeric(df["Impressions"], errors="coerce").fillna(0)
            monthly_impressions = df.groupby("Month")["Impressions"].sum().reindex(months, fill_value=0)
        else:
            monthly_impressions = pd.Series(0, index=months)
        
        # BMQ data (average BMQ)
        if "BMQ" in df.columns:
            df["BMQ"] = pd.to_numeric(df["BMQ"], errors="coerce")
            monthly_bmq = df.groupby("Month")["BMQ"].mean().reindex(months, fill_value=0)
        else:
            monthly_bmq = pd.Series(0, index=months)

        if mode == "by_company":
            for month, count in monthly_counts.items():
                volume_data.append({
                    "Month": month,
                    "Company": brand,
                    "Volume": count
                })
            
            for month, impressions in monthly_impressions.items():
                impressions_data.append({
                    "Month": month,
                    "Company": brand,
                    "Impressions": impressions
                })
            
            for month, bmq in monthly_bmq.items():
                bmq_data.append({
                    "Month": month,
                    "Company": brand,
                    "BMQ": bmq
                })
        else:  # combined
            for month, count in monthly_counts.items():
                volume_data.append({
                    "Month": month,
                    "Company": "All Brands",
                    "Volume": count if brand == BRANDS[0] else 0  # initialize only once
                })
            
            for month, impressions in monthly_impressions.items():
                impressions_data.append({
                    "Month": month,
                    "Company": "All Brands",
                    "Impressions": impressions if brand == BRANDS[0] else 0  # initialize only once
                })
            
            for month, bmq in monthly_bmq.items():
                bmq_data.append({
                    "Month": month,
                    "Company": "All Brands",
                    "BMQ": bmq if brand == BRANDS[0] else 0  # initialize only once
                })

    # Create tabs for different metrics
    tab1, tab2, tab3 = st.tabs(["📊 Volume", "👁️ Impressions", "⭐ BMQ"])
    
    # Volume Tab
    with tab1:
        if not volume_data:
            st.warning("No volume data found.")
        else:
            df_volume = pd.DataFrame(volume_data)
            
            if mode == "combined":
                df_volume = df_volume.groupby("Month", as_index=False).agg({"Volume": "sum"})
                df_volume["Company"] = "All Brands"

            fig_volume = px.line(
                df_volume,
                x="Month",
                y="Volume",
                color="Company",
                markers=True,
                title="Monthly Trend of Media Mentions"
            )

            fig_volume.update_layout(
                xaxis_title="Month",
                yaxis_title="Number of Articles",
                xaxis=dict(
                    tickmode="array",
                    tickvals=sorted(df_volume["Month"].unique()),
                    ticktext=[pd.to_datetime(m).strftime('%b %Y') for m in sorted(df_volume["Month"].unique())]
                )
            )

            st.plotly_chart(fig_volume, use_container_width=True)
    
    # Impressions Tab
    with tab2:
        if not impressions_data:
            st.warning("No impressions data found.")
        else:
            df_impressions = pd.DataFrame(impressions_data)
            
            if mode == "combined":
                df_impressions = df_impressions.groupby("Month", as_index=False).agg({"Impressions": "sum"})
                df_impressions["Company"] = "All Brands"

            fig_impressions = px.line(
                df_impressions,
                x="Month",
                y="Impressions",
                color="Company",
                markers=True,
                title="Monthly Trend of Total Impressions"
            )

            fig_impressions.update_layout(
                xaxis_title="Month",
                yaxis_title="Total Impressions",
                xaxis=dict(
                    tickmode="array",
                    tickvals=sorted(df_impressions["Month"].unique()),
                    ticktext=[pd.to_datetime(m).strftime('%b %Y') for m in sorted(df_impressions["Month"].unique())]
                )
            )

            st.plotly_chart(fig_impressions, use_container_width=True)
    
    # BMQ Tab
    with tab3:
        if not bmq_data:
            st.warning("No BMQ data found.")
        else:
            df_bmq = pd.DataFrame(bmq_data)
            
            if mode == "combined":
                # For combined mode, we need to recalculate the average BMQ across all brands
                # First, collect all BMQ data for each month
                all_bmq_data = []
                for brand in BRANDS:
                    df = load_agility_data(brand)
                    if df is None or "Published Date" not in df.columns or "BMQ" not in df.columns:
                        continue
                    
                    df["Published Date"] = pd.to_datetime(df["Published Date"], errors="coerce")
                    df = df.dropna(subset=["Published Date"])
                    df["Month"] = df["Published Date"].dt.to_period("M").dt.to_timestamp()
                    df["BMQ"] = pd.to_numeric(df["BMQ"], errors="coerce")
                    
                    for month, bmq in df.groupby("Month")["BMQ"].mean().items():
                        all_bmq_data.append({
                            "Month": month,
                            "BMQ": bmq
                        })
                
                if all_bmq_data:
                    df_all_bmq = pd.DataFrame(all_bmq_data)
                    df_bmq = df_all_bmq.groupby("Month", as_index=False).agg({"BMQ": "mean"})
                    df_bmq["Company"] = "All Brands"

            fig_bmq = px.line(
                df_bmq,
                x="Month",
                y="BMQ",
                color="Company",
                markers=True,
                title="Monthly Trend of Average Article Quality (BMQ)"
            )

            fig_bmq.update_layout(
                xaxis_title="Month",
                yaxis_title="Average BMQ",
                xaxis=dict(
                    tickmode="array",
                    tickvals=sorted(df_bmq["Month"].unique()),
                    ticktext=[pd.to_datetime(m).strftime('%b %Y') for m in sorted(df_bmq["Month"].unique())]
                )
            )

            st.plotly_chart(fig_bmq, use_container_width=True)
