# utils/config.py

import os

# Top-level folder where your data is stored
DATA_FOLDER = os.path.join("Tracking/data")  # or the actual path if it's "data sirin april"

# Brands to include in the dashboard
BRANDS = ["Swedbank", "Citadele", "Luminor", "SEB", "Artea"]

BRAND_NAME_MAPPING = {
    "arteagrupe": "Artea",
    "seb-lietuvoje": "SEB",
    "swedbanklietuvoje": "Swedbank",
    "citadele-bankas-lietuvoje": "Citadele",
    "luminorlietuva": "Luminor"
}