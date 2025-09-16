# === Configuration ===
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_TOKEN")   # Set in .env file or environment variable

TIMEZONE = "Europe/Vilnius"
DAYS_BACK = 14            # today + yesterday
MAX_ADS = 50
MAX_WORKERS = 8          # number of parallel scraping threads

# === PATH CONFIGURATION ===
# Choose your deployment setup:
# Option 1: For direct repository root deployment (current setup)
# MASTER_XLSX = "./data/ads_master_file.xlsx"
# SUMMARIES_XLSX = "./data/summaries.xlsx"

# Option 2: For "Akropolis Ad Updates" folder deployment
MASTER_XLSX = "./Akropolis_Ad_Updates/data/ads_master_file.xlsx"
SUMMARIES_XLSX = "./Akropolis_Ad_Updates/data/summaries.xlsx"

# Uncomment the option you want to use and comment out the other

# === GPT Labeling Configuration ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")     # Set in .env file or environment variable
GPT_MAX_WORKERS = 20    # number of parallel GPT API calls
ENABLE_GPT_LABELING = True  # Set to False to skip GPT labeling
ENABLE_WEEKLY_SUMMARIES = True  # Set to False to skip weekly summary generation

URLS = [
    "https://www.facebook.com/ozas.lt/",
    "https://www.facebook.com/panorama.lt/",
    "https://www.facebook.com/MAXIMALT/",
    "https://www.facebook.com/lidllietuva/?locale=lt_LT",
    "https://www.facebook.com/RimiLietuva/",
    "https://www.facebook.com/PrekybosTinklasIKI/",
    "https://www.facebook.com/akropolis.vilnius/",
    "https://www.facebook.com/kaunoakropolis/?locale=lt_LT",
    "https://www.facebook.com/akropolis.klaipeda/",
    "https://www.facebook.com/akropolis.siauliai/",
    "https://www.facebook.com/vilniusoutlet/?locale=lt_LT",
    "https://www.facebook.com/outletparklietuva/",
    "https://www.facebook.com/CUPprekyboscentras/",
    "https://www.facebook.com/nordika.lt/",
    "https://www.facebook.com/bigvilnius/",
    "https://www.facebook.com/pceuropa.lt/",
    "https://www.facebook.com/G9shoppingcenter/",
    "https://www.facebook.com/saulesmiestas/?locale=lt_LT",
    "https://www.facebook.com/MOLAS.Klaipeda/",
    "https://www.facebook.com/Mega.lt/"
    ]



# Columns to uniquely identify an ad (as you specified)
DEDUP_KEYS = [
    "pageID",
    "adArchiveID",
    "startDateFormatted"
]
