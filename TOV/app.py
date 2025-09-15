"""
app.py — Streamlit UI for the LLM Copy POC.

Pages:
- Editor: paste text, add instructions, pick tone/length, generate/regen/copy/like.
- History: per-project generations, restore, liked filter.
- Tone Admin: edit/save guidelines.
- Export/Import: export current project or import JSON.

Environment:
  OPENAI_API_KEY must be set.
  LLM_MODEL (optional, defaults to "gpt-4").
"""
import streamlit as st
from pathlib import Path
import json

from storage import (
    load_state, persist_and_return,
    get_guidelines, update_guidelines,
    list_projects, create_project, set_current_project, get_current_project,
    add_generation, list_generations, toggle_like, list_liked,
    export_project_to_file, import_project_from_file
)
from prompting import build_prompts
from llm import generate

st.set_page_config(page_title="LLM Copy POC", layout="wide")

STATE = load_state()

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Editor", "History", "Tone Admin", "Export/Import"])

# Project selection
st.sidebar.markdown("---")
projects = list_projects(STATE)
cur_proj = get_current_project(STATE)
sel_proj = st.sidebar.selectbox("Project", projects, index=projects.index(cur_proj))
if sel_proj != cur_proj:
    STATE = set_current_project(STATE, sel_proj)
    STATE = persist_and_return(STATE)

new_name = st.sidebar.text_input("New project name")
if st.sidebar.button("Create project") and new_name.strip():
    STATE = create_project(STATE, new_name.strip())
    STATE = persist_and_return(STATE)
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.write(f"Guidelines version: {get_guidelines(STATE)[1]}")

# ---------------- Editor ----------------
if page == "Editor":
    st.header("Editor")
    source_text = st.text_area("Source text (leave blank to create new)", height=150)
    instructions = st.text_area("Specific instructions (optional)", height=100)
    tone_level = st.slider("Guideline adherence", 0, 3, 1, format="%d", 
                          help="0 = Keep original text mostly intact, 3 = Apply guidelines very strictly")
    length_code = st.selectbox("Copy length", ["short", "medium", "long"], index=1)

    if st.button("Generate"):
        g_content, _, _ = get_guidelines(STATE)
        spec = build_prompts(
            guidelines=g_content,
            source_text=source_text,
            instructions=instructions,
            tone_level=tone_level,
            length_code=length_code,
        )
        resp = generate(spec.system, spec.user, params=spec.params, model="gpt-4o")
        STATE = add_generation(
            STATE,
            source=source_text,
            instr=instructions,
            tone=tone_level,
            length=length_code,
            out=resp["text"],
        )
        STATE = persist_and_return(STATE)
        st.session_state["last_output"] = resp["text"]

    if "last_output" in st.session_state:
        st.subheader("Latest output")
        st.text_area("Generated text", st.session_state["last_output"], height=200)
        if st.button("Copy to clipboard"):
            st.code(st.session_state["last_output"])
        if st.button("Regenerate"):
            # re-run with same inputs
            g_content, _, _ = get_guidelines(STATE)
            spec = build_prompts(
                guidelines=g_content,
                source_text=source_text,
                instructions=instructions,
                tone_level=tone_level,
                length_code=length_code,
            )
            resp = generate(spec.system, spec.user, params=spec.params, model="gpt-4o")
            STATE = add_generation(
                STATE,
                source=source_text,
                instr=instructions,
                tone=tone_level,
                length=length_code,
                out=resp["text"],
            )
            STATE = persist_and_return(STATE)
            st.session_state["last_output"] = resp["text"]

# ---------------- History ----------------
elif page == "History":
    st.header(f"History — {get_current_project(STATE)}")
    gens = list_generations(STATE)
    if not gens:
        st.info("No generations yet.")
    else:
        for g in reversed(gens):
            st.markdown(f"**{g['ts']}** — Tone {g['tone']} — {g['length']}")
            with st.expander("View"):
                st.text_area("Output", g["out"], height=150)
                if st.button("Toggle like", key=f"like-{g['id']}"):
                    STATE = toggle_like(STATE, g["id"])
                    STATE = persist_and_return(STATE)
        st.markdown("---")
        st.subheader("Liked texts")
        liked = list_liked(STATE)
        for g in liked:
            st.text_area(f"Liked: {g['ts']}", g["out"], height=100)

# ---------------- Tone Admin ----------------
elif page == "Tone Admin":
    st.header("Tone of Voice Guidelines")
    content, ver, updated = get_guidelines(STATE)
    txt = st.text_area("Edit guidelines", content, height=400)
    if st.button("Save guidelines"):
        STATE = update_guidelines(STATE, txt)
        STATE = persist_and_return(STATE)
        st.success("Guidelines updated.")

# ---------------- Export/Import ----------------
elif page == "Export/Import":
    st.header("Export or Import Projects")
    exp_path = Path(f"export_{get_current_project(STATE)}.json")
    if st.button("Export current project"):
        export_project_to_file(STATE, exp_path)
        with exp_path.open("rb") as f:
            st.download_button("Download export", f, file_name=exp_path.name)

    st.subheader("Import project")
    file = st.file_uploader("Choose JSON file")
    if file is not None:
        temp = Path("import_tmp.json")
        temp.write_bytes(file.read())
        STATE, new_name = import_project_from_file(STATE, temp)
        STATE = persist_and_return(STATE)
        st.success(f"Imported as project '{new_name}'.")
