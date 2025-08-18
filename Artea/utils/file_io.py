import os
import pandas as pd
import streamlit as st

DATA_ROOT = "Artea/data"

# ------------------------
# 📄 Load Agility (News)
# ------------------------
@st.cache_data
def load_agility_data(company_name: str):
    path = os.path.join(DATA_ROOT, "agility", f"{company_name.lower()}_agility.xlsx")
    if not os.path.exists(path):
        return None
    try:
        xls = pd.ExcelFile(path)
        target_sheet = "Raw Data" if "Raw Data" in xls.sheet_names else xls.sheet_names[0]
        df = pd.read_excel(xls, sheet_name=target_sheet)
    except Exception as e:
        st.error(f"[Agility] Error loading {company_name}: {e}")
        return None

    # Normalize Published Date column if needed
    if "Published Date" not in df.columns:
        for candidate in ["PublishedDate", "published_date", "Date", "date"]:
            if candidate in df.columns:
                df = df.rename(columns={candidate: "Published Date"})
                break

    return df

# ------------------------
# 📱 Load Social Media Data
# ------------------------

@st.cache_data
def load_social_data(company_name: str, platform: str, use_consolidated: bool = True):
    """Load Facebook or LinkedIn file for a company, normalize date format.
    
    Args:
        company_name: Name of the company
        platform: 'facebook' or 'linkedin'
        use_consolidated: If True, load from consolidated files (linkedin_posts.xlsx/fb_posts.xlsx)
                         If False, load from individual company files
    """
    platform = platform.lower()
    if platform not in {"facebook", "linkedin"}:
        raise ValueError("Platform must be 'facebook' or 'linkedin'")

    if use_consolidated:
        # Load from consolidated files
        if platform == "linkedin":
            filename = "linkedin_posts.xlsx"
            company_col = "user_id"
        else:  # facebook
            filename = "fb_posts.xlsx"
            company_col = "user_username_raw"
        
        path = os.path.join(DATA_ROOT, "social_media", filename)
        
        if not os.path.exists(path):
            return None
            
        try:
            df = pd.read_excel(path, sheet_name=0)
            # Filter for the specific company
            if company_col in df.columns:
                df = df[df[company_col] == company_name].copy()
                if df.empty:
                    return None
            else:
                st.error(f"[Social] Company column '{company_col}' not found in {filename}")
                return None
        except Exception as e:
            st.error(f"[Social] Error loading {platform} data for {company_name}: {e}")
            return None
    else:
        # Load from individual company files (original behavior)
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
        elif "PublishedDate" in df.columns:
            df["Published Date"] = pd.to_datetime(df["PublishedDate"], utc=True, errors="coerce").dt.tz_localize(None)
        else:
            st.warning(f"No recognizable date column in {filename}. Available columns: {list(df.columns)}")
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

def load_all_social_data(brands, platform: str, use_consolidated: bool = False):
    """Return dict[brand] = DataFrame for selected platform (e.g. Facebook).
    
    Args:
        brands: List of brand names
        platform: 'facebook' or 'linkedin'
        use_consolidated: If True, load from consolidated files (linkedin_posts.xlsx/fb_posts.xlsx)
                         If False, load from individual company files
    """
    results = {}
    for brand in brands:
        df = load_social_data(brand, platform, use_consolidated=use_consolidated)
        if df is not None and not df.empty:
            results[brand] = df
    return results

# ------------------------
# 📢 Load Ads Intelligence data
# ------------------------

@st.cache_data
def load_ads_data():
    """
    Load ads scraping Excel and normalize key fields.
    Returns a pandas DataFrame or None if not found.
    """
    # Try common roots
    candidate_paths = [
        os.path.join(DATA_ROOT, "ads", "ads.xlsx"),
        os.path.join(DATA_ROOT, "ads", "ads_scraping.xlsx"),
        os.path.join(DATA_ROOT, "ads", "ads_scraping (2).xlsx"),
        os.path.join(DATA_ROOT, "ads", "ads_scraping.xlsx"),
    ]

    path = next((p for p in candidate_paths if os.path.exists(p)), None)
    if path is None:
        st.warning("Ads data file not found in expected locations.")
        return None

    try:
        df = pd.read_excel(path, sheet_name=0)
    except Exception as e:
        st.error(f"[Ads] Error loading ads data: {e}")
        return None

    # Normalize dates
    for col in ["startDateFormatted", "endDateFormatted"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True, errors="coerce").dt.tz_localize(None)

    # Normalize numeric reach
    reach_col = "ad_details/aaa_info/eu_total_reach"
    if reach_col in df.columns:
        df["reach"] = pd.to_numeric(df[reach_col], errors="coerce")
    else:
        df["reach"] = 0

    # Brand and flags
    if "pageName" in df.columns:
        df["brand"] = df["pageName"]
    if "isActive" in df.columns:
        df["isActive"] = df["isActive"].astype(bool)

    # Duration
    if "startDateFormatted" in df.columns and "endDateFormatted" in df.columns:
        df["duration_days"] = (df["endDateFormatted"] - df["startDateFormatted"]).dt.days

    return df

# ------------------------
# 🎯 Load Audience Affinity outputs (pickled)
# ------------------------

@st.cache_data
def load_audience_affinity_outputs():
    path = os.path.join(DATA_ROOT, "audience_affinity", "audience_affinity_outputs.pkl")
    if not os.path.exists(path):
        st.warning("Audience affinity outputs not found.")
        return None
    try:
        import pickle
        with open(path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        st.error(f"[Audience Affinity] Error loading outputs: {e}")
        return None

# ------------------------
# 🧱 Load Content Pillars outputs (pickled)
# ------------------------

@st.cache_data
def load_content_pillar_outputs():
    path = os.path.join(DATA_ROOT, "content_pillars", "content_pillar_outputs.pkl")
    if not os.path.exists(path):
        st.warning("Content pillar outputs not found.")
        return None
    try:
        import pickle
        with open(path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        st.error(f"[Content Pillars] Error loading outputs: {e}")
        return None


