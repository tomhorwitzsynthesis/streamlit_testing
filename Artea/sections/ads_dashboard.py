# streamlit_app.py

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta
from utils.date_utils import get_selected_date_range
from utils.file_io import load_ads_data
import ast
# NEW imports
import os
import glob
from utils.file_io import load_agility_data
from utils.config import BRANDS

# Added: local path for ads compos files
ADS_COMPOS_DIR = os.path.join("data", "ads", "compos")


def _parse_platforms(val):
    try:
        if isinstance(val, str):
            return ast.literal_eval(val)
        elif isinstance(val, list):
            return val
    except Exception:
        return []
    return []


# Added: brand normalization helper to align names across sources
def _normalize_brand(name: str) -> str:
    if not isinstance(name, str):
        return ""
    base = name.split("|")[0].strip()
    cleaned = "".join(ch.lower() if (ch.isalnum() or ch.isspace()) else " " for ch in base)
    return " ".join(cleaned.split())


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


# --- New helpers pulled from LP dashboard (adapted to current data layout) ---

@st.cache_data(ttl=0)
def _load_creativity():
    path = os.path.join("data", "creativity", "creativity_ranking.xlsx")
    if not os.path.exists(path):
        return pd.DataFrame(columns=['brand', 'rank', 'originality_score', 'justification', 'examples'])
    try:
        df_cre = pd.read_excel(path, sheet_name="Overall Ranking")
        df_cre = df_cre.rename(columns={c: str(c).lower() for c in df_cre.columns})
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


# New: Load brand strength from data/ads/compos (fallback to Agility if empty)
def _load_brand_strength_from_ads_compos():
    strength = {}
    if os.path.isdir(ADS_COMPOS_DIR):
        for path in glob.glob(os.path.join(ADS_COMPOS_DIR, "*.xlsx")):
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


# Kept for fallback

def _compute_brand_strength_from_agility():
    """Return dict brand -> % of dominant archetype from Agility data."""
    strength = {}
    for brand in BRANDS:
        df_ag = load_agility_data(brand)
        if df_ag is None or df_ag.empty:
            continue
        if 'Top Archetype' in df_ag.columns and len(df_ag.dropna(subset=['Top Archetype'])) > 0:
            vc = df_ag['Top Archetype'].dropna().value_counts()
            pct = float((vc.max() / vc.sum()) * 100) if vc.sum() > 0 else 0.0
            strength[brand] = pct
    return strength


# New: Load top archetypes from data/ads/compos (fallback to Agility if empty)
def _load_top_archetypes_from_ads_compos():
    results = {}
    if os.path.isdir(ADS_COMPOS_DIR):
        for path in glob.glob(os.path.join(ADS_COMPOS_DIR, "*.xlsx")):
            fname = os.path.basename(path)
            if fname.startswith("~$"):
                continue
            brand_display = fname.replace("_compos_analysis.xlsx", "").replace(".xlsx", "").strip()
            try:
                try:
                    df_comp = pd.read_excel(path, sheet_name="Raw Data")
                except Exception:
                    df_comp = pd.read_excel(path)
                if 'Top Archetype' in df_comp.columns:
                    vc = df_comp['Top Archetype'].dropna().value_counts()
                    total = int(vc.sum()) if vc.sum() else 0
                    top3 = vc.head(3)
                    items = []
                    for archetype, count in top3.items():
                        pct = (count / total) * 100 if total > 0 else 0
                        items.append({'archetype': archetype, 'percentage': pct, 'count': int(count)})
                    if items:
                        results[brand_display] = items
            except Exception:
                pass
    return results


def _load_top_archetypes_from_agility():
    """Return dict brand -> list of top 3 archetypes with percentage and count."""
    results = {}
    for brand in BRANDS:
        df_ag = load_agility_data(brand)
        if df_ag is None or df_ag.empty or 'Top Archetype' not in df_ag.columns:
            continue
        vc = df_ag['Top Archetype'].dropna().value_counts()
        total = int(vc.sum()) if vc.sum() else 0
        top3 = vc.head(3)
        items = []
        for archetype, count in top3.items():
            pct = (count / total) * 100 if total > 0 else 0
            items.append({
                'archetype': archetype,
                'percentage': pct,
                'count': int(count)
            })
        if items:
            results[brand] = items
    return results


@st.cache_data(ttl=0)
def _load_key_advantages():
    path = os.path.join("data", "key_advantages", "key_advantages.xlsx")
    if not os.path.exists(path):
        return {}
    advantages = {}
    try:
        xls = pd.ExcelFile(path)
        for sheet_name in xls.sheet_names:
            brand_name = sheet_name.replace("_", " ")
            df_adv = pd.read_excel(path, sheet_name=sheet_name)
            df_adv.columns = [str(col).lower().strip() for col in df_adv.columns]
            required_cols = ['advantage_id', 'title', 'evidence_list', 'example_ad_index', 'example_quote']
            for col in required_cols:
                if col not in df_adv.columns:
                    df_adv[col] = ""
            advantages[brand_name] = df_adv[required_cols]
    except Exception as e:
        st.error(f"Error loading key advantages: {e}")
    return advantages


def _load_key_advantages_summary():
    path = os.path.join("data", "key_advantages", "key_advantages_summary.xlsx")
    if not os.path.exists(path):
        return ""
    try:
        df_summary = pd.read_excel(path)
        summary_col = None
        for col in df_summary.columns:
            if 'summary' in str(col).lower():
                summary_col = col
                break
        if summary_col and len(df_summary) > 0:
            return str(df_summary[summary_col].iloc[0])
        else:
            return ""
    except Exception as e:
        st.error(f"Error loading key advantages summary: {e}")
        return ""


def _format_simple_metric_card(label, val, pct=None, rank_now=None, total_ranks=None):
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

    # Summary stats (midpoint split) for potential future use; old 4 cards removed
    mid_date = start_date + (end_date - start_date) / 2
    reach_stats = _summary(df_filtered, 'reach', mid_date)
    df_filtered['ad_count'] = 1
    ads_stats = _summary(df_filtered, 'ad_count', mid_date)
    duration_stats = _summary(df_filtered, 'duration_days', mid_date) if 'duration_days' in df_filtered.columns else None

    # --- Brand Summary (cards + creativity analysis) ---
    st.markdown("### Brand Summary")

    # Compute 6-month reach totals and ranks using the fixed window
    reach_6m = df_fixed.groupby('brand')['reach'].sum() if not df_fixed.empty else pd.Series(dtype=float)
    reach_mean = reach_6m.mean() if len(reach_6m) else 0
    reach_ranks = reach_6m.rank(ascending=False, method="min") if len(reach_6m) else pd.Series(dtype=float)

    # Brand strength from compos files in data/ads/compos, fallback to Agility
    strength_map = _load_brand_strength_from_ads_compos()
    if not strength_map:
        strength_map = _compute_brand_strength_from_agility()
    if strength_map:
        bs_df = pd.DataFrame({'brand': list(strength_map.keys()), 'strength': list(strength_map.values())})
        bs_df['brand_norm'] = bs_df['brand'].apply(_normalize_brand)
        bs_df['rank'] = bs_df['strength'].rank(ascending=False, method='min')
        bs_mean = bs_df['strength'].mean() if len(bs_df) else 0
        bs_df['delta_vs_mean_pct'] = ((bs_df['strength'] - bs_mean) / (bs_mean if bs_mean != 0 else 1)) * 100
    else:
        bs_df = pd.DataFrame(columns=['brand', 'brand_norm', 'strength', 'rank', 'delta_vs_mean_pct'])
        bs_mean = 0

    creativity_df = _load_creativity()
    if not creativity_df.empty:
        creativity_df['rank'] = pd.to_numeric(creativity_df['rank'], errors='coerce')
        creativity_df['originality_score'] = pd.to_numeric(creativity_df['originality_score'], errors='coerce')
        cre_mean = creativity_df['originality_score'].mean()
        denom = cre_mean if cre_mean != 0 else 1
        creativity_df['delta_vs_mean_pct'] = ((creativity_df['originality_score'] - denom) / denom) * 100

    # Build brand tabs from union of brands across sources (ads, compos, creativity)
    ads_brands = set(df_fixed['brand'].dropna().unique())
    compos_brands = set(bs_df['brand'].unique()) if len(bs_df) else set()
    creativity_brands = set(creativity_df['brand'].dropna().unique()) if not creativity_df.empty else set()

    # Normalize for matching, but display original preferred names: prefer ads brand if available, else compos/creativity name
    norm_to_display = {}
    for b in compos_brands.union(ads_brands).union(creativity_brands):
        norm = _normalize_brand(b)
        # priority: ads -> compos -> creativity
        if norm not in norm_to_display:
            # choose best display
            if b in ads_brands:
                norm_to_display[norm] = b
            else:
                norm_to_display[norm] = b

    available_brands = sorted(list(norm_to_display.values()))

    if not available_brands:
        st.info("No brands available to display.")
    else:
        brand_tabs = st.tabs(available_brands)
        for i, brand_name in enumerate(available_brands):
            with brand_tabs[i]:
                col1, col2, col3 = st.columns(3)

                # Reach 6 months
                with col1:
                    total_reach = int(reach_6m.get(brand_name, 0)) if len(reach_6m) else 0
                    delta_mean_pct = ((total_reach - (reach_mean if reach_mean != 0 else 1)) / (reach_mean if reach_mean != 0 else 1)) * 100 if reach_mean != 0 else 0
                    rank_now = reach_ranks.get(brand_name, None) if len(reach_ranks) else None
                    _format_simple_metric_card(
                        label="Reach (6 months)",
                        val=f"{total_reach:,}",
                        pct=delta_mean_pct,
                        rank_now=rank_now,
                        total_ranks=len(reach_ranks) if len(reach_ranks) else None
                    )

                # Brand Strength
                with col2:
                    row = bs_df[bs_df['brand_norm'] == _normalize_brand(brand_name)]
                    if not row.empty:
                        strength = float(row['strength'].iloc[0])
                        rank_bs = int(row['rank'].iloc[0])
                        delta_bs = float(row['delta_vs_mean_pct'].iloc[0])
                        _format_simple_metric_card(
                            label="Brand Strength",
                            val=f"{strength:.1f}%",
                            pct=delta_bs,
                            rank_now=rank_bs,
                            total_ranks=len(bs_df)
                        )
                    else:
                        _format_simple_metric_card("Brand Strength", "N/A")

                # Creativity
                with col3:
                    cre_row = creativity_df[creativity_df['brand'].astype(str).str.lower() == brand_name.lower()] if not creativity_df.empty else pd.DataFrame()
                    if not cre_row.empty:
                        score = cre_row['originality_score'].iloc[0]
                        rank_cre = int(cre_row['rank'].iloc[0]) if pd.notna(cre_row['rank'].iloc[0]) else None
                        delta_cre = float(cre_row['delta_vs_mean_pct'].iloc[0]) if pd.notna(cre_row['delta_vs_mean_pct'].iloc[0]) else None
                        _format_simple_metric_card(
                            label="Creativity",
                            val=f"{score:.2f}",
                            pct=delta_cre,
                            rank_now=rank_cre,
                            total_ranks=creativity_df['brand'].nunique() if not creativity_df.empty else None
                        )
                    else:
                        _format_simple_metric_card("Creativity", "N/A")

                # Creativity Analysis section
                if not creativity_df.empty:
                    cre_row = creativity_df[creativity_df['brand'].astype(str).str.lower() == brand_name.lower()]
                    if not cre_row.empty:
                        score = cre_row['originality_score'].iloc[0]
                        rank_cre = int(cre_row['rank'].iloc[0]) if pd.notna(cre_row['rank'].iloc[0]) else None
                        just_text = str(cre_row['justification'].iloc[0]) if pd.notna(cre_row['justification'].iloc[0]) else ""
                        examples_text = str(cre_row['examples'].iloc[0]) if pd.notna(cre_row['examples'].iloc[0]) else ""
                        if just_text or examples_text:
                            st.markdown("#### Creativity Analysis")
                            st.markdown(f"""
                            <div style=\"border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px;\">
                                <h5 style=\"margin:0;\">{brand_name} — {f'Rank {rank_cre} — ' if rank_cre is not None else ''}Score {score:.2f}</h5>
                                {f'<p style=\"margin:8px 0 0; color:#444;\">{just_text}</p>' if just_text else ''}
                                {f'<p style=\"margin:8px 0 0; color:#444;\">Examples: {examples_text}</p>' if examples_text else ''}
                            </div>
                            """, unsafe_allow_html=True)

    # --- Top Archetypes by Company ---
    st.markdown("### Top Archetypes by Company")
    archetypes_data = _load_top_archetypes_from_ads_compos()
    if not archetypes_data:
        archetypes_data = _load_top_archetypes_from_agility()
    if archetypes_data:
        # Compute overall top archetypes
        overall_counts = {}
        overall_total = 0
        for archetypes in archetypes_data.values():
            for item in archetypes:
                archetype = item['archetype']
                count = item['count']
                overall_counts[archetype] = overall_counts.get(archetype, 0) + count
                overall_total += count
        overall_top3 = sorted(overall_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        overall_items = []
        for archetype, count in overall_top3:
            pct = (count / overall_total) * 100 if overall_total > 0 else 0
            overall_items.append({'archetype': archetype, 'percentage': pct, 'count': count})

        tab_labels = ["🌍 Overall"] + list(archetypes_data.keys())
        company_tabs = st.tabs(tab_labels)
        # Overall tab
        with company_tabs[0]:
            st.subheader("Overall - Top 3 Archetypes")
            col1, col2, col3 = st.columns(3)
            for j, archetype_info in enumerate(overall_items):
                col = col1 if j == 0 else col2 if j == 1 else col3
                with col:
                    st.markdown(f"""
                    <div style="border:1px solid #ddd; border-radius:10px; padding:10px; margin-bottom:10px; text-align:center;">
                        <h4 style="margin:0; color:#333;">{archetype_info['archetype']}</h4>
                        <h2 style="margin:5px 0; color:#333; font-size:2.0em;">{archetype_info['percentage']:.1f}%</h2>
                        <p style="margin:0; color:#666; font-size:0.9em;">{archetype_info['count']} items</p>
                    </div>
                    """, unsafe_allow_html=True)
        # Company tabs
        for i, (company, archetypes) in enumerate(archetypes_data.items()):
            with company_tabs[i + 1]:
                st.subheader(f"{company} - Top 3 Archetypes")
                col1, col2, col3 = st.columns(3)
                for j, archetype_info in enumerate(archetypes):
                    col = col1 if j == 0 else col2 if j == 1 else col3
                    with col:
                        st.markdown(f"""
                        <div style="border:1px solid #ddd; border-radius:10px; padding:10px; margin-bottom:10px; text-align:center;">
                            <h4 style="margin:0; color:#333;">{archetype_info['archetype']}</h4>
                            <h2 style="margin:5px 0; color:#333; font-size:2.0em;">{archetype_info['percentage']:.1f}%</h2>
                            <p style="margin:0; color:#666; font-size:0.9em;">{archetype_info['count']} items</p>
                        </div>
                        """, unsafe_allow_html=True)
    else:
        st.info("No archetype data available. Ensure compos files are in data/ads/compos or Agility files contain 'Top Archetype'.")

    # --- Key Advantages ---
    st.markdown("### Key Advantages")
    key_advantages_data = _load_key_advantages()
    if not key_advantages_data:
        st.info("No key advantages data loaded. Place key_advantages.xlsx in data/key_advantages.")
    else:
        brand_tabs = st.tabs(list(key_advantages_data.keys()))
        for i, brand_disp in enumerate(key_advantages_data.keys()):
            with brand_tabs[i]:
                st.subheader(f"{brand_disp} Key Advantages")
                brand_data = key_advantages_data.get(brand_disp)
                if brand_data is None or brand_data.empty:
                    st.info(f"No specific key advantages found for {brand_disp}.")
                else:
                    grouped_data = brand_data.groupby(['title', 'evidence_list']).agg({
                        'example_quote': lambda x: list(x)
                    }).reset_index()
                    col1, col2 = st.columns(2)
                    for idx, (_, row) in enumerate(grouped_data.iterrows()):
                        with (col1 if idx % 2 == 0 else col2):
                            examples_html = ""
                            for ii, example in enumerate(row['example_quote']):
                                if example and str(example).strip():
                                    examples_html += f"<li style='margin:4px 0; color:#444;'>{example}</li>"
                            examples_html = f"<ul style='margin:4px 0 0; padding-left:20px;'>{examples_html}</ul>" if examples_html else "<p style='margin:4px 0 0; color:#444;'>No examples available</p>"
                            st.markdown(f"""
                            <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px; max-height:800px; overflow-y:auto;">
                                <h5 style="margin:0; word-wrap:break-word;">{row['title']}</h5>
                                <p style="margin:8px 0 0; font-weight:bold; color:#333;">Evidence:</p>
                                <p style="margin:4px 0 8px; color:#444; word-wrap:break-word; white-space:pre-wrap;">{row['evidence_list']}</p>
                                <p style="margin:8px 0 0; font-weight:bold; color:#333;">Examples:</p>
                                {examples_html}
                            </div>
                            """, unsafe_allow_html=True)

        st.subheader("Key Advantages Summary")
        summary_text = _load_key_advantages_summary()
        if isinstance(summary_text, str) and summary_text.strip():
            st.markdown(summary_text)
        else:
            # Fallback simple table if summary file absent: show companies only
            try:
                summary_path = os.path.join("data", "key_advantages", "key_advantages_summary.xlsx")
                if os.path.exists(summary_path):
                    summary_df = pd.read_excel(summary_path)
                    st.table(summary_df)
            except Exception:
                pass

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



