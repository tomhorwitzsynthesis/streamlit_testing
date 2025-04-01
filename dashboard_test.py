import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import os

st.subheader("15 Minute City")

# Load your Excel file
df = pd.read_excel("Survey_Data.xlsx")  # Adjust filename/sheet if needed

# Mapping district number to names
district_names = {1: "Antakalnis", 2: "Fabijoniškės"}

# Dropdown menu to select a district
selected_name = st.selectbox("Select District", options=list(district_names.values()))

st.write(selected_name)

selected_id = [k for k, v in district_names.items() if v == selected_name][0]

# Filter for selected district
filtered_df = df[df["District"] == selected_id]

# Group the 18 questions into 6 groups
question_groups = {
    "Life": ["Accommodation quality", "Essential services", "Satisfaction"],
    "Work": ["Local Suitable Jobs", "Remote Working Spaces", "Job Variety"],
    "Shops": ["Local shops", "Local Business Support", "Economic Situation"],
    "Health": ["Health Care facilities", "Sports and Recreation", "Psychological support"],
    "Education": ["Educational facilities", "Educational services", "Adult learning"],
    "Entertainment": ["Cultural Activities", "Restaurants and Entertainment", "Community events"]
}

# Get averages for each question
averages = filtered_df.mean(numeric_only=True)

# Layout: 2 columns
col1, col2 = st.columns(2)

# Loop through question groups and plot
for i, (group, questions) in enumerate(question_groups.items()):
    group_scores = averages[questions].reset_index()
    group_scores.columns = ["Question", "Score"]

    fig = px.bar(
        group_scores,
        x="Score",
        y="Question",
        orientation="h",
        title=group,
    )
    fig.update_layout(height=300, margin=dict(t=40, b=30))

    (col1 if i % 2 == 0 else col2).plotly_chart(fig, use_container_width=True)



st.subheader("CompOS")

# Archetypes
archetypes = [
    "DEVELOPED", "ORDERLY", "CONVENIENT", "CHARACTERISTIC",
    "SIMPLE", "DIVERSE", "CULTURAL", "FRIENDLY",
    "DYNAMIC", "PROMISING", "SAFE", "INNOVATIVE",
    "RESPONSIBLE", "COLLABORATIVE", "OPEN", "GREEN"
]

# Get average scores
selected_method = st.selectbox("Select Method", options=["Average Score", "Top 2 Box"])

if selected_method == "Average Score":
    averages = df[archetypes].mean()
else:
    averages = (df[archetypes] >= 4).sum() / df[archetypes].notna().sum() * 100








archetype_positions = {
    "DEVELOPED": (-1.5, 1.5),
    "ORDERLY": (-1.5, 0.5),
    "SIMPLE": (-1.5, -0.5),
    "CULTURAL": (-1.5, -1.5),

    "CONVENIENT": (-0.5, 1.5),
    "CHARACTERISTIC": (-0.5, 0.5),
    "DIVERSE": (-0.5, -0.5),
    "FRIENDLY": (-0.5, -1.5),

    "DYNAMIC": (0.5, 1.5),
    "SAFE": (0.5, 0.5),
    "RESPONSIBLE": (0.5, -0.5),
    "OPEN": (0.5, -1.5),

    "PROMISING": (1.5, 1.5),
    "INNOVATIVE": (1.5, 0.5),
    "COLLABORATIVE": (1.5, -0.5),
    "GREEN": (1.5, -1.5)
}


# Combine data
matrix_data = [(name, averages[name], archetype_positions[name]) for name in archetypes]

# Create figure
fig = go.Figure()

# Get top 2 and bottom 2 scores
top_scores = averages.nlargest(2)
bottom_scores = averages.nsmallest(2)

if selected_method == "Average Score":

    cell_size = 1
    for name, score, (x, y) in matrix_data:

        # Draw rectangle cell
        fig.add_shape(
            type="rect",
            x0=x - cell_size / 2,
            y0=y - cell_size / 2,
            x1=x + cell_size / 2,
            y1=y + cell_size / 2,
            line=dict(color="black")
        )

            # Determine color for score
        if name in top_scores.index:
            score_color = "green"
        elif name in bottom_scores.index:
            score_color = "red"
        else:
            score_color = "gray"

        # Add archetype name
        fig.add_annotation(
            x=x, y=y + 0.2,
            text=f"<b>{name}</b>",
            showarrow=False,
            font=dict(size=12, color=score_color)
        )

        # Add score
        fig.add_annotation(
            x=x, y=y - 0.2,
            text=f"{score:.2f}",
            showarrow=False,
            font=dict(size=20, color=score_color)
        )

    fig.update_layout(
        width=700,
        height=700,
        xaxis=dict(
            tickvals=[-1.5, -0.5, 0.5, 1.5],
            range=[-2, 2],
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        yaxis=dict(
            tickvals=[-1.5, -0.5, 0.5, 1.5],
            range=[-2, 2],
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        plot_bgcolor="white",
        margin=dict(t=30, b=30, l=30, r=30)
    )


    # Display in Streamlit
    st.plotly_chart(fig, use_container_width=True)

else:

    cell_size = 1
    for name, score, (x, y) in matrix_data:

        # Draw rectangle cell
        fig.add_shape(
            type="rect",
            x0=x - cell_size / 2,
            y0=y - cell_size / 2,
            x1=x + cell_size / 2,
            y1=y + cell_size / 2,
            line=dict(color="black")
        )

            # Determine color for score
        if name in top_scores.index:
            score_color = "green"
        elif name in bottom_scores.index:
            score_color = "red"
        else:
            score_color = "gray"

        # Add archetype name
        fig.add_annotation(
            x=x, y=y + 0.2,
            text=f"<b>{name}</b>",
            showarrow=False,
            font=dict(size=12, color=score_color)
        )

        # Add score
        fig.add_annotation(
            x=x, y=y - 0.2,
            text=f"<b>{score:.0f}%</b>",
            showarrow=False,
            font=dict(size=20, color=score_color)
        )

    fig.update_layout(
        width=700,
        height=700,
        xaxis=dict(
            tickvals=[-1.5, -0.5, 0.5, 1.5],
            range=[-2, 2],
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        yaxis=dict(
            tickvals=[-1.5, -0.5, 0.5, 1.5],
            range=[-2, 2],
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        plot_bgcolor="white",
        margin=dict(t=30, b=30, l=30, r=30)
    )


    # Display in Streamlit
    st.plotly_chart(fig, use_container_width=True) 

key_spots_list = ["https://www.google.com/maps/d/u/0/embed?mid=1EX2VtgUIJq9vI1xusfb3Kkj_ct9D0PU&ehbc=2E312F&noprof=1", 
                  "https://www.google.com/maps/d/u/0/embed?mid=1zml8JcwmZ_-II3pAokn6uygW4rh4wos&ehbc=2E312F&noprof=1"]

key_spots_link = key_spots_list[selected_id-1]

components.iframe(key_spots_link, height = 600, width = 800)



media_df = pd.read_excel("Media_Data.xlsx", sheet_name=selected_name)

# ============================
# 📊 Sentiment: Horizontal Stacked Bar
# ============================

sentiment_counts = media_df["Sentiment"].value_counts().reindex(["Positive", "Neutral", "Negative"], fill_value=0)

fig_sentiment = go.Figure()
fig_sentiment.add_trace(go.Bar(
    x=[sentiment_counts["Positive"]],
    y=["Sentiment"],
    name="Positive",
    orientation="h",
    marker_color="green"
))
fig_sentiment.add_trace(go.Bar(
    x=[sentiment_counts["Neutral"]],
    y=["Sentiment"],
    name="Neutral",
    orientation="h",
    marker_color="gray"
))
fig_sentiment.add_trace(go.Bar(
    x=[sentiment_counts["Negative"]],
    y=["Sentiment"],
    name="Negative",
    orientation="h",
    marker_color="red"
))
fig_sentiment.update_layout(barmode='stack', title="Media Sentiment Distribution", height=300)

st.plotly_chart(fig_sentiment, use_container_width=True)

# ============================
# 🗂 Topics & 🧭 Archetypes: Side by Side
# ============================

col1, col2 = st.columns(2)

with col1:
    st.subheader("🗂 Top 5 Topics")

    topic_counts = {"Cluster_Topic1": {}, "Cluster_Topic2": {}, "Cluster_Topic3": {}}

    for column in ["Cluster_Topic1", "Cluster_Topic2", "Cluster_Topic3"]:
        if column in media_df.columns:
            for topic in media_df[column].dropna():
                topic_counts[column][topic] = topic_counts[column].get(topic, 0) + 1

    all_topic_counts = {}
    for col in topic_counts:
        for topic, count in topic_counts[col].items():
            all_topic_counts[topic] = all_topic_counts.get(topic, 0) + count

    sorted_topics = sorted(all_topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    total_topic_mentions = sum(all_topic_counts.values())

    topics_data = [
        {"Topic Cluster": topic, "Count": count, "Percentage": round((count / total_topic_mentions) * 100, 2)}
        for topic, count in sorted_topics
    ]

    for row in topics_data:
        st.markdown(
            f'<div style="display: flex; justify-content: space-between; border: 1px solid #ccc; padding: 5px; border-radius: 5px; margin-bottom: 5px;">'
            f'<div style="background-color: white; padding: 5px; border-radius: 5px; flex: 1;">{row["Topic Cluster"]}</div>'
            f'<div style="background-color: lightgray; padding: 5px; border-radius: 5px; margin-left: 10px;">{row["Percentage"]}%</div>'
            f'</div>',
            unsafe_allow_html=True
        )

with col2:
    st.subheader("🧭 Top 3 Archetypes")

    if "Top Archetype" in media_df.columns:
        archetype_counts = media_df["Top Archetype"].value_counts()
        top_archetypes = archetype_counts.head(3)
        total_archetype_mentions = archetype_counts.sum()

        for archetype, count in top_archetypes.items():
            percentage = round((count / total_archetype_mentions) * 100, 2)
            st.markdown(
                f'<div style="display: flex; justify-content: space-between; border: 1px solid #ccc; padding: 5px; border-radius: 5px; margin-bottom: 5px;">'
                f'<div style="background-color: white; padding: 5px; border-radius: 5px; flex: 1;">{archetype}</div>'
                f'<div style="background-color: lightgray; padding: 5px; border-radius: 5px; margin-left: 10px;">{percentage}%</div>'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        st.write("No 'Top Archetype' column found in media data.")


st.markdown("<br>", unsafe_allow_html=True)  # Adds one line of vertical space
st.markdown("<br>", unsafe_allow_html=True)  # Adds one line of vertical space

st.subheader("Segments")





# Load segment data
segment_df = pd.read_excel("Segment_Data.xlsx")

# Segment-to-filename mapping
image_folder = "images"  # Adjust if images are in a different folder
image_files = {
    "Aktyvūs tyrinėtojai": "aktyvus_tyrinetojai.png",
    "Įsitraukę klajokliai": "isitrauke_klajokliai.png",
    "Neutralūs pragmatikai": "neutralus_pragmatikai.png",
    "Savarankiški tradicionalistai": "savarankiski_tradicionalistai.png",
    "Uždarieji senbūviai": "uzdarieji_senbuviai.png"
}

# Create two columns
col1, col2 = st.columns(2)

# Split rows for layout balance (3 left, 2 right)
left_segments = segment_df.iloc[:3]
right_segments = segment_df.iloc[3:]

# Reusable segment display function
def display_segment(row):
    seg_name = row["Segment"]
    desc = row["Description"]
    percent = row[selected_name]
    img_path = os.path.join(image_folder, image_files.get(seg_name, ""))

    if os.path.exists(img_path):
        st.image(img_path, width=100)
    st.markdown(f"**{seg_name}**")
    st.markdown(f"*{desc}*")
    st.markdown(f"**{int(percent * 100)}%**")
    st.markdown("---")

# Left column segments
with col1:
    for _, row in left_segments.iterrows():
        display_segment(row)

# Right column segments
with col2:
    for _, row in right_segments.iterrows():
        display_segment(row)



st.header("Maps")


import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import matplotlib.pyplot as plt
import json

st.subheader("District Problems")

# === Load problem data ===
problems_df = pd.read_excel("Problem_Data.xlsx")

# === Load and convert ESRI-style boundaries.json ===
with open("boundaries.json", encoding="utf-8") as f:
    esri_json = json.load(f)

def convert_esri_feature(feature):
    geom = feature.get("geometry")
    if not geom or "rings" not in geom:
        return None

    try:
        polygon = Polygon(geom["rings"][0])
        return {
            "geometry": polygon,
            "attributes": feature.get("attributes", {})
        }
    except Exception:
        return None

converted = [convert_esri_feature(f) for f in esri_json["features"]]
converted = [f for f in converted if f is not None]

# Create GeoDataFrame
gdf = gpd.GeoDataFrame(
    [f["attributes"] for f in converted],
    geometry=[f["geometry"] for f in converted],
    crs="EPSG:3346"  # Lithuania's projection
)
gdf = gdf.rename(columns={"SENIUNIJA": "District"})
gdf["District"] = gdf["District"].str.strip()

# Merge with problem data
merged = gdf.merge(problems_df, on="District", how="left")

# Dropdown to select category
columns_to_plot = [
    "Animal", "Environmental", "Infrastructure", "Traffic", "Violations", "Total_Problems"
]
selected_category = st.selectbox("Select problem category:", columns_to_plot)

# === Plot static map ===
fig, ax = plt.subplots(figsize=(8, 8))
merged.plot(
    column=selected_category,
    cmap="OrRd",
    linewidth=0.8,
    edgecolor='black',
    legend=True,
    ax=ax
)
ax.set_title(f"{selected_category} Problems by District", fontsize=14)
ax.axis("off")

st.pyplot(fig)


st.subheader("General Statistics")

# === Load problem data ===
problems_df = pd.read_excel("Problem_Data.xlsx")

# === Load and convert ESRI-style boundaries.json ===
with open("boundaries.json", encoding="utf-8") as f:
    esri_json = json.load(f)

def convert_esri_feature(feature):
    geom = feature.get("geometry")
    if not geom or "rings" not in geom:
        return None

    try:
        polygon = Polygon(geom["rings"][0])
        return {
            "geometry": polygon,
            "attributes": feature.get("attributes", {})
        }
    except Exception:
        return None

converted = [convert_esri_feature(f) for f in esri_json["features"]]
converted = [f for f in converted if f is not None]

# Create GeoDataFrame
gdf = gpd.GeoDataFrame(
    [f["attributes"] for f in converted],
    geometry=[f["geometry"] for f in converted],
    crs="EPSG:3346"  # Lithuania's projection
)
gdf = gdf.rename(columns={"SENIUNIJA": "District"})
gdf["District"] = gdf["District"].str.strip()

# Merge with problem data
merged = gdf.merge(problems_df, on="District", how="left")

# Dropdown to select category
columns_to_plot = [
    "Population", "Green Area", "Average Age", "Average children", "Male", "Female"
]
selected_category = st.selectbox("Select problem category:", columns_to_plot)

# === Plot static map ===
fig, ax = plt.subplots(figsize=(8, 8))
merged.plot(
    column=selected_category,
    cmap="OrRd",
    linewidth=0.8,
    edgecolor='black',
    legend=True,
    ax=ax
)
ax.set_title(f"{selected_category} Problems by District", fontsize=14)
ax.axis("off")

st.pyplot(fig)



