import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from pathlib import Path

st.set_page_config(page_title="Farm Reward Eligibility Dashboard", layout="wide")

PKL_PATH = "merged_data.pkl"
AVG_CSV_PATH = "dashboard_averages.csv"

# =========================
# Data loading / prep
# =========================
@st.cache_data(show_spinner=False)
def load_merged(_cache_buster:int=0):
    return pd.read_pickle(PKL_PATH)

def first_present(df: pd.DataFrame, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

@st.cache_data(show_spinner=False)
def load_or_build_averages(df: pd.DataFrame):
    """
    Try to load dashboard_averages.csv; if missing/mismatched, compute from df.
    """
    if Path(AVG_CSV_PATH).exists():
        try:
            avg_df = pd.read_csv(AVG_CSV_PATH)
            # Basic sanity
            required_cols = {"Segment","All Farms","Trip Receivers",
                             "Small Trip Receivers","Big Trip Receivers","Other Prizes"}
            if required_cols.issubset(set(avg_df.columns)):
                return avg_df
        except Exception:
            pass

    # Compute from df
    segments = list(pd.Series(df["Size_Segment"].dropna().unique()).sort_values())

    def seg_avg(seg_df, mask):
        s = seg_df.loc[mask, "Revenue_24_25"]
        return float(s.mean()) if not s.empty else np.nan

    rows = []
    for seg in segments:
        seg_df = df[df["Size_Segment"] == seg]
        rows.append({
            "Segment": seg,
            "All Farms": seg_avg(seg_df, seg_df["Revenue_24_25"] > 0),
            "Trip Receivers": seg_avg(seg_df, seg_df.get("Received_Target_Trip", pd.Series(False, index=seg_df.index))),
            "Small Trip Receivers":  seg_avg(seg_df, seg_df.get("Received_Small_Trip",  pd.Series(False, index=seg_df.index))),
            "Big Trip Receivers":    seg_avg(seg_df, seg_df.get("Received_Big_Trip",    pd.Series(False, index=seg_df.index))),
            "Other Prizes":          seg_avg(seg_df, seg_df.get("Received_Other_Prize", pd.Series(False, index=seg_df.index))),
        })
    return pd.DataFrame(rows)

# Load merged data
try:
    merged = load_merged(_cache_buster=1)
except FileNotFoundError:
    st.error(f"'{PKL_PATH}' not found. Re-run your preprocessing script to generate it.")
    st.stop()

# Ensure 24/25 revenue exists and numeric
rev_col = first_present(merged, ["Revenue_24_25", "Apyvarta, Eur 2024/25_UPDATED", "Apyvarta, Eur 2024/25"])
if rev_col is None:
    st.error("Could not find a 2024/25 revenue column in merged_data.pkl.")
    st.stop()
merged["Revenue_24_25"] = pd.to_numeric(merged[rev_col], errors="coerce").fillna(0.0)

# Ensure Size_Segment
if "Size_Segment" not in merged.columns:
    st.error("Column 'Size_Segment' is missing in merged_data.pkl.")
    st.stop()

# Rebuild gift flags robustly if missing
TRIP_GIFT_NAME = "Dovanos, prizai (KELIONĖS) klientams pagal kampanijos ID"
ALLOWED_TRIPS = ["ATĖNAI_202506 (Graikija)", "ŠRY LANKA_202501"]

gift_col   = first_present(merged, ["Gift_Type", "Dovanos pavadinimas"])
series_col = first_present(merged, ["Series_Number", "Serijos numeris", "Serijos numeris "])

if gift_col is None:
    merged["Gift_Type"] = np.nan
    gift_col = "Gift_Type"
else:
    merged[gift_col] = merged[gift_col].astype(str).str.strip()

if series_col is None:
    merged["Series_Number"] = np.nan
    series_col = "Series_Number"
else:
    merged[series_col] = merged[series_col].astype(str).str.strip()

if "Is_Target_Trip_Gift" not in merged.columns:
    merged["Is_Target_Trip_Gift"] = merged[gift_col].eq(TRIP_GIFT_NAME)

for flag in ["Received_Small_Trip","Received_Big_Trip","Received_Target_Trip","Received_Other_Prize"]:
    if flag not in merged.columns:
        merged[flag] = False

# Recompute consistently (won’t hurt if already present)
merged["Received_Small_Trip"]  = merged["Is_Target_Trip_Gift"] & merged[series_col].eq(ALLOWED_TRIPS[0])
merged["Received_Big_Trip"]    = merged["Is_Target_Trip_Gift"] & merged[series_col].eq(ALLOWED_TRIPS[1])
merged["Received_Target_Trip"] = merged["Received_Small_Trip"] | merged["Received_Big_Trip"]
merged["Received_Other_Prize"] = merged[gift_col].str.contains("KITI", na=False) & ~merged["Is_Target_Trip_Gift"]

# Base + segments
base = merged[merged["Revenue_24_25"] > 0].copy()
all_possible_segments = [
    "Large",
    "Medium",
    "Small Sizeable",
    "Small Medium",
    "Small Tiny"
]
segments = [seg for seg in all_possible_segments if seg in merged["Size_Segment"].unique()]
if not segments:
    st.error("No non-null values found in 'Size_Segment'.")
    st.stop()

# =========================
# UI: Title and top table
# =========================
st.title("Farm Reward Eligibility Dashboard")
st.caption("Disjoint thresholds: Small Trip = [small, big), Big Trip = [big, ∞). Revenue uses 2024/25 only.")

# Load or compute averages for defaults/top table
avg_tbl = load_or_build_averages(merged)

# Show top averages table
fmt_currency = lambda x: "€ {:,.0f}".format(x) if pd.notnull(x) else "—"
show_tbl = avg_tbl.copy()
for col in ["All Farms","Trip Receivers","Small Trip Receivers","Big Trip Receivers","Other Prizes"]:
    if col in show_tbl.columns:
        show_tbl[col] = show_tbl[col].apply(fmt_currency)

# Sort the table by your desired segment order
show_tbl = show_tbl.set_index("Segment").reindex(segments).reset_index()

st.subheader("Average Revenue by Segment and Gift Category (24/25)")
st.dataframe(show_tbl, use_container_width=True)

# Defaults for sliders (NaN -> 0)
defaults_small = {}
defaults_big = {}

if "Small Trip Receivers" in avg_tbl and "Big Trip Receivers" in avg_tbl:
    for seg in avg_tbl["Segment"]:
        small_val = avg_tbl.loc[avg_tbl["Segment"] == seg, "Small Trip Receivers"].values[0]
        big_val = avg_tbl.loc[avg_tbl["Segment"] == seg, "Big Trip Receivers"].values[0]
        # If no receivers (NaN or 0), set to 100000/200000
        defaults_small[seg] = 300000 if pd.isna(small_val) or small_val == 0 else small_val
        defaults_big[seg]   = 400000 if pd.isna(big_val)   or big_val == 0 else big_val

# =========================
# Sidebar: Global sliders
# =========================
st.sidebar.header("Global Cutoffs (override all segments)")

global_small = st.sidebar.slider(
    "Global Small Trip cutoff (€)",
    min_value=0, max_value=2_000_000, value=400_000, step=1000,
    help="Overrides all segment Small Trip cutoffs"
)
global_big = st.sidebar.slider(
    "Global Big Trip cutoff (€)",
    min_value=0, max_value=2_000_000, value=500_000, step=1000,
    help="Overrides all segment Big Trip cutoffs"
)

use_global = st.sidebar.checkbox("Use global cutoffs for all segments", value=False)

# =========================
# Sidebar sliders (two per segment)
# =========================
st.sidebar.header("Cutoffs per Segment (Revenue €)")

small_cutoffs = {}
big_cutoffs = {}

def suggested_max_for_segment(seg_df: pd.DataFrame, defaults: list[float]) -> int:
    m = 1000000
    return int(max(m, 0))

for seg in segments:
    seg_base = base[base["Size_Segment"] == seg]
    s_def = int(round(float(defaults_small.get(seg, 0) or 0)))
    b_def = int(round(float(defaults_big.get(seg, 0)   or 0)))
    seg_max = suggested_max_for_segment(seg_base, [s_def, b_def])

    with st.sidebar.expander(f"{seg}", expanded=False):
        col_small, col_big = st.columns(2)

        # Small Trip input + slider
        with col_small:
            small_val = st.number_input(
                f"Small Trip cutoff (€) — {seg}",
                min_value=0, max_value=int(seg_max), value=s_def, step=1000,
                help="Lower bound for Small Trip. Small eligibility is [small, big)."
            )
        with col_big:
            small_slider = st.slider(
                f"Small Trip slider — {seg}",
                min_value=0, max_value=int(seg_max), value=small_val, step=1000,
                label_visibility="collapsed"
            )
        # Use global if checked
        small_cutoffs[seg] = global_small if use_global else (small_slider if small_slider != small_val else small_val)

        col_small2, col_big2 = st.columns(2)

        # Big Trip input + slider
        with col_small2:
            big_val = st.number_input(
                f"Big Trip cutoff (€) — {seg}",
                min_value=0, max_value=int(seg_max), value=b_def, step=1000,
                help="Lower bound for Big Trip. Also the upper bound for Small Trip."
            )
        with col_big2:
            big_slider = st.slider(
                f"Big Trip slider — {seg}",
                min_value=0, max_value=int(seg_max), value=big_val, step=1000,
                label_visibility="collapsed"
            )
        # Use global if checked
        big_cutoffs[seg] = global_big if use_global else (big_slider if big_slider != big_val else big_val)

        if small_cutoffs[seg] >= big_cutoffs[seg]:
            st.info("Small cutoff is ≥ Big cutoff. Small eligibility will be empty until you lower it.")

# =========================
# Disjoint eligibility logic
# =========================
def eligibility_tables_disjoint(df, small_cut_dict, big_cut_dict):
    res_small, res_big = [], []
    for seg in segments:
        seg_df = df[(df["Size_Segment"] == seg) & (df["Revenue_24_25"] > 0)]
        total = len(seg_df)
        if seg_df.empty:
            res_small.append({"Segment": seg, "Cutoff (€)": 0, "Upper (€)": 0,
                              "Farms Eligible": 0, "Total Farms": 0, "% of Segment": 0.0})
            res_big.append({"Segment": seg, "Cutoff (€)": 0,
                            "Farms Eligible": 0, "Total Farms": 0, "% of Segment": 0.0})
            continue

        sc = int(small_cut_dict.get(seg, 0))
        bc = int(big_cut_dict.get(seg, 0))

        # Small: [sc, bc)
        elig_small = seg_df[(seg_df["Revenue_24_25"] >= sc) & (seg_df["Revenue_24_25"] < bc)]
        # Big: [bc, ∞)
        elig_big   = seg_df[seg_df["Revenue_24_25"] >= bc]

        res_small.append({
            "Segment": seg,
            "Cutoff (€)": sc,
            "Upper (€)": bc,
            "Farms Eligible": len(elig_small),
            "Total Farms": total,
            "% of Segment": round(100 * len(elig_small) / total, 1),
        })
        res_big.append({
            "Segment": seg,
            "Cutoff (€)": bc,
            "Farms Eligible": len(elig_big),
            "Total Farms": total,
            "% of Segment": round(100 * len(elig_big) / total, 1),
        })
    return pd.DataFrame(res_small), pd.DataFrame(res_big)

res_small, res_big = eligibility_tables_disjoint(merged, small_cutoffs, big_cutoffs)

# =========================
# Display results
# =========================
col1, col2 = st.columns(2, gap="large")

with col1:
    st.subheader("Eligibility — Small Trip")
    df_small_show = res_small.copy()
    df_small_show["Cutoff (€)"] = df_small_show["Cutoff (€)"].map(lambda v: f"€ {v:,.0f}")
    df_small_show["Upper (€)"]  = df_small_show["Upper (€)"].map(lambda v: f"€ {v:,.0f}")
    st.dataframe(df_small_show, use_container_width=True)

with col2:
    st.subheader("Eligibility — Big Trip")
    df_big_show = res_big.copy()
    df_big_show["Cutoff (€)"] = df_big_show["Cutoff (€)"].map(lambda v: f"€ {v:,.0f}")
    st.dataframe(df_big_show, use_container_width=True)

st.subheader("Share of Farms Eligible by Segment")

chart_small = alt.Chart(res_small).mark_bar().encode(
    x=alt.X("Segment:N", sort=segments, title="Segment"),
    y=alt.Y("% of Segment:Q", title="Eligible (%)"),
    tooltip=[
        alt.Tooltip("Segment:N"),
        alt.Tooltip("Cutoff (€):Q", format=",.0f", title="Lower (€)"),
        alt.Tooltip("Upper (€):Q",  format=",.0f", title="Upper (€)"),
        alt.Tooltip("Farms Eligible:Q"),
        alt.Tooltip("Total Farms:Q"),
        alt.Tooltip("% of Segment:Q")
    ],
).properties(height=320)

chart_big = alt.Chart(res_big).mark_bar().encode(
    x=alt.X("Segment:N", sort=segments, title="Segment"),
    y=alt.Y("% of Segment:Q", title="Eligible (%)"),
    tooltip=[
        alt.Tooltip("Segment:N"),
        alt.Tooltip("Cutoff (€):Q", format=",.0f", title="Lower (€)"),
        alt.Tooltip("Farms Eligible:Q"),
        alt.Tooltip("Total Farms:Q"),
        alt.Tooltip("% of Segment:Q")
    ],
).properties(height=320)

tabs = st.tabs(["Small Trip", "Big Trip"])
with tabs[0]:
    st.altair_chart(chart_small, use_container_width=True)
with tabs[1]:
    st.altair_chart(chart_big, use_container_width=True)

# =========================
# Context: actual receivers
# =========================
def actual_receivers(df):
    rows = []
    for seg in segments:
        seg_df = df[df["Size_Segment"] == seg]
        rows.append({
            "Segment": seg,
            "Actual Small Trip Receivers": int(seg_df["Received_Small_Trip"].sum()),
            "Actual Big Trip Receivers": int(seg_df["Received_Big_Trip"].sum()),
            "Actual Trip Receivers": int(seg_df["Received_Target_Trip"].sum()),
            "Actual Other Prize Receivers": int(seg_df["Received_Other_Prize"].sum()),
        })
    return pd.DataFrame(rows)

st.subheader("Actual Receivers by Segment (reference)")
st.dataframe(actual_receivers(merged), use_container_width=True)
