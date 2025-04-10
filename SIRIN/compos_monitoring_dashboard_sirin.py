import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
import numpy as np
import re
from datetime import datetime, timedelta




# Folder containing data files
DATA_FOLDER = "data march"

# Load company-file mappings from JSON
keys_file = os.path.join(DATA_FOLDER, "keys.txt")

if not os.path.exists(keys_file):
    st.error("Error: keys.txt file is missing in the data folder!")
    st.stop()

with open(keys_file, "r") as f:
    keys_data = json.load(f)

# Mapping of display names to actual keys
display_name_map = {
    "Darnu": "Darnu",
    "Eika": "Eika",
    "Kapitel": "Kapitel",
    "Piche": "Piche",
    "Restate": "Restate",
    "SIRIN": "SIRIN"
}

# Create reverse map for dropdown
reverse_map = {v: k for k, v in display_name_map.items()}

# Create dropdown options with display names, sorted as needed
#dropdown_options = ["Overview"] + [reverse_map[key] for key in keys_data.keys()]

# Sidebar for company selection
#selected_display_name = st.sidebar.selectbox("Select a Company", dropdown_options)

# Get the corresponding internal key (only if not "Overview")
#selected_company = display_name_map.get(selected_display_name, "Overview")

def extract_date(snippet):
    # Simulated "current" date: last day of the previous month
    today = pd.Timestamp.today()
    first_day_this_month = pd.Timestamp(today.year, today.month, 1)
    reference_date = first_day_this_month - pd.Timedelta(days=1)  # Last day of previous month

    # Handle relative dates
    if "day ago" in snippet or "days ago" in snippet:
        match = re.search(r"(\d+)\s+day[s]?\s+ago", snippet)
        if match:
            days_ago = int(match.group(1))
            return (reference_date - timedelta(days=days_ago)).strftime("%m/%d/%Y")

    elif "hour ago" in snippet or "hours ago" in snippet:
        match = re.search(r"(\d+)\s+hour[s]?\s+ago", snippet)
        if match:
            hours_ago = int(match.group(1))
            return (reference_date - timedelta(hours=int(match.group(1)))).strftime("%m/%d/%Y")

    # Handle absolute dates like "Sep 25, 2024"
    match = re.match(r"([A-Za-z]{3} \d{1,2}, \d{4})", snippet)
    if match:
        try:
            extracted_date = pd.to_datetime(match.group(1), format="%b %d, %Y")
            return extracted_date.strftime("%m/%d/%Y")
        except:
            return None

    return None





# Dictionary to store Volume, Quality, and Archetypes for each company
company_summary = {}

############################### NEWS ###############################################################################################################################################

st.title("Monitoring Dashboard")

st.header("News")

st.subheader("📊 Company Performance Overview")

st.markdown("""
This matrix showcases **three top brand archetypes** for each market player. The archetypes are determined by analyzing the content of the articles and mentions, and identifying key values that are communicated.

- **X-axis** represents the **volume of articles** captured over 6 months by the Google API.  
- **Y-axis** shows the **quality of sources**, determined by the authority of the web domain that features the content. The higher the quality, the more authoritative and established the domains or websites are that mention the brands.

This matrix is based on a larger brand mention sample over an extended period of time to more accurately determine the brand archetypes communicated by brands.

Read more about brand archetypes here: [Brandtypes](https://www.comp-os.com/brandtypes).
""")



# Extract Volume, Quality, and Archetypes from each raw file
for company, filename in keys_data.items():
    company_lower = company.lower()  # Ensure lowercase for file name
    file_path = os.path.join(DATA_FOLDER, "agility", f"{company_lower}_agility.xlsx")

    if os.path.exists(file_path):
        df = pd.read_excel(file_path, sheet_name="Raw Data")  # Load the raw data file

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

        #else:
            #st.warning(f"⚠️ No news data for {company}!")

# Convert dictionary to DataFrame
summary_df = pd.DataFrame.from_dict(company_summary, orient="index").reset_index()
summary_df.columns = ["Company", "Volume", "Quality", "Archetypes"]

# 🎯 Create Scatter Plot (Volume vs. Quality)

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
min_y_distance = 0.03 * summary_df["Quality"].max()  # Dynamic adjustment factor

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
        font=dict(size=8, color="black"),
        align="center",
        xanchor="center",
        yanchor="top",
        bordercolor="lightgray",
        borderwidth=1,
        borderpad=2,
        bgcolor="white",
    )


# Improve layout to prevent overlapping text
fig.update_layout(
    xaxis_title="Volume (Number of Articles)",
    yaxis_title="Quality (Avg. BMQ Score)",
    margin=dict(l=40, r=40, t=30, b=40),
    dragmode=False  # Disable zoom to keep positions fixed
)

# Display the scatter plot at the top of the dashboard
st.plotly_chart(fig, use_container_width=True)

# 🎭 Sentiment Analysis - Stacked Bar Chart
st.subheader("📊 Sentiment Distribution Across Companies")

st.markdown("""Sentiment scores showcase positive, negative and neutral context for company mentions. 
            Take note that AI engine also more broadly classifies negative mentions as ones including a more negative context as well as negative news related to the company itself. 
            """)

# Dictionary to store sentiment counts
sentiment_summary = {}

for company, filename in keys_data.items():
    company_lower = company.lower()  # Ensure lowercase for file name
    file_path = os.path.join(DATA_FOLDER, "agility", f"{company_lower}_agility.xlsx")

    if os.path.exists(file_path):
        df = pd.read_excel(file_path, sheet_name="Raw Data")  # Load the raw data file

        if not df.empty and "Sentiment" in df.columns:
            sentiment_counts = df["Sentiment"].value_counts(normalize=True) * 100  # Convert to percentages
            positive = sentiment_counts.get("Positive", 0)
            neutral = sentiment_counts.get("Neutral", 0)
            negative = sentiment_counts.get("Negative", 0)

            sentiment_summary[company] = {
                "Positive": positive,
                "Neutral": neutral,
                "Negative": negative
            }

# Convert dictionary to DataFrame
sentiment_df = pd.DataFrame.from_dict(sentiment_summary, orient="index").reset_index()
sentiment_df = sentiment_df.melt(id_vars=["index"], var_name="Sentiment", value_name="Percentage")
sentiment_df.columns = ["Company", "Sentiment", "Percentage"]

# Create stacked bar chart using Plotly
fig_sentiment = px.bar(
    sentiment_df,
    x="Company",
    y="Percentage",
    color="Sentiment",
    text="Percentage",
    title="Sentiment Distribution Per Company",
    color_discrete_map={"Positive": "green", "Neutral": "grey", "Negative": "red"},
)

# Improve layout for readability
fig_sentiment.update_traces(texttemplate='%{text:.1f}%', textposition='inside')
fig_sentiment.update_layout(barmode="stack", xaxis_title="Company", yaxis_title="Percentage")

# Display the stacked bar chart
st.plotly_chart(fig_sentiment, use_container_width=True)

    # ############################### TOP 5 TOPICS ###########################################################################

st.subheader("Key Topics")

st.markdown("Key topics reflect main themes across all of the communicating companies:")

# Function to compute topic counts and return top 5 topics
def get_top_topics(dataframes_dict):
    topic_counts = {
        "Cluster_Topic1": {},
        "Cluster_Topic2": {},
        "Cluster_Topic3": {}
    }

    for company, df in dataframes_dict.items():
        if all(col in df.columns for col in topic_counts.keys()):
            for column in topic_counts:
                for topic in df[column].dropna():
                    topic_counts[column][topic] = topic_counts[column].get(topic, 0) + 1

    all_topic_counts = {}
    for column in topic_counts:
        for topic, count in topic_counts[column].items():
            all_topic_counts[topic] = all_topic_counts.get(topic, 0) + count

    total_count = sum(all_topic_counts.values())
    sorted_topics = sorted(all_topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    topics_data = []
    for topic, count in sorted_topics:
        percentage = (count / total_count) * 100
        topics_data.append({
            "Topic Cluster": topic,
            "Count": count,
            "Percentage": round(percentage, 2)
        })

    return pd.DataFrame(topics_data)

# Load all company data
all_company_data = {}
for company, filename in keys_data.items():
    file_path = os.path.join(DATA_FOLDER, "agility", f"{company.lower()}_agility.xlsx")

    if os.path.exists(file_path):
        df = pd.read_excel(file_path, sheet_name="Raw Data")
        all_company_data[company] = df
    else:
        st.warning(f"File for {company} not found.")

# Create tabs
tab_titles = ["🌍 Total"] + [f"🏢 {company}" for company in all_company_data.keys()]
tabs = st.tabs(tab_titles)

# Render Total tab
with tabs[0]:
    total_df = get_top_topics(all_company_data)
    for _, row in total_df.iterrows():
        st.markdown(
            f'<div style="display: flex; justify-content: space-between; border: 1px solid #ccc; padding: 5px; border-radius: 5px; margin-bottom: 5px;">'
            f'<div style="background-color: white; padding: 5px; border-radius: 5px; flex: 1;">{row["Topic Cluster"]}</div>'
            f'<div style="background-color: lightgray; padding: 5px; border-radius: 5px; margin-left: 10px;">{row["Percentage"]}%</div>'
            f'</div>',
            unsafe_allow_html=True
        )

# Render individual company tabs
for idx, company in enumerate(all_company_data.keys(), start=1):
    with tabs[idx]:
        company_df = get_top_topics({company: all_company_data[company]})
        for _, row in company_df.iterrows():
            st.markdown(
                f'<div style="display: flex; justify-content: space-between; border: 1px solid #ccc; padding: 5px; border-radius: 5px; margin-bottom: 5px;">'
                f'<div style="background-color: white; padding: 5px; border-radius: 5px; flex: 1;">{row["Topic Cluster"]}</div>'
                f'<div style="background-color: lightgray; padding: 5px; border-radius: 5px; margin-left: 10px;">{row["Percentage"]}%</div>'
                f'</div>',
                unsafe_allow_html=True
            )


st.subheader("📰 Media Mentions Coverage Share Last 6 Months")

st.markdown("""
Online reputation represents how news items are captured by Google algorithms - it reflects the long-term impact company mentions have on Google results. 
The bigger the share, the more visible the news items are to Google. 
""")

# Dictionary to store non-organic volume data
non_organic_data = []

for company, filename in keys_data.items():
    file_path = os.path.join(DATA_FOLDER, filename)

    if os.path.exists(file_path):
        df_agility = pd.read_excel(file_path)
        df_agility["Company"] = company  # Add company name to each row
        non_organic_data.append(df_agility)
    else:
        st.write(f"{company} DOES NOT EXIST")

# Combine all data into one DataFrame
if non_organic_data:
    full_df = pd.concat(non_organic_data, ignore_index=True)

    # Create tabs
    tab_total, tab_lt, tab_lv, tab_ee = st.tabs(["🌍 Total", "🇱🇹 Lithuania", "🇱🇻 Latvia", "🇪🇪 Estonia"])

    # Function to filter data and generate pie chart
    def plot_mention_share(dataframe, title):
        count_df = dataframe.groupby("Company").size().reset_index(name="Volume")
        total_mentions = count_df["Volume"].sum()
        count_df["Percentage"] = (count_df["Volume"] / total_mentions) * 100

        # Only explicitly define the color for SIRIN
        color_map = {"SIRIN": "#00FF00"}

        fig_pie = px.pie(
            count_df,
            names="Company",
            values="Volume",
            title=title,
            hover_data=["Percentage"],
            labels={"Percentage": "% of Total"},
            color="Company",
            color_discrete_map=color_map  # Only maps SIRIN, others get default Plotly colors
        )

        fig_pie.update_traces(
            textinfo="label+percent",
            hovertemplate="%{label}: %{value} articles (%{customdata[0]:.1f}%)"
        )
        st.plotly_chart(fig_pie, use_container_width=True)


    with tab_total:
        plot_mention_share(full_df, "Total Share of Media Mentions Coverage")

    with tab_lt:
        plot_mention_share(full_df[full_df["Country"] == "Lithuania"], "Lithuania Media Mentions Coverage")

    with tab_lv:
        plot_mention_share(full_df[full_df["Country"] == "Latvia"], "Latvia Media Mentions Coverage")

    with tab_ee:
        plot_mention_share(full_df[full_df["Country"] == "Estonia"], "Estonia Media Mentions Coverage")
else:
    st.warning("No data loaded.")

# Format hover tooltips
#fig_pie.update_traces(textinfo="label+percent", hovertemplate="%{label}: %{value} articles (%{customdata[0]:.1f}%)")

# Display Pie Chart
#st.plotly_chart(fig_pie, use_container_width=True)

st.subheader("📈 Monthly Trends for Media Mentions & Online Reputation Volume")

st.markdown("""Media mentions shows overall number of company mentions for a given period. Online reputation shows what impact do media mentions make on Google search results.
            """)

# Get the current month and year
now = pd.Timestamp.now()
previous_month = now.month - 1 if now.month > 1 else 12
previous_year = now.year if now.month > 1 else now.year - 1

current_month = previous_month
current_year = previous_year

# Define the past 6 months
date_range = pd.date_range(end=pd.Timestamp(previous_year, previous_month, 1), periods=3, freq='MS')
month_labels = [date.strftime('%b %Y') for date in date_range]

# Dictionary to store time-series data
time_series_data = {company: {"Month": [], "Volume": [], "NonOrganicVolume": [0] * len(date_range)} for company in keys_data}

# Extract monthly Organic Volume & Quality data from each file
for company, filename in keys_data.items():
    file_path = os.path.join(DATA_FOLDER, filename)

    if os.path.exists(file_path):
        df = pd.read_excel(file_path)  # Load data file

        # Check if "Published Date" column exists, if not, create it
        if "Published Date" not in df.columns:
            df["Published Date"] = df["Snippet"].apply(lambda x: extract_date(x) if isinstance(x, str) else None)

        if not df.empty and "Published Date" in df.columns:
            df["Published Date"] = pd.to_datetime(df["Published Date"], format="%m/%d/%Y", errors="coerce")
            df["Month"] = df["Published Date"].dt.to_period("M")  # Extract Year-Month

            for i, month in enumerate(date_range):
                month_period = month.to_period("M")
                month_df = df[df["Month"] == month_period]

                # Compute Volume (count) & Quality (mean BMQ)
                volume = len(month_df)

                time_series_data[company]["Month"].append(month.strftime('%b %Y'))
                time_series_data[company]["Volume"].append(volume)

# Extract Non-Organic Volume from Agility Data
#for company in keys_data.keys():
#    company_lower = company.lower()  # Match file format
#    agility_file = os.path.join(DATA_FOLDER, "agility", f"{company_lower}_agility.xlsx")#

#    if os.path.exists(agility_file):
#        df_agility = pd.read_excel(agility_file, sheet_name="Raw Data")  # Load agility data

#        if not df_agility.empty and "Published Date" in df_agility.columns:
#            df_agility["Published Date"] = pd.to_datetime(df_agility["Published Date"], format="%m/%d/%Y", errors="coerce")
#            df_agility["Month"] = df_agility["Published Date"].dt.to_period("M")  # Extract Year-Month

 #           for i, month in enumerate(date_range):
 #               month_period = month.to_period("M")
 #               month_df = df_agility[df_agility["Month"] == month_period]
  #              non_organic_volume = len(month_df)  # Count number of articles

                # Ensure correct list length before assignment
                #if len(time_series_data[company]["NonOrganicVolume"]) == len(date_range):
                 #   time_series_data[company]["NonOrganicVolume"][i] = non_organic_volume

# Ensure non-organic data is zero for companies with no organic data
for company in time_series_data.keys():
    if len(time_series_data[company]["Month"]) == 0:  # No organic data found
        #st.warning(f"⚠️ **{company} has no organic data, setting non-organic volume to 0.**")
        time_series_data[company]["Month"] = [month.strftime('%b %Y') for month in date_range]
        time_series_data[company]["Volume"] = [0] * len(date_range)
        #time_series_data[company]["NonOrganicVolume"] = [0] * len(date_range)  # Ensure all values are zero

# If the error persists, this will reveal which list has a length mismatch
time_series_df = pd.concat(
    [pd.DataFrame({"Company": company, "Month": data["Month"], "Volume": data["Volume"]})
    for company, data in time_series_data.items()], ignore_index=True
)

# Convert dictionary to DataFrame
print("🔄 Converting to DataFrame...")
for company, data in time_series_data.items():
    print(f"📊 {company}: Months={len(data['Month'])}, Volumes={len(data['Volume'])}")

# If the error persists, this will reveal which list has a length mismatch
time_series_df = pd.concat(
    [pd.DataFrame({"Company": company, "Month": data["Month"], "Volume": data["Volume"]})
    for company, data in time_series_data.items()], ignore_index=True
)





st.subheader("📊 Online Reputation Volume Trend")

fig_volume = px.line(
    time_series_df,
    x="Month",
    y="Volume",
    color="Company",
    markers=True,
    title="Monthly Online Reputation Volume Trend per Company",
)

fig_volume.update_layout(
    xaxis_title="Month",
    yaxis_title="Online Reputation Volume (Articles)",
    xaxis=dict(categoryorder="array", categoryarray=month_labels)
)

st.plotly_chart(fig_volume, use_container_width=True)




