# utils/config.py

import os

# Top-level folder where your data is stored
DATA_ROOT = os.path.join("data")

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

BRAND_COLORS = {
    "Swedbank Lietuvoje": "#4083B3",  # Plotly Blue
    "SEB Lietuvoje":      "#2FB375",  # Teal/Green
    "Luminor Lietuva":    "#FF0E0E",  # Plotly Orange-Red
    "Citadele bankas":    "#FF9896",  # Light Red / Pink
    "Artea":              "#BECFE6",  # Light Blue
}