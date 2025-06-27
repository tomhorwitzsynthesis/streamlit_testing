import streamlit as st
import streamlit.components.v1 as components

# Embedding the HTML/JS code
html_code = """
<script type="text/javascript" src="https://ssl.gstatic.com/trends_nrtr/4116_RC01/embed_loader.js"></script> <script type="text/javascript"> trends.embed.renderExploreWidget("GEO_MAP", {"comparisonItem":[{"keyword":"Akropolis","geo":"LT","time":"2025-04-20 2025-06-01"}],"category":0,"property":""}, {"exploreQuery":"date=2025-04-20%202025-06-01&geo=LT&q=Akropolis&hl=en","guestPath":"https://trends.google.com:443/trends/embed/"}); </script>
"""

# Use Streamlit components to render the HTML
components.html(html_code, height=600)
