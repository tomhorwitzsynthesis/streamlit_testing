import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import os

# Data configuration
DATA_ROOT = "Narvesen_compos_analysis.xlsx"  # Change this to your data source
REITAN_DATA_ROOT = "Reitan_compos_analysis.xlsx"  # Change this to your data source

def _format_simple_metric_card(label, val, pct=None, rank_now=None, total_ranks=None):
    """Format a metric card with optional percentage change and ranking."""
    rank_color = "gray"
    if rank_now is not None and total_ranks:
        if int(rank_now) == 1:
            rank_color = "green"
        elif int(rank_now) == int(total_ranks):
            rank_color = "red"
    
    pct_color = None
    if pct is not None:
        pct_color = "green" if pct > 0 else "red" if pct < 0 else "gray"
    
    pct_html = f'<p style="margin:0; color:{pct_color};">Δ {pct:.1f}%</p>' if pct is not None else ''
    rank_html = f'<p style="margin:0; color:{rank_color};">Rank {int(rank_now)}</p>' if rank_now is not None else ''
    
    st.markdown(
        f"""
        <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px;">
            <h5 style="margin:0;">{label}</h5>
            <h3 style="margin:5px 0;">{val}</h3>
            {pct_html}
            {rank_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

# Page configuration
st.set_page_config(
    page_title="Reitan Monthly Dashboard",
    page_icon="📊",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .archetype-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
        border-left: 4px solid #ff7f0e;
    }
    .topic-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
        border-left: 4px solid #2ca02c;
    }
    .brand-header {
        font-size: 1.1rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .section-header {
        font-size: 1.3rem;
        font-weight: bold;
        color: #2c3e50;
        margin: 1.5rem 0 1rem 0;
        border-bottom: 2px solid #ecf0f1;
        padding-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_monthly_data():
    """Load monthly data from Excel files and process real daily counts"""
    try:
        # Load Narvesen data
        narvesen_df = pd.read_excel(DATA_ROOT, sheet_name='Raw Data')
        reitan_df = pd.read_excel(REITAN_DATA_ROOT, sheet_name='Raw Data')
        
        # Process Narvesen data
        narvesen_df['Published Date'] = pd.to_datetime(narvesen_df['Published Date'])
        narvesen_daily = narvesen_df.groupby('Published Date').agg({
            'Article': 'count',  # Count articles per day
            'Impressions': 'sum',  # Sum impressions per day
            'BMQ': 'mean'  # Average BMQ per day
        }).reset_index()
        
        # Process Reitan data
        reitan_df['Published Date'] = pd.to_datetime(reitan_df['Published Date'])
        reitan_daily = reitan_df.groupby('Published Date').agg({
            'Article': 'count',  # Count articles per day
            'Impressions': 'sum',  # Sum impressions per day
            'BMQ': 'mean'  # Average BMQ per day
        }).reset_index()
        
        # Get all days in September 2025
        dates = pd.date_range('2025-09-01', '2025-09-30', freq='D')
        
        # Create arrays for all days
        narvesen_articles = []
        narvesen_impressions = []
        narvesen_bmq = []
        reitan_articles = []
        reitan_impressions = []
        reitan_bmq = []
        
        for date in dates:
            # Narvesen data for this date
            narvesen_day = narvesen_daily[narvesen_daily['Published Date'].dt.date == date.date()]
            narvesen_articles.append(narvesen_day['Article'].sum() if not narvesen_day.empty else 0)
            narvesen_impressions.append(narvesen_day['Impressions'].sum() if not narvesen_day.empty else 0)
            narvesen_bmq.append(narvesen_day['BMQ'].mean() if not narvesen_day.empty else 0)
            
            # Reitan data for this date
            reitan_day = reitan_daily[reitan_daily['Published Date'].dt.date == date.date()]
            reitan_articles.append(reitan_day['Article'].sum() if not reitan_day.empty else 0)
            reitan_impressions.append(reitan_day['Impressions'].sum() if not reitan_day.empty else 0)
            reitan_bmq.append(reitan_day['BMQ'].mean() if not reitan_day.empty else 0)
        
        data = {
            'Date': dates,
            'Narvesen_Articles': narvesen_articles,
            'Narvesen_Impressions': narvesen_impressions,
            'Narvesen_BMQ': narvesen_bmq,
            'Reitan_Articles': reitan_articles,
            'Reitan_Impressions': reitan_impressions,
            'Reitan_BMQ': reitan_bmq
        }
        
        return pd.DataFrame(data)
        
    except Exception as e:
        st.error(f"Error loading monthly data: {e}")
        # Fallback to sample data if files can't be read
        dates = pd.date_range('2025-09-01', '2025-09-30', freq='D')
        np.random.seed(42)
        narvesen_articles = np.random.poisson(3, 30)
        narvesen_impressions = np.random.poisson(3000, 30)
        reitan_articles = np.random.poisson(4, 30)
        reitan_impressions = np.random.poisson(4000, 30)
        
        sample_data = {
            'Date': dates,
            'Narvesen_Articles': narvesen_articles,
            'Narvesen_Impressions': narvesen_impressions,
            'Narvesen_BMQ': np.random.uniform(0.3, 0.8, 30),
            'Reitan_Articles': reitan_articles,
            'Reitan_Impressions': reitan_impressions,
            'Reitan_BMQ': np.random.uniform(0.4, 0.9, 30)
        }
        return pd.DataFrame(sample_data)

@st.cache_data
def load_archetype_data():
    """Load archetype data from Excel files and process real data"""
    try:
        # Load data from Excel files
        narvesen_df = pd.read_excel(DATA_ROOT, sheet_name='Raw Data')
        reitan_df = pd.read_excel(REITAN_DATA_ROOT, sheet_name='Raw Data')
        
        # Process Narvesen archetypes
        if 'Top Archetype' in narvesen_df.columns:
            narvesen_archetype_counts = narvesen_df['Top Archetype'].value_counts()
            narvesen_total = narvesen_archetype_counts.sum()
            narvesen_archetypes = {k: round((v/narvesen_total)*100, 1) for k, v in narvesen_archetype_counts.items()}
        else:
            narvesen_archetypes = {}
        
        # Process Reitan archetypes
        if 'Top Archetype' in reitan_df.columns:
            reitan_archetype_counts = reitan_df['Top Archetype'].value_counts()
            reitan_total = reitan_archetype_counts.sum()
            reitan_archetypes = {k: round((v/reitan_total)*100, 1) for k, v in reitan_archetype_counts.items()}
        else:
            reitan_archetypes = {}
        
        return narvesen_archetypes, reitan_archetypes
        
    except Exception as e:
        st.error(f"Error loading archetype data: {e}")
        # Fallback to sample data
        narvesen_archetypes = {
            'Financial Performance': 45,
            'Market Competition': 32,
            'Retail Operations': 28,
            'Profitability Analysis': 22,
            'Nordic Market': 18
        }
        
        reitan_archetypes = {
            'Financial Performance': 52,
            'Market Competition': 38,
            'Retail Operations': 35,
            'Profitability Analysis': 29,
            'Nordic Market': 24
        }
        
        return narvesen_archetypes, reitan_archetypes

@st.cache_data
def load_topic_data():
    """Load topic data from Excel files and process real data"""
    try:
        # Load data from Excel files
        narvesen_df = pd.read_excel(DATA_ROOT, sheet_name='Raw Data')
        reitan_df = pd.read_excel(REITAN_DATA_ROOT, sheet_name='Raw Data')
        
        # Process Narvesen topics from cluster topic columns
        narvesen_topics = {}
        topic_columns = ['Cluster_Topic1', 'Cluster_Topic2', 'Cluster_Topic3']
        narvesen_all_topics = []
        
        for col in topic_columns:
            if col in narvesen_df.columns:
                topics = narvesen_df[col].dropna().tolist()
                narvesen_all_topics.extend(topics)
        
        if narvesen_all_topics:
            narvesen_topic_counts = pd.Series(narvesen_all_topics).value_counts()
            narvesen_total = narvesen_topic_counts.sum()
            narvesen_topics = {k: round((v/narvesen_total)*100, 1) for k, v in narvesen_topic_counts.items()}
        
        # Process Reitan topics from cluster topic columns
        reitan_topics = {}
        reitan_all_topics = []
        
        for col in topic_columns:
            if col in reitan_df.columns:
                topics = reitan_df[col].dropna().tolist()
                reitan_all_topics.extend(topics)
        
        if reitan_all_topics:
            reitan_topic_counts = pd.Series(reitan_all_topics).value_counts()
            reitan_total = reitan_topic_counts.sum()
            reitan_topics = {k: round((v/reitan_total)*100, 1) for k, v in reitan_topic_counts.items()}
        
        return narvesen_topics, reitan_topics
        
    except Exception as e:
        st.error(f"Error loading topic data: {e}")
        # Fallback to sample data
        narvesen_topics = {
            'Financial Performance & Profitability': 67,
            'Market Competition & Benchmarking': 45,
            'Retail Operations & Efficiency': 38,
            'Nordic Market Analysis': 29,
            'Brand Portfolio Management': 22
        }
        
        reitan_topics = {
            'Financial Performance & Profitability': 78,
            'Market Competition & Benchmarking': 56,
            'Retail Operations & Efficiency': 42,
            'Nordic Market Analysis': 35,
            'Brand Portfolio Management': 28
        }
        
        return narvesen_topics, reitan_topics

@st.cache_data
def load_top_articles():
    """Load top 3 articles by impressions for each brand"""
    try:
        # Load data from Excel files
        narvesen_df = pd.read_excel(DATA_ROOT, sheet_name='Raw Data')
        reitan_df = pd.read_excel(REITAN_DATA_ROOT, sheet_name='Raw Data')
        
        # Process Narvesen top articles
        narvesen_top = narvesen_df.nlargest(3, 'Impressions')[['Title', 'Impressions', 'Published Date', 'Link']].copy()
        narvesen_top['Brand'] = 'Narvesen'
        
        # Process Reitan top articles
        reitan_top = reitan_df.nlargest(3, 'Impressions')[['Title', 'Impressions', 'Published Date', 'Link']].copy()
        reitan_top['Brand'] = 'Reitan'
        
        # Combine and return
        all_top_articles = pd.concat([narvesen_top, reitan_top], ignore_index=True)
        return all_top_articles
        
    except Exception as e:
        st.error(f"Error loading top articles: {e}")
        # Fallback to sample data
        sample_data = {
            'Title': ['Sample Article 1', 'Sample Article 2', 'Sample Article 3'],
            'Impressions': [50000, 45000, 40000],
            'Published Date': ['2025-09-15', '2025-09-20', '2025-09-25'],
            'Brand': ['Narvesen', 'Narvesen', 'Narvesen']
        }
        return pd.DataFrame(sample_data)

@st.cache_data
def load_sentiment_data():
    """Load sentiment data from Excel files"""
    try:
        # Load data from Excel files
        narvesen_df = pd.read_excel(DATA_ROOT, sheet_name='Raw Data')
        reitan_df = pd.read_excel(REITAN_DATA_ROOT, sheet_name='Raw Data')
        
        # Process sentiment data
        narvesen_sentiment = {}
        reitan_sentiment = {}
        
        if 'Sentiment' in narvesen_df.columns:
            narvesen_sentiment_counts = narvesen_df['Sentiment'].value_counts(normalize=True) * 100
            narvesen_sentiment = narvesen_sentiment_counts.to_dict()
        
        if 'Sentiment' in reitan_df.columns:
            reitan_sentiment_counts = reitan_df['Sentiment'].value_counts(normalize=True) * 100
            reitan_sentiment = reitan_sentiment_counts.to_dict()
        
        return narvesen_sentiment, reitan_sentiment
        
    except Exception as e:
        st.error(f"Error loading sentiment data: {e}")
        # Fallback to sample data
        narvesen_sentiment = {'Positive': 45, 'Neutral': 35, 'Negative': 20}
        reitan_sentiment = {'Positive': 50, 'Neutral': 30, 'Negative': 20}
        return narvesen_sentiment, reitan_sentiment

@st.cache_data
def load_compos_matrix_data():
    """Load data for compos matrix (Volume vs Quality)"""
    try:
        # Load data from Excel files
        narvesen_df = pd.read_excel(DATA_ROOT, sheet_name='Raw Data')
        reitan_df = pd.read_excel(REITAN_DATA_ROOT, sheet_name='Raw Data')
        
        # Process data for compos matrix
        narvesen_volume = len(narvesen_df)
        narvesen_quality = narvesen_df['BMQ'].mean() if 'BMQ' in narvesen_df.columns else 0
        
        reitan_volume = len(reitan_df)
        reitan_quality = reitan_df['BMQ'].mean() if 'BMQ' in reitan_df.columns else 0
        
        # Get archetype data for display
        narvesen_archetypes = {}
        reitan_archetypes = {}
        
        if 'Top Archetype' in narvesen_df.columns:
            narvesen_archetype_counts = narvesen_df['Top Archetype'].value_counts()
            narvesen_archetypes = narvesen_archetype_counts.head(3).to_dict()
        
        if 'Top Archetype' in reitan_df.columns:
            reitan_archetype_counts = reitan_df['Top Archetype'].value_counts()
            reitan_archetypes = reitan_archetype_counts.head(3).to_dict()
        
        return {
            'Narvesen': {'Volume': narvesen_volume, 'Quality': narvesen_quality, 'Archetypes': narvesen_archetypes},
            'Reitan': {'Volume': reitan_volume, 'Quality': reitan_quality, 'Archetypes': reitan_archetypes}
        }
        
    except Exception as e:
        st.error(f"Error loading compos matrix data: {e}")
        # Fallback to sample data
        return {
            'Narvesen': {'Volume': 25, 'Quality': 0.65, 'Archetypes': {'Financial Performance': 8, 'Market Competition': 6, 'Retail Operations': 5}},
            'Reitan': {'Volume': 30, 'Quality': 0.72, 'Archetypes': {'Financial Performance': 10, 'Market Competition': 8, 'Retail Operations': 7}}
        }

# Load data
df = load_monthly_data()
narvesen_archetypes, reitan_archetypes = load_archetype_data()
narvesen_topics, reitan_topics = load_topic_data()
top_articles = load_top_articles()
narvesen_sentiment, reitan_sentiment = load_sentiment_data()
compos_matrix_data = load_compos_matrix_data()

# Header
st.title("📊 Reitan Monthly Dashboard")
st.markdown("**Period:** September 2025")

# Monthly aggregated metrics
st.markdown('<div class="section-header">📈 Monthly Overview</div>', unsafe_allow_html=True)

# Create tabs for monthly overview
overview_tab1, overview_tab2, overview_tab3 = st.tabs(["🏢 Narvesen", "🏢 Reitan", "📊 Comparison"])

with overview_tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        total_articles = df['Narvesen_Articles'].sum()
        
        # Use the same card styling as the daily dashboard
        st.markdown(
            f"""
            <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px;">
                <h5 style="margin:0;">📰 Total Articles (September)</h5>
                <h3 style="margin:5px 0;">{total_articles:,}</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col2:
        total_impressions = df['Narvesen_Impressions'].sum()
        
        # Use the same card styling as the daily dashboard
        st.markdown(
            f"""
            <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px;">
                <h5 style="margin:0;">👁️ Total Impressions (September)</h5>
                <h3 style="margin:5px 0;">{total_impressions:,}</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )

with overview_tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        total_articles = df['Reitan_Articles'].sum()
        
        # Use the same card styling as the daily dashboard
        st.markdown(
            f"""
            <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px;">
                <h5 style="margin:0;">📰 Total Articles (September)</h5>
                <h3 style="margin:5px 0;">{total_articles:,}</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col2:
        total_impressions = df['Reitan_Impressions'].sum()
        
        # Use the same card styling as the daily dashboard
        st.markdown(
            f"""
            <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px;">
                <h5 style="margin:0;">👁️ Total Impressions (September)</h5>
                <h3 style="margin:5px 0;">{total_impressions:,}</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )

with overview_tab3:
    col1, col2 = st.columns(2)
    
    with col1:
        # Comparison metrics
        narvesen_articles = df['Narvesen_Articles'].sum()
        reitan_articles = df['Reitan_Articles'].sum()
        articles_diff = reitan_articles - narvesen_articles
        
        st.markdown(
            f"""
            <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px;">
                <h5 style="margin:0;">📰 Articles Comparison</h5>
                <h3 style="margin:5px 0;">Narvesen: {narvesen_articles:,}</h3>
                <h3 style="margin:5px 0;">Reitan: {reitan_articles:,}</h3>
                <p style="margin:0; color:green;">Reitan +{articles_diff:,} more</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col2:
        narvesen_impressions = df['Narvesen_Impressions'].sum()
        reitan_impressions = df['Reitan_Impressions'].sum()
        impressions_diff = reitan_impressions - narvesen_impressions
        
        st.markdown(
            f"""
            <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px;">
                <h5 style="margin:0;">👁️ Impressions Comparison</h5>
                <h3 style="margin:5px 0;">Narvesen: {narvesen_impressions:,}</h3>
                <h3 style="margin:5px 0;">Reitan: {reitan_impressions:,}</h3>
                <p style="margin:0; color:green;">Reitan +{impressions_diff:,} more</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# Compos Matrix section (moved up)
st.markdown('<div class="section-header">🏷️ Brand Archetypes: Volume vs. Quality</div>', unsafe_allow_html=True)

# Create the compos matrix scatter plot
fig_compos = go.Figure()

# Add Narvesen point
narvesen_data = compos_matrix_data['Narvesen']
fig_compos.add_trace(go.Scatter(
    x=[narvesen_data['Volume']],
    y=[narvesen_data['Quality']],
    mode='markers+text',
    name='Narvesen',
    marker=dict(size=15, color='#1f77b4'),
    text=['Narvesen'],
    textposition='top center',
    hovertemplate=f"<b>Narvesen</b><br>Volume: {narvesen_data['Volume']}<br>Quality: {narvesen_data['Quality']:.2f}<br>Archetypes: {', '.join(narvesen_data['Archetypes'].keys())}<extra></extra>"
))

# Add Reitan point
reitan_data = compos_matrix_data['Reitan']
fig_compos.add_trace(go.Scatter(
    x=[reitan_data['Volume']],
    y=[reitan_data['Quality']],
    mode='markers+text',
    name='Reitan',
    marker=dict(size=15, color='#ff7f0e'),
    text=['Reitan'],
    textposition='top center',
    hovertemplate=f"<b>Reitan</b><br>Volume: {reitan_data['Volume']}<br>Quality: {reitan_data['Quality']:.2f}<br>Archetypes: {', '.join(reitan_data['Archetypes'].keys())}<extra></extra>"
))

# Add annotations with top 3 archetypes for each brand
narvesen_archetypes_text = "<br>".join([f"{k} ({v})" for k, v in list(narvesen_data['Archetypes'].items())[:3]])
reitan_archetypes_text = "<br>".join([f"{k} ({v})" for k, v in list(reitan_data['Archetypes'].items())[:3]])

# Add Narvesen annotation
fig_compos.add_annotation(
    x=narvesen_data['Volume'],
    y=narvesen_data['Quality'],
    text=f"<b>Narvesen</b><br>{narvesen_archetypes_text}",
    showarrow=False,
    font=dict(size=9),
    align="center",
    bgcolor="white",
    borderpad=4
)

# Add Reitan annotation
fig_compos.add_annotation(
    x=reitan_data['Volume'],
    y=reitan_data['Quality'],
    text=f"<b>Reitan</b><br>{reitan_archetypes_text}",
    showarrow=False,
    font=dict(size=9),
    align="center",
    bgcolor="white",
    borderpad=4
)

# Update layout
fig_compos.update_layout(
    title="Company Positioning by Volume & Quality",
    xaxis_title="Volume (Articles)",
    yaxis_title="Quality (Avg. BMQ)",
    template='plotly_white',
    height=500,
    showlegend=True,
    margin=dict(l=40, r=40, t=40, b=40),
    dragmode=False
)

st.plotly_chart(fig_compos, use_container_width=True)

# Add explanation
st.markdown("""
**Quality definition:** The Brand Mention Quality (BMQ) score is a measure of how well the brand is represented in the article. 
It takes into account the [PageRank](https://en.wikipedia.org/wiki/PageRank) of the website, how often the brand is mentioned 
and where the brand is mentioned in the article. The BMQ score ranges from 0 to 1, where 1 is the best possible score.
""")

# Monthly volume analysis with tabs
st.markdown('<div class="section-header">📊 Monthly Volume Analysis</div>', unsafe_allow_html=True)

# Create tabs for volume analysis
volume_tab1, volume_tab2, volume_tab3 = st.tabs(["📰 Articles", "👁️ Impressions", "⭐ BMQ"])

with volume_tab1:
    # Articles graph
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
        title="Daily Articles - Both Brands (September 2025)",
        xaxis_title="Date",
        yaxis_title="Number of Articles",
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    st.plotly_chart(fig_articles, use_container_width=True)

with volume_tab2:
    # Impressions graph
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
        title="Daily Impressions - Both Brands (September 2025)",
        xaxis_title="Date",
        yaxis_title="Impressions",
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    st.plotly_chart(fig_impressions, use_container_width=True)

with volume_tab3:
    # BMQ graph
    fig_bmq = go.Figure()
    
    # Add Narvesen line
    fig_bmq.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Narvesen_BMQ'],
        mode='lines+markers',
        name='Narvesen',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8)
    ))
    
    # Add Reitan line
    fig_bmq.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Reitan_BMQ'],
        mode='lines+markers',
        name='Reitan',
        line=dict(color='#ff7f0e', width=3),
        marker=dict(size=8)
    ))
    
    fig_bmq.update_layout(
        title="Daily Average BMQ - Both Brands (September 2025)",
        xaxis_title="Date",
        yaxis_title="Average BMQ",
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    st.plotly_chart(fig_bmq, use_container_width=True)

# Top Archetypes section
st.markdown('<div class="section-header">🎯 Top Archetypes</div>', unsafe_allow_html=True)

# Create tabs for archetypes
archetype_tab1, archetype_tab2, archetype_tab3 = st.tabs(["🏢 Narvesen", "🏢 Reitan", "📈 Comparison"])

with archetype_tab1:
    col1, col2, col3 = st.columns(3)
    
    # Get top 3 archetypes for Narvesen
    top_archetypes = sorted(narvesen_archetypes.items(), key=lambda x: x[1], reverse=True)[:3]
    
    for i, (archetype, percentage) in enumerate(top_archetypes, 1):
        with [col1, col2, col3][i-1]:
            # Use the same card styling as the daily dashboard
            st.markdown(
                f"""
                <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px;">
                    <h5 style="margin:0;">#{i} {archetype}</h5>
                    <h3 style="margin:5px 0;">{percentage:.1f}%</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

with archetype_tab2:
    col1, col2, col3 = st.columns(3)
    
    # Get top 3 archetypes for Reitan
    top_archetypes = sorted(reitan_archetypes.items(), key=lambda x: x[1], reverse=True)[:3]
    
    for i, (archetype, percentage) in enumerate(top_archetypes, 1):
        with [col1, col2, col3][i-1]:
            # Use the same card styling as the daily dashboard
            st.markdown(
                f"""
                <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px;">
                    <h5 style="margin:0;">#{i} {archetype}</h5>
                    <h3 style="margin:5px 0;">{percentage:.1f}%</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

with archetype_tab3:
    # Create comparison chart
    fig_archetypes = go.Figure()
    
    # Add bars for both brands
    fig_archetypes.add_trace(go.Bar(
        name='Narvesen',
        x=list(narvesen_archetypes.keys()),
        y=list(narvesen_archetypes.values()),
        marker_color='#1f77b4'
    ))
    
    fig_archetypes.add_trace(go.Bar(
        name='Reitan',
        x=list(reitan_archetypes.keys()),
        y=list(reitan_archetypes.values()),
        marker_color='#ff7f0e'
    ))
    
    fig_archetypes.update_layout(
        title="Archetype Comparison",
        xaxis_title="Archetype",
        yaxis_title="Percentage",
        barmode='group',
        template='plotly_white',
        height=400
    )
    
    st.plotly_chart(fig_archetypes, use_container_width=True)

# Top Topics section
st.markdown('<div class="section-header">📝 Top Topics</div>', unsafe_allow_html=True)

# Create tabs for topics
topic_tab1, topic_tab2 = st.tabs(["🏢 Narvesen", "🏢 Reitan"])

with topic_tab1:
    col1, col2, col3 = st.columns(3)
    
    # Get top 3 topics for Narvesen
    top_topics = sorted(narvesen_topics.items(), key=lambda x: x[1], reverse=True)[:3]
    
    for i, (topic, percentage) in enumerate(top_topics, 1):
        with [col1, col2, col3][i-1]:
            # Use the same card styling as the daily dashboard
            st.markdown(
                f"""
                <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px;">
                    <h5 style="margin:0;">#{i} {topic}</h5>
                    <h3 style="margin:5px 0;">{percentage:.1f}%</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

with topic_tab2:
    col1, col2, col3 = st.columns(3)
    
    # Get top 3 topics for Reitan
    top_topics = sorted(reitan_topics.items(), key=lambda x: x[1], reverse=True)[:3]
    
    for i, (topic, percentage) in enumerate(top_topics, 1):
        with [col1, col2, col3][i-1]:
            # Use the same card styling as the daily dashboard
            st.markdown(
                f"""
                <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px;">
                    <h5 style="margin:0;">#{i} {topic}</h5>
                    <h3 style="margin:5px 0;">{percentage:.1f}%</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

# Top 3 Articles section
st.markdown('<div class="section-header">📰 Top 3 Articles by Impressions</div>', unsafe_allow_html=True)

# Create tabs for top articles
articles_tab1, articles_tab2 = st.tabs(["🏢 Narvesen", "🏢 Reitan"])

with articles_tab1:
    # Get top 3 Narvesen articles
    narvesen_articles = top_articles[top_articles['Brand'] == 'Narvesen'].head(3)
    
    if not narvesen_articles.empty:
        for i, (_, article) in enumerate(narvesen_articles.iterrows(), 1):
            # Create clickable link if URL is available
            link = article['Link'] if pd.notna(article['Link']) and article['Link'] else "#"
            title_html = f'<a href="{link}" target="_blank" style="color: #1f77b4; text-decoration: none;">{article["Title"]}</a>' if link != "#" else article['Title']
            
            st.markdown(
                f"""
                <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px;">
                    <h5 style="margin:0;">#{i} {title_html}</h5>
                    <p style="margin:5px 0; color:#666;">Impressions: {article['Impressions']:,}</p>
                    <p style="margin:5px 0; color:#666;">Published: {article['Published Date']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No articles found for Narvesen")

with articles_tab2:
    # Get top 3 Reitan articles
    reitan_articles = top_articles[top_articles['Brand'] == 'Reitan'].head(3)
    
    if not reitan_articles.empty:
        for i, (_, article) in enumerate(reitan_articles.iterrows(), 1):
            # Create clickable link if URL is available
            link = article['Link'] if pd.notna(article['Link']) and article['Link'] else "#"
            title_html = f'<a href="{link}" target="_blank" style="color: #1f77b4; text-decoration: none;">{article["Title"]}</a>' if link != "#" else article['Title']
            
            st.markdown(
                f"""
                <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px;">
                    <h5 style="margin:0;">#{i} {title_html}</h5>
                    <p style="margin:5px 0; color:#666;">Impressions: {article['Impressions']:,}</p>
                    <p style="margin:5px 0; color:#666;">Published: {article['Published Date']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No articles found for Reitan")


# Footer
st.markdown("---")
st.markdown("*Dashboard updated: September 30, 2025*")
