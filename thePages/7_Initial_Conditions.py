import streamlit as st
import numpy as np
from state import *
from foamlib import FoamFieldFile

st.title("Initial Conditions")  # Change the title for each page
st.write("This page is under construction.")

case_dir = get_selected_case_path()
if case_dir is None:
    st.warning("Please select a case directory first.")
elif not case_dir.exists(): # Better safe than sorry
    st.warning("Case does not exist. Please try Case Selection again.")
elif not has_mesh():
    st.warning("Please create a mesh first.")
else:
    # Get the selected solver type and its fields
    solver_type = get_solver_type()
    fields = SOLVER_OPTIONS[solver_type]["fields"]
    for i, field in enumerate(fields):

        field_file = FoamFieldFile(Path(get_case()) / "0" / FIELD_REGIONS[field] / field)
        initial_field = field_file.internal_field
        if isinstance(initial_field, float):
            st.number_input(f"Initial Field for {field}",value=initial_field)
        else:
            st.text_input(f"Initial Field for {field}",value=' '.join(initial_field.astype("str")))
