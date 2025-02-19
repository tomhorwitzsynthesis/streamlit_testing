import streamlit as st
import pandas as pd
import plotly.express as px
from matrix_overlay import overlay_top_archetypes
from process_data import process_data
import os
import time

# Define file names
input_file = "CompOS_testing/aarcorp_data.xlsx"  # Raw data file
output_file = "CompOS_testing/aarcorp_data_processed.xlsx"  # Processed output file

# Process the raw data into structured format
processed_file = process_data(input_file, output_file)

# Load the processed Excel file
xls = pd.ExcelFile(processed_file)

# Read sheets into dataframes
volume_quality_df = pd.read_excel(xls, sheet_name="Volume & Quality")
sentiment_df = pd.read_excel(xls, sheet_name="Sentiment")
top_archetypes_df = pd.read_excel(xls, sheet_name="Top Archetypes")
key_topics_df = pd.read_excel(xls, sheet_name="Key Topics")
topics_per_archetype_df = pd.read_excel(xls, sheet_name="Topics per Archetype")

# Format percentages to one decimal place
sentiment_df = sentiment_df.round(1)
key_topics_df["Percentage"] = key_topics_df["Percentage"].round(1)
topics_per_archetype_df["Percentage"] = topics_per_archetype_df["Percentage"].round(1)

title = "Emirates Engineering Dashboard"

# Streamlit app
st.title(title)

# Volume & Quality Tags
st.subheader("Volume & Quality")
col1, col2 = st.columns(2)
col1.metric("Volume", volume_quality_df.iloc[0, 0])
col2.metric("Quality", f"{volume_quality_df.iloc[0, 1]:.2f}")

# Sentiment Stacked Bar Chart
st.subheader("Sentiment Analysis")
sentiment_melted = sentiment_df.melt(var_name="Sentiment", value_name="Percentage")
fig = px.bar(
    sentiment_melted,
    x="Percentage",
    y="Sentiment",  # Fixed issue causing empty grid
    color="Sentiment",
    orientation="h",
    text="Percentage",
    barmode="stack",
    color_discrete_map={"Negative": "red", "Neutral": "gray", "Positive": "green"}
)
fig.update_layout(yaxis_title=None)
st.plotly_chart(fig)

# Key Topics Box Design
st.subheader("Key Topics")
for _, row in key_topics_df.iterrows():
    st.markdown(
        f'<div style="display: flex; justify-content: space-between; border: 1px solid #ccc; padding: 5px; border-radius: 5px; margin-bottom: 5px;">'
        f'<div style="background-color: white; padding: 5px; border-radius: 5px; flex: 1;">{row["Topic Cluster"]}</div>'
        f'<div style="background-color: lightgray; padding: 5px; border-radius: 5px; margin-left: 10px;">{row["Percentage"]}%</div>'
        f'</div>',
        unsafe_allow_html=True
    )


# Topics per Archetype with Compact Display
st.subheader("Topics per Archetype")
top_3_per_archetype = (
    topics_per_archetype_df.groupby("Archetype")
    .apply(lambda x: x.nlargest(3, "Percentage"))
    .reset_index(drop=True)
)

previous_archetype = None
for _, row in top_3_per_archetype.iterrows():
    archetype_display = f"<b>{row['Archetype']}</b>" if row["Archetype"] != previous_archetype else ""
    previous_archetype = row["Archetype"]
    st.markdown(
        f'<div style="display: flex; justify-content: space-between; border: 1px solid #ccc; padding: 5px; border-radius: 5px; margin-bottom: 5px;">'
        f'<div style="background-color: white; padding: 5px; border-radius: 5px; flex: 1;">{archetype_display}</div>'
        f'<div style="background-color: white; padding: 5px; border-radius: 5px; flex: 2;">{row["Topic Cluster"]}</div>'
        f'<div style="background-color: lightgray; padding: 5px; border-radius: 5px; margin-left: 10px;">{row["Percentage"]}%</div>'
        f'</div>', unsafe_allow_html=True
    )

st.subheader("Top Archetypes")

# Get absolute script path
#script_dir = os.path.dirname(os.path.abspath(__file__))
matrix_image_path = "CompOS_testing/matrix.jpg"

# Extract the Top 3 Archetypes from the DataFrame
top_archetypes = top_archetypes_df.nlargest(3, "Percentage")[["Top Archetype", "Percentage"]].values.tolist()

# ✅ Remove "The " from each archetype name
top_archetypes = [(name.replace("The ", ""), percentage) for name, percentage in top_archetypes]

# Generate and save the matrix image with overlays
saved_matrix_path = overlay_top_archetypes(matrix_image_path, top_archetypes, title)

# Force Streamlit to reload the image
time.sleep(1)  # Small delay to ensure image processing is complete
st.image(saved_matrix_path, caption="Archetype Matrix", use_container_width =True)
