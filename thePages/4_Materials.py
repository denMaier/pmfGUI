import streamlit as st
from alpha_runtime import collect_missing_paths
from stages.mechanical import main_mechanical
from stages.hydraulics import main_hydraulic
from state import *

st.title("Materials")

case_dir = get_selected_case_path()

if case_dir is None:
    st.warning("Please select a case directory first.")
elif not case_dir.exists():
    st.error("Selected case does not exist")
elif not has_mesh():
    st.warning("Please create a mesh first.")
else:
    missing_paths = collect_missing_paths(case_dir, ["physicsProperties", "mechanicalProperties", "poroHydraulicProperties"])
    if missing_paths:
        st.error("This case is missing required material files:")
        st.code("\n".join(str(path) for path in missing_paths), language="text")
        st.stop()

    foamCase = get_case()
    solver = get_solver_type()

    st.caption(f"Case path: {case_dir}")
    st.caption(f"Mechanical save path: {case_dir / 'constant/solid/mechanicalProperties'}")
    st.caption(f"Hydraulic save path: {case_dir / 'constant/poroFluid/poroHydraulicProperties'}")

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
                with open(get_file('mechanicalProperties'),'r') as f:
                    with st.expander("Current mechanicalProperties"):
                        st.code(f.read(),language="cpp")

    if solver in ["Groundwater","Coupled"]:
        with tabs[tabnames.index("Groundwater")]:
            col1, col2 = st.columns(2)

            with col1:
                main_hydraulic(foamCase)
            with col2:
                with open(get_file('poroHydraulicProperties'),'r') as f:
                    with st.expander("Current poroHydraulicProperties"):
                        st.code(f.read(),language="cpp")
