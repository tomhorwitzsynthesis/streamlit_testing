import streamlit as st
import pandas as pd
import os
import glob
from utils.file_io import load_agility_data
from utils.config import BRANDS, DATA_ROOT, BRAND_COLORS
from utils.date_utils import get_selected_date_range

BRAND_ORDER = list(BRAND_COLORS.keys())
DEFAULT_COLOR = "#BDBDBD"  # used for any brand not in BRAND_COLORS

AGILITY_DIR = os.path.join(DATA_ROOT, "agility")
CREATIVITY_PATH = os.path.join(DATA_ROOT, "creativity", "creativity_ranking.xlsx")


def _normalize_brand(name: str) -> str:
    """Normalize brand name for consistent matching."""
    if not isinstance(name, str):
        return ""
    base = name.split("|")[0].strip()
    cleaned = "".join(ch.lower() if (ch.isalnum() or ch.isspace()) else " " for ch in base)
    normalized = " ".join(cleaned.split())
    
    # Apply brand mapping to normalize variants to canonical names
    brand_mapping = {
        "kaun": "kauno grudai",
        "thermo": "thermo fisher",
        "acme": "acme",
        "ignitis": "ignitis", 
        "sba": "sba"
    }
    
    return brand_mapping.get(normalized, normalized)


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


@st.cache_data(ttl=0)
def _load_creativity():
    """Load creativity ranking data."""
    if not os.path.exists(CREATIVITY_PATH):
        return pd.DataFrame(columns=['brand', 'rank', 'originality_score', 'justification', 'examples'])
    
    try:
        df_cre = pd.read_excel(CREATIVITY_PATH, sheet_name="Overall Ranking")
        df_cre = df_cre.rename(columns={c: str(c).lower() for c in df_cre.columns})
        
        # Ensure required columns exist
        for col in ['brand', 'rank', 'originality_score']:
            if col not in df_cre.columns:
                df_cre[col] = None
        
        if 'justification' not in df_cre.columns:
            df_cre['justification'] = ""
        if 'examples' not in df_cre.columns:
            df_cre['examples'] = ""
        
        return df_cre[['brand', 'rank', 'originality_score', 'justification', 'examples']]
    except Exception:
        return pd.DataFrame(columns=['brand', 'rank', 'originality_score', 'justification', 'examples'])


def _load_brand_strength_from_agility_compos():
    """Load brand strength from agility compos files."""
    strength = {}
    if not os.path.isdir(AGILITY_DIR):
        return strength
    
    for path in glob.glob(os.path.join(AGILITY_DIR, "*_compos_analysis.xlsx")):
        fname = os.path.basename(path)
        if fname.startswith("~$"):
            continue
        
        brand_display = fname.replace("_compos_analysis.xlsx", "").replace(".xlsx", "").strip()
        
        try:
            try:
                df_comp = pd.read_excel(path, sheet_name="Raw Data")
            except Exception:
                df_comp = pd.read_excel(path)
            
            if 'Top Archetype' in df_comp.columns and len(df_comp.dropna(subset=['Top Archetype'])) > 0:
                vc = df_comp['Top Archetype'].dropna().value_counts()
                pct = float((vc.max() / vc.sum()) * 100) if vc.sum() > 0 else 0.0
                strength[brand_display] = pct
        except Exception:
            pass
    
    return strength


def _compute_pr_reach_totals():
    """Compute total impressions (reach) for each brand from PR data."""
    reach_totals = {}
    start_date, end_date = get_selected_date_range()
    
    for brand in BRANDS:
        df = load_agility_data(brand)
        if df is None or df.empty:
            continue
        
        # Filter by date range
        if "Published Date" in df.columns:
            df['Published Date'] = pd.to_datetime(df['Published Date'], errors='coerce')
            df = df[(df['Published Date'] >= start_date) & (df['Published Date'] <= end_date)]
        
        # Calculate total impressions
        if "Impressions" in df.columns:
            df["Impressions"] = pd.to_numeric(df["Impressions"], errors="coerce").fillna(0)
            total_impressions = df["Impressions"].sum()
            reach_totals[brand] = total_impressions
        else:
            reach_totals[brand] = 0
    
    return reach_totals


def render():
    """Render the PR ranking section with metric cards."""
    st.markdown("### PR Performance Ranking")
    
    # Load creativity data
    creativity_df = _load_creativity()
    if not creativity_df.empty:
        creativity_df['rank'] = pd.to_numeric(creativity_df['rank'], errors='coerce')
        creativity_df['originality_score'] = pd.to_numeric(creativity_df['originality_score'], errors='coerce')
        cre_mean = creativity_df['originality_score'].mean()
        denom = cre_mean if cre_mean != 0 else 1
        creativity_df['delta_vs_mean_pct'] = ((creativity_df['originality_score'] - denom) / denom) * 100
    else:
        st.info("Creativity ranking data not found. Please ensure creativity_ranking.xlsx is available in data/creativity/.")
    
    # Load brand strength from agility compos files
    strength_map = _load_brand_strength_from_agility_compos()
    if strength_map:
        bs_df = pd.DataFrame({'brand': list(strength_map.keys()), 'strength': list(strength_map.values())})
        bs_df['brand_norm'] = bs_df['brand'].apply(_normalize_brand)
        bs_df['rank'] = bs_df['strength'].rank(ascending=False, method='min')
        bs_mean = bs_df['strength'].mean() if len(bs_df) else 0
        bs_df['delta_vs_mean_pct'] = ((bs_df['strength'] - bs_mean) / (bs_mean if bs_mean != 0 else 1)) * 100
    else:
        bs_df = pd.DataFrame(columns=['brand', 'brand_norm', 'strength', 'rank', 'delta_vs_mean_pct'])
        bs_mean = 0
    
    # Compute PR reach totals (impressions)
    reach_totals = _compute_pr_reach_totals()
    
    # Build brand tabs from union of brands across sources
    pr_brands = set(reach_totals.keys())
    compos_brands = set(bs_df['brand'].unique()) if len(bs_df) else set()
    creativity_brands = set(creativity_df['brand'].dropna().unique()) if not creativity_df.empty else set()
    
    # Normalize for matching and aggregate data by canonical brand names
    canonical_brands = {}
    norm_to_display = {}
    
    # Define canonical brand names (preferred display names)
    canonical_names = {
        "kauno grudai": "Kauno grūdai",
        "thermo fisher": "Thermo Fisher", 
        "acme": "Acme",
        "ignitis": "Ignitis",
        "sba": "SBA"
    }
    
    # Aggregate PR reach data by canonical brand
    aggregated_reach = {}
    for brand, reach in reach_totals.items():
        norm = _normalize_brand(brand)
        canonical = canonical_names.get(norm, brand)
        if canonical not in aggregated_reach:
            aggregated_reach[canonical] = 0
        aggregated_reach[canonical] += reach
        norm_to_display[norm] = canonical
    
    # Aggregate brand strength data by canonical brand
    aggregated_strength = {}
    if len(bs_df) > 0:
        for _, row in bs_df.iterrows():
            brand = row['brand']
            strength = row['strength']
            norm = _normalize_brand(brand)
            canonical = canonical_names.get(norm, brand)
            if canonical not in aggregated_strength:
                aggregated_strength[canonical] = []
            aggregated_strength[canonical].append(strength)
            norm_to_display[norm] = canonical
        
        # Average strength values for each canonical brand
        for canonical, strengths in aggregated_strength.items():
            aggregated_strength[canonical] = sum(strengths) / len(strengths)
    
    # Aggregate creativity data by canonical brand
    aggregated_creativity = {}
    if not creativity_df.empty:
        for _, row in creativity_df.iterrows():
            brand = row['brand']
            norm = _normalize_brand(brand)
            canonical = canonical_names.get(norm, brand)
            if canonical not in aggregated_creativity:
                aggregated_creativity[canonical] = row
            norm_to_display[norm] = canonical
    
    # Get all available canonical brands
    all_canonical = set(aggregated_reach.keys()) | set(aggregated_strength.keys()) | set(aggregated_creativity.keys())
    available_brands = sorted(list(all_canonical))
    
    if not available_brands:
        st.info("No brands available to display. Please ensure PR data and compos files are available.")
        return
    
    # Calculate rankings for aggregated data
    reach_series = pd.Series(aggregated_reach)
    reach_mean = reach_series.mean() if len(reach_series) else 0
    reach_ranks = reach_series.rank(ascending=False, method="min") if len(reach_series) else pd.Series(dtype=float)
    
    strength_series = pd.Series(aggregated_strength)
    strength_mean = strength_series.mean() if len(strength_series) else 0
    strength_ranks = strength_series.rank(ascending=False, method="min") if len(strength_series) else pd.Series(dtype=float)
    
    # Create brand tabs
    brand_tabs = st.tabs(available_brands)
    for i, brand_name in enumerate(available_brands):
        with brand_tabs[i]:
            col1, col2, col3 = st.columns(3)
            
            # PR Reach (Impressions)
            with col1:
                total_reach = int(aggregated_reach.get(brand_name, 0))
                delta_mean_pct = ((total_reach - (reach_mean if reach_mean != 0 else 1)) / (reach_mean if reach_mean != 0 else 1)) * 100 if reach_mean != 0 else 0
                rank_now = reach_ranks.get(brand_name, None) if len(reach_ranks) else None
                _format_simple_metric_card(
                    label="Reach",
                    val=f"{total_reach:,}",
                    pct=delta_mean_pct,
                    rank_now=rank_now,
                    total_ranks=len(reach_ranks) if len(reach_ranks) else None
                )
            
            # Brand Strength
            with col2:
                if brand_name in aggregated_strength:
                    strength = float(aggregated_strength[brand_name])
                    rank_bs = int(strength_ranks.get(brand_name, 0))
                    delta_bs = ((strength - (strength_mean if strength_mean != 0 else 1)) / (strength_mean if strength_mean != 0 else 1)) * 100 if strength_mean != 0 else 0
                    _format_simple_metric_card(
                        label="Brand Strength",
                        val=f"{strength:.1f}%",
                        pct=delta_bs,
                        rank_now=rank_bs,
                        total_ranks=len(strength_ranks)
                    )
                else:
                    _format_simple_metric_card("Brand Strength", "N/A")
            
            # Creativity
            with col3:
                if brand_name in aggregated_creativity:
                    cre_row = aggregated_creativity[brand_name]
                    score = cre_row['originality_score']
                    rank_cre = int(cre_row['rank']) if pd.notna(cre_row['rank']) else None
                    delta_cre = float(cre_row['delta_vs_mean_pct']) if pd.notna(cre_row['delta_vs_mean_pct']) else None
                    _format_simple_metric_card(
                        label="Creativity",
                        val=f"{score:.2f}",
                        pct=delta_cre,
                        rank_now=rank_cre,
                        total_ranks=len(aggregated_creativity)
                    )
                else:
                    _format_simple_metric_card("Creativity", "N/A")
            
            # Creativity Analysis section
            if brand_name in aggregated_creativity:
                cre_row = aggregated_creativity[brand_name]
                score = cre_row['originality_score']
                rank_cre = int(cre_row['rank']) if pd.notna(cre_row['rank']) else None
                just_text = str(cre_row['justification']) if pd.notna(cre_row['justification']) else ""
                examples_text = str(cre_row['examples']) if pd.notna(cre_row['examples']) else ""
                
                if just_text or examples_text:
                    st.markdown("#### Creativity Analysis")
                    st.markdown(f"""
                    <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px;">
                        <h5 style="margin:0;">{brand_name} — {f'Rank {rank_cre} — ' if rank_cre is not None else ''}Score {score:.2f}</h5>
                        {f'<p style="margin:8px 0 0; color:#444;">{just_text}</p>' if just_text else ''}
                        {f'<p style="margin:8px 0 0; color:#444;">Examples: {examples_text}</p>' if examples_text else ''}
                    </div>
                    """, unsafe_allow_html=True)
