import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
import numpy as np
from company_dashboard import generate_company_dashboard  # Import company-specific function

# Folder containing data files
DATA_FOLDER = "CompOS_testing/data"

# Load company-file mappings from JSON
keys_file = os.path.join(DATA_FOLDER, "keys.txt")

if not os.path.exists(keys_file):
    st.error("Error: keys.txt file is missing in the data folder!")
    st.stop()

with open(keys_file, "r") as f:
    keys_data = json.load(f)

# Dictionary to store Volume, Quality, and Archetypes for each company
company_summary = {}

# Extract Volume, Quality, and Archetypes from each raw file
for company, filename in keys_data.items():
    file_path = os.path.join(DATA_FOLDER, filename)

    if os.path.exists(file_path):
        df = pd.read_excel(file_path)  # Load the raw data file

        if not df.empty:
            volume = len(df)  # Number of rows = number of articles
            quality = df["BMQ"].mean()  # Average of BMQ column

            # Compute Archetype Percentages
            if "Top Archetype" in df.columns:
                archetype_counts = df["Top Archetype"].value_counts(normalize=True) * 100  # Convert to percentages
                top_3_archetypes = archetype_counts.nlargest(3)  # Get top 3 archetypes
                
                # Format as a vertical list using <br> for new lines
                archetype_text = "<br>".join([f"{archetype} ({percent:.1f}%)" for archetype, percent in top_3_archetypes.items()])
            else:
                archetype_text = "No Archetype Data"

            # Store company metrics
            company_summary[company] = {
                "Volume": volume,
                "Quality": round(quality, 2) if not pd.isna(quality) else 0,  # Ensure valid quality score
                "Archetypes": archetype_text  # Store top 3 archetypes
            }

# Convert dictionary to DataFrame
summary_df = pd.DataFrame.from_dict(company_summary, orient="index").reset_index()
summary_df.columns = ["Company", "Volume", "Quality", "Archetypes"]

# 🎯 Create Scatter Plot (Volume vs. Quality)
st.subheader("📊 Company Performance Overview")

fig = px.scatter(
    summary_df,
    x="Volume",
    y="Quality",
    text="Company",  # Company names displayed above points
    hover_data=["Archetypes"],  # Show Archetypes on hover
    size_max=15,
    title="Company Performance (Volume vs. Quality) with Archetypes",
)

# Enhance the plot: Position company names correctly
fig.update_traces(
    textposition="top center",
    marker=dict(size=10, color="blue")
)

# Avoid text overlap: Calculate dynamic Y-positions
y_positions = []
min_y_distance = 0.1 * summary_df["Quality"].max()  # Dynamic adjustment factor

for i, row in summary_df.iterrows():
    y_pos = row["Quality"] - min_y_distance  # Default position (below point)
    
    # If another label is too close, shift the new one further down
    while any(abs(y_pos - prev_y) < min_y_distance for prev_y in y_positions):
        y_pos -= min_y_distance  # Move text further down

    y_positions.append(y_pos)  # Store adjusted position

    fig.add_annotation(
        x=row["Volume"],
        y=y_pos,
        text=f"<b>{row['Company']}</b><br>{row['Archetypes']}",  # ✅ Add company name
        showarrow=False,
        font=dict(size=10, color="black"),
        align="center",
        xanchor="center",
        yanchor="top",
        bordercolor="lightgray",
        borderwidth=1,
        borderpad=4,
        bgcolor="white",
    )


# Improve layout to prevent overlapping text
fig.update_layout(
    xaxis_title="Volume (Number of Articles)",
    yaxis_title="Quality (Avg. BMQ Score)",
    margin=dict(l=40, r=40, t=40, b=40),
    dragmode=False  # Disable zoom to keep positions fixed
)

# Display the scatter plot at the top of the dashboard
st.plotly_chart(fig, use_container_width=True)

# Sidebar for company selection
selected_company = st.sidebar.selectbox("Select a Company", list(keys_data.keys()))

# Generate the selected company's dashboard
if selected_company:
    input_file = os.path.join(DATA_FOLDER, keys_data[selected_company])
    generate_company_dashboard(input_file)
