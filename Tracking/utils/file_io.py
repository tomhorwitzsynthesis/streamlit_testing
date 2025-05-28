import os
import pandas as pd
import streamlit as st

DATA_ROOT = "Tracking/data"

# ------------------------
# 📄 Load Agility (News)
# ------------------------
@st.cache_data
def load_agility_data(company_name: str):
    path = os.path.join(DATA_ROOT, "agility", f"{company_name.lower()}_agility.xlsx")
    if not os.path.exists(path):
        return None
    try:
        return pd.read_excel(path, sheet_name="Raw Data")
    except Exception as e:
        st.error(f"[Agility] Error loading {company_name}: {e}")
        return None

# ------------------------
# 📱 Load Social Media Data
# ------------------------

@st.cache_data
def load_social_data(company_name: str, platform: str):
    """Load Facebook or LinkedIn file for a company, normalize date format."""
    platform = platform.lower()
    if platform not in {"facebook", "linkedin"}:
        raise ValueError("Platform must be 'facebook' or 'linkedin'")

    filename = f"{company_name.lower()}_{platform}.xlsx"
    path = os.path.join(DATA_ROOT, "social_media", filename)

    if not os.path.exists(path):
        return None

    try:
        df = pd.read_excel(path, sheet_name=0)
    except Exception as e:
        st.error(f"[Social] Error loading {platform} data for {company_name}: {e}")
        return None

    # Normalize datetime column
    if "Published Date" not in df.columns:
        if "date_posted" in df.columns:
            df["Published Date"] = pd.to_datetime(df["date_posted"], utc=True, errors="coerce").dt.tz_localize(None)
        else:
            st.warning(f"No recognizable date column in {filename}")
            return None
    else:
        df["Published Date"] = pd.to_datetime(df["Published Date"], utc=True, errors="coerce").dt.tz_localize(None)

    return df

# ------------------------
# 🗃️ Load the Actual Volume 
# ------------------------

AGILITY_METADATA_PATH = os.path.join("data", "agility", "agility_metadata.xlsx")

def load_agility_volume_map():
    if os.path.exists(AGILITY_METADATA_PATH):
        return pd.read_excel(AGILITY_METADATA_PATH, index_col="Company").to_dict()["Volume"]
    else:
        return {}

# ------------------------
# 🗃️ Load All Brands' Social Media Data for a Platform
# ------------------------

def load_all_social_data(brands, platform: str):
    """Return dict[brand] = DataFrame for selected platform (e.g. Facebook)."""
    results = {}
    for brand in brands:
        df = load_social_data(brand, platform)
        if df is not None and not df.empty:
            results[brand] = df
    return results
