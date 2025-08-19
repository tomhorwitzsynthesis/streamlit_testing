# utils/config.py

import os

# Top-level folder where your data is stored
DATA_ROOT = os.path.join("Artea", "data")

# Brands to include in the dashboard
# BRANDS = ["Swedbank", "Citadele", "Luminor", "SEB", "Artea"]
BRANDS = ["Swedbank", "Citadele", "Luminor", "SEB", "Artea"]

BRAND_NAME_MAPPING = {
    "Artea": "Artea",
    "SEB Lietuvoje": "SEB",
    "Swedbank Lietuvoje": "Swedbank",
    "Citadele bankas": "Citadele",
    "Luminor Lietuva": "Luminor"

}

