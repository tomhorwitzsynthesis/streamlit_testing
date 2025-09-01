# utils/config.py

import os

# Top-level folder where your data is stored
DATA_ROOT = os.path.join("Kauno grudai","data")
# DATA_ROOT = os.path.join("data")

# Brands to include in the dashboard (normalized display names)
BRANDS = ["Acme", "Ignitis", "Kauno grūdai", "SBA", "Thermo Fisher"]

# Map various source variants to normalized display names used across the app
BRAND_NAME_MAPPING = {
    # Normalized names map to themselves
    "Acme": "Acme",
    "Ignitis": "Ignitis",
    "Kauno grūdai": "Kauno grūdai",
    "SBA": "SBA",
    "Thermo Fisher": "Thermo Fisher",
    # Short codes seen in agility/composition filenames
    "Kaun": "Kauno grūdai",
    "Thermo": "Thermo Fisher",
    # Lithuanian/long variants (Facebook and PR sources)
    "Acme grupė": "Acme",
    "Ignitis grupė": "Ignitis",
    "Kauno Grūdai": "Kauno grūdai",
    "SBA grupė": "SBA",
    "Thermo Fisher Scientific": "Thermo Fisher",
    # LinkedIn slugs
    "acme-grupe": "Acme",
    "ignitis-grupe": "Ignitis",
    "kauno-grudai": "Kauno grūdai",
    "sba-invent-everyday": "SBA",
    "thermo-fisher-scientific": "Thermo Fisher",
}

# Platform-specific helpers (optional, for convenience in sections)
# Map platform-specific identifiers to normalized names
FACEBOOK_NAME_TO_BRAND = {
    "Acme grupė": "Acme",
    "Ignitis grupė": "Ignitis",
    "Kauno Grūdai": "Kauno grūdai",
    "SBA grupė": "SBA",
    "Thermo Fisher Scientific": "Thermo Fisher",
}

LINKEDIN_SLUG_TO_BRAND = {
    "acme-grupe": "Acme",
    "ignitis-grupe": "Ignitis",
    "kauno-grudai": "Kauno grūdai",
    "sba-invent-everyday": "SBA",
    "thermo-fisher-scientific": "Thermo Fisher",
}

# Brand colors keyed by normalized display names
BRAND_COLORS = {
    "Acme": "#4083B3",
    "Ignitis": "#2FB375",
    "Kauno grūdai": "#FF0E0E",
    "SBA": "#FF9896",
    "Thermo Fisher": "#BECFE6",

}
