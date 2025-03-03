import streamlit as st
from stages.solver_settings import main, get_solver_state_from_case
from state import *
import os

st.header("Stage 2: Solver Settings")

case_dir = get_selected_case_path()

if case_dir is None:
    st.warning("Please select a case directory first.")
elif not case_dir.exists(): #Better safe than sorry
    st.warning("Case does not exist. Please try Case Selection again.")
else:
    st.write(f"Selected Case Directory: {case_dir}")

    main()
