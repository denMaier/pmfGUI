import streamlit as st
from stages.mechanical import main_mechanical
from stages.hydraulics import main_hydraulic
from state import *
from pathlib import Path

st.title("Materials")

case_dir = get_selected_case_path()

if case_dir is None:
    st.warning("Please select a case directory first.")
elif not case_dir.exists():
    st.error("Selected case does not exist")
elif not has_mesh():
    st.warning("Please create a mesh first.")
else:
    foamCase = get_case()
    solver = get_solver_type()

    st.write(f"Selected Case Directory: {case_dir}")

    tabnames = [solver]
    if solver == "Coupled":
        tabnames = ["Mechanics","Groundwater"]

    tabs = st.tabs(tabnames)

    if solver in ["Mechanics","Coupled"]:

        with tabs[tabnames.index("Mechanics")]:
            col1, col2 = st.columns(2)

            with col1:
                main_mechanical(foamCase)
            with col2:
                with get_file('mechanicalProperties').open() as f:
                    with st.expander("Current mechanicalProperties"):
                        st.code(f.read(),language="cpp")

    if solver in ["Groundwater","Coupled"]:
        with tabs[tabnames.index("Groundwater")]:
            col1, col2 = st.columns(2)

            with col1:
                main_hydraulic(foamCase)
            with col2:
                with get_file('poroHydraulicProperties').open() as f:
                    with st.expander("Current poroHydraulicProperties"):
                        st.code(f.read(),language="cpp")
