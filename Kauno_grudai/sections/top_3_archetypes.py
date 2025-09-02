import os
import pandas as pd
import streamlit as st
from utils.config import DATA_ROOT, BRAND_NAME_MAPPING, BRANDS, BRAND_COLORS

def _normalize_brand(name: str) -> str:
    if not isinstance(name, str):
        return ""
    base = name.split("|")[0].strip()
    cleaned = "".join(ch.lower() if (ch.isalnum() or ch.isspace()) else " " for ch in base)
    return " ".join(cleaned.split())

def _get_compos_file_path(source: str, brand: str) -> str:
    """
    Returns the path to the compos analysis file for a given source and brand.
    source: 'pr', 'linkedin', or 'facebook'
    """
    if source == "pr":
        folder = os.path.join(DATA_ROOT, "agility")
    elif source in {"linkedin", "facebook"}:
        folder = os.path.join(DATA_ROOT, "social_media", "compos")
    else:
        return None
    # Try matching by normalized brand name
    norm = _normalize_brand(brand)
    for fname in os.listdir(folder):
        if fname.startswith("~$") or not fname.lower().endswith("_compos_analysis.xlsx"):
            continue
        fname_norm = _normalize_brand(fname.replace("_compos_analysis.xlsx", "").replace(".xlsx", ""))
        if norm in fname_norm or fname_norm in norm:
            return os.path.join(folder, fname)
    return None

def load_top_3_archetypes(source: str, brand: str):
    """
    Loads the top 3 archetypes for a brand from the compos analysis file for the given source.
    Returns a list of dicts: [{archetype, percentage, count}]
    """
    path = _get_compos_file_path(source, brand)
    if not path or not os.path.exists(path):
        return []
    try:
        # Try to read 'Raw Data' sheet first
        try:
            df = pd.read_excel(path, sheet_name="Raw Data")
        except Exception:
            df = pd.read_excel(path)
    except Exception:
        return []
    if 'Top Archetype' not in df.columns:
        return []
    vc = df['Top Archetype'].dropna().value_counts()
    total = int(vc.sum()) if vc.sum() else 0
    top3 = vc.head(3)
    result = []
    for archetype, count in top3.items():
        pct = (count / total) * 100 if total > 0 else 0
        result.append({'archetype': archetype, 'percentage': pct, 'count': int(count)})
    return result

def render_top_3_archetypes(source: str, brand: str):
    """
    Renders 3 cards for the top 3 archetypes for a brand and source.
    """
    archetypes = load_top_3_archetypes(source, brand)
    if not archetypes:
        st.info(f"No archetype data found for {brand} [{source}].")
        return
    cols = st.columns(3)
    for i, arch in enumerate(archetypes):
        with cols[i]:
            st.markdown(f"""
            <div style='border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px;'>
                <h5 style='margin:0;'>{arch['archetype']}</h5>
                <h3 style='margin:5px 0;'>{arch['percentage']:.1f}%</h3>
            </div>
            """, unsafe_allow_html=True)
