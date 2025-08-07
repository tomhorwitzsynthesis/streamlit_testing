import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# === Load your preprocessed merged DataFrame ===
@st.cache_data
def load_data():
    return pd.read_pickle("merged_data.pkl")  # You need to save it from your notebook first

merged = load_data()

# === Set up the app ===
st.title("Farm Reward Eligibility Dashboard")
st.markdown("Define reward criteria by revenue or percentile per segment and see who qualifies.")

segments = sorted(merged["Size_Segment"].dropna().unique())

# === Sidebar controls ===
method = st.sidebar.radio("Reward selection method", ["Revenue Cutoff (€)", "Percentile"])

user_inputs = {}
st.sidebar.markdown("### Set thresholds per segment:")

for segment in segments:
    if method == "Revenue Cutoff (€)":
        val = st.sidebar.number_input(f"{segment} (€)", min_value=0, step=1000, value=100000)
    else:
        val = st.sidebar.slider(f"{segment} (percentile)", min_value=0, max_value=100, value=80)
    user_inputs[segment] = val


# === Analysis Functions ===
def reward_by_absolute_cutoffs(df, cutoffs):
    results = []
    for segment in segments:
        df_seg = df[(df["Size_Segment"] == segment) & (df["Revenue_24_25"] > 0)]
        if df_seg.empty:
            continue
        cutoff = cutoffs.get(segment, np.inf)
        eligible = df_seg[df_seg["Revenue_24_25"] >= cutoff]
        results.append({
            "Segment": segment,
            "Cutoff (€)": cutoff,
            "Farms Eligible": len(eligible),
            "Total Farms": len(df_seg),
            "% of Segment": round(len(eligible) / len(df_seg) * 100, 1)
        })
    return pd.DataFrame(results)


def reward_by_percentile_cutoffs(df, percentiles):
    results = []
    for segment in segments:
        df_seg = df[(df["Size_Segment"] == segment) & (df["Revenue_24_25"] > 0)]
        if df_seg.empty:
            continue
        percentile = percentiles.get(segment, 100)
        cutoff = np.percentile(df_seg["Revenue_24_25"], percentile)
        eligible = df_seg[df_seg["Revenue_24_25"] >= cutoff]
        results.append({
            "Segment": segment,
            "Cutoff (€)": round(cutoff, 2),
            "Farms Eligible": len(eligible),
            "Total Farms": len(df_seg),
            "% of Segment": round(len(eligible) / len(df_seg) * 100, 1)
        })
    return pd.DataFrame(results)

# === Compute and display result ===
if method == "Revenue Cutoff (€)":
    results_df = reward_by_absolute_cutoffs(merged, user_inputs)
else:
    results_df = reward_by_percentile_cutoffs(merged, user_inputs)

# === Display outputs ===
st.markdown("### Reward Eligibility by Segment")
st.dataframe(results_df)

# === Plot ===
chart = alt.Chart(results_df).mark_bar().encode(
    x=alt.X("Segment", sort=segments),
    y=alt.Y("% of Segment", title="Percentage Eligible"),
    tooltip=["Segment", "Cutoff (€)", "% of Segment"]
).properties(
    width=600,
    height=400
)

st.altair_chart(chart, use_container_width=True)
