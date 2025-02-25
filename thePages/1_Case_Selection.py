import streamlit as st
from stages.case_selection import case_selection_stage
from state import initialize_state, set_case, get_selected_case

initialize_state()  # Call the initialization function

st.title("Case Selection")  # Page title
case_selection_stage()  # Call your stage function

if get_selected_case() is not None:
    set_case(get_selected_case())