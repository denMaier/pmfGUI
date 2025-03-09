import streamlit as st
from stages.boundary.boundary import main
from state import get_selected_case_path, has_mesh

st.title("Boundary Conditions")

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
    main()
