import os
import pandas as pd
import streamlit as st
from utils.config import DATA_ROOT  # <-- import here
from utils.config import BRAND_NAME_MAPPING

# ------------------------
# 📄 Load Agility (News)
# ------------------------
@st.cache_data
def load_agility_data(company_name: str):
    """Load PR data for a brand.

    Strategy:
    1) Prefer consolidated file data/agility/full_pr.xlsx filtering by Brand variants
    2) Fallback to brand-specific compos files if present
    """
    agility_dir = os.path.join(DATA_ROOT, "agility")

    # Helper: all variants that map to this normalized brand
    normalized = BRAND_NAME_MAPPING.get(company_name, company_name)
    variants = [normalized] + [k for k, v in BRAND_NAME_MAPPING.items() if v == normalized]

    def _normalize_brand_key(text: str) -> str:
        if not isinstance(text, str):
            return ""
        t = text.strip().lower().replace("-", " ").replace("_", " ")
        t = " ".join(t.split())
        # basic accent folding for LT characters
        replacements = {
            "ū": "u", "ė": "e", "š": "s", "ž": "z", "ą": "a", "ę": "e", "į": "i", "č": "c", "į": "i", "Ū": "u",
        }
        for k, v in replacements.items():
            t = t.replace(k, v)
        return t

    normalized_key = _normalize_brand_key(normalized)
    variant_keys = {_normalize_brand_key(v) for v in variants}

    # Option A: consolidated file
    full_path = os.path.join(agility_dir, "full_pr.xlsx")
    if os.path.exists(full_path):
        try:
            xls = pd.ExcelFile(full_path)
            target_sheet = "Raw Data" if "Raw Data" in xls.sheet_names else xls.sheet_names[0]
            df = pd.read_excel(xls, sheet_name=target_sheet)
            # Filter by Brand variants if a brand/company column exists
            brand_col = "company"
            for c in df.columns:
                cname = str(c).strip().lower()
                if "brand" in cname or "company" in cname:
                    brand_col = c
                    break
            if brand_col is not None:
                df = df.copy()
                df["__brand_key__"] = df[brand_col].astype(str).map(_normalize_brand_key)
                df = df[df["__brand_key__"].isin(variant_keys)].copy()
                df = df.drop(columns=["__brand_key__"], errors="ignore")
        except Exception as e:
            st.error(f"[Agility] Error loading consolidated PR data: {e}")
            df = None
        if df is not None:
            # Normalize Published Date column if needed
            if "Published Date" not in df.columns:
                for candidate in ["PublishedDate", "published_date", "Date", "date"]:
                    if candidate in df.columns:
                        df = df.rename(columns={candidate: "Published Date"})
                        break
            return df

    # Option B: brand-specific compos files, attempt flexible matching
    if not os.path.isdir(agility_dir):
        return None
    try:
        candidate_files = [f for f in os.listdir(agility_dir) if f.lower().endswith("_compos_analysis.xlsx") and not f.startswith("~$")]
        # Pick files whose base name contains a token mapping to our brand
        matched = None
        for f in candidate_files:
            base = f.replace("_compos_analysis.xlsx", "").replace(".xlsx", "")
            # If this base (or title-case, lower-case) maps to our normalized brand, accept
            mapped = BRAND_NAME_MAPPING.get(base, BRAND_NAME_MAPPING.get(base.title(), base))
            if mapped == normalized:
                matched = os.path.join(agility_dir, f)
                break
        if matched is None:
            # Try simple heuristics for Kaun/Thermo
            simple_map = {
                "Kaun": "Kauno grūdai",
                "Thermo": "Thermo Fisher",
            }
            for f in candidate_files:
                base = f.replace("_compos_analysis.xlsx", "").replace(".xlsx", "")
                if simple_map.get(base) == normalized:
                    matched = os.path.join(agility_dir, f)
                    break
        if matched:
            try:
                xls = pd.ExcelFile(matched)
                target_sheet = "Raw Data" if "Raw Data" in xls.sheet_names else xls.sheet_names[0]
                df = pd.read_excel(xls, sheet_name=target_sheet)
            except Exception as e:
                st.error(f"[Agility] Error loading {company_name} from {os.path.basename(matched)}: {e}")
                return None
            # Normalize Published Date column if needed
            if "Published Date" not in df.columns:
                for candidate in ["PublishedDate", "published_date", "Date", "date"]:
                    if candidate in df.columns:
                        df = df.rename(columns={candidate: "Published Date"})
                        break
            return df
    except Exception:
        pass

    return None

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

AGILITY_METADATA_PATH = os.path.join(DATA_ROOT, "agility", "agility_metadata.xlsx")

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
	# Build potential roots: configured root, module-relative root, and CWD/data
	module_dir = os.path.dirname(os.path.abspath(__file__))
	project_root = os.path.abspath(os.path.join(module_dir, os.pardir))
	module_data_root = os.path.join(project_root, "data")
	cwd_data_root = os.path.join(os.getcwd(), "data")
	roots = [DATA_ROOT, module_data_root, cwd_data_root]

	candidate_filenames = [
		"ads.xlsx",
		"ads_scraping.xlsx",
		"ads_scraping (2).xlsx",
		"ads_scraping_LP.xlsx",
	]

	candidate_paths = []
	for root in roots:
		candidate_paths.extend([os.path.join(root, "ads", fname) for fname in candidate_filenames])

	# Deduplicate while preserving order
	seen = set()
	candidate_paths = [p for p in candidate_paths if not (p in seen or seen.add(p))]

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
		# Fallbacks commonly seen in exports
		for alt in ["reach", "estimated_audience_size", "eu_total_reach"]:
			if alt in df.columns:
				df["reach"] = pd.to_numeric(df[alt], errors="coerce")
				break
		else:
			df["reach"] = 0

	# Brand and flags
	if "pageName" in df.columns:
		df["brand"] = df["pageName"]
	elif "page_name" in df.columns:
		df["brand"] = df["page_name"]
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
def load_audience_affinity_outputs(source: str = "pr"):
	"""Load audience affinity outputs for a given source ('pr' or 'linkedin').

	Returns a dict with keys:
	- 'summary_df': pandas.DataFrame
	- 'gpt_summary': Optional[str]

	Handles pickles that either store a dict or directly a DataFrame.
	"""
	source = (source or "pr").strip().lower()
	filename_by_source = {
		"pr": "audience_affinity_outputs_pr.pkl",
		"linkedin": "audience_affinity_outputs_linkedin.pkl",
	}

	filename = filename_by_source.get(source)
	if filename is None:
		st.error(f"[Audience Affinity] Unknown source '{source}'. Use 'pr' or 'linkedin'.")
		return None

	path = os.path.join(DATA_ROOT, "audience_affinity", filename)
	if not os.path.exists(path):
		st.warning(f"Audience affinity outputs not found for source '{source}'.")
		return None
	try:
		import pickle
		with open(path, 'rb') as f:
			obj = pickle.load(f)

		# Normalize structure
		if isinstance(obj, dict):
			result = dict(obj)
			summary_df = result.get("summary_df")
			if summary_df is None:
				# try to find any DataFrame value in the dict
				for v in result.values():
					if isinstance(v, pd.DataFrame):
						summary_df = v
						break
				if summary_df is None:
					st.error("[Audience Affinity] Loaded data but could not find a summary DataFrame.")
					return None
			result["summary_df"] = summary_df
			result.setdefault("gpt_summary", None)
			return result
		elif isinstance(obj, pd.DataFrame):
			return {"summary_df": obj, "gpt_summary": None}
		else:
			st.error("[Audience Affinity] Unsupported data format in pickle file.")
			return None
	except Exception as e:
		st.error(f"[Audience Affinity] Error loading outputs for '{source}': {e}")
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
