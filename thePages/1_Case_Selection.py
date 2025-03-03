import streamlit as st
from stages.case_selection import main, load_state
from state import *
from stages.solver_settings import get_solver_state_from_case

initialize_state()  # Call the initialization function

st.title("Case Selection")  # Page title
main()  # Call your stage function

case_dir = get_selected_case_path()
if case_dir is not None:
    if not case_dir.exists():
        st.error("Selected case does not exist")
    elif st.button("Reload Case"): #better safe than sorry
        load_state(case_dir)
else:
    st.warning("No case selected")
