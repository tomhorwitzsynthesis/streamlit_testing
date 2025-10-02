import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import os

# Data configuration
DATA_ROOT = "Reitan-Proposal/Narvesen_compos_analysis.xlsx"  # Change this to your data source
REITAN_DATA_ROOT = "Reitan-Proposal/Reitan_compos_analysis.xlsx"  # Change this to your data source

# Page configuration
st.set_page_config(
    page_title="Reitan Daily Dashboard",
    page_icon="📊",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .brand-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load data from Excel files and process real daily counts"""
    try:
        # Load Narvesen data
        narvesen_df = pd.read_excel(DATA_ROOT, sheet_name='Raw Data')
        reitan_df = pd.read_excel(REITAN_DATA_ROOT, sheet_name='Raw Data')
        
        # Get the last 7 days (September 23-29, 2025)
        dates = pd.date_range('2025-09-23', '2025-09-29', freq='D')
        
        # Process Narvesen data
        narvesen_df['Published Date'] = pd.to_datetime(narvesen_df['Published Date'])
        narvesen_daily = narvesen_df.groupby('Published Date').agg({
            'Article': 'count',  # Count articles per day
            'Impressions': 'sum'  # Sum impressions per day
        }).reset_index()
        
        # Process Reitan data
        reitan_df['Published Date'] = pd.to_datetime(reitan_df['Published Date'])
        reitan_daily = reitan_df.groupby('Published Date').agg({
            'Article': 'count',  # Count articles per day
            'Impressions': 'sum'  # Sum impressions per day
        }).reset_index()
        
        # Create arrays for the 7 days
        narvesen_articles = []
        narvesen_impressions = []
        reitan_articles = []
        reitan_impressions = []
        
        for date in dates:
            # Narvesen data for this date
            narvesen_day = narvesen_daily[narvesen_daily['Published Date'].dt.date == date.date()]
            narvesen_articles.append(narvesen_day['Article'].sum() if not narvesen_day.empty else 0)
            narvesen_impressions.append(narvesen_day['Impressions'].sum() if not narvesen_day.empty else 0)
            
            # Reitan data for this date
            reitan_day = reitan_daily[reitan_daily['Published Date'].dt.date == date.date()]
            reitan_articles.append(reitan_day['Article'].sum() if not reitan_day.empty else 0)
            reitan_impressions.append(reitan_day['Impressions'].sum() if not reitan_day.empty else 0)
        
        data = {
            'Date': dates,
            'Narvesen_Articles': narvesen_articles,
            'Narvesen_Impressions': narvesen_impressions,
            'Reitan_Articles': reitan_articles,
            'Reitan_Impressions': reitan_impressions
        }
        
        return pd.DataFrame(data)
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        # Fallback to sample data if files can't be read
        dates = pd.date_range('2025-09-23', '2025-09-29', freq='D')
        sample_data = {
            'Date': dates,
            'Narvesen_Articles': [2, 3, 1, 4, 3, 2, 3],
            'Narvesen_Impressions': [2500, 3200, 1800, 4200, 3500, 2800, 3100],
            'Reitan_Articles': [3, 4, 2, 5, 4, 3, 4],
            'Reitan_Impressions': [3800, 4500, 2900, 5200, 4800, 3600, 4200]
        }
        return pd.DataFrame(sample_data)

# Load data
df = load_data()

# Header
st.title("📊 Reitan Daily Dashboard")
st.markdown("**Date:** September 29, 2025")

# Brand selection dropdown
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    selected_brand = st.selectbox(
        "Select Brand:",
        ["Narvesen", "Reitan"],
        key="brand_selector"
    )

st.markdown("---")

# Main metrics cards
col1, col2 = st.columns(2)

# Get the latest day's data (September 29, 2025) and previous day for comparison
latest_data = df.iloc[-1]  # Last row (September 29)
previous_data = df.iloc[-2]  # Previous day (September 28)

with col1:
    articles_value = latest_data['Narvesen_Articles'] if selected_brand == "Narvesen" else latest_data['Reitan_Articles']
    previous_articles = previous_data['Narvesen_Articles'] if selected_brand == "Narvesen" else previous_data['Reitan_Articles']
    articles_change = articles_value - previous_articles
    articles_delta = f"{'+' if articles_change >= 0 else ''}{articles_change} from yesterday"
    
    # Use the same card styling as the example
    delta_color = "green" if articles_change >= 0 else "red"
    st.markdown(
        f"""
        <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px;">
            <h5 style="margin:0;">📰 Number of Articles</h5>
            <h3 style="margin:5px 0;">{articles_value}</h3>
            <p style="margin:0; color:{delta_color};">{articles_delta}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    impressions_value = latest_data['Narvesen_Impressions'] if selected_brand == "Narvesen" else latest_data['Reitan_Impressions']
    previous_impressions = previous_data['Narvesen_Impressions'] if selected_brand == "Narvesen" else previous_data['Reitan_Impressions']
    impressions_change = impressions_value - previous_impressions
    impressions_delta = f"{'+' if impressions_change >= 0 else ''}{impressions_change:,} from yesterday"
    
    # Use the same card styling as the example
    delta_color = "green" if impressions_change >= 0 else "red"
    st.markdown(
        f"""
        <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px;">
            <h5 style="margin:0;">👁️ Total Impressions</h5>
            <h3 style="margin:5px 0;">{impressions_value:,}</h3>
            <p style="margin:0; color:{delta_color};">{impressions_delta}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Summary cards
st.markdown("### 📋 Daily Summary")

# Narvesen summary
if selected_brand == "Narvesen":
    st.markdown('<div class="brand-header">Narvesen (29/09/2025)</div>', unsafe_allow_html=True)
    st.markdown("""
    On this date, Narvesen was covered mainly in the context of financial performance within the retail market. 
    Articles noted that the brand is part of Reitan Retail's portfolio and highlighted that profitability in this group, 
    including Narvesen, was weaker than that of Swedish and Danish grocery chains. Reporting emphasized that Narvesen's 
    operations are tied to broader concerns about market competitiveness and profitability, with findings pointing to 
    underperformance compared to international benchmarks.
    """)

# Reitan summary
else:
    st.markdown('<div class="brand-header">Reitan (29/09/2025)</div>', unsafe_allow_html=True)
    st.markdown("""
    Coverage centered on financial comparisons between Reitan Retail and its Nordic competitors. Reports underscored 
    that Swedish and Danish grocery chains are achieving higher profitability, while Reitan Retail is lagging behind. 
    Analyses on this date drew attention to "surprising findings" about pricing and performance among Reitan's grocery 
    operations, reflecting challenges in maintaining competitiveness and efficiency. The reporting portrayed Reitan as 
    under pressure to close the profitability gap with its regional peers.
    """)

# 7-day trend graph
st.markdown("### 📈 7-Day Trend Analysis")

# Create tabs for the graph
tab1, tab2 = st.tabs(["📰 Total Articles", "👁️ Total Impressions"])

with tab1:
    fig_articles = go.Figure()
    
    # Add Narvesen line
    fig_articles.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Narvesen_Articles'],
        mode='lines+markers',
        name='Narvesen',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8)
    ))
    
    # Add Reitan line
    fig_articles.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Reitan_Articles'],
        mode='lines+markers',
        name='Reitan',
        line=dict(color='#ff7f0e', width=3),
        marker=dict(size=8)
    ))
    
    fig_articles.update_layout(
        title="Articles Published (Last 7 Days)",
        xaxis_title="Date",
        yaxis_title="Number of Articles",
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    st.plotly_chart(fig_articles, use_container_width=True)

with tab2:
    fig_impressions = go.Figure()
    
    # Add Narvesen line
    fig_impressions.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Narvesen_Impressions'],
        mode='lines+markers',
        name='Narvesen',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8)
    ))
    
    # Add Reitan line
    fig_impressions.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Reitan_Impressions'],
        mode='lines+markers',
        name='Reitan',
        line=dict(color='#ff7f0e', width=3),
        marker=dict(size=8)
    ))
    
    fig_impressions.update_layout(
        title="Total Impressions (Last 7 Days)",
        xaxis_title="Date",
        yaxis_title="Impressions",
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    st.plotly_chart(fig_impressions, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("*Dashboard updated: September 29, 2025*")

