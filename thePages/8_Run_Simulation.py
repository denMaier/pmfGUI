import streamlit as st
from state import *
from render_inputs import *

st.title("Run Simulation")  # Change the title for each page
st.write("This page is under construction.")

case_dir = get_selected_case_path()
if case_dir is None:
    st.warning("Please select a case directory first.")
elif not case_dir.exists():  # Better safe than sorry
    st.warning("Case does not exist. Please try Case Selection again.")
elif not has_mesh():
    st.warning("Please create a mesh first.")
else:
    # Get the selected solver type and its fields
    tabs = st.tabs(["Settings", "Run"])
    with tabs[0]:
        controlDict = get_case().control_dict
        for key, value in controlDict.as_dict().items():
            render_input_element(key,value)
