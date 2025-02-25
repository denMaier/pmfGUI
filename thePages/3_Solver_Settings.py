import streamlit as st
from stages.solver_settings import entry, get_solver_state_from_case
from state import get_selected_case, get_solver_type
import os

st.header("Stage 2: Solver Settings")

case_dir = get_selected_case()

if case_dir is None:
    st.warning("Please select a case directory first.")
elif not os.path.exists(case_dir):
    st.warning("Case does not exist. Please try Case Selection again.")
else:
    st.write(f"Selected Case Directory: {case_dir}")

    if get_solver_type() is None:
        get_solver_state_from_case()

    entry()