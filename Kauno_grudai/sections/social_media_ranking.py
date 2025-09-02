import streamlit as st
import pandas as pd
import os
import glob
from utils.file_io import load_social_data
from utils.config import BRANDS, DATA_ROOT, BRAND_COLORS, LINKEDIN_SLUG_TO_BRAND
from utils.date_utils import get_selected_date_range

BRAND_ORDER = list(BRAND_COLORS.keys())
DEFAULT_COLOR = "#BDBDBD"  # used for any brand not in BRAND_COLORS

SOCIAL_MEDIA_COMPOS_DIR = os.path.join(DATA_ROOT, "social_media", "compos")
CREATIVITY_PATH = os.path.join(DATA_ROOT, "creativity", "social_media", "creativity_ranking.xlsx")


def _normalize_brand(name: str) -> str:
    """Normalize brand name for consistent matching."""
    if not isinstance(name, str):
        return ""
    base = name.split("|")[0].strip()
    cleaned = "".join(ch.lower() if (ch.isalnum() or ch.isspace()) else " " for ch in base)
    normalized = " ".join(cleaned.split())
    
    # Apply brand mapping to normalize variants to canonical names
    # This includes LinkedIn slug names from compos files
    brand_mapping = {
        "kaun": "kauno grudai",
        "thermo": "thermo fisher",
        "acme": "acme",
        "ignitis": "ignitis", 
        "sba": "sba",
        # LinkedIn slug mappings from compos files
        "acme grupe": "acme",
        "ignitis grupe": "ignitis",
        "kauno grudai": "kauno grudai",
        "sba invent everyday": "sba",
        "thermo fisher scientific": "thermo fisher"
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


def _load_brand_strength_from_social_compos():
    """Load brand strength from social media compos files."""
    strength = {}
    if not os.path.isdir(SOCIAL_MEDIA_COMPOS_DIR):
        return strength
    
    # Map LinkedIn slug filenames to canonical brand names
    filename_to_brand = {
        "acme-grupe": "Acme",
        "ignitis-grupe": "Ignitis", 
        "kauno-grudai": "Kauno grūdai",
        "sba-invent-everyday": "SBA",
        "thermo-fisher-scientific": "Thermo Fisher"
    }
    
    for path in glob.glob(os.path.join(SOCIAL_MEDIA_COMPOS_DIR, "*_compos_analysis.xlsx")):
        fname = os.path.basename(path)
        if fname.startswith("~$"):
            continue
        
        # Extract brand slug from filename
        brand_slug = fname.replace("_compos_analysis.xlsx", "").replace(".xlsx", "").strip()
        
        # Map to canonical brand name
        brand_display = filename_to_brand.get(brand_slug, brand_slug)
        
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


def _compute_linkedin_engagement_totals():
    """Compute total engagement for each brand from LinkedIn data."""
    engagement_totals = {}
    start_date, end_date = get_selected_date_range()
    
    # Use LinkedIn slug to brand mapping
    for linkedin_slug, brand_display in LINKEDIN_SLUG_TO_BRAND.items():
        df = load_social_data(linkedin_slug, "linkedin")
        if df is None or df.empty:
            continue
        
        # Filter by date range
        if "Published Date" in df.columns:
            df['Published Date'] = pd.to_datetime(df['Published Date'], errors='coerce')
            df = df[(df['Published Date'] >= start_date) & (df['Published Date'] <= end_date)]
        
        # Calculate total engagement (same formula as volume_engagement_trends)
        if not df.empty:
            engagement = (
                df.get("num_likes", pd.Series(0)).sum()
                + df.get("num_comments", pd.Series(0)).sum() * 3
            )
            engagement_totals[brand_display] = engagement
    
    return engagement_totals


def render():
    """Render the social media ranking section with metric cards."""
    st.markdown("### Social Media Performance Ranking")
    
    # Load creativity data
    creativity_df = _load_creativity()
    if not creativity_df.empty:
        creativity_df['rank'] = pd.to_numeric(creativity_df['rank'], errors='coerce')
        creativity_df['originality_score'] = pd.to_numeric(creativity_df['originality_score'], errors='coerce')
        cre_mean = creativity_df['originality_score'].mean()
        denom = cre_mean if cre_mean != 0 else 1
        creativity_df['delta_vs_mean_pct'] = ((creativity_df['originality_score'] - denom) / denom) * 100
    else:
        st.info("Social media creativity ranking data not found. Please ensure creativity_ranking.xlsx is available in data/creativity/social_media/.")
    
    # Load brand strength from social media compos files
    strength_map = _load_brand_strength_from_social_compos()
    if strength_map:
        bs_df = pd.DataFrame({'brand': list(strength_map.keys()), 'strength': list(strength_map.values())})
        bs_df['brand_norm'] = bs_df['brand'].apply(_normalize_brand)
        bs_df['rank'] = bs_df['strength'].rank(ascending=False, method='min')
        bs_mean = bs_df['strength'].mean() if len(bs_df) else 0
        bs_df['delta_vs_mean_pct'] = ((bs_df['strength'] - bs_mean) / (bs_mean if bs_mean != 0 else 1)) * 100
    else:
        bs_df = pd.DataFrame(columns=['brand', 'brand_norm', 'strength', 'rank', 'delta_vs_mean_pct'])
        bs_mean = 0
    
    # Compute LinkedIn engagement totals
    engagement_totals = _compute_linkedin_engagement_totals()
    
    # Build brand tabs from union of brands across sources
    social_brands = set(engagement_totals.keys())
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
    
    # Aggregate social media engagement data by canonical brand
    aggregated_engagement = {}
    for brand, engagement in engagement_totals.items():
        norm = _normalize_brand(brand)
        canonical = canonical_names.get(norm, brand)
        if canonical not in aggregated_engagement:
            aggregated_engagement[canonical] = 0
        aggregated_engagement[canonical] += engagement
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
    all_canonical = set(aggregated_engagement.keys()) | set(aggregated_strength.keys()) | set(aggregated_creativity.keys())
    available_brands = sorted(list(all_canonical))
    
    if not available_brands:
        st.info("No brands available to display. Please ensure LinkedIn data and compos files are available.")
        return
    
    # Calculate rankings for aggregated data
    engagement_series = pd.Series(aggregated_engagement)
    engagement_mean = engagement_series.mean() if len(engagement_series) else 0
    engagement_ranks = engagement_series.rank(ascending=False, method="min") if len(engagement_series) else pd.Series(dtype=float)
    
    strength_series = pd.Series(aggregated_strength)
    strength_mean = strength_series.mean() if len(strength_series) else 0
    strength_ranks = strength_series.rank(ascending=False, method="min") if len(strength_series) else pd.Series(dtype=float)
    
    # Create brand tabs
    brand_tabs = st.tabs(available_brands)
    for i, brand_name in enumerate(available_brands):
        with brand_tabs[i]:
            col1, col2, col3 = st.columns(3)
            
            # Social Media Engagement
            with col1:
                total_engagement = int(aggregated_engagement.get(brand_name, 0))
                delta_mean_pct = ((total_engagement - (engagement_mean if engagement_mean != 0 else 1)) / (engagement_mean if engagement_mean != 0 else 1)) * 100 if engagement_mean != 0 else 0
                rank_now = engagement_ranks.get(brand_name, None) if len(engagement_ranks) else None
                _format_simple_metric_card(
                    label="Engagement",
                    val=f"{total_engagement:,}",
                    pct=delta_mean_pct,
                    rank_now=rank_now,
                    total_ranks=len(engagement_ranks) if len(engagement_ranks) else None
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
