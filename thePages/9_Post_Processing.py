from pathlib import Path

import streamlit as st

from alpha_runtime import get_post_processing_path, list_time_directories
from state import get_selected_case_path


st.title("Post Processing")
st.warning("Post-processing actions are experimental and disabled in alpha.")
st.caption("The alpha build focuses on setup plus solver launch. This page stays read-only so you can inspect passive case outputs.")

case_dir = get_selected_case_path()
if case_dir is None:
    st.warning("Please select a case directory first.")
elif not case_dir.exists():
    st.warning("Case does not exist. Please try Case Selection again.")
else:
    post_processing_path = get_post_processing_path(case_dir)
    time_dirs = list_time_directories(case_dir)

    st.caption(f"Case path: {case_dir}")
    st.caption(f"postProcessing path: {post_processing_path}")

    if time_dirs:
        st.write("Available time directories:")
        st.code("\n".join(time_dirs), language="text")
    else:
        st.info("No OpenFOAM time directories were found yet.")

    if post_processing_path.exists():
        children = sorted(child.name for child in Path(post_processing_path).iterdir())
        if children:
            st.write("Current postProcessing entries:")
            st.code("\n".join(children), language="text")
        else:
            st.info("The postProcessing directory exists but is empty.")
    else:
        st.info("No postProcessing directory exists for this case yet.")
