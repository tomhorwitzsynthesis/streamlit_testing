# sections/content_pillars.py

import streamlit as st
import pickle
from utils.config import BRAND_NAME_MAPPING

def render():
    try:
        with open('Tracking/data/content_pillars/content_pillar_outputs.pkl', 'rb') as f:
            content_pillar_outputs = pickle.load(f)

        st.subheader("🏛️ Content Pillar Analysis")

        if not content_pillar_outputs:
            st.warning("No analysis data found.")
            return

        # Map keys to display names
        brand_keys = list(content_pillar_outputs.keys())
        display_names = [BRAND_NAME_MAPPING.get(key, key) for key in brand_keys]
        brand_display_map = dict(zip(display_names, brand_keys))

        selected_display = st.selectbox("Select Brand", display_names)
        selected_key = brand_display_map[selected_display]
        data = content_pillar_outputs[selected_key]

        if isinstance(data, str):
            st.error(data)
            return

        for theme in data:
            st.header(theme['theme'])

            for share in theme['shares']:
                st.markdown(f"**Share:** {share}")

            for post in theme['posts']:
                st.markdown(f"**Post:** {post}")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Subtopics")
                for subtopic in theme['subtopics']:
                    st.markdown(f"**{subtopic['subtopic']}**: {subtopic['description']}")

            with col2:
                st.subheader("Examples")
                for example in theme['examples']:
                    st.markdown(f"- {example}")

    except Exception as e:
        st.error("🚨 Failed to load content pillar analysis.")
        st.exception(e)
