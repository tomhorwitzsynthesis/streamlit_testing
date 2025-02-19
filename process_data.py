import pandas as pd

def process_data(input_file="emirates_data.xlsx", output_file="emirates_data_processed.xlsx"):
    """
    Reads the raw data from `input_file`, processes it into structured data,
    and saves the new processed file as `output_file`.
    """
    # Load raw data from the Excel file
    xls = pd.ExcelFile(input_file)

    # Read the raw data sheet (assuming it's named "Sheet1")
    raw_data_df = pd.read_excel(xls, sheet_name="Sheet1")

    ### --- 1. Calculate Volume & Quality ---
    volume = len(raw_data_df)  # Number of articles
    quality = raw_data_df["BMQ"].mean()  # Average BMQ score

    volume_quality_df = pd.DataFrame({"Volume": [f"{volume}/100"], "Quality": [quality]})

    ### --- 2. Calculate Sentiment Distribution ---
    sentiment_counts = raw_data_df["Sentiment"].value_counts(normalize=True) * 100
    sentiment_df = pd.DataFrame({
        "Negative": [sentiment_counts.get("Negative", 0)],
        "Neutral": [sentiment_counts.get("Neutral", 0)],
        "Positive": [sentiment_counts.get("Positive", 0)]
    }).round(1)

    ### --- 3. Calculate Key Topics Distribution ---
    # Flatten all Cluster_Topic columns and count occurrences
    all_topics = raw_data_df[["Cluster_Topic1", "Cluster_Topic2", "Cluster_Topic3"]].values.flatten()
    key_topics_series = pd.Series(all_topics).value_counts(normalize=True) * 100

    key_topics_df = pd.DataFrame({
        "Topic Cluster": key_topics_series.index,
        "Percentage": key_topics_series.values
    }).round(1)

    ### --- 4. Calculate Topics per Archetype ---
    topics_per_archetype = []

    # Loop through unique archetypes
    for archetype in raw_data_df["Top Archetype"].unique():
        # Filter rows for this archetype
        archetype_rows = raw_data_df[raw_data_df["Top Archetype"] == archetype]

        # Count topics from Cluster_Topic1-3
        archetype_topics = archetype_rows[["Cluster_Topic1", "Cluster_Topic2", "Cluster_Topic3"]].values.flatten()
        archetype_topic_counts = pd.Series(archetype_topics).value_counts(normalize=True) * 100

        # Get top 3 topics for this archetype
        for topic, percentage in archetype_topic_counts.nlargest(3).items():
            topics_per_archetype.append([topic, percentage, archetype])

    topics_per_archetype_df = pd.DataFrame(
        topics_per_archetype, columns=["Topic Cluster", "Percentage", "Archetype"]
    ).round(1)

    ### --- 5. Calculate Top Archetypes ---
    top_archetype_counts = raw_data_df["Top Archetype"].value_counts(normalize=True) * 100
    top_archetypes_df = pd.DataFrame({
        "Top Archetype": top_archetype_counts.index,
        "Count": top_archetype_counts.values * volume / 100,  # Convert percentage back to count
        "Percentage": top_archetype_counts.values
    }).round(1)

    ### --- 6. Save to Excel ---
    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
        volume_quality_df.to_excel(writer, sheet_name="Volume & Quality", index=False)
        sentiment_df.to_excel(writer, sheet_name="Sentiment", index=False)
        top_archetypes_df.to_excel(writer, sheet_name="Top Archetypes", index=False)
        key_topics_df.to_excel(writer, sheet_name="Key Topics", index=False)
        topics_per_archetype_df.to_excel(writer, sheet_name="Topics per Archetype", index=False)

    print(f"✅ Processed data saved as '{output_file}'")

    return output_file  # Return the processed file name
